from price_indexr import *
from interface import scan_products
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
        update_time = datetime.now() - timedelta(days=2)
        hiatus_time = datetime.now() - timedelta(days=30)

        for prod in prod_list:
            if (prod["last_update"] <= update_time) and (prod["last_update"] >= hiatus_time):
                collection_routine(product=prod)
            elif prod["last_update"] < hiatus_time:
                continue
        sleep(900)

if __name__ == "__main__":
    time_and_execute()
