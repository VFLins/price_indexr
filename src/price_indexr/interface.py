from price_indexr import db, collect
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.orm import Session


BOLD, ITALIC, ENDSTYLE = "\033[1m", "\033[3m", "\033[0m"
_empty_ = f"{ITALIC}empty{ENDSTYLE}"
_undefined_ = f"{ITALIC}undefined{ENDSTYLE}"
_price_ = f"{ITALIC}:price:{ENDSTYLE}"
_product_ = f"{ITALIC}:product:{ENDSTYLE}"
_product_name_ = f"{ITALIC}:product_name:{ENDSTYLE}"
_product_category_ = f"{ITALIC}:product_category:{ENDSTYLE}"


def handle_empty_field(table_cls: db.TableClass | None, field_name: str) -> str:
    f"""
    Handles field values in `TableClass` objects that might be empty or undefined:

    **Args**
        `table_cls`: Table class from where the value should be extracted
        `field_name`: Name of the field where the desired value is expected to be

    **Returns**
        `str` {_empty_} if defined but empty, {_undefined_}, or the actual field value
    """
    if not table_cls:
        return _undefined_

    try:
        field_value = table_cls.__dict__[field_name]
    except KeyError:
        return _undefined_

    if field_value in [None, ""]:
        return _empty_
    return field_value


def select_category_id() -> int | None:
    """
    Displays available categories and then prompts the user to select a category id.

    **Returns**
        `int` if user inserted a valid value, `None` otherwise.
    """
    print_category_names()
    try:
        category_id = int(input("Insert the category Id: "))
        if not db.id_category_exists(category_id):
            raise ValueError()
        return category_id
    except ValueError:
        print("Not a valid Id number")
        return None


def select_name_id() -> int | None:
    """
    Displays available names and then prompts the user to select a name id.

    **Returns**
        `int` if user inserted a valid value, `None` otherwise.
    """
    print_product_names()
    try:
        name_id = int(input("Insert the name Id: "))
        if not db.id_name_exists(name_id):
            raise ValueError()
        return name_id
    except ValueError:
        print("Not a valid Id number")
        return None


def select_product_id() -> int | None:
    """
    Prompts the user to select a *product id* after selecting a *name id*.

    **Returns**
        `int` if user inserted a valid value, `None` otherwise.
    """
    name_id = select_name_id()
    if not name_id:
        return None

    products_list = db.scan_products(name_id)
    for row in products_list:
        print(f"Id: {row.Id} | Model: {row.ProductBrand} {row.ProductModel}")

    try:
        product_id = int(input("Insert the prodcut Id: "))
        if not db.id_product_exists(product_id):
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


def input_date(msg: str, end_of_day: bool = False) -> datetime | None:
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
    Recieves inputs for navigating between menus. Will always be uppercased.

    **Args**
        `menu_name`: Indicates to the user, what menu they are interacting with

    **Returns**
        Uppercased value inserted by the user.
    """
    BOLD, ENDSTYLE = "\033[1m", "\033[0m"
    inp = input(f"{BOLD}[{menu_name}]{ENDSTYLE} Choose an option and press enter: ")
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
        name="Main",
        options={
            "C": (lambda: create_menu()),
            "L": (lambda: navigate_menu()),
            "U": (lambda: update_menu()),
            "D": (lambda: delete_menu()),
            "K": (lambda: collect_menu()),
            "H": (
                lambda: print_help(
                    [
                        "C: Create a new product to price index",
                        "L: Navigate the database",
                        "U: Update a recorded product",
                        "D: Delete elements from the database",
                        f"K: Collect {_price_}",
                        "H: Show this help message",
                        "Q: Quit",
                    ]
                )
            ),
        },
    )


def collect_menu():
    _options_menu(
        name="Main > Collect",
        options={
            "A": (lambda: collect_prices_from_products(rows=db.scan_products())),
            "S": (lambda: update_prices()),
            "H": (
                lambda: print_help(
                    [
                        f"A: Collect {_price_} from all products",
                        f"S: Collect {_price_} for a specific collection of products",
                        "H: Show this help message",
                        "Q: Return to main menu",
                    ]
                )
            ),
        },
    )


def navigate_menu():
    _options_menu(
        name="Main > Navigate",
        options={
            "A": (lambda: print_products()),
            "S": (lambda: list_products_by_name()),
            "P": (lambda: navigate_prices_menu()),
            "H": (
                lambda: print_help(
                    [
                        f"A: List all {_product_}",
                        f"S: List {_product_} by {_product_name_}",
                        "P: Prices menu",
                        "H: Show this help message",
                        "Q: Return to main menu",
                    ]
                )
            ),
        },
    )


def navigate_prices_menu():
    _options_menu(
        name="Main > Navigate > Prices",
        options={
            "A": (lambda: list_prices_by_name()),
            "S": (lambda: list_prices_by_product()),
            "D": (lambda: list_low_price_outliers()),
            "H": (
                lambda: print_help(
                    [
                        f"A: From {_product_name_} (broader)",
                        f"S: From {_product_}",
                        f"D: Lowest prices from {_product_name_}",
                        "H: Show this help message",
                        "Q: Return to navigate menu",
                    ]
                )
            ),
        },
    )


def delete_menu():
    _options_menu(
        name="Main > Delete",
        options={
            "A": (lambda: delete_product()),
            "S": (lambda: delete_price()),
            "D": (lambda: delete_by_low_price()),
            "H": (
                lambda: print_help(
                    [
                        f"A: Delete a {_product_}",
                        f"S: Delete a {_price_} registry",
                        f"D: [Caution] Remove all {_price_} from a product below a cutoff",
                        "H: Show this help message",
                        "Q: Return to main menu",
                    ]
                )
            ),
        },
    )


def update_menu():
    _options_menu(
        name="Main > Update",
        options={
            "A": (lambda: assign_category()),
            "F": (lambda: update_product()),
            "H": (
                lambda: print_help(
                    [
                        f"A: Assign {_product_category_} to {_product_name_}",
                        "F: Update product filters",
                        "H: Show this help message",
                        "Q: Return to main menu",
                    ]
                )
            ),
        },
    )


def create_menu():
    _options_menu(
        name="Main > Create",
        options={
            "A": (lambda: create_product()),
            "S": (lambda: create_product_name()),
            "D": (lambda: create_product_category()),
            "H": (
                lambda: print_help(
                    [
                        f"A: Create a {_product_} assigned to an existing {_product_name_}",
                        f"S: Create a {_product_name_} assigned to an existing {_product_category_}",
                        f"D: Create a {_product_category_}",
                        "H: Show this help message",
                        "Q: Return to main menu",
                    ]
                )
            ),
        },
    )


def pick_product_by_id(message: str = "Pick a product") -> db.products | None:
    """Gets an input fom the user and returns a product if valid, `None` otherwise."""
    id_num = input(message + " (leave blank to cancel): ")
    try:
        id_num = int(id_num)
    except ValueError:
        print("Not a valid ID number.")
        return None
    if not db.id_product_exists(id_num):
        print("This ID is not present on data.")
        return None
    return db.product_by_id(id_num)


def pick_name_by_id(message: str = "Pick a product ID") -> db.product_names | None:
    """Gets an input fom the user and returns a product if valid, `None` otherwise."""
    id_num = input_integer(message + " (leave blank to cancel)")
    if not id_num:
        print("Not a valid ID number.")
        return None
    if not db.id_name_exists(id_num):
        print("This ID is not present on data.")
        return None
    return db.product_name_by_id(id_num)


def pick_price_by_id(message: str = "Pick a price ID") -> db.prices | None:
    id_num = input_integer(message + " (leave blank to cancel)")
    if not id_num:
        print("Not a valid ID number.")
        return None
    if not db.id_price_exists(id_num):
        print("This ID is not present on data.")
        return None
    return db.price_by_id(id_num)


def print_category_names(rows: list[db.product_categories] | None = None):
    """Displays all rows from *product_categories* table to the user."""
    if not rows:
        rows = db.scan_categories()
    for row in rows:
        category_filters = handle_empty_field(row, "CategoryFilters")
        row_id = handle_empty_field(row, "Id")
        print(
            f"Id: {row_id}",
            f"{row.CategoryName}",
            f"Filters: {category_filters}",
            sep=" | ",
        )


def print_product_names(rows: list[db.product_names] | None = None):
    """Displays all rows from *product_names* table to the user."""
    if not rows:
        rows = db.scan_names()
    for row in rows:
        product_category = db.product_category_by_id(row.CategoryId)
        category_name = handle_empty_field(product_category, "CategoryName")
        name_filters = handle_empty_field(row, "NameFilters")
        row_id = handle_empty_field(row, "Id")
        print(
            f"Id: {row_id}",
            f"({category_name}) {row.ProductName}",
            f"Filters: {name_filters}",
            sep=" | ",
        )


def print_products(rows: list[db.products] | None = None):
    """Displays a list of `rows` from *products* table to the user."""
    if not rows:
        rows = db.scan_products()
    for row in rows:
        product_name_obj = db.product_name_by_id(row.NameId)
        product_name = handle_empty_field(product_name_obj, "ProductName")
        row_id = handle_empty_field(row, "Id")
        product_filters = handle_empty_field(row, "ProductFilters")
        print(
            f"Id: {row_id}",
            f"Search: {row.ProductBrand} {product_name} {row.ProductModel}",
            f"Filters: {product_filters}",
            f"Last update: {row.LastUpdate}",
            sep=" | ",
        )


def print_prices(rows: list[db.prices]):
    """Display a list of `rows` from *prices* table to the user."""
    for row in rows:
        print(
            f"Id: {row.Id}",
            f"{row.Date.strftime('%Y-%m-%d')}",
            f"{row.Currency} {row.Price:.2f}",
            f"{row.Name}",
            f"Store: {row.Store}",
            sep=" | ",
        )


def print_help(help_mgs: list[str]):
    print("\nChoose an operation to perform:", *help_mgs, sep="\n")


def list_products_by_name():
    """
    Displays available names and prompts the user to select one, if the user selects correctly, displays products with the name selected.
    """
    name_id = select_name_id()
    if name_id:
        rows = db.scan_products(name_id)
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
        stmt = delete(db.products).where(db.products.Id == row.Id)
        with Session(db.DB_ENGINE) as ses:
            ses.execute(stmt)
            ses.commit()
    except Exception as err:
        print("Not able to delete", str(err), sep="\n")


def delete_price():
    """Prompts the user to remove a price from the database."""
    row = pick_price_by_id(f"Select a {ITALIC}:price:{ENDSTYLE} ID to delete")
    if not row:
        print("This row Id doesn't exist!")
        return

    print_prices([row])
    confirm = input_confirm(f"Delete this {ITALIC}:price:{ENDSTYLE}?")
    if not confirm:
        print("Aborting operation...")
        return
    db.delete_price_rows([row])


def delete_by_low_price():
    """Prompts the user to remove all prices below a cutoff from a product."""
    prices = list_low_price_outliers(returns=True)
    confirm = input_confirm(
        f"Confirm deletion of ALL these {_price_}s? (CANNOT BE UNDONE)"
    )
    if confirm:
        db.delete_price_rows(prices)
        print(f"{len(prices)} {_price_} removed.")
        return
    print("Aborting operation...")


def create_product_category():
    """Prompts the user to create an entry to *product_categories* table."""
    category_name = db.format_name(input(f"Insert the new {_product_category_} name: "))
    category_filters = db.format_name(
        input(f"Insert the new {_product_category_} filters: ")
    )
    product_category_obj = db.product_categories(
        CategoryName=category_name, CategoryFilters=category_filters
    )
    print_category_names([product_category_obj])
    confirm = input_confirm("Add this entry to the database?")
    if not confirm:
        print("Aborting operation...")
        return
    new_id = db.add_product_category_to_db(product_category_obj)
    if new_id:
        print(f"Id for the new category is {new_id}.")
    else:
        print(
            f"Identical {ITALIC}category name{ENDSTYLE} in database, Aborting operation..."
        )


def create_product_name():
    """Prompts the user to create an entry to *product_names* table."""
    if not db.table_has_data("product_categories"):
        print(
            f"Create a {ITALIC}category name{ENDSTYLE} before you add a {_product_name_} to the database."
        )
        return
    category_id = select_category_id()
    if not category_id:
        print("Aborting operation...")
        return
    product_name = db.format_name(input(f"Insert the new {_product_name_} name: "))
    name_filters = db.format_name(input(f"Insert the new {_product_name_} filters: "))
    product_name_obj = db.product_names(
        ProductName=product_name,
        CategoryId=category_id,
        NameFilters=name_filters,
    )
    print_product_names([product_name_obj])
    confirm = input_confirm("Add this entry to the database?")
    if not confirm:
        print("Aborting operation...")
        return
    new_id = db.add_product_name_to_db(product_name_obj)
    if new_id:
        print(f"Id for the new {_product_name_} is {new_id}.")
    else:
        print(f"Identical {_product_name_} in database, Aborting operation...")


def create_product():
    if not db.table_has_data("product_names"):
        print(
            f"Create a {_product_name_} before you add a {_product_name_} to the database."
        )
        return
    name_id = select_name_id()
    if not name_id:
        print("Aborting operation...")
        return
    brand_name = db.format_name(input("Brand name: "))
    model_name = db.format_name(input("Product model: "))
    filters = db.format_name(input("Filters (e.g: foo, bar, multi_word_filter): "))
    name_obj = db.product_name_by_id(name_id)
    product_obj = db.products(
        NameId=name_obj.Id,
        ProductName=name_obj.ProductName,
        ProductModel=model_name,
        ProductBrand=brand_name,
        ProductFilters=filters,
        Created=datetime.now(),
    )
    print_products([product_obj])
    confirm = input_confirm("Add this entry to the database?")
    if not confirm:
        print("Aborting operation...")
        return
    new_id = db.add_product_to_db(product_obj)
    if not new_id:
        print(f"Identical {_product_} in database, Aborting operation...")
        return
    print(f"Id for the new {_product_} is {new_id}.")
    product_obj.Id = new_id
    collect_prices_from_products([product_obj])


def collect_prices_from_products(rows: list[db.products]):
    n, i = len(rows), 0
    while i < n:
        print(f" Collecting... {(i+1)/n*100:.2f}%", end="\r\r")
        collect.collect_prices(rows[i].Id)
        i = i + 1
    msg = f"Collected {_price_} for {n} product"
    if n > 1:
        msg = msg + "s"
    print(msg)


def list_prices_by_name():
    name_id = select_name_id()
    if not name_id:
        print("Aborting operation...")
        return
    products_ids = [i.Id for i in db.scan_products(name_id=name_id)]
    date_min = input_date("Insert a start date")
    date_max = input_date("Insert an end date", end_of_day=True)
    prices = db.scan_prices(
        product_ids=products_ids, date_max=date_max, date_min=date_min
    )
    print_prices(prices)


def list_prices_by_product():
    product_id = select_product_id()
    if not product_id:
        print("Aborting operation...")
        return
    date_min = input_date("Insert a start date")
    date_max = input_date("Insert an end date", end_of_day=True)
    prices = db.scan_prices(
        product_ids=[product_id], date_max=date_max, date_min=date_min
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
    products_ids = [i.Id for i in db.scan_products(name_id=name_id)]
    prices = db.scan_prices(product_ids=products_ids, price_max=max_price_val)
    print_prices(prices)
    if returns:
        return prices


def update_prices():
    name_id = select_name_id()
    if not name_id:
        print("Invalid Id provided.\n")
        return
    update_products = db.scan_products(name_id)
    use_specific = input_confirm("Collect prices for a single model?")
    if not use_specific:
        collect_prices_from_products(rows=update_products)
        return
    print_products(update_products)
    selected_prod = pick_product_by_id(f"Pick a product to collect {_price_}")
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
    new_filters = input(
        "Insert the new filters (retype existing ones that you want to keep): "
    )
    with Session(db.DB_ENGINE) as ses:
        selected_row = ses.execute(
            select(db.products).where(db.products.Id == row.Id)
        ).scalar_one()
        selected_row.ProductFilters = new_filters
        ses.commit()


def assign_category():
    if not db.table_has_data("product_categories"):
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
    category = db.product_category_by_id(category_id)
    name = db.product_name_by_id(name_id)
    confirm = input_confirm(
        f"Set category {category.CategoryName} to {name.ProductName}?"
    )
    if not confirm:
        print("Aborting operation...")
        return
    db.set_category_to_name(name_id, category_id)
    print("Completed")


if __name__ == "__main__":
    print("===== Price_indexr central v0.3 =====")
    main_menu()
