import sqlalchemy as alch
from sqlalchemy.ext.declarative import declarative_base
import requests
import re
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
        # 4. Blank line
        log_file.write("\n")

def write_sucess_log(results: list):
    with open("exec_log.txt", 'a+', newline='', encoding = "UTF8") as log_file:
        # 1. Success message with time
        log_file.write(f"[{str(datetime.now())}] {TABLE_NAME} Successful execution")
        # 2. Number of entries added
        log_file.write(f"\n{str( len(results) )} entries added")
        # 3. Blank line
        log_file.write("\n")

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
DB_CON = argv[1]
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
TABLE_NAME = f"price_indexr-{'_'.join(POS_KEYWORDS_LOWER)}"

# SETUP PLACE TO SAVE THE DATA 
if DB_CON.upper() == ".CSV":
    CSV_FILENAME = f"{TABLE_NAME}.csv"
    def write_results_csv(results):
        # 'results' must be a list of lists that are ordered as 'fields' in this next line:
        fields = ["Date", "Currency", "Price", "Name", "Store", "Url"]
        # write results
        with open(CSV_FILENAME, "a+", newline="", encoding = "UTF8") as write_file:
            for row in results:
                DictWriter(write_file, fieldnames=fields).writerow(row)

else:
    DB_DECBASE = declarative_base()
    DB_ENGINE = alch.create_engine(DB_CON)
    DB_SESSION = alch.orm.sessionmaker(bind = DB_ENGINE)
    DB_MSESSION = DB_SESSION()
    
    DB_METADATA = alch.MetaData()
    current_table = alch.Table(
        TABLE_NAME, DB_METADATA,
        alch.Column("Id", alch.Integer, primary_key = True),
        alch.Column("Date", alch.Date),
        alch.Column("Currency", alch.String),
        alch.Column("Price", alch.Float),
        alch.Column("Name", alch.String),
        alch.Column("Store", alch.String),
        alch.Column("Url", alch.String))
    DB_METADATA.create_all(DB_ENGINE, checkfirst = True)
    
    """
    class prices_table(DB_DECBASE):
        __tablename__ = TABLE_NAME
        Id = alch.Column(alch.Integer, primary_key = True)
        Date = alch.Column(alch.Date)
        Currency = alch.Column(alch.String)
        Price = alch.Column(alch.Float)
        Name = alch.Column(alch.String)
        Store = alch.Column(alch.String)
        Url = alch.Column(alch.String)

        def __repr__(self):
            return "<entry(Date={}, Currency={}, Price={}, Name={}, Store={}, Url={})>".format(
            self.Date, self.Currency, self.Price, self.Name, self.Store, self.Url)
    """

    def write_results_db(results):
        DB_ENGINE.connect().execute(
            current_table.insert(), results)
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
    Url = f"https://google.com{result['href']}"
    handle_data_line()

for result in bing_grid:
    name_block = result.find("div", {"class": "br-pdItemName"}) 
    if name_block.has_attr('title'): Name = name_block["title"]
    else: Name = name_block.get_text()
    if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): continue

    Price = result.find("div", {"class": "pd-price"}).string
    Store = result.find("span", {"class": "br-sellersCite"}).get_text()
    Url = f"https://bing.com{result['data-url']}"
    handle_data_line()

for result in bing_inline:
    name_block = result.find("div", {"class": "br-offTtl"}).find("span")
    if name_block.has_attr('title'): Name = name_block["title"]
    else: Name = name_block.get_text()
    if not filtered_by_name(Name, SEARCH_KEYWORDS["positive"], SEARCH_KEYWORDS["negative"]): continue

    Price = result.find("div", {"class": "br-price"}).string
    Store = result.find("span", {"class": "br-offSlrTxt"}).get_text()
    Url = result.find("a", {"class": "br-offLink"})["href"]
    handle_data_line()

# SAVE
try:
    if DB_CON.lower() == ".csv": write_results_csv(output_data)
    else: write_results_db(output_data)
    write_sucess_log(output_data)
except Exception as save_error:
    write_message_log(
        save_error,
        "Unexpected error while trying to save the data:")
