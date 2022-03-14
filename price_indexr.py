import sqlalchemy as alch
import requests
import re
#import json
from csv import writer, DictWriter
from datetime import datetime
from bs4 import BeautifulSoup
from os.path import isfile
from sys import argv

# DEFINE CONSTANTS
DB_CON = argv[1]
SEARCH_FIELD = argv[2]
if len(argv) >= 4:
    LOCATION_CODE = argv[3]

SEARCH_KEYWORDS = SEARCH_FIELD.split(" ")

SEARCH_KEYWORDS_LOWER = [keyword.lower() for keyword in SEARCH_KEYWORDS]
TABLE_NAME = "price_indexr-" + "_".join(SEARCH_KEYWORDS_LOWER)

# ERROR MANAGEMENT
def write_error_log(error, message):
    # write 3 lines on the error message.
    with open("error_log.csv", 'a+', newline='', encoding = "UTF8") as log_file:
        # 1. Time and tablename
        log_file.write(str(datetime.now()) + " - " + TABLE_NAME + "\n")
        # 2. Message and Exception
        log_file.write(message + ": " + error + "\n")
        # 3. Break line
        log_file.write("\n")

def write_sucess_log(results):
    with open("error_log.csv", 'a+', newline='', encoding = "UTF8") as log_file:
        # 1. Success message with time
        log_file.write("Successfully executed at: " + str(datetime.now()))
        # 2. Number of entries added
        log_file.write(str( len(results) ) + " entries added")
        # 3. Break line
        log_file.write("\n")

# SETUP PLACE TO SAVE THE DATA 
if DB_CON.upper() == ".CSV":
    CSV_FILENAME = TABLE_NAME + ".csv"

    def write_results_csv(results):
        # 'results' must be a list of lists that are ordered as 'fields' in this next line:
        fields = ["Date", "Currency", "Price", "Name", "Store", "Url"]
        # write results
        with open(CSV_FILENAME, "a+", newline="", encoding = "UTF8") as write_file:
            for row in results:
                DictWriter(write_file, fieldnames=fields).writerow(row)

else:
    DB_DECBASE = alch.declarative_base()
    DB_ENGINE = alch.create_engine(DB_CON)
    DB_SESSION = alch.sessionmaker(bind = DB_ENGINE)
    DB_MSESSION = DB_SESSION()

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
    
    def write_results_db(results):
        for row in results:
            trow_line = prices_table(
                Date = row[0],
                Currency = row[1],
                Price = row[2],
                Name = row[3],
                Store = row[4],
                Url = row[5]
            )
            DB_MSESSION.add(trow_line)
            DB_MSESSION.commit()
    
# COLLECT DATA

### Ensure data was collected
try:
    for try in range(10):
        SEARCH_HEADERS = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.121 Safari/537.36"
        }
        SEARCH_PARAMS = {"q" : SEARCH_FIELD, "tbm" : "shop", "hl" : "en"}
        if len(argv) >= 4: SEARCH_PARAMS["hl"] = LOCATION_CODE

        SEARCH_RESPONSE = requests.get(
            "https://www.google.com/search",
            params = SEARCH_PARAMS,
            headers = SEARCH_HEADERS
        )
        sopa = BeautifulSoup(SEARCH_RESPONSE.text, "lxml")
        sopa_grid = sopa.find_all("div", {"class": "sh-dgr__gr-auto sh-dgr__grid-result"})
        sopa_inline = sopa.find_all("a", {"class": "shntl sh-np__click-target"})

        if len(sopa_grid) > 0 and len(sopa_inline) > 0:
            break
except Exception as connection_error:
    write_error_log(connection_error, "Não foi possível obter dados, verifique a conexão ou seu User-Agent.")

# SAVE

print( len(sopa_grid), len(sopa_inline) )

# to inspect the html:
#with open("html_sopa.txt", "w") as kekeke:
#        kekeke.writelines( f"\n {sopa}" )
