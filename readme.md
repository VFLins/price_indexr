   
# Description

Price_indexr is intended to get a set of product prices for a given simultaneous search on Google shopping and Bing shopping and store it locally. To ensure you will get only the desired results, you can filter what will be saved locally based on the title each individual product. This program can automatically update the price information for each product individually on a weekly basis.

### This branch: `Central` 

Features added to this branch:

- Targeted for collecting Graphics Cards prices
- Centralizes the prices for all different products in a single SQLite database
- Now it's much easier to schedule for the price collection of multiple products
- Filtering is simpler

### How can this help me?

This can be used to satisfy business and personal necessities, for monitoring your competitor's prices, help on calculating price indexes for specific types of products or monitoring the price of a product you want to buy.

# Requirements

- Python version 3.10 or superior
- Packages listed in [requirements.txt](https://github.com/VFLins/Price_indexr/blob/central/requirements.txt)

# How to use?

This version is intended to be used from [interface.py](https://github.com/VFLins/Price_indexr/blob/central/interface.py), this is a TUI (Text User Interface), where you can add new products to monitor.

To accommodate the initial need to obtain prices for GPUs from many different models and manufacturers, the products are organized into a two-level hierarchy.

1. In the **higher level** are the "product names", originally used to store the chip names
2. In the **lower level** are the "brand", "model" and "filters"
   - Filters are used to mark words that should not appear on the targeted product title
   - Hardcoded filters are added to reduce typing time
  
**To add a product for monitoring**: simply double-click `interface.py`, open with a python interpreter, and follow the instructions on the screen.

# See also:

- [Prind_Monitor:](https://github.com/VFLins/Prind_Monitor) Report generator for price data obtained by this piece of software, only compatible with SQLite databases for now. 
