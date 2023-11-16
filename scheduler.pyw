from price_indexr import *
from interface import scan_products
from sqlalchemy import ForeignKey, Integer, create_engine, DateTime, insert, update, select
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, Session
from datetime import date, datetime, timedelta
from time import sleep

def time_and_execute():
    def collection_routine(product):
        try:
            collect_prices(product["id"])
        except Exception as expt:
            write_message_log(
                expt, "Unexpected error on collection routine:", 
                f"{product['brand']} {product['name']} {product['model']}",
                prod_id=product['id']
            )
            
            sleep(300)

    while True:
        prod_list = scan_products()
        update_time = datetime.now() - timedelta(days=3)

        for prod in prod_list:
            if prod["last_update"] <= update_time:
                collection_routine(product=prod)
        sleep(900)

if __name__ == "__main__":
    time_and_execute()
