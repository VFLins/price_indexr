from typing import List
from price_indexr import *
from interface import scan_products
from sqlalchemy import ForeignKey, Integer, create_engine, DateTime, insert, update, select
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, Session
from datetime import date, datetime, timedelta
from time import sleep

def time_and_execute():
    while True:
        prod_list = scan_products()
        update_time = datetime.now() - timedelta(days=7)

        for prod in prod_list:
            if prod["last_update"] <= update_time:
                collect_prices(prod["id"])
        sleep(900)

if __name__ == "scheduler":
    time_and_execute()

if __name__ == "__main__":
    print(scan_products())
