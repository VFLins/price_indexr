from price_indexr import *
from interface import scan_products
from datetime import date, datetime, timedelta
from time import sleep

log = LocalLogger("scheduler")


def time_and_execute():
    def collection_routine(product):
        try:
            collect_prices(product["id"])
        except Exception as expt:
            prodname = f"{product["ProductBrand"]} {product["ProductModel"]} {product["ProductName"]}"
            log.error(f"Unexpected error collecting prices from '{prodname}'. Reason: {str(expt)}")
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
