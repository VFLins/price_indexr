import price_indexr as pi
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.orm import Session


HELP_MSG_MAIN = [
    "C: Create a new product to price index", 
    "L: List products", 
    "U: Update a recorded product",
    "D: Delete a product by ID number", 
    "K: Collect prices",
    "H: Show this help message",
    "Q: Quit"
]

HELP_MSG_COLLECTPRICES = [
    "A: Collect prics from all products",
    "S: Collect prices for a specific collection of products"
    "H: Show this help message",
    "Q: Return to main menu"
]

def scan_names() -> list:
    """Read product_names table to get a list of rows as dicts"""
    output = []
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_names)
        result = ses.execute(stmt).scalars()

        for i in result:
            output.append({
                "id": i.Id, 
                "name": i.ProductName})
    return output


def scan_products() -> list:
    """Read products table to get a list of rows as dicts"""
    output = []
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.products)
        result = ses.execute(stmt).scalars()

        for i in result:
            output.append({
                "id": i.Id, 
                "name_id": i.NameId,
                "name": i.ProductName,
                "model": i.ProductModel,
                "brand": i.ProductBrand,
                "filters": i.ProductFilters,
                "created": i.Created,
                "last_update": i.LastUpdate})
    return output


def get_input(menu_name: str):
    inp = input(f"\n{menu_name}: Choose a letter and press enter: ")
    return inp.upper()


def options_menu(options: dict, name: str = "unnamed menu"):
    # run help function at the beginning
    if "H" in options.keys():
        options["H"]()

    while True:
        inp = get_input(name)
        if (name != "Main Menu") and (inp == "Q"):
            break
        if inp in options:
            options[inp]()
        else:
            print("Insert a valid value!")


def main_menu():
    options_menu(
        options={
            "C": (lambda: create_product()),
            "L": (lambda: list_products()),
            "U": (lambda: update_product()),
            "D": (lambda: delete_product()),
            "K": (lambda: collect_prices_menu()),
            "H": (lambda: print_help(help_mgs=HELP_MSG_MAIN)),
            "Q": (lambda: quit())
        },
        name = "Main"
    )


def collect_prices_menu():
    options_menu(
        options={
            "A": (lambda: update_all_prices()),
            "S": (lambda: update_prices()),
            "H": (lambda: print_help(help_mgs=HELP_MSG_COLLECTPRICES)),
            "Q": None
        },
        name = "Collect Prices"
    )

""" def main_menu():
    while True:
        print_help()
        inp = get_input()

        while True:
            match inp.upper():
                case "C": run_next = "Create"; break
                case "L": run_next = "List"; break
                case "U": run_next = "Update"; break
                case "D": run_next = "Delete"; break
                case "H": run_next = "Help"; break 
                case "K": run_next = "Prices"; break
                case "Q": quit()
                case _: 
                    print("Insert a valid value!")
                    inp = get_input()

        match run_next:
            case "Create": create_product()
            case "List": list_products()
            case "Update": update_product()
            case "Help": print_help()
            case "Prices": update_prices()
            case "Delete": delete_product()        
 """


def confirmation(ask: str) -> bool:
    def get_input():
        inp = input(ask + ". Confirm? [Y/n]: ")
        return inp

    inp = get_input()
    while True:
        if inp.upper() in ["Y", ""]:
            output = True
            break
        elif inp.upper() in ["N"]:
            output = False
            break
        else:
            print("Invalid answer!")
            inp = get_input()
    return output


def pick_product_by_id(message):
    products = scan_products()
    
    while True:
        try:
            id_num = input(message + " (leave blank to cancel): ")
            # test if left blank
            if id_num == "": raise Exception
            # coerce and test for integer value, natively raise ValueError
            id_num = int(id_num)
            # test if exists
            id_exists  = False
            for row in products:
                if id_num == row['id']: 
                    id_exists = True
                    product = row
                    break
            if not id_exists: raise IndexError
            break
        except ValueError:
            print("Insert a valid number!")
        except IndexError: return None
        except: return None
    return product


def list_products():
    rows = scan_products()
    for row in rows:
        print(
            f"Id: {row['id']}",
            f"Search: {row['brand']} {row['name']} {row['model']}",
            f"Filters: {row['filters']}",
            f"Last update: {row['last_update']}", sep=" | ")


def delete_product():
    row = pick_product_by_id("Select a product to delete")

    # run if row exists
    if row:
        id_num = row['id']
        # show the row selected
        print(
            f"Id: {id_num}",
            f"Search: {row['brand']} {row['name']} {row['model']}",
            f"Filters: {row['filters']}",
            f"Last update: {row['last_update']}", sep=" | ")
        # confirm deletion to execute
        confirm = confirmation("You will delete this record")
        if confirm:
            try:
                stmt = delete(pi.products).where(pi.products.Id == id_num)
                with Session(pi.DB_ENGINE) as ses:
                    ses.execute(stmt)
                    ses.commit()
            except Exception as DeletionError:
                print("Not able to delete", DeletionError, sep="\n")
        else: quit()
    else:
        print("This row Id doesn't exist!")


"""
def retry(expr, tries, **kwargs):
    for i in tries:
        try: return expr(**kwargs)
        except Exception as err: 
            print(err)
            continue
        else: break
"""

def create_product():
    names_list = scan_names()
    is_first_name = len(names_list) == 0

    is_new_name = False
    if not is_first_name:
        use_existing_name = confirmation("Use an existing name?")
        if use_existing_name:
            for i in names_list:
                print(
                    f"Id: {i['id']}",
                    f"Name: {i['name']}", sep=" | ")
            while True:
                try: 
                    name_id = int(input("Select the name Id: "))
                    id_exists = False
                    for i in names_list:
                        if i['id'] == name_id:
                            id_exists = True
                            name = i['name']
                            break
                    if not id_exists: raise IndexError("Value not present in the data")
                except: print("Insert a valid number!")
                else: break
        else: 
            is_new_name = True
            while True:
                try:
                    name = input("Product name: ").title()
                    for i in names_list:
                        if i['name'] == name: raise Exception
                except: 
                    print("This name already exists")
                    return
                else: break
    else:
        is_new_name = True
        name = input("Product name: ").title()
        
    created = datetime.now()
    brand = input("Brand name: ").title()
    model = input("Product model: ").title()
    filters = input("Filters: ").title()

    print(
        "\nYou will create this entry:\n"
        f"Search: {brand} {name} {model}",
        f"Filters: {filters}",
        f"Created: {created}", sep=" | ")
    

    # Add new name and get NameId
    if is_new_name:
        name_stmt = pi.product_names(ProductName=name)
        with Session(pi.DB_ENGINE) as ses:
            # Save new name
            ses.add(name_stmt)
            ses.commit()
    with Session(pi.DB_ENGINE) as ses:
        # Get id for the used name
        stmt = select(pi.product_names).where(pi.product_names.ProductName == name)
        result = ses.execute(stmt).scalar_one()
        new_name_id = result.Id


    checkout = confirmation("This data will be saved")
    if checkout:            
        prod_stmt = pi.products(
            NameId=new_name_id,
            ProductName=name,
            ProductModel=model,
            ProductBrand=brand,
            ProductFilters=filters,
            Created=created)
        with Session(pi.DB_ENGINE) as ses:
            ses.add(prod_stmt)
            ses.commit()
            # Get created product id
            stmt = select(pi.products).where(pi.products.Created == created)
            result = ses.execute(stmt).scalars()

        for i in result: new_product_id = i.Id
        print("\nCollecting current prices...")
        pi.collect_prices(new_product_id)
        print(f"\nThe ID for this product is: {new_product_id}")
        print("Transaction success!")
    else:
        print("Transaction cancelled!")


def update_product():
    print("You can only update the filters's field in this version...")
    row = pick_product_by_id("Select the product with the filter to update")

    if row:
        id_num = row['id']
        print(
            f"Id: {id_num}",
            f"Search: {row['brand']} {row['name']} {row['model']}",
            f"Filters: {row['filters']}",
            f"Last update: {row['last_update']}", sep=" | ")
        # confirm update and execute
        confirm = confirmation("You will retype the filters for this record")
        if confirm:
            new_filters = input("Insert the new filters (retype existing ones that you want to keep): ")
            with Session(pi.DB_ENGINE) as ses:
                selected_row = ses.execute(select(pi.products).where(pi.products.Id == id_num)).scalar_one()
                selected_row.ProductFilters = new_filters
                ses.commit()
    else:
        print("This row Id doesn't exist!")

def print_help(help_mgs: list = HELP_MSG_MAIN):
    print(
        "Choose an operation to perform:", 
        *help_mgs, sep="\n")


def update_all_prices():
    products = scan_products()
    n = len(products)
    i = 0

    while i <= n:
        print(f"Collecting... {i/n*100:.2f}%", end="\r\r")
        pi.collect_prices(products[i]["id"])
        i = i + 1
    print("Completed! Check 'exec_log.txt' for more information.")


def update_prices():
    names_list = scan_names()
    for row in names_list:
        print(f"Id: {row['id']} | Name: {row['name']}")
    while True:
        try: 
            name_id = int(input("Select the name Id: "))
            id_exists = False
            for i in names_list:
                if i['id'] == name_id:
                    id_exists = True
                    break
            if not id_exists: raise IndexError("Value not present in the data")
        except: print("Insert a valid number!")
        else: break
    products = scan_products()
    update_products = [pr for pr in products if pr["name_id"]==name_id]

    use_specific = confirmation("Collect prices for a single model")
    if not use_specific:
        print("Working... Please wait.")
        for prod in update_products:
            try:
                pi.collect_prices(prod["id"])
            except Exception as expt:
                pi.write_message_log(
                    expt, "Unexpected error on collection routine:", 
                    f"{prod['brand']} {prod['name']} {prod['model']}",
                    prod_id=prod['id']
                )

    else:
        for row in update_products:
            print(f"Id: {row['id']} | Model: {row['name']} {row['model']}")
        while True:
            try: 
                prod_id = int(input("Select the product Id: "))
                id_exists = False
                for i in update_products:
                    if i['id'] == prod_id:
                        id_exists = True
                        break
                if not id_exists: raise IndexError("Value not present in the data")
            except: print("Insert a valid number!")
            else: break
        print("Working... Please wait.")
        pi.collect_prices(prod_id)
    
    print("Completed! Check 'exec_log.txt' for more information.")

if __name__ == "__main__":
    print("===== Price_indexr central v0.2 =====")
    main_menu()