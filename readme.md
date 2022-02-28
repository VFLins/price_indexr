# Description

Price_indexr is intended to get a set of product prices for a given search on google shopping and store it in a database.

This process migh be automated by [cron](https://cron-job.org/en/) to schedule new data over time.

This can be used to satisfy business and personal necessities, for stablishing market prices, calculating price indexes for specific types of products or monitoring the price of a product you want to buy.

# Requirements

- Linux/Unix operating system
    - [cron/anacron](https://cron-job.org/en/) or [cronitor](https://cronitor.io) installed
- [Bash CLI](http://tiswww.case.edu/php/chet/bash/bashtop.html)
- Python version 3.8 or superior and packages:
    - [bs4](https://pypi.org/project/beautifulsoup4/)
    - [sqlalchemy]()
    - [requests](https://pypi.org/project/requests/)
    - [sepapi](https://pypi.org/project/googlesearch-python/)

# How to use?

**Currently this project is under construction, and not working properly**

The intended usage is on a bash terminal, to create a schedule:

```
PYTHON_PATH = "<path to your python installation>"
SCRIPT_PATH = "<path to price_indexr.py>"
DB_CON = "your database connection string" #or ".csv" to save in a text file in the same folder of your script
cron -e
@monthly PYTHON_PATH SCRIPT_PATH DB_CON "my product search"
```

If a database was selected to store the data, a table called "price_indexr-my_product_search" will be created in the database on the first execution. Next executions will append new data to the same table. If you preferred a text file, the name of the file will follow the same naming pattern.
