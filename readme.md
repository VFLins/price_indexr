# Description

### What it does?

Price_indexr is intended to get a set of product prices for a given search on google shopping and store it in a database or a .csv file. It will return up to 20 results, if no product is found at the moment it will register a message in a text file in the same folder as the script. It is recomended to automate this task to be performed periodically with [cron](https://cron-job.org/en/) to schedule new data over time.

### How can this help me?

This can be used to satisfy business and personal necessities, for stablishing market prices, help on calculating price indexes for specific types of products or monitoring the price of a product you want to buy.

# Requirements

- Python version 3.8 or superior and packages:
    - [bs4](https://pypi.org/project/beautifulsoup4/)
    - [sqlalchemy](https://pypi.org/project/SQLAlchemy/)
    - [requests](https://pypi.org/project/requests/)

<details>
    <summary> Recommended for scheduling </summary>
    
For macOS/Unix operating systems:
- [Bash](http://tiswww.case.edu/php/chet/bash/bashtop.html)
- [cron/anacron](https://cron-job.org/en/) or [cronitor](https://cronitor.io) installed

For Windows operating systems:
- [PowerShell](https://docs.microsoft.com/pt-br/powershell/scripting/overview?view=powershell-7.2)
- [Windows Task Scheduler](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)
    
</details>

# How to use?

***Currently this project is under construction, and not working properly (~~maybe not working at all~~)***

The intended usage is on a terminal:

```
python price_indexr.py "<Database connection string or '.csv'>" "my product search" "<location code [optional]>"
```

This will use python to run the ```price_indexr.py``` script with 3 different arguments on order:
1. A connection string to a database supported by SQLAlchemy on it's [Included Dialects](https://docs.sqlalchemy.org/en/14/dialects/#included-dialects), or simply ".csv" to save in a text file;
2. A search that you would type on google's search field. Must be inside quotes or double qutoes if it contains more than one word;
3. [Optional] A location code for the country (e.g. "us" for the United States, or "pt-br" for Brazil). If not included, google search engine will guess the country by the IP address that you are using.


To create a schedule:

### Unix/macOS with Bash

<details>
    <summary> Example of automation with crontab </summary>

    ```
    PYTHON_PATH="<path to desired python interpreter>"
    SCRIPT_PATH="<path to price_indexr.py>"
    DB_CON="<your database connection string>" 
    # or ".csv" to save in a text file in the same folder of your script instead of a database

    crontab -e
    @monthly "$PYTHON_PATH" "$SCRIPT_PATH" "$DB_CON" "my product search"
    # To check the schedules made:
    crontab -l
    ```
</details> 

### Windows with PowerShell

<details>
    <summary> Example of automation with Windows Task Scheduler </summary>

    ```
    $PYTHON_PATH = "<path to desired python interpreter>"
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
</details>

If a database was selected to store the data, a table called "price_indexr-my_product_search" will be created in the database on the first execution. Next executions will append new data to the same table. If you preferred a text file, the name of the file will follow the same naming pattern.
