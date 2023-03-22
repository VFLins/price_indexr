from price_indexr import *

print("===== Price_indexr central v0.0.1 =====",
        "Choose an operation to perform:", 
        "L: List all products", 
        "D: Delete product by ID number", 
        "C: Create a new product to price index", sep="\n")

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
    inp = input("\nChoose a letter and press enter:")
    return inp

def main_menu():
    inp = get_input()
    while True:
        match inp.upper():
            case "L": run_next = "List"; break
            case "D": run_next = "Delete"; break
            case "C": run_next = "Create"; break
            case _: 
                print("Insert a valid value!")
                inp = get_input()

    match run_next:
        case "List": 
            list_products()
        case "Delete":
            print("Delete")
        case "Create":
            print("Create")

def list_products():
    print(scan_products())
    main_menu()

if __name__ == "__main__":
    main_menu()