from price_indexr import *
from sqlalchemy import select, delete

def scan_names() -> list:
    """Read product_names table to get a list of rows as dicts"""
    output = []
    with Session(DB_ENGINE) as ses:
        stmt = select(product_names)
        result = ses.execute(stmt).scalars()

        for i in result:
            output.append({
                "id": i.Id, 
                "name": i.ProductName})
    return output

def scan_products() -> list:
    """Read products table to get a list of rows as dicts"""
    output = []
    with Session(DB_ENGINE) as ses:
        stmt = select(products)
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

def main_menu():
    while True:
        def get_input():
            inp = input("\nChoose a letter and press enter: ")
            return inp
        
        inp = get_input()
        while True:
            match inp.upper():
                case "C": run_next = "Create"; break
                case "L": run_next = "List"; break
                case "U": run_next = "Update"; break
                case "D": run_next = "Delete"; break
                case "Q": quit()
                case _: 
                    print("Insert a valid value!")
                    inp = get_input()

        match run_next:
            case "Create": create_product()
            case "List": list_products()
            case "Update": update_product()
            case "Delete": delete_product()        

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
        except IndexError:
            print("This ID doesn't exists yet!")
        except:
            quit()
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
            stmt = delete(products).where(products.Id == id_num)
            with Session(DB_ENGINE) as ses:
                ses.execute(stmt)
                ses.commit()
        except Exception as DeletionError:
            print("Not able to delete", DeletionError, sep="\n")
    else: quit()

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
        name_stmt = product_names(ProductName=name)
        with Session(DB_ENGINE) as ses:
            # Save new name
            ses.add(name_stmt)
            ses.commit()
    with Session(DB_ENGINE) as ses:
        # Get id for the used name
        stmt = select(product_names).where(product_names.ProductName == name)
        result = ses.execute(stmt).scalar_one()
        new_name_id = result.Id

    checkout = confirmation("This data will be saved")
    if checkout:            
        prod_stmt = products(
            NameId=new_name_id,
            ProductName=name,
            ProductModel=model,
            ProductBrand=brand,
            ProductFilters=filters,
            Created=created)
        with Session(DB_ENGINE) as ses:
            ses.add(prod_stmt)
            ses.commit()
            # Get created product id
            stmt = select(products).where(products.Created == created)
            result = ses.execute(stmt).scalars()

        for i in result: new_product_id = i.Id
        print("\nCollecting current prices...")
        collect_prices(new_product_id)
        print(f"\nThe ID for this product is: {new_product_id}")
        print("Transaction success!")
    else:
        print("Transaction cancelled!")


def update_product():
    print("You can only update the filters's field in this version...")
    row = pick_product_by_id("Select the product with the filter to update")
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
        with Session(DB_ENGINE) as ses:
            selected_row = ses.execute(select(products).where(products.Id == id_num)).scalar_one()
            selected_row.ProductFilters = new_filters
            ses.commit()

if __name__ == "__main__":
    print("===== Price_indexr central v0.1 =====",
        "Choose an operation to perform:", 
        "C: Create a new product to price index", 
        "L: List all products", 
        "U: Update a recorded product",
        "D: Delete a product by ID number", 
        "Q: Quit", sep="\n")
    
    main_menu()