import price_indexr as pi
from datetime import datetime, timedelta
from typing import Literal
import re
from sqlalchemy import select, delete, update, func, table, literal_column
from sqlalchemy.orm import Session


BOLD, ITALIC, ENDSTYLE = "\033[1m", "\033[3m", "\033[0m"


def format_name(name:str) -> str:
    """Returns `name` in the format it should be retrieved from/inserted to the database."""
    return re.sub(" +", " ", name.title())


def table_has_data(tablename: Literal["prices", "product_names", "product_categories"]):
    stmt = (
        select(func.count()).select_from(
            select(literal_column("1"))
            .select_from(table(tablename))
            .limit(1)
            .subquery()
        )
    )
    with Session(pi.DB_ENGINE) as ses:
        return bool(ses.execute(stmt).scalar())


def scan_categories() -> list[pi.product_categories]:
    """Read *product_categories* table to get a list of rows."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_categories)
        result = ses.execute(stmt).scalars()
        return [row for row in result]


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
        date_min: datetime|None = None,
        price_max: float|None = None,
        price_min: float|None = None,
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
    if price_max:
        stmt = stmt.where(pi.prices.Price <= price_max)
    if price_min:
        stmt = stmt.where(pi.prices.Price >= price_min)
    with Session(pi.DB_ENGINE) as ses:
        result = ses.execute(stmt).scalars()
        return [row for row in result]


def delete_price_rows(rows: list[pi.prices]):
    """
    Delete a list of rows from *prices* table.

    **Args**
        `rows`: list of rows to be deleted.
    """
    rows_id = [r.Id for r in rows]
    stmt = delete(pi.prices).where(pi.prices.Id.in_(rows_id))
    with Session(pi.DB_ENGINE) as ses:
        ses.execute(stmt)
        ses.commit()


def product_category_by_id(id: int) -> pi.product_categories|None:
    """Return an entry from *product_categories* table with the specified `id`. `None` if it doesn't exist."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_categories).where(pi.product_categories.Id == id)
        return ses.execute(stmt).scalar_one_or_none()


def product_name_by_id(id: int) -> pi.product_names|None:
    """Return an entry from *product_names* table with the specified `id`. `None` if it doesn't exist."""
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
        result = ses.execute(stmt).scalar_one_or_none()
    return result


def title_category_exists(name: str) -> bool:
    """Returns a boolean value indicating wether `name` exist in *product_categories* table or not."""
    name = format_name(name)
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_categories).where(pi.product_categories.CategoryName == name)
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def title_name_exists(name: str) -> bool:
    """Returns a boolean value indicating wether `name` exist in *product_names* table or not."""
    name = re.sub(" +", " ", name.title())
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.product_names).where(pi.product_names.ProductName == name)
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def product_exists(product_obj: pi.products) -> bool:
    stmt = (
        select(pi.products)
        .where(pi.products.ProductBrand == product_obj.ProductBrand)
        .where(pi.products.ProductName == product_obj.ProductName)
        .where(pi.products.ProductModel == product_obj.ProductModel)
    )
    with Session(pi.DB_ENGINE) as ses:
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def id_by_category_name(name: str) -> int|None:
    """Returns the ID number of the corresponding `name` in *product_categories* table, or `None` if not present."""
    name = format_name(name)
    stmt = select(pi.product_categories.Id).where(pi.product_categories.CategoryName == name)
    with Session(pi.DB_ENGINE) as ses:
        result = ses.execute(stmt).scalar_one_or_none()
    return int(result)


def id_by_product_name(name: str) -> int|None:
    """Returns the ID number of the corresponding `name` in *product_categories* table, or `None` if not present."""
    name = format_name(name)
    stmt = select(pi.product_names.Id).where(pi.product_names.ProductName == name)
    with Session(pi.DB_ENGINE) as ses:
        result = ses.execute(stmt).scalar_one_or_none()
    return result


def id_product_by_created_time(dt: datetime) -> int:
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.products.Id).where(pi.products.Created == dt)
        return ses.execute(stmt).scalar_one_or_none()


def id_category_exists(category_id: int) -> bool:
    """Returns a boolean value indicating wether `category_id` exist or not."""
    stmt = select(pi.product_categories).where(pi.product_categories.Id == category_id)
    with Session(pi.DB_ENGINE) as ses:
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def id_name_exists(name_id: int) -> bool:
    """Returns a boolean value indicating wether `name_id` exist or not."""
    stmt = select(pi.product_names).where(pi.product_names.Id == name_id)
    with Session(pi.DB_ENGINE) as ses:
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def id_product_exists(product_id: int) -> bool:
    """Returns a boolean value indicating wether `product_id` exist or not."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.products).where(pi.products.Id == product_id)
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def id_price_exists(price_id: int) -> bool:
    """Returns a boolean value indicating wether `price_id` exist or not."""
    with Session(pi.DB_ENGINE) as ses:
        stmt = select(pi.prices).where(pi.prices.Id == price_id)
        result = tuple( ses.execute(stmt).scalars() )
    return bool(len(result))


def product_name_has_category(name_id: int) -> bool:
    """Returns a boolean value indicating wether `name_id` has a category ID associated to it or not."""
    if not id_name_exists(name_id):
        print("This name ID is not in database.")
        return None
    stmt = select(pi.product_names.CategoryId).where(pi.product_names.Id == name_id)
    with Session(pi.DB_ENGINE) as ses:
        result = ses.execute(stmt).scalar_one_or_none()
    return bool(result)


def add_product_category_to_db(product_category_obj: pi.product_categories) -> int|None:
    """Creates an entry in *product_categories* table, returns the ID of the entry created or `None` if `category_name` already exists."""
    category_name = product_category_obj.CategoryName
    if title_category_exists(name=category_name):
        return None
    with Session(pi.DB_ENGINE) as ses:
        ses.add(product_category_obj)
        ses.commit()
        new_id = id_by_category_name(category_name)
    return new_id


def add_product_name_to_db(product_name_obj: pi.product_names):
    """Creates an entry in *product_names* table, returns the ID of the entry created or `None` if `category_name` already exists."""
    product_name = product_name_obj.ProductName
    if title_name_exists(name=product_name):
        return None
    with Session(pi.DB_ENGINE) as ses:
        ses.add(product_name_obj)
        ses.commit()
        new_id = id_by_product_name(product_name)
    return new_id


def add_product_to_db(product_obj: pi.products):
    """Creates an entry in *products* table, returns the ID of the entry created or `None` if `product_obj` already exists."""
    if product_exists(product_obj):
        return None
    with Session(pi.DB_ENGINE) as ses:
        ses.add(product_obj)
        ses.commit()
        new_id = id_product_by_created_time(product_obj.Created)
    return new_id


def set_category_to_name(name_id: int, category_id: int):
    """Set `category_id` to *CategoryId* column in *product_names* table for the specified `name_id`."""
    stmt = (
        update(pi.product_names)
        .where(pi.product_names.Id == name_id)
        .values(CategoryId=category_id)
    )
    with Session(pi.DB_ENGINE) as ses:
        ses.execute(stmt)
        ses.commit()


def select_category_id() -> int|None:
    """
    Displays available categories and then prompts the user to select a category id.

    **Returns**
        `int` if user inserted a valid value, `None` otherwise.
    """
    print_category_names()
    try:
        category_id = int(input("Insert the category Id: "))
        if not id_category_exists(category_id):
            raise ValueError()
        return category_id
    except ValueError:
        print("Not a valid Id number")
        return None


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


def input_integer(msg: str) -> int:
    """
    Prompts the user to insert an integer number.
    
    **Args**
        `msg`: message to be prompted to the user
    
    **Returns**
        Number inserted as `int`, or `None` if not valid.
    """
    response = input(msg + ", must be an integer number: ")
    try:
        return int(response)
    except ValueError:
        return None


def input_floating_point(msg: str) -> float:
    """
    Prompts the user to insert a number with decimal places.

    **Args**
        `msg`: message to be prompted to the user
    
    **Returns**
        Number inserted as `float`, or `None` if not valid.
    """
    response = input(msg + ", must be a number (format 0.00): ")
    try:
        return float(response)
    except ValueError:
        return None


def input_date(msg: str, end_of_day: bool = False) -> datetime|None:
    """
    Prompts the user to insert a date.

    **Args**
        `msg`: message to be prompted to the user
        `end_of_day`: Should the time portion of the returned `datetime` refer to the last moment of the day?

    **Returns**
        Date inserted as `datetime`, or `None` if not valid.
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
    response = input(msg + " [Y/n]: ")
    if response.upper() == "N":
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
            "C": (lambda: create_menu()),
            "L": (lambda: navigate_menu()),
            "U": (lambda: update_menu()),
            "D": (lambda: delete_menu()),
            "K": (lambda: collect_menu()),
            "H": (lambda: print_help([
                "C: Create a new product to price index",
                "L: Navigate the database",
                "U: Update a recorded product",
                "D: Delete elements from the database",
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
            "D": (lambda: list_low_price_outliers()),
            "H": (lambda: print_help([
                "A: From product name (broader)",
                "S: From product",
                "D: Lowest prices from product name",
                "H: Show this help message",
                "Q: Return to navigate menu"
            ]))
        }
    )


def delete_menu():
    _options_menu(
        name = "Main > Delete",
        options = {
            "A": (lambda: delete_product()),
            "S": (lambda: delete_price()),
            "D": (lambda: delete_by_low_price()),
            "H": (lambda: print_help([
                "A: Delete a product",
                "S: Delete a price registry",
                "D: [Caution] Remove all prices from a product below a cutoff",
                "H: Show this help message",
                "Q: Return to main menu"
            ])),
        }
    )


def update_menu():
    _options_menu(
        name = "Main > Update",
        options = {
            "A": (lambda: assign_category()),
            "F": (lambda: update_product()),
            "H": (lambda: print_help([
                "A: Assign category to product name",
                "F: Update product filters",
                "H: Show this help message",
                "Q: Return to main menu",
            ]))
        }
    )


def create_menu():
    _options_menu(
        name = "Main > Collect",
        options = {
            "A": (lambda: create_product()),
            "S": (lambda: create_product_name()),
            "D": (lambda: create_product_category()),
            "H": (lambda: print_help([
                f"A: Create a {ITALIC}product{ENDSTYLE} assigned to an existing {ITALIC}product name{ENDSTYLE}",
                f"S: Create a {ITALIC}product name{ENDSTYLE} assigned to an existing {ITALIC}product category{ENDSTYLE}",
                f"D: Create a {ITALIC}product category{ENDSTYLE}",
                "H: Show this help message",
                "Q: Return to main menu",
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


def pick_name_by_id(message: str = "Pick a product ID") -> pi.product_names|None:
    """Gets an input fom the user and returns a product if valid, `None` otherwise."""
    id_num = input_integer(message + " (leave blank to cancel)")
    if not id_num:
        print("Not a valid ID number.")
        return None
    if not id_name_exists(id_num):
        print("This ID is not present on data.")
        return None
    return product_name_by_id(id_num)


def pick_price_by_id(message: str = "Pick a price ID") -> pi.prices|None:
    id_num = input_integer(message + " (leave blank to cancel)")
    if not id_num:
        print("Not a valid ID number.")
        return None
    if not id_price_exists(id_num):
        print("This ID is not present on data.")
        return None
    return price_by_id(id_num)


def print_category_names(rows: list[pi.product_categories]|None = None):
    """Displays all rows from *product_categories* table to the user."""
    if not rows:
        rows = scan_categories()
    for row in rows:
        print(f"Id: {row.Id}", f"{row.CategoryName}", sep=" | ")


def print_product_names(rows: list[pi.product_names]|None = None):
    """Displays all rows from *product_names* table to the user."""
    if not rows:
        rows = scan_names()
    for row in rows:
        category_name = product_category_by_id(row.CategoryId)
        if category_name:
            category_name = category_name.CategoryName
        print(f"Id: {row.Id}", f"{row.ProductName}", f"Category: {category_name}", sep=" | ")


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
            f"{row.Name}",
            f"Store: {row.Store}", sep=" | "
        )


def print_help(help_mgs: list[str]):
    print("\nChoose an operation to perform:", *help_mgs, sep="\n")


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
    row = pick_product_by_id("Select a product ID to delete")
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


def delete_price():
    """Prompts the user to remove a price from the database."""
    row = pick_price_by_id("Select a price ID to delete")
    if not row:
        print("This row Id doesn't exist!")
        return

    print_prices([row])
    confirm = input_confirm("Delete this price?")
    if not confirm:
        print("Aborting operation...")
        return
    delete_price_rows([row])


def delete_by_low_price():
    """Prompts the user to remove all prices below a cutoff from a product."""
    prices = list_low_price_outliers(returns=True)
    confirm = input_confirm("Confirm deletion of ALL these prices? (CANNOT BE UNDONE)")
    if confirm:
        delete_price_rows(prices)
        print(f"{len(prices)} prices removed.")
        return
    print("Aborting operation...")


def create_product_category():
    """Prompts the user to create an entry to *product_categories* table."""
    category_name = format_name(input("Insert the new category name: "))
    product_category_obj = pi.product_categories(
        CategoryName=category_name
    )
    print_category_names([product_category_obj])
    confirm = input_confirm("Add this entry to the database?")
    if not confirm:
        print("Aborting operation...")
        return
    new_id = add_product_category_to_db(product_category_obj)
    if new_id:
        print(f"Id for the new category is {new_id}.")
    else:
        print(f"Identical {ITALIC}category name{ENDSTYLE} in database, Aborting operation...")
    

def create_product_name():
    """Prompts the user to create an entry to *product_names* table."""
    if not table_has_data("product_categories"):
        print(f"Create a {ITALIC}category name{ENDSTYLE} before you add a product name to the database.")
        return
    category_id = select_category_id()
    if not category_id:
        print("Aborting operation...")
        return
    product_name = format_name(input("Insert the new product name: "))
    product_name_obj = pi.product_names(
        ProductName=product_name,
        CategoryId=category_id,
    )
    print_product_names([product_name_obj])
    confirm = input_confirm("Add this entry to the database?")
    if not confirm:
        print("Aborting operation...")
        return
    new_id = add_product_name_to_db(product_name_obj)
    if new_id:
        print(f"Id for the new {ITALIC}product name{ENDSTYLE} is {new_id}.")
    else:
        print(f"Identical {ITALIC}product name{ENDSTYLE} in database, Aborting operation...")


def create_product():
    if not table_has_data("product_names"):
        print(f"Create a {ITALIC}product name{ENDSTYLE} before you add a product name to the database.")
        return
    product_id = select_product_id()
    if not product_id:
        print("Aborting operation...")
        return
    brand_name = format_name(input("Brand name: "))
    model_name = format_name(input("Product model: "))
    filters = format_name(input("Filters (e.g: foo, bar, multi_word_filter): "))
    name_obj = product_name_by_id(product_id)
    product_obj = pi.products(
        NameId=name_obj.Id,
        ProductName=name_obj.ProductName,
        ProductModel=model_name,
        ProductBrand=brand_name,
        ProductFilters=filters,
        Created=datetime.now()
    )
    print_products([product_obj])
    confirm = input_confirm("Add this entry to the database?")
    if not confirm:
        print("Aborting operation...")
        return
    new_id = add_product_to_db(product_obj)
    if new_id:
        print(f"Id for the new {ITALIC}product{ENDSTYLE} is {new_id}.")
    else:
        print(f"Identical {ITALIC}product{ENDSTYLE} in database, Aborting operation...")


def collect_prices_from_products(rows: list[pi.products]):
    n, i = len(rows), 0
    while i < n:
        print(f" Collecting... {(i+1)/n*100:.2f}%", end="\r\r")
        pi.collect_prices(rows[i].Id)
        i = i + 1
    print(f"Collected prices for {n} products")


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
    date_max = input_date("Insert an end date", end_of_day=True)
    prices = scan_prices(
        product_ids=[product_id],
        date_max=date_max,
        date_min=date_min
    )
    print_prices(prices)


def list_low_price_outliers(returns: bool = False):
    name_id = select_name_id() 
    if not name_id:
        print("Invalid Id provided.\n")
        return
    max_price_val = input_floating_point("Insert the maximum price to filter")
    if not max_price_val:
        print("Invalid price value.\n")
        return
    products_ids = [i.Id for i in scan_products(name_id=name_id)]
    prices = scan_prices(
        product_ids=products_ids,
        price_max=max_price_val
    )
    print_prices(prices)
    if returns:
        return prices


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


def assign_category():
    if not table_has_data("product_categories"):
        print("You need to create a category before assigning, go to [Main > Create].")
        return
    name_id = select_name_id()
    if not name_id:
        print("Aborting operation...")
        return
    category_id = select_category_id()
    if not category_id:
        print("Aborting operation...")
        return
    category = product_category_by_id(category_id)
    name = product_name_by_id(name_id)
    confirm = input_confirm(f"Set category {category.CategoryName} to {name.ProductName}?")
    if not confirm:
        print("Aborting operation...")
        return
    set_category_to_name(name_id, category_id)
    print("Completed")


if __name__ == "__main__":
    print("===== Price_indexr central v0.3 =====")
    main_menu()
