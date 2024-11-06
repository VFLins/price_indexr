import price_indexr as pi
from datetime import datetime, timedelta
from typing import Literal
import re
from sqlalchemy import select, delete
from sqlalchemy.orm import Session


def scan_names() -> list[pi.product_names]:
    """Read *product_names* table to get a list of rows."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_names)
        result = ses.execute(stmt).scalars()
        return [row for row in result]


def scan_products(name_id: int|None = None) -> list[pi.products]:
    """
    Read *products* table to get a list of rows.

    **Args**
        `name_id`: ID number of the desired name. `None`, if should get all products.
    """
    stmt = select(pi.products)
    if name_id:
        stmt = stmt.where(pi.products.NameId == name_id)
    with Session(pi.DB_ENGINE) as ses:
        result = ses.execute(stmt).scalars()
        return [row for row in result]


def scan_prices(
        product_ids: list[int]|None = None,
        date_max: datetime|None = None,
        date_min: datetime|None = None
    ) -> list[pi.prices]:
    """
    Read *prices* table to get a list of rows.

    **Args**
        `product_ids`: list of ID numbers of the desired products. `None` if should get from all products.
        `date_max`: Maximum date to retrieve prices. `None` if should get up to the latest.
        `date_max`: Minimum date to retrieve prices. `None` if should get down to the first.
    """
    stmt = select(pi.prices)
    if product_ids:
        stmt = stmt.where(pi.prices.ProductId.in_(product_ids))
    if date_max:
        stmt = stmt.where(pi.prices.Date <= date_max)
    if date_min:
        stmt = stmt.where(pi.prices.Date >= date_min)
    with Session(pi.DB_ENGINE) as ses:
        result = ses.execute(stmt).scalars()
        return [row for row in result]


def product_name_by_id(id: int) -> pi.product_names|None:
    """Return an entry from product names table with the specified `id`. `None` if it doesn't exist."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_names).where(pi.product_names.Id == id)
        return ses.execute(stmt).scalar_one_or_none()


def product_by_id(id: int) -> pi.products|None:
    """Return an entry from products table with the specified `id`. `None` if it doesn't exist."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.products).where(pi.products.Id == id)
        return ses.execute(stmt).scalar_one_or_none()


def price_by_id(id: int) -> pi.prices|None:
    """Return an entry from prices table with the specified `id`. `None` if it doesn't exist."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.prices).where(pi.prices.Id == id)
        return ses.execute(stmt).scalar_one_or_none()


def title_name_exists(name: str) -> bool:
    """Returns a boolean value indicating wether `name` exist in *product_names* table or not."""
    name = re.sub(" +", " ", name.title())
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_names).where(pi.product_names.ProductName == name)
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def id_name_exists(name_id: int) -> bool:
    """Returns a boolean value indicating wether `name_id` exist or not."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_names).where(pi.product_names.Id == name_id)
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def id_product_exists(product_id: int) -> bool:
    """Returns a boolean value indicating wether `product_id` exist or not."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.products).where(pi.products.Id == product_id)
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def select_name_id() -> int|None:
    """
    Displays available names and then prompts the user to select a name id.

    **Returns**
        `int` if user inserted a valid value, `None` otherwise.
    """
    print_product_names()
    try:
        name_id = int(input("Insert the name Id: "))
        if not id_name_exists(name_id):
            raise ValueError()
        return name_id
    except ValueError:
        print("Not a valid Id number")
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
        print(f"Id: {row.Id} | Model: {row.ProductBrand} {row.ProductModel}")

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


def input_date(msg: str, end_of_day: bool = False) -> datetime|None:
    """
    Prompts the user to insert a date.

    **Args**
        `msg`: message to be prompted to the user
        `end_of_day`: Should the time portion of the returned `datetime` refer to the last moment of the day?

    **Returns**
        Date inserted as `datetime`, or `None` if invalid input.
        Will return today's date if left blank.
    """
    response = input(msg + ", leave blank for today's date (format YYYY-MM-DD): ")
    if response.strip() != "":
        try:
            date = datetime.strptime(response, "%Y-%m-%d")
        except ValueError:
            return
    date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    if end_of_day:
        return date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return date


def input_confirm(msg: str) -> bool:
    """
    Prompts the user to confirm an operation.

    **Args**
        `msg`: message to be prompted to the user

    **Returns**
        User's response as boolean value, `False` if "N", `True` otherwise.
    """
    response = input(msg + " [Y/n]: ").upper()
    if response == "N":
        return False
    else:
        return True


def input_option(menu_name: str) -> str:
    """
    Recieves inputs for navigating between menus.

    **Args**
        `menu_name`: Indicates to the user, what menu they are interacting with
    
    **Returns**
        Uppercased value inserted by the user.
    """
    BOLD, ENDSTYLE = "\033[1m", "\033[0m"
    inp = input(f"{BOLD}[{menu_name}]{ENDSTYLE} Choose a letter and press enter: ")
    return inp.upper()


def _options_menu(name: str, options: dict):
    """Menu constructor to handle menu navigation, should not be used directly."""
    # run help function at the beginning
    if "H" in options.keys():
        options["H"]()

    while True:
        inp = input_option(name)
        if inp == "Q":
            if name == "Main":
                quit()
            break
        if inp in options:
            options[inp]()
        else:
            print("Insert a valid value!")


def main_menu():
    _options_menu(
        name = "Main",
        options={
            "C": (lambda: create_product()),
            "L": (lambda: navigate_menu()),
            "U": (lambda: update_product()),
            "D": (lambda: delete_product()),
            "K": (lambda: collect_menu()),
            "H": (lambda: print_help([
                "C: Create a new product to price index", 
                "L: Navigate the database", 
                "U: Update a recorded product",
                "D: Delete a product by ID number", 
                "K: Collect prices",
                "H: Show this help message",
                "Q: Quit"
                ])
            )
        }
    )


def collect_menu():
    _options_menu(
        name = "Main > Collect",
        options = {
            "A": (lambda: collect_prices_from_products(rows=scan_products())),
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


def navigate_menu():
    _options_menu(
        name = "Main > Navigate",
        options = {
            "A": (lambda: print_products(rows=scan_products())),
            "S": (lambda: list_products_by_name()),
            "P": (lambda: navigate_prices_menu()),
            "H": (lambda: print_help([
                "A: List all products",
                "S: List a specific collection of products",
                "P: Prices menu",
                "H: Show this help message",
                "Q: Return to main menu",
                ])
            )
        }
    )


def navigate_prices_menu():
    _options_menu(
        name = "Main > Navigate > Prices",
        options = {
            "A": (lambda: list_prices_by_name()),
            "S": (lambda: list_prices_by_product()),
            "H": (lambda: print_help([
                "A: From product name (broader)",
                "S: From product",
                "H: Show this help message",
                "Q: Return to navigate menu"
            ]))
        }
    )


def pick_product_by_id(message: str = "Pick a product") -> pi.products|None:
    """Gets an input fom the user and returns a product if valid, `None` otherwise."""
    id_num = input(message + " (leave blank to cancel): ")
    try:
        id_num = int(id_num)
    except ValueError:
        print("Not a valid ID number.")
        return None
    if not id_product_exists(id_num):
        print("This ID is not present on data.")
        return None
    return product_by_id(id_num)


def pick_name_by_id(message: str = "Pick a product name") -> pi.product_names|None:
    """Gets an input fom the user and returns a product if valid, `None` otherwise."""
    id_num = input(message + " (leave blank to cancel): ")
    try:
        id_num = int(id_num)
    except ValueError:
        print("Not a valid ID number.")
        return None
    if not id_name_exists(id_num):
        print("This ID is not present on data.")
        return None
    return product_name_by_id(id_num)


def print_product_names():
    """Displays all rows from *product_names* table to the user."""
    rows = scan_names()
    for row in rows:
        print(f"Id: {row.Id}", f"{row.ProductName}", sep=" | ")


def print_products(rows: list[pi.products]):
    """Displays a list of `rows` from *products* table to the user."""
    for row in rows:
        print(
            f"Id: {row.Id}",
            f"Search: {row.ProductBrand} {row.ProductName} {row.ProductModel}",
            f"Filters: {row.ProductFilters}",
            f"Last update: {row.LastUpdate}", sep=" | "
        )


def print_prices(rows: list[pi.prices]):
    """Display a list of `rows` from *prices* table to the user."""
    for row in rows:
        print(
            f"Id: {row.Id}",
            f"{row.Date.strftime('%Y-%m-%d')}",
            f"{row.Currency} {row.Price:.2f}",
            f"{row.Name}", sep=" | "
        )


def list_products_by_name():
    """
    Displays available names and prompts the user to select one, if the user selects correctly, displays products with the name selected.
    """
    name_id = select_name_id()
    if name_id:
        rows = scan_products(name_id)
        print_products(rows)
        return
    print("Aborting operation...\n")   


def delete_product():
    row = pick_product_by_id("Select a product to delete")
    if not row:
        print("This row Id doesn't exist!")
        return

    print_products(rows=[row])
    confirm = input_confirm("Delete this product?")
    if not confirm:
        print("Aborting operation...")
        return

    try:
        stmt = delete(pi.products).where(pi.products.Id == row.Id)
        with Session(pi.DB_ENGINE) as ses:
            ses.execute(stmt)
            ses.commit()
    except Exception as err:
        print("Not able to delete", str(err), sep="\n")    


def create_product():
    names_list = scan_names()
    is_first_name = len(names_list) == 0

    is_new_name = False
    if not is_first_name:
        use_existing_name = input_confirm("Use an existing name?")
        if use_existing_name:
            name_id = select_name_id()
            if not name_id:
                print("Aborting operation...")
                return
            product_name = product_name_by_id(name_id).ProductName
        else:
            is_new_name = True
            product_name = input("Product name: ").title()
            if title_name_exists(product_name):
                print("This name already exists")
                return
    else:
        is_new_name = True
        product_name = input("Product name: ").title()

    created = datetime.now()
    brand = input("Brand name: ").title()
    model = input("Product model: ").title()
    filters = input("Filters (e.g: foo, bar, multi_word_filter): ").title()

    print(
        "\nYou will create this entry:\n"
        f"Search: {brand} {product_name} {model}",
        f"Filters: {filters}",
        f"Created: {created}", sep=" | ")

    # Add new name and get NameId
    checkout = input_confirm("Save this data?")
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
                ProductName=product_name,
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
    if not row:
        print("This row Id doesn't exist!")
        return

    print_products(rows=[row])
    confirm = input_confirm("Retype the filters for this record?")
    if not confirm:
        print("Aborting operation...")
        return

    new_filters = input("Insert the new filters (retype existing ones that you want to keep): ")
    with Session(pi.DB_ENGINE) as ses:
        selected_row = ses.execute(select(pi.products).where(pi.products.Id == row.Id)).scalar_one()
        selected_row.ProductFilters = new_filters
        ses.commit()


def print_help(help_mgs: list[str]):
    print("\nChoose an operation to perform:", *help_mgs, sep="\n")


def collect_prices_from_products(rows: list[pi.products]):
    n, i = len(rows), 0
    while i < n:
        print(f" Collecting... {(i+1)/n*100:.2f}%", end="\r\r")
        pi.collect_prices(rows[i].Id)
        i = i + 1


def list_prices_by_name():
    name_id = select_name_id()
    if not name_id:
        print("Aborting operation...")
        return
    products_ids = [i.Id for i in scan_products(name_id=name_id)]
    date_min = input_date("Insert a start date")
    date_max = input_date("Insert an end date", end_of_day=True)
    prices = scan_prices(
        product_ids=products_ids,
        date_max=date_max,
        date_min=date_min
    )
    print_prices(prices)


def list_prices_by_product():
    product_id = select_product_id()
    if not product_id:
        print("Aborting operation...")
        return
    date_min = input_date("Insert a start date")
    date_max = input_date("Insert an end date")
    prices = scan_prices(
        product_ids=[product_id],
        date_max=date_max,
        date_min=date_min
    )
    print_prices(prices)


def update_prices():
    name_id = select_name_id()
    if not name_id:
        print("Invalid Id provided.\n")
        return
    update_products = scan_products(name_id)

    use_specific = input_confirm("Collect prices for a single model?")
    if not use_specific:
        collect_prices_from_products(rows=update_products)
        return

    print_products(update_products)
    selected_prod = pick_product_by_id("Pick a product to collect prices")
    if not selected_prod:
        print("Aborting operation...")
        return
    if selected_prod.Id not in [i.Id for i in update_products]:
        print("ID not in the list, aborting operation...")
        return
    collect_prices_from_products(rows=[selected_prod])


if __name__ == "__main__":
    print("===== Price_indexr central v0.3 =====")
    main_menu()
