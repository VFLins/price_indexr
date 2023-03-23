from price_indexr import *
from sqlalchemy import select

print("===== Price_indexr central v0.0.1 =====",
        "Choose an operation to perform:", 
        "C: Create a new product to price index", 
        "L: List all products", 
        "U: Update a recorded product",
        "D: Delete a product by ID number", 
        "Q: Quit", sep="\n")

def scan_products() -> list:
    """Read products table to get pairs of Id and LastUpdate
    of products that hasn't been updated in the last 7 days"""
    output = []
    with Session(DB_ENGINE) as ses:
        stmt = select(products)
        result = ses.execute(stmt).scalars()

        for i in result:
            output.append({
                "id" : i.Id, 
                "name" : i.ProductName,
                "model" : i.ProductModel,
                "brand" : i.ProductBrand,
                "filters" : i.ProductFilters,
                "created" : i.Created,
                "last_update" : i.LastUpdate})
    return output

def get_input():
    inp = input("\nChoose a letter and press enter: ")
    return inp

def main_menu():
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
        case "Update": print(run_next)
        case "Delete":print(run_next)
        

def list_products():
    rows = scan_products()
    for row in rows:
        print(
            f"Id: {row['id']}",
            f"Search: {row['brand']} {row['name']} {row['model']} {row['filters']}",
            f"Last update: {row['last_update']}", sep=" | ")

def create_product():
    created = datetime.now()
    name = input("Product name: ")
    brand = input("Brand name: ")
    model = input("Product model: ")
    filters = input("Filters: ")

    print(
        "\nYou will create this entry:\n"
        f"Search: {brand} {name} {model} {filters}",
        f"Created: {created}", sep=" | ")
    
    checkout = input("Confirm? [Y/n] ")
    while True:
        match checkout.upper():
            case "Y" | "":
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
                        print(f"\nThe ID for this product is: {i.Id}")
                        created_id = i.Id
                print("\nCollecting current prices...")
                collect_prices(created_id)
                print("Transaction success!")
            case "N":
                print("Transaction cancelled!")
            case _:
                print("Insert a valid response (y, or n)")
                checkout = input("Confirm? [Y/n] ")

if __name__ == "__main__":
    main_menu()