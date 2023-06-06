   
# Description

Price_indexr is intended to get a set of product prices for a given simultaneous search on Google shopping and Bing shopping and store it locally. To ensure you will get only the desired results, you can filter what will be saved locally based on the title each individual product. This program can be prompted manually, or scheduled to run by other softwares like [cron](https://cron-job.org/en/), or Windows's task scheduler.

### This branch: **`Central`**

Features added to this branch:

- Centralizes the prices for all different products in a single SQLite database
- Now it's much easier to schedule for the price collection of multiple products
- Filtering and scheduling are made simpler

### How can this help me?

This can be used to satisfy business and personal necessities, for stablishing market prices, help on calculating price indexes for specific types of products or monitoring the price of a product you want to buy.

# Requirements

- Python version 3.10 or superior
    - Packages listed in [requirements.txt](https://github.com/VFLins/Price_indexr/blob/central/requirements.txt)

# How to use?

This version is intended to be used from [interface.py](https://github.com/VFLins/Price_indexr/blob/central/interface.py), this is a TUI (Text User Interface), where you can add new products to monitor, and do some other things that we will see next.

## Adding the first product

The first thing that we'll need to do is run `interface.py`, type "`c`" and follow the instructions. Once all the steps are followed throughly, `price_indexr.py` will be called for the first time for this product, and you will be able to find a new folder with a new file inside (`data/database.db`) holding the new data that you just added!

This is enough to have prices to the product you want stored in a database, but you can also schedule for new price collections. Once you registered a product, you can use `scheduler.pyw`. On windows, you can set the python interpreter as the default program to open this kind of file, and then use [Windows Task Scheduler](https://www.wintips.org/how-to-start-a-program-at-startup-with-task-scheduler/) to run this every time the computer starts.

Once you've registered your product names and set the scheduler to run every time your computer starts, you will get new prices for the last 

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
