from price_indexr import *
from sqlalchemy import select, delete

print("===== Price_indexr central v0.0.1 =====",
        "Choose an operation to perform:", 
        "C: Create a new product to price index", 
        "L: List all products", 
        "U: Update a recorded product",
        "D: Delete a product by ID number", 
        "Q: Quit", sep="\n")

def scan_names() -> list:
    """Read product_names table to get a list of rows as dicts"""
    output = []
    with Session(DB_ENGINE) as ses:
        stmt = select(product_names())
        result = ses.execute(stmt).scalars()

        for i in result:
            output.append({
                "id": i.Id, 
                "name": i.Name})
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
        case "Update": print(run_next); quit()
        case "Delete": delete_product()
        

def confirmation(ask: str) -> Bool:
    def get_input():
        inp = input(ask + ". Confirm? [Y/n]")
        return inp
    
    inp = get_input()
    while True:
        match inp.upper():
            case "Y" | "": 
                output = True
                break
            case "N":
                output = False
                break
            case _: 
                print("Invalid answer!")
                inp = get_input()



def list_products() -> None:
    

    rows = scan_products()
    for row in rows:
        print(
            f"Id: {row['id']}",
            f"Search: {row['brand']} {row['name']} {row['model']}",
            f"Filters: {row['filters']}",
            f"Last update: {row['last_update']}", sep=" | ")

def delete_product() -> None:
    while True:
        try:
            id_num = input("Insert the product ID to delete: ")
            id_num = int(id_num)
            break
        except:
            print("Insert a valid ID!")
    
    rows = scan_products()
    id_exists = False
    for row in rows:
        if row['id'] == id_num:
            id_exists = True
            break

    if id_exists:
        stmt = delete(products).where(products.Id == id_num)
        with Session(DB_ENGINE) as ses:
            ses.execute(stmt)
            ses.commit()
    else: print("This ID does't exist yet!")
    main_menu()

def create_product():
    created = datetime.now()
    brand = input("Brand name: ")
    name = input("Product name: ")
    model = input("Product model: ")
    filters = input("Filters: ")

    print(
        "\nYou will create this entry:\n"
        f"Search: {brand} {name} {model}",
        f"Filters: {filters}",
        f"Created: {created}", sep=" | ")
    
    checkout = confirmation("This data will be saved")
    if checkout:
        stmt = products(
            ProductName=name,
            ProductModel=model,
            ProductBrand=brand,
            ProductFilters=filters,
            Created = created)
        with Session(DB_ENGINE) as ses:
            ses.add(stmt)
            ses.commit()

        stmt = select(products).where(products.Created == created)
        result = ses.execute(stmt).scalars()
        for i in result:
            created_id = i.Id
        print("\nCollecting current prices...")
        collect_prices(created_id)
        print(f"\nThe ID for this product is: {created_id}")
        print("Transaction success!")
    else:
        print("Transaction cancelled!")
    main_menu()

if __name__ == "__main__":
    main_menu()