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


# ========== #
# EXCEPTIONS #
# ========== #

class HtmlParseError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

# ================ #
# MANAGE RESPONSES #
# ================ #
        
class SearchResponses:
    def __init__(
            self, 
            google_inline: AsyncClient.get,
            google_grid: AsyncClient.get,
            google_highlight: AsyncClient.get,
            bing_inline: AsyncClient.get,
            bing_grid: AsyncClient.get,
            product: products,
            filter_kws: dict
        ):

        self.google_inline = google_inline
        self.google_grid = google_grid
        self.google_highlight = google_highlight
        self.bing_inline = bing_inline
        self.bing_grid = bing_grid
        self.product = product
        self.filter_kws = filter_kws

        self.product_name = f"{product.ProductBrand} {product.ProductModel} {product.ProductName}"
        self.Date = datetime.now()
        self.results = []


    def parse_all(self):
        log = LocalLogger("SearchResponses.parse_all")
        parsers = (p for p in [
            self._parse_google_inline,
            self._parse_google_grid,
            self._parse_google_highlight,
            self._parse_bing_inline,
            self._parse_bing_grid]
        )

        _errors: int = 5
        for parser in parsers:
            try:
                parser()
            except HtmlParseError:
                _errors = _errors - 1

                if _errors == 0:
                    results_amount = len(self.results)
                    log.error(f"(Product ID: {self.product.Id}) Skipping data parsing, too many errors")
                    
                    if results_amount == 0:
                        log.error(f"(Product ID: {self.product.Id}) No data collected")

                else: 
                    continue

        log.info(f"Parsed {len(self.results)} results for {self.product_name}")
                        

    def _parse_google_inline(self):
        log = LocalLogger("SearchResponses._parse_google_inline")
        if not self.google_inline:
            log.error("No `google_inline` element found, skipping...")
            return

        for result in self.google_inline:
            try:
                line = {}
                Name = result.find("h3", {"class": "sh-np__product-title translate-content"}).get_text()

                if not filtered_by_name(Name, self.filter_kws): 
                    continue

                Price = strip_price_str( result.find("b", {"class" : "translate-content"}).get_text() )
                
                url_complement = result.find('a', {"class": "shntl sh-np__click-target"}).attrs["href"]
                line["Url"] = f"https://google.com{url_complement}"
                line["Name"] = Name
                line["Date"] = self.Date
                line["Store"] = result.find("span", {"class" : "E5ocAb"}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = self.product.Id
        
                self.results.append(prices(**line))

            except Exception as google_inline_faliure:
                log.critical(
                    f"Prod. ID: {self.product.Id}. Could not parse:\n{result}"+
                    f"\nReason: {google_inline_faliure}")

                raise HtmlParseError(f"Error in _parse_google_inline")
                

    def _parse_google_grid(self):
        log = LocalLogger("SearchResponses._parse_google_grid")

        for result in self.google_grid:
            try:
                line = {}
                Name = result.find("h3", {"class": "tAxDx"}).get_text()

                if not filtered_by_name(Name, self.filter_kws): 
                    continue

                Price = strip_price_str( result.find("span", {"class" : "a8Pemb"}).get_text() )

                line["Url"] = f"https://www.google.com{result.find('a', {'class' : 'xCpuod'})['href']}"
                line["Name"] = Name
                line["Date"] = self.Date
                line["Store"] = result.find("div", {"class" : "aULzUe IuHnof"}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = self.product.Id

                self.results.append(prices(**line))

            except Exception as google_grid_faliure:
                log.critical(
                    f"Prod. ID: {self.product.Id}. Could not parse:\n{result}"+
                    f"\nReason: {google_grid_faliure}")

                raise HtmlParseError("Error in _parse_google_grid")
            
    
    def _parse_google_highlight(self):
        log = LocalLogger("SearchResponses._parse_google_highlight")

        if  self.google_highlight:
            try:
                Name = self.google_highlight.find("a", {"class": " _-lC sh-t__title sh-t__title-popout shntl translate-content"}).get_text()

                if not filtered_by_name(Name, self.filter_kws):
                    for result in self.google_highlight.find_all("div", {"class": "_-oB"}):
                        line = {}

                        line["Name"] = Name
                        Price = strip_price_str(result.find("span", {"class": "_-p5 _-p1"}).get_text())
                        line["Url"] = f"https://google.com/{result.find('a', {'href': True})['href']}"
                        line["Date"] = self.Date
                        line["Store"] = result.find("div", {"class": "_-oH _-oF"}).get_text()
                        line["Price"] = Price[1]
                        line["Currency"] = Price[0]
                        line["ProductId"] = self.product.Id

                        self.results.append(prices(**line))
            
            except Exception as google_highlight_faliure:
                log.critical(
                f"Prod. ID: {self.product.Id}. Could not parse:\n{result}"+
                f"\nReason: {google_highlight_faliure}")

                raise HtmlParseError("Error in _parse_google_higlight")


    def _parse_bing_inline(self):
        log = LocalLogger("SearchResponses._parse_bing_inline")

        for result in self.bing_inline:
            try:
                line = {}
                name_block = result.find("span", {"title" : True})
                Name = name_block["title"]

                if not filtered_by_name(Name, self.filter_kws): 
                    filtered = filtered + 1
                    continue
                Price = strip_price_str( result.find("div", {"class": "br-price"}).get_text() )

                line["Url"] = result.find("a", {"class": "br-offLink"})["href"]
                line["Name"] = Name
                line["Date"] = self.Date
                line["Store"] = result.find("span", {"class": "br-offSlrTxt"}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = self.product.Id

                self.results.append(prices(**line))

            except Exception as bing_inline_faliure:
                log.critical(
                    f"Prod. ID: {self.product.Id}. Could not parse:\n{result}"+
                    f"\nReason: {bing_inline_faliure}")
                
                raise HtmlParseError("Error in _parse_bing_inline")


    def _parse_bing_grid(self):
        log = LocalLogger()

        for result in self.bing_grid:
            try:
                line = {}
                name_block = result.find("div", {"class": "br-pdItemName"})
                Name = name_block.get_text()
                

                if not filtered_by_name(Name, self.filter_kws): 
                    filtered = filtered + 1
                    continue
                Price = strip_price_str( result.find("div", {"class" : "pd-price"}).get_text() )
                
                line["Url"] = f"https://bing.com{result['data-url']}"
                line["Name"] = Name
                line["Date"] = self.Date
                line["Store"] = result.find("span", {"class" : "br-sellersCite"}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = self.product.Id
                
                self.results.append(prices(**line))

            except Exception as bing_grid_faliure:
                log.critical(
                    f"Prod. ID: {self.product.Id}. Could not parse:\n{result}"+
                    f"\nReason: {bing_grid_faliure}")
                
                raise HtmlParseError("Error in _parse_bing_grid")

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

def collect_search(q: str, product: products, keywords: dict) -> SearchResponses:
    log = LocalLogger(f"collect_search: {q}")

    bing_params = {"q" : q}; google_params = {"q" : q, "tbm" : "shop"}

    urls = ["https://www.bing.com/shop", "https://www.google.com/search"]
    params = [bing_params, google_params]
    metas = zip(urls, params)

    async def request_webpage():
            async with AsyncClient() as client:
                try:
                    ets = (client.get(url, params=param, headers=SEARCH_HEADERS) for url, param in metas)

                except TimeoutException as timeout:
                    log.error("Connection timed out, skiping...")
                    return

                return await asyncio.gather(*ets)
            
    bing_response, google_response = asyncio.run(request_webpage())
    soup_bing = BeautifulSoup(bing_response.text, "lxml")
    soup_google = BeautifulSoup(google_response.text, "lxml")

    return SearchResponses(
        google_inline=soup_google.find_all("div", {"class": "KZmu8e"}),
        google_grid=soup_google.find_all("div", {"class": "sh-dgr__content"}),
        google_highlight=soup_google.find("div", {"class": "_-oX"}),
        bing_inline=soup_bing.find_all("div", {"class": "slide", "data-appns": "commerce", "tabindex": True}),
        bing_grid=soup_bing.find_all("li", {"class": "br-item"}),
        product=product,
        filter_kws=keywords
    )


def write_results(results: list) -> None:
    pass

    
def collect_prices(CURR_PROD_ID):
    log = LocalLogger("collect_prices")

    try:
        curr_product = validate_integer_input(CURR_PROD_ID)
        search_field, search_kewords = generate_filters(curr_product)
        responses = collect_search(
            q=search_field,
            keywords=search_kewords,
            product=curr_product
        )
        responses.parse_all()
        write_results(responses.results)

    except Exception as uncaught_exception:
        log.critical(f"Uncaught exception on {search_field}:\n{uncaught_exception}")
        return

        

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
