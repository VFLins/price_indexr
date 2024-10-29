import price_indexr as pi
from datetime import datetime
import re
from sqlalchemy import select, delete
from sqlalchemy.orm import Session


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


def scan_products(name_id: int|None = None) -> list:
    """
    Read products table to get a list of rows as dicts

    **Args**
        `name_id`: ID number of the desired name. None, if should get all products.
    """
    rows = []
    with Session(pi.DB_ENGINE) as ses:
        if name_id:
            stmt = select(pi.products).where(pi.products.NameId == name_id)
        else:
            stmt = select(pi.products)
        result = ses.execute(stmt).scalars()

        for i in result:
            rows.append({
                "id": i.Id, 
                "name_id": i.NameId,
                "name": i.ProductName,
                "model": i.ProductModel,
                "brand": i.ProductBrand,
                "filters": i.ProductFilters,
                "created": i.Created,
                "last_update": i.LastUpdate})
    return rows


def title_name_exists(title: str) -> bool:
    """Returns a boolean value indicating wether `title` exist in *product_names* table or not."""
    title = re.sub(" +", " ", title.title())

    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_names).where(pi.product_names.ProductName == title)
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def id_name_exists(name_id: int) -> bool:
    """Returns a boolean value indicating wether `name_id` exist or not."""
    names_list = scan_names()
    id_exists = False
    for i in names_list:
        if i['id'] == name_id:
            id_exists = True
            break
    return id_exists


def id_product_exists(product_id: int) -> bool:
    """Returns a boolean value indicating wether `product_id` exist or not."""
    products_list = scan_products()
    id_exists = False
    for i in products_list:
        if i['id'] == product_id:
            id_exists = True
            break
    return id_exists


def select_name_id() -> int|None:
    """
    Prompts the user to select a name id.
    
    **Returns**
        `int` if user inserted a valid value, `None` otherwise.
    """
    names_list = scan_names()
    for row in names_list:
        print(f"Id: {row['id']} | Name: {row['name']}")

    try:
        name_id = int(input("Insert the name Id: "))
        if not id_name_exists(name_id):
            raise IndexError("Value not present in the data")
        return name_id

    except IndexError:
        print("Id number not valid")
        return None
    except ValueError:
        print("This is not an integer number")
        return None


def select_product_id() -> int|None:
    """
    Prompts the user to select a *product id* after selecting a *name id*.
    
    **Returns**
        `int` if user inserted a valid value, `None` otherwise.
    """
    name_id = select_name_id()
    if not name_id:
        return None
    
    products_list = scan_products(name_id)
    for row in products_list:
        print(f"Id: {row['id']} | Model: {row['name']} {row['model']}")

    try:
        product_id = int(input("Insert the prodcut Id: "))
        if not id_product_exists(product_id):
            raise IndexError("Value not present in the data")
        return product_id
    
    except IndexError:
        print("Id number not valid")
        return None
    except ValueError:
        print("This is not an integer number")
        return None


def get_input(menu_name: str):
    inp = input(f"\n[{menu_name}] Choose a letter and press enter: ")
    return inp.upper()


def options_menu(name: str, options: dict):
    # run help function at the beginning
    if "H" in options.keys():
        options["H"]()

    while True:
        inp = get_input(name)
        if inp == "Q":
            if name == "Main":
                quit()
            break
        if inp in options:
            options[inp]()
        else:
            print("Insert a valid value!")


def main_menu():
    options_menu(
        name = "Main",
        options={
            "C": (lambda: create_product()),
            "L": (lambda: list_products_menu()),
            "U": (lambda: update_product()),
            "D": (lambda: delete_product()),
            "K": (lambda: collect_prices_menu()),
            "H": (lambda: print_help([
                "C: Create a new product to price index", 
                "L: List products", 
                "U: Update a recorded product",
                "D: Delete a product by ID number", 
                "K: Collect prices",
                "H: Show this help message",
                "Q: Quit"
                ])
            )
        }
    )


def collect_prices_menu():
    options_menu(
        name = "Collect Prices",
        options = {
            "A": (lambda: update_all_prices()),
            "S": (lambda: update_prices()),
            "H": (lambda: print_help([
                "A: Collect prices from all products",
                "S: Collect prices for a specific collection of products",
                "H: Show this help message",
                "Q: Return to main menu",
                ])
            )
        }
    )


def list_products_menu():
    options_menu(
        name = "List Products",
        options = {
            "A": (lambda: list_all_products()),
            "S": (lambda: list_products()),
            "H": (lambda: print_help([
                "A: List all products",
                "S: List a specific collection of products",
                "H: Show this help message",
                "Q: Return to main menu",
                ])
            )
        }
    )


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


def list_all_products():
    rows = scan_products()
    for row in rows:
        print(
            f"Id: {row['id']}",
            f"Search: {row['brand']} {row['name']} {row['model']}",
            f"Filters: {row['filters']}",
            f"Last update: {row['last_update']}", sep=" | "
        )


def list_products():
    name_id = select_name_id()
    if not name_id:
        print("Aborting operation...")
        return
    rows = scan_products(name_id)
    for row in rows:
        print(
            f"Id: {row['id']}",
            f"Search: {row['brand']} {row['name']} {row['model']}",
            f"Filters: {row['filters']}",
            f"Last update: {row['last_update']}", sep=" | "
        )


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


def create_product():
    names_list = scan_names()
    is_first_name = len(names_list) == 0

    is_new_name = False
    if not is_first_name:
        use_existing_name = confirmation("Use an existing name?")
        if use_existing_name:
            name_id = select_name_id()
            if not name_id:
                print("Aborting operation...")
                return
        else:
            is_new_name = True
            product_name = input("Product name: ").title()
            if title_name_exists(product_name):
                print("This name already exists")
                return
    else:
        is_new_name = True
        name = input("Product name: ").title()

    created = datetime.now()
    brand = input("Brand name: ").title()
    model = input("Product model: ").title()
    filters = input("Filters: ").title()

    print(
        "\nYou will create this entry:\n"
        f"Search: {brand} {product_name} {model}",
        f"Filters: {filters}",
        f"Created: {created}", sep=" | ")
    # Add new name and get NameId
    
    with Session(pi.DB_ENGINE) as ses:
        # Get id for the used name
        stmt = select(pi.product_names).where(pi.product_names.ProductName == product_name)
        result = ses.execute(stmt).scalar_one()
        new_name_id = result.Id


    checkout = confirmation("This data will be saved")
    if checkout:
        if is_new_name:
            with Session(pi.DB_ENGINE) as ses:
                stmt = pi.product_names(ProductName=product_name)
                ses.add(stmt)
                ses.commit()

        with Session(pi.DB_ENGINE) as ses:
            # Get id for the used name
            stmt = select(pi.product_names)\
                .where(pi.product_names.ProductName == product_name)
            result = ses.execute(stmt).scalar_one()
            new_name_id = result.Id

        with Session(pi.DB_ENGINE) as ses:
            stmt = pi.products(
                NameId=new_name_id,
                ProductName=name,
                ProductModel=model,
                ProductBrand=brand,
                ProductFilters=filters,
                Created=created)
            ses.add(stmt)
            ses.commit()
            # Get created product id
            stmt = select(pi.products).where(pi.products.Created == created)
            result = ses.execute(stmt).scalars()

        for i in result:
            new_product_id = i.Id
        print("\nCollecting current prices...")
        pi.collect_prices(new_product_id)
        print(f"\nThe ID for this product is: {new_product_id}")
        print("Transaction completed")
    else:
        print("Transaction cancelled")


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


def print_help(help_mgs: list):
    print(
        "Choose an operation to perform:", 
        *help_mgs, sep="\n")


def update_all_prices():
    products = scan_products()
    n = len(products)
    i = 0

    while i < n:
        print(f"Collecting... {i/n*100:.2f}%", end="\r\r")
        pi.collect_prices(products[i]["id"])
        i = i + 1
    print("Completed! Check 'exec_log.txt' for more information.")


def update_prices():
    name_id = select_name_id()
    if not name_id:
        return
    update_products = scan_products(name_id)
    n = len(update_products)
    i = 0

    use_specific = confirmation("Collect prices for a single model")
    if not use_specific:
        while i < n:
            print(f"Collecting... {i/n*100:.2f}%", end="\r\r")
            pi.collect_prices(update_products[i]["id"])
            i = i + 1
        print("Completed! Check 'exec_log.txt' for more information.")

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