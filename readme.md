   
# Description

Price_indexr is intended to get a set of product prices for a given simultaneous search on Google shopping and Bing shopping and store it locally. To ensure you will get only the desired results, you can filter what will be saved locally based on the title each individual product. This program can be prompted manually, or scheduled to run by other softwares like [cron](https://cron-job.org/en/), or Windows's task scheduler.

### This branch: `Central` 

Features added to this branch:

- Centralizes the prices for all different products in a single SQLite database
- Now it's much easier to schedule for the price collection of multiple products
- Filtering is simpler

### How can this help me?

This can be used to satisfy business and personal necessities, for stablishing market prices, help on calculating price indexes for specific types of products or monitoring the price of a product you want to buy.

# Requirements

- Python version 3.10 or superior
- Packages listed in [requirements.txt](https://github.com/VFLins/Price_indexr/blob/central/requirements.txt)

<details>
    <summary> <b>Recommended for scheduling</b> </summary>
    
For macOS/Unix operating systems:
- [Bash](http://tiswww.case.edu/php/chet/bash/bashtop.html)
- [cron/anacron](https://cron-job.org/en/) or [cronitor](https://cronitor.io) installed

For Windows operating systems:
- [PowerShell](https://docs.microsoft.com/pt-br/powershell/scripting/overview?view=powershell-7.2)
- [Windows Task Scheduler](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)
    
</details>

# How to use?

This version is intended to be used from [interface.py](https://github.com/VFLins/Price_indexr/blob/central/interface.py), this is a TUI (Text User Interface), where you can add new products to monitor, and some other things.

```
python price_indexr.py "<Database connection string or '.csv'>" "my product search" "<location code [optional]>"
```

This will use python to run the ```price_indexr.py``` script with 3 different arguments in order:
1. A connection string to a database supported by SQLAlchemy on it's [Included Dialects](https://docs.sqlalchemy.org/en/14/dialects/#included-dialects), or simply ".csv" to save in a text file;
2. A search that you would type on google's search field. Must be inside quotes or double qutoes if it contains more than one word;
3. [Optional] A location code for the country (e.g. "us" for the United States, or "pt-br" for Brazil). If not included, google search engine will guess the country by the IP address that you are using.

### How the search works?

The search results could come with a lot of similar products that doesn't meet your expectations. For that reason, every word you type in the search argument is a filter, Price_indexr works with two kinds of filters:

1. **Positive:** this filter contains every word that you demand to be in the title of the product. This also will be used to fill the google shopping's search bar.
2. **Negative:** this filter contains every word that you demand ***NOT*** to be in the title of the product. This will never be used to fill the google shopping's search bar, as it would bring more unwanted results.

So your search would look like: `"gtx 1660 -pc -notebook"`*

In the example above, "gtx" and "1660" are positive filters and "pc" and "notebook" are negative. In this case you want to search the "gtx 1660" graphics card's price, but as the results might bring unwanted computers and notebooks that comes with this graphics card equiped, you should use negative filters such as those to avoid adding them to your database. The positive filters would naturally prevent you from getting similar graphics cards such as "gtx 1650" and ensuring you get data only from the desired model.

 *Note that positive filters should **always** come first.

### Scheduling on Unix/macOS with Bash

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

### Scheduling on Windows with PowerShell

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
    
# Troubleshooting

1. Depending on the user-agent, the results may or not appear for Price_indexr, usually, changing the user-agent on the line 125 of the script will solve the problem.

# See also:

- [Prind_Monitor:](https://github.com/VFLins/Prind_Monitor) Report generator for price data obtained by this piece of software, only compatible with SQLite databases for now. 
