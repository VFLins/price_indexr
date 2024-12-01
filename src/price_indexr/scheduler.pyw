import price_indexr as pi
from price_indexr.interface import scan_products
from datetime import date, datetime, timedelta
from time import sleep


log = pi.LocalLogger("scheduler")


def time_and_execute():
    _context = "time_and_execute"

    def collection_routine(product: pi.products):
        _context = "time_and_execute.collection_routine"
        try:
            pi.collect_prices(product.Id)
        except Exception as err:
            prodname = f"{product.ProductBrand} {product.ProductName} {product.ProductModel}"
            log.error(_context,f"Unexpected error collecting prices from '{prodname}'. Reason: {str(err)}")
            sleep(300)

    while True:
        prod_list = scan_products()
        update_time = datetime.now() - timedelta(days=2)
        hiatus_time = datetime.now() - timedelta(days=30)
        
        for prod in prod_list:
            prodname = f"{prod.ProductBrand} {prod.ProductName} {prod.ProductModel}"
            try:
                if prod.LastUpdate is None:
                    log.info(_context, f"Trying to collect prices for '{prodname}' (never collected before)")
                    collection_routine(product=prod)

                elif (prod.LastUpdate <= update_time) and (prod.LastUpdate >= hiatus_time):
                    collection_routine(product=prod)

                elif prod.LastUpdate < hiatus_time:
                    tdelta = datetime.now() - prod.LastUpdate
                    log.info(_context, f"Skipping '{prodname}', last update was too long ago ({tdelta.days} days)")
                    continue

            except Exception as err:
                log.critical(_context, f"Unexpected error while managing price collection after {prodname}: {err}")
        sleep(900)

if __name__ == "__main__":
    time_and_execute()
