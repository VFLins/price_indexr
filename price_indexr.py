from typing import List, Tuple, Dict
import logging
from sqlalchemy import ForeignKey, Integer, create_engine, DateTime, insert, update, select
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, Session
from httpx import AsyncClient, TimeoutException
import asyncio
import re
import os
from os.path import split, join
from datetime import date, datetime
from bs4 import BeautifulSoup
from sys import argv


SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
DATA_FOLDER = SCRIPT_FOLDER + "\\data"
os.makedirs(DATA_FOLDER, exist_ok=True)
SEARCH_HEADERS = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76"}

# ===================== #
# DATABASE ARCHITECTURE #
# ===================== #
DB_ENGINE = create_engine(f"sqlite:///{SCRIPT_FOLDER}\\data\\database.db", echo=False)
class dec_base(DeclarativeBase): pass

class product_names(dec_base):
    __tablename__ = "product_names"
    Name: Mapped["products"] = relationship(back_populates="Name")

    Id: Mapped[int] = mapped_column(primary_key=True)
    ProductName: Mapped[str] = mapped_column()

class prices(dec_base):
    __tablename__ = "prices"
    Product: Mapped[List["products"]] = relationship(back_populates="Product")

    Id: Mapped[int] = mapped_column(primary_key=True)
    ProductId: Mapped[int] = mapped_column(ForeignKey("products.Id"))
    Date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    Currency: Mapped[str] = mapped_column()
    Price: Mapped[float] = mapped_column()
    Name: Mapped[str] = mapped_column()
    Store: Mapped[str] = mapped_column()
    Url: Mapped[str] = mapped_column()

class products(dec_base):
    __tablename__ = "products"
    Product: Mapped["prices"] = relationship(back_populates="Product")
    Name: Mapped[List["product_names"]] = relationship(back_populates="Name")

    Id: Mapped[int] = mapped_column(primary_key=True)
    NameId: Mapped[int] = mapped_column(ForeignKey("product_names.Id"))
    ProductName: Mapped[str] = mapped_column()
    ProductModel: Mapped[str] = mapped_column()
    ProductBrand: Mapped[str] = mapped_column()
    ProductFilters: Mapped[str] = mapped_column()
    Created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    LastUpdate: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
dec_base.metadata.create_all(DB_ENGINE)


# =============== #
# LOGGING HANDLER #
# =============== #

class LocalLogger():
    """Generate an ephemeral logger inside the function scope."""
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        self.handler = logging.FileHandler(filename=join(SCRIPT_FOLDER, "exec_log.txt"))
        self.formatter = logging.Formatter(
            fmt="%(levelname)s [%(asctime)s] - %(name)s :: %(message)s\n"
        )

        self.handler.setFormatter(self.formatter)
        self.handler.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)
        self.logger.propagate = False

    def debug(self, message):
        """Log a `debug` level message"""
        self.logger.debug(msg=message)

    def info(self, message):
        """Log a `info` level message"""
        self.logger.info(msg=message)

    def warn(self, message):
        """Log a `warning` level message"""
        self.logger.warn(msg=message)

    def error(self, message):
        """Log a `error` level message"""
        self.logger.error(msg=message)

    def critical(self, message):
        """Log a `critical` level message"""
        self.logger.critical(msg=message)


# ================ #
# MANAGE RESPONSES #
# ================ #
        
class SearchResponses:
    def __init__(
            self, 
            google_inline: AsyncClient.get,
            google_grid: AsyncClient.get,
            bing_inline: AsyncClient.get,
            bing_grid: AsyncClient.get,
            product: products,
            filter_kws: dict
        ):

        self.google_inline = google_inline
        self.google_grid = google_grid
        self.bing_inline = bing_inline
        self.bing_grid = bing_grid
        self.product = product
        self.filter_kws = filter_kws

        self.results = []

    def _error_amount_handler(
            self, 
            error_msg: str, current_amount: int, max_amount: int = 5
        ):
        pass

    def _parse_google_inline(self):
        log = LocalLogger("SearchResponses._parse_google_inline")
        if not self.google_inline:
            log.error("No `google_inline` element found, skipping...")
            return

        for result in self.google_inline:
            error_count = 0
            try:
                line = {}
                Name = result.find("h3", {"class": "sh-np__product-title translate-content"}).get_text()

                if not filtered_by_name(Name, self.filter_kws): 
                    continue

                Price = strip_price_str( result.find("b", {"class" : "translate-content"}).get_text() )
                
                url_complement = result.find('a', {"class": "shntl sh-np__click-target"}).attrs["href"]
                line["Url"] = f"https://google.com{url_complement}"
                line["Name"] = Name
                line["Date"] = datetime.now()
                line["Store"] = result.find("span", {"class" : "E5ocAb"}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = self.product.Id
        
                self.results.append(prices(**line))

            except Exception as google_inline_faliure:
                log.critical(
                    f"Prod. ID: {self.product.Id}. Could not parse:\n{result}"+
                    f"\nReason: {google_inline_faliure}")
                error_count = error_count + 1

                if error_count > 5:
                    log.debug("Exiting for amount of erros")
                    return


# ===== #
# UTILS #
# ===== #

def validate_integer_input(inp: int) -> products:
    """
    Validates an integer input and retrieves a product from the database.

    ### Args:
        inp (`int`): The input value to validate.

    ### Returns:
        `products`: The product retrieved from the database.

    ### Raises:
        `ValueError`: If the input cannot be converted to an integer.
        `IndexError`: If the specified ID is not found in the database.
    """
    log = LocalLogger(f"validate_integer_input '{inp}'")

    try:
        inp = int(inp)
    except ValueError:
        log.error("Input must be of type `int` or coercible to `int`")
        raise ValueError
    
    try:
        with Session(DB_ENGINE) as ses:
            stmt = select(products).where(products.Id == inp)
            curr_product = ses.execute(stmt).scalar_one()
    except Exception as not_found_id_error:
        log.error(f"database returned an error: {not_found_id_error}")
        raise IndexError

    return curr_product


def generate_filters(product: products) -> Tuple[str, Dict[str, list]]:
    """
    ### Filters handling:

    1. retrieve from `product`:
        `'pc,personal_computer,something,foo,foo_bar'`

    2. split on commas:
        `['pc','personal_computer','something','foo','foo_bar']`

    3. underscores become spaces:
        `['pc','personal computer','something','foo','foo bar']`

    ### Args:
        product (`products`): A row retrieved from database of class `products`

    ### Returns:
        A `tuple` containing:
            `str` the product's full name (brand, name, and model)
            `dict` of filters with two keys: `'negative'` and `'positive'`
    """
    log = LocalLogger(f"generate_filters {product}")

    try:
        product_fullname = f"{product.ProductBrand} {product.ProductName} {product.ProductModel}"
        posf = re.split(" ", product_fullname)
        hard_negf = ["Usado", "Used", "Pc", "Computador", "Ventoinhas", "Ventilador",
                    "Fan", "Cooler", "Notebook", "Bloco De Água", "Water Block"]
        negf = set(re.split(",", product.ProductFilters.replace(" ", "")) + hard_negf)

        keywords = {}
        keywords["negative"] = [x.replace("_", " ") for x in negf]
        keywords["positive"] = [x.replace("_", " ") for x in posf]
    except Exception as generate_filters_error:
        log.error(generate_filters_error)
        raise Exception
    
    return product_fullname, keywords


# =========== #
# GATHER DATA #
# =========== #
def collect_search(q: str):
    BING_PARAMS = {"q" : q}
    GOOGLE_PARAMS = {"q" : q, "tbm" : "shop"}
    
def collect_prices(CURR_PROD_ID):

    try:
        curr_product = validate_integer_input(CURR_PROD_ID)
        SEARCH_FIELD, SEARCH_KEYWORDS = generate_filters(curr_product)
    except Exception:
        return

    # COLLECT DATA

    results = collect_search(q=SEARCH_FIELD)
    def connect():
        

        

        URLS = ["https://www.bing.com/shop", "https://www.google.com/search"]
        PARAMS = [BING_PARAMS, GOOGLE_PARAMS]
        METAS = zip(URLS, PARAMS)
        
        async def request_webpage():
            async with AsyncClient() as client:
                try:
                    ets = (client.get(url, params=param, headers=SEARCH_HEADERS) for url, param in METAS)
                except TimeoutException as timeout:
                    write_message_log(
                        timeout, 
                        "Connection timed out, skiping...", 
                        SEARCH_FIELD, CURR_PROD_ID
                    )
                    return
                return await asyncio.gather(*ets)
    
        BING_RESPONSE, GOOLGE_RESPONSE = asyncio.run(request_webpage())

        ### Ensure data was collected
        try:
            try_con = 1
            maximum_try_con = 10
            while try_con <= maximum_try_con:
                
                soup_google = BeautifulSoup(GOOLGE_RESPONSE.text, "lxml")
                google_grid = soup_google.find_all("div", {"class": "sh-dgr__content"})
                google_inline = soup_google.find_all("div", {"class": "KZmu8e"})
                google_highlight = soup_google.find("div", {"class": "_-oX"}) # might bring up to 3 results but will count as 1

                soup_bing = BeautifulSoup(BING_RESPONSE.text, "lxml")
                bing_grid = soup_bing.find_all("li", {"class": "br-item"})
                bing_inline = soup_bing.find_all("div", {"class": "slide", "data-appns": "commerce", "tabindex": True})

                google_n_results = len(google_grid) + len(google_inline)
                if google_highlight:
                    google_n_results = google_n_results + len(google_highlight)
                bing_n_results = len(bing_grid) + len(bing_inline)

                if ((google_n_results > 0) and (bing_n_results > 0)):
                    break
                
                try_con = try_con + 1
                if try_con > maximum_try_con: raise ConnectionError("Maximum number of connection attempts exceeded")
        except TimeoutError as connection_error:
            write_message_log(
                connection_error, 
                "Couldn't obtain data, check your internet connection or User-Agent used on the source code.",
                SEARCH_FIELD, prod_id=CURR_PROD_ID
            )
            quit()
        except Exception as unexpected_error:
            write_message_log(
                unexpected_error, "Unexpected error, closing connection...", 
                SEARCH_FIELD, prod_id=CURR_PROD_ID
            )
            quit()
        return (
            google_grid, 
            google_inline, 
            google_highlight, 
            bing_grid, 
            bing_inline, 
            google_n_results, 
            bing_n_results, 
            try_con
        )

    ### Structure results into a list sqlalchemy insert statements
    def gather():
        google_grid, google_inline, google_highlight, bing_grid, bing_inline, google_n_results, bing_n_results, try_con = connect()
        try:
            output_data = []
            filtered = 0
            Date = datetime.now()
            
            for result in google_grid:
                line = {}
                Name = result.find("h3", {"class": "tAxDx"}).get_text()
                if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): 
                    filtered = filtered + 1
                    continue
                Price = strip_price_str( result.find("span", {"class" : "a8Pemb"}).get_text() )

                line["Url"] = f"https://www.google.com{result.find('a', {'class' : 'xCpuod'})['href']}"
                line["Name"] = Name
                line["Date"] = Date
                line["Store"] = result.find("div", {"class" : "aULzUe IuHnof"}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = CURR_PROD_ID

                output_data.append(prices(**line))
        except Exception as google_grid_faliure:
            write_message_log(
                google_grid_faliure, 
                "Unexpected error while trying to collect prices from `google_grid`", 
                SEARCH_FIELD, prod_id=CURR_PROD_ID
            )
        
        try:
            if not google_inline:
                raise IndexError("No `google_inline` element found, skipping...")
            for result in google_inline:
                
                line = {}
                Name = result.find("h3", {"class": "sh-np__product-title translate-content"}).get_text()
                if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): 
                    filtered = filtered + 1
                    continue
                Price = strip_price_str( result.find("b", {"class" : "translate-content"}).get_text() )
                
                url_complement = result.find('a', {'class': 'shntl sh-np__click-target'}).attrs['href']
                line["Url"] = f"https://google.com{url_complement}"
                line["Name"] = Name
                line["Date"] = Date
                line["Store"] = result.find("span", {"class" : "E5ocAb"}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = CURR_PROD_ID
        
                output_data.append(prices(**line))

        except Exception as google_inline_faliure:
            write_message_log(
                google_inline_faliure, 
                "Unexpected error while trying to collect prices from `google_inline`", 
                SEARCH_FIELD, prod_id=CURR_PROD_ID
            )

        try:
            if  google_highlight:
                Name = google_highlight.find("a", {"class": " _-lC sh-t__title sh-t__title-popout shntl translate-content"}).get_text()
                line["Name"] = Name
                if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]):
                    for result in google_highlight.find_all("div", {"class": "_-oB"}):
                        
                        Price = strip_price_str(result.find("span", {"class": "_-p5 _-p1"}).get_text())
                        line["Url"] = f"https://google.com/{result.find('a', {'href': True})['href']}"
                        line["Date"] = Date
                        line["Store"] = result.find("div", {"class": "_-oH _-oF"}).get_text()
                        line["Price"] = Price[1]
                        line["Currency"] = Price[0]
                        line["ProductId"] = CURR_PROD_ID

                        output_data.append(prices(**line))
        
        except Exception as google_highlight_faliure:
            write_message_log(
                google_highlight_faliure, 
                "Unexpected error while trying to collect prices from `google_highlight`", 
                SEARCH_FIELD, prod_id=CURR_PROD_ID
            )

        try:
            for result in bing_grid:
                line = {}
                try:
                    name_block = result.find("div", {"class": "br-pdItemName"})
                    Name = name_block.get_text()
                except Exception as bing_grid_name_collection_fail:
                    write_message_log(
                        result, "Problem collecting `Name` from `bing_grid`", 
                        bing_grid_name_collection_fail, prod_id=CURR_PROD_ID)
                    break

                if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): 
                    filtered = filtered + 1
                    continue
                Price = strip_price_str( result.find("div", {"class" : "pd-price"}).get_text() )
                
                line["Url"] = f"https://bing.com{result['data-url']}"
                line["Name"] = Name
                line["Date"] = Date
                line["Store"] = result.find("span", {"class" : "br-sellersCite"}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = CURR_PROD_ID
                
                output_data.append(prices(**line))

        except Exception as bing_grid_faliure:
            write_message_log(
                bing_grid_faliure, 
                "Unexpected error while trying to collect prices from `bing_grid`", 
                SEARCH_FIELD, prod_id=CURR_PROD_ID
            )

        try:
            for result in bing_inline:
                line = {}

                try:
                    name_block = result.find("span", {"title" : True})
                    Name = name_block["title"]
                except Exception as bing_inline_name_collection_fail:
                    write_message_log(
                        result, "Problem collecting `Name` from `bing_grid`", 
                        bing_inline_name_collection_fail, prod_id=CURR_PROD_ID
                    )
                    break

                if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): 
                    filtered = filtered + 1
                    continue
                Price = strip_price_str( result.find("div", {"class": "br-price"}).get_text() )

                line["Url"] = result.find("a", {"class": "br-offLink"})["href"]
                line["Name"] = Name
                line["Date"] = Date
                line["Store"] = result.find("span", {"class": "br-offSlrTxt"}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = CURR_PROD_ID

                output_data.append(prices(**line))
                
        except Exception as bing_inline_faliure:
            write_message_log(
                bing_inline_faliure, 
                "Unexpected error while trying to collect prices from `bing_grid`", 
                SEARCH_FIELD, CURR_PROD_ID
            )

        return (
            output_data, 
            Date,
            google_n_results, 
            bing_n_results, 
            try_con
        )

    # SAVE
    n_retries = 5
    for n_tries in range(n_retries):
        output_data, Date, google_n_results, bing_n_results, try_con = gather()
        n_results = len(output_data)
        if n_results > 0:
            try:
                write_results(output_data, CURR_PROD_ID, date = Date)
                write_message_log(
                        f"Using {google_n_results} results from google, and {bing_n_results} from bing",
                        f"Connection was successful after trying {try_con} times",
                        SEARCH_FIELD=SEARCH_FIELD, prod_id=CURR_PROD_ID)
                write_sucess_log(output_data, SEARCH_FIELD=SEARCH_FIELD, n_retries=n_tries, prod_id=CURR_PROD_ID)
            except Exception as save_error:
                write_message_log(save_error, "Unexpected error while trying to save the data:", SEARCH_FIELD, CURR_PROD_ID)
            break
    else:
        write_message_log("no valid result found", "Couldn't collect prices", SEARCH_FIELD, CURR_PROD_ID)

# ERROR MANAGEMENT AND RESULTS FILTERING
def filtered_by_name(name_to_filter: str, pos_filters: list, neg_filters: list) -> bool:
    """
    Checks if the product title has every keyword it is supposed to have,
    and if it does NOT have the keywords it isn't supposed to have,
    with every test passed, return 'True'.
    """

    checks_up = False
    for word in pos_filters:
        # skip when word is an empty string
        if word == "": 
            continue
        # checks_up when the positive filter is found
        pos_filter_check = re.search(rf"\b{word.lower()}\b", name_to_filter.lower())
        if bool(pos_filter_check): 
            checks_up = True
        else: 
            checks_up = False
        if not checks_up: 
            break
    
    if len(neg_filters) > 0 and checks_up:
        for word in neg_filters:
            if word == "": 
                continue
            neg_filter_fail = re.search(rf"\b{word.lower()}\b", name_to_filter.lower())
            if not bool(neg_filter_fail): 
                checks_up = True
            else: 
                checks_up = False
            if not checks_up: 
                break
    return checks_up

def write_message_log(error, message: str, SEARCH_FIELD: str, prod_id: int):
    # write 4 lines on the error message.
    with open("exec_log.txt", 'a+', newline='', encoding = "UTF8") as log_file:
        # 1. Time and table name
        log_file.write(f"\n[{str(datetime.now())}] {prod_id} | {SEARCH_FIELD}\n")
        # 2 and 3. Message and Exception
        log_file.write(f"{message}:\n{error}\n")

def write_sucess_log(results: list, SEARCH_FIELD: str, n_retries: int, prod_id: int):
    with open("exec_log.txt", 'a+', newline='', encoding = "UTF8") as log_file:
        # 1. Success message with time
        log_file.write(f"[{prod_id} | {SEARCH_FIELD}] Successful execution: {str( len(results) )} entries added with {n_retries} retries\n")

def strip_price_str(price_str):
    price_str = price_str.replace("\xa0", " ")
    price_expr = r"[\d.,]*[,.]\d*"
    curr_expr = r"[^\d., ]*"
    dec_expr = r"[,.](?=[^,.]*$)"

    price = re.search(price_expr, price_str).group(0)
    curr = re.search(curr_expr, price_str).group(0)
    dec = re.search(dec_expr, price_str).group(0)

    if dec==",": price = float( price.replace(".", "").replace(",", ".") )
    elif dec==".": price = float( price.replace(",", "") )
    return [curr, price]

def write_results(results: list, CURR_PROD_ID: int, date: datetime):
    time_stmt = update(products).where(products.Id == CURR_PROD_ID).values(LastUpdate = datetime.now())
    with Session(DB_ENGINE) as ses:
        ses.add_all(results)
        ses.commit()
        ses.execute(time_stmt)
        ses.commit()
