from sqlalchemy import ForeignKey, Integer, create_engine, DateTime, insert
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, sessionmaker
import requests
import re
import os
from csv import writer, DictWriter
from datetime import date, datetime
from bs4 import BeautifulSoup
from sys import argv

# ERROR MANAGEMENT AND RESULTS FILTERING
def filtered_by_name(name_to_filter: str, pos_filters: list, neg_filters: list) -> bool:
    """
    Checks if the product title has every keyword it is supposed to have,
    and if it does NOT have the keywords it isn't supposed to have,
    with every test passed, return 'True'.
    """
    checks_up = False
    for word in pos_filters:
        if bool( re.search(word.lower(), name_to_filter.lower()) ): checks_up = True
        else: checks_up = False
        if not checks_up: break
    
    if len(neg_filters) > 0 and checks_up:
        for word in neg_filters:
            if not bool( re.search(word.lower(), name_to_filter.lower()) ): checks_up = True
            else: checks_up = False
            if not checks_up: break
    return checks_up

def write_message_log(error, message: str):
    # write 4 lines on the error message.
    with open("exec_log.txt", 'a+', newline='', encoding = "UTF8") as log_file:
        # 1. Time and table name
        log_file.write(f"\n[{str(datetime.now())}] {TABLE_NAME}\n")
        # 2 and 3. Message and Exception
        log_file.write(f"{message}:\n{error}\n")

def write_sucess_log(results: list):
    with open("exec_log.txt", 'a+', newline='', encoding = "UTF8") as log_file:
        # 1. Success message with time
        log_file.write(f"{TABLE_NAME} Successful execution. {str( len(results) )} entries added")

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

def handle_data_line():
    try:
        current_result = {
            "Date":Date, "Currency":strip_price_str(Price)[0], 
            "Price":strip_price_str(Price)[1], 
            "Name":Name, "Store":Store, "Url":Url}
        output_data.append(current_result)
    except IndexError:
        current_result = {
            "Date":Date, "Currency":None, 
            "Price":strip_price_str(Price)[0], 
            "Name":Name, "Store":Store, "Url":Url}
        output_data.append(current_result)
    except Exception as collect_error:
        write_message_log(collect_error, "Unexpected error collecting inline results:")

# DEFINE CONSTANTS
PRODUCT = argv[1]
SEARCH_FIELD = argv[2].lower()

# SORT FILTERS
try:
    # raise error if doesn't start with a positive filter
    if bool(re.match("-", SEARCH_FIELD)): raise TypeError
    SEARCH_KEYWORDS = {}
    SEARCH_KEYWORDS["negative"] = re.split(" -", SEARCH_FIELD)[1:]
    SEARCH_KEYWORDS["positive"] = re.split(" ", re.split(" -", SEARCH_FIELD)[0])
except TypeError as input_error:
    write_message_log(
        input_error, 
        "Your search should start with at least one positive filter and end with negative filters, if any")

POS_KEYWORDS_LOWER = [keyword.lower() for keyword in SEARCH_KEYWORDS["positive"]]
NEG_KEYWORDS_LOWER = [keyword.lower() for keyword in SEARCH_KEYWORDS["negative"]]
TABLE_NAME = POS_KEYWORDS_LOWER
SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))

# SETUP PLACE TO SAVE THE DATA 
class dec_base(DeclarativeBase): pass
DB_ENGINE = create_engine(f"sqlite:///{SCRIPT_FOLDER}\data\database.sqlite", echo=True)
#DB_SESSION = sessionmaker(bind=DB_ENGINE)
#DB_MSESSION = DB_SESSION()

class prices(dec_base):
    __tablename__ = "prices"
    Id: Mapped[int] = mapped_column(primary_key=True)
    ProductId: Mapped[int] = mapped_column(ForeignKey("products.Id"))
    Product: Mapped[List["products"]] = relationship(back_populates="Product")
    Model: Mapped[str] = mapped_column()
    Date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    Currency: Mapped[str] = mapped_column()
    Price: Mapped[float] = mapped_column()
    Name: Mapped[str] = mapped_column()
    Store: Mapped[str] = mapped_column()
    Url: Mapped[str] = mapped_column()

class products(dec_base):
    __tablename__ = "products"
    Id: Mapped[int] = mapped_column(primary_key=True)
    Product: Mapped["prices"] = relationship(back_populates="Product")
    Created: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    LastUpdate: Mapped[datetime] = mapped_column(DateTime(timezone=True))


dec_base.metadata.create_all(DB_ENGINE)

def write_results(results):
    DB_ENGINE.connect().execute(prices.insert(), results)
    """
    trow_line = current_table(
        Date = row["Date"],
        Currency = row["Currency"],
        Price = row["Price"],
        Name = row["Name"],
        Store = row["Store"],
        Url = row["Url"]
    )
    DB_MSESSION.add(trow_line)
    DB_MSESSION.commit()
    """

dec_base.metadata.create_all(DB_ENGINE)

# COLLECT DATA

SEARCH_HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.121 Safari/537.36"}

BING_SEARCH_PARAMS = {"q" : SEARCH_FIELD}
BING_SEARCH_RESPONSE = requests.get(
    "https://www.bing.com/shop",
    params = BING_SEARCH_PARAMS,
    headers = SEARCH_HEADERS)

GOOGLE_SEARCH_PARAMS = {"q" : SEARCH_FIELD, "tbm" : "shop"}
GOOGLE_SEARCH_RESPONSE = requests.get(
    "https://www.google.com/search",
    params = GOOGLE_SEARCH_PARAMS,
    headers = SEARCH_HEADERS)

### Ensure data was collected
try:
    try_con = 1
    maximum_try_con = 10
    while try_con <= maximum_try_con:
        
        soup_google = BeautifulSoup(GOOGLE_SEARCH_RESPONSE.text, "lxml")
        google_grid = soup_google.find_all("div", {"class": "sh-dgr__content"})
        google_inline = soup_google.find_all("a", {"class": "shntl sh-np__click-target"})

        soup_bing = BeautifulSoup(BING_SEARCH_RESPONSE.text, "lxml")
        bing_grid = soup_bing.find_all("li", {"class": "br-item"})
        bing_inline = soup_bing.find_all("div", {"class": "slide"})

        if ((len(google_grid)+len(google_inline) > 0) and (len(bing_grid)+len(bing_inline) > 0)):
            write_message_log(
                f"Using {len(google_grid)+len(google_inline)} results from google, and {len(bing_grid)+len(bing_inline)} from bing",
                f"Connection was successful after trying {try_con} times")
            break
        
        try_con = try_con + 1
        if try_con > maximum_try_con: raise ConnectionError("Maximum number of connection tries exceeded")
except TimeoutError as connection_error:
    write_message_log(connection_error, 
        "Couldn't obtain data, check your internet connection or User-Agent used on the source code.")
    quit()
except Exception as unexpected_error:
    write_message_log(unexpected_error, "Unexpected error, closing connection...")
    quit()

### Structure results into a list of dictionaries
output_data = []
Date = date.today()

for result in google_grid:
    Name = result.find("h3", {"class":"tAxDx"}).get_text()
    if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): continue

    #Price = result.find("span", {"class" : "a8Pemb OFFNJ"}).get_text().split("\xa0")
    Price = result.find("span", {"class" : "a8Pemb"}).get_text()
    Store = result.find("div", {"class" : "aULzUe IuHnof"}).get_text()
    #Store = result.find("div", {"data-mr" : True})["data-mr"]
    Url = f"https://www.google.com{result.find('a', {'class' : 'xCpuod'})['href']}"
    handle_data_line()

for result in google_inline:
    Name = result.find("h3", {"class" : "sh-np__product-title"}).get_text()
    if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): continue

    Price = result.find("b", {"class" : "translate-content"}).get_text()
    Store = result.find("span", {"class" : "E5ocAb"}).get_text()
    Url = f"https://shopping.google.com{result['href']}"
    handle_data_line()

for result in bing_grid:
    name_block = result.find("div", {"class" : "br-pdItemName"}) 
    if name_block.has_attr('title'): Name = name_block["title"]
    else: Name = name_block.get_text()
    if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): continue

    Price = result.find("div", {"class" : "pd-price"}).get_text()
    Store = result.find("span", {"class" : "br-sellersCite"}).get_text()
    Url = f"https://bing.com{result['data-url']}"
    handle_data_line()

for result in bing_inline:
    name_block = result.find("span", {"title" : True})
    Name = name_block["title"]
    if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): continue

    Price = result.find("div", {"class": "br-price"}).get_text()
    Store = result.find("span", {"class": "br-offSlrTxt"}).get_text()
    Url = result.find("a", {"class": "br-offLink"})["href"]
    handle_data_line()

# SAVE
try:
    write_results(output_data)
    write_sucess_log(output_data)
except Exception as save_error:
    write_message_log(save_error, "Unexpected error while trying to save the data:")
