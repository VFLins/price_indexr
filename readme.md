# Description

Price_indexr is intended to get a set of product prices for a given search on google shopping and store it in a database. It will return up to 20 results, and "NA" if no product is found at the moment.

This process migh be automated by [cron](https://cron-job.org/en/) to schedule new data over time.

This can be used to satisfy business and personal necessities, for stablishing market prices, calculating price indexes for specific types of products or monitoring the price of a product you want to buy.

# Requirements

- Python version 3.8 or superior and packages:
    - [bs4](https://pypi.org/project/beautifulsoup4/)
    - [sqlalchemy]()
    - [requests](https://pypi.org/project/requests/)
    - [sepapi](https://pypi.org/project/googlesearch-python/)

For Linux/Unix operating systems:
- [Bash CLI](http://tiswww.case.edu/php/chet/bash/bashtop.html)
- [cron/anacron](https://cron-job.org/en/) or [cronitor](https://cronitor.io) installed
For Windows operating systems:
- 

# How to use?

**Currently this project is under construction, and not working properly**

The intended usage is on a terminal, to create a schedule:

### Linux/Unix with Bash

With 'python' on the bin folder:

```
SCRIPT_PATH="<path to price_indexr.py>"
DB_CON="<your database connection string>" 
# or ".csv" to save in a text file in the same folder of your script instead of a database

crontab -e
@monthly python "$SCRIPT_PATH" "$DB_CON" "my product search"
# To check the schedules made:
crontab -l
```
### Windows with PowerShell

With 'python3' added to PATH:

```
$SCRIPT_PATH = "<path to price_indexr.py>"
$DB_CON = "<your database connection string>" 

$price_indexr_action = New-ScheduledTaskAction 
    -Execute "python3 $SCRIPT_PATH $DB_CON 'my product search'"
$monthly = New-ScheduledTaskTrigger -Monthly -At 0:00am
$task_<unique name> = Register-ScheduledTask 
    -Action $price_indexr_action
    -Trigger $monthly 
    -TaskName "<unique name>" 
    -Description "<Your Description>"
$task_<unique name> | Set-ScheduledTask
```

If a database was selected to store the data, a table called "price_indexr-my_product_search" will be created in the database on the first execution. Next executions will append new data to the same table. If you preferred a text file, the name of the file will follow the same naming pattern.
