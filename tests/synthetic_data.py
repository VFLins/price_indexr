from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric


GENERIC_PRICES_COLS = {
    "Id": Column("Id", Integer, primary_key=True),
    "ProductId": Column("ProductId", Integer),
    "Date": Column("Date", String),
    "Currency": Column("Currency", String),
    "Price": Column("Price", Numeric),
    "Name": Column("Name", String),
    "Store": Column("Store", String),
    "Url": Column("Url", String),
}


def as_dt(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")


product_categories_data = [
    {
        "Id": 1,
        "CategoryName": "Graphics Cards",
        "CategoryFilters": "Water_block, Cooler, Notebook, Computer, Used",
    },
    {
        "Id": 2,
        "CategoryName": "Computer Processor",
        "CategoryFilters": "Cooler, Computer, Notebook, Used",
    },
    {"Id": 3, "CategoryName": "Sata SSDs", "CategoryFilters": "Used"},
]


product_names_data = [
    {
        "Id": 1,
        "CategoryId": 1,
        "ProductName": "Geforce Rtx 3050",
        "NameFilters": None,
        "SupersededBy": None,
    },
    {
        "Id": 2,
        "CategoryId": 1,
        "ProductName": "Geforce Rtx 4060",
        "NameFilters": None,
        "SupersededBy": None,
    },
    {
        "Id": 3,
        "CategoryId": 1,
        "ProductName": "Geforce Rtx 4060 Ti",
        "NameFilters": "16Gb 16_Gb",
        "SupersededBy": None,
    },
    {
        "Id": 4,
        "CategoryId": 2,
        "ProductName": "Core i5 13400F",
        "NameFilters": None,
        "SupersededBy": None,
    },
    {
        "Id": 5,
        "CategoryId": 2,
        "ProductName": "Core i3 12100",
        "NameFilters": None,
        "SupersededBy": None,
    },
    {
        "Id": 6,
        "CategoryId": 3,
        "ProductName": "SSD Sata 1Tb",
        "NameFilters": None,
        "SupersededBy": None,
    },
    {
        "Id": 7,
        "CategoryId": 3,
        "ProductName": "SSD Sata 500Gb",
        "NameFilters": None,
        "SupersededBy": None,
    },
    {
        "Id": 8,
        "CategoryId": 3,
        "ProductName": "SSD Sata 480Gb",
        "NameFilters": None,
        "SupersededBy": None,
    },
]


products_data = [
    {
        "Id": 1,
        "NameId": 1,
        "ProductName": "Geforce Rtx 3050",
        "ProductModel": "Dual",
        "ProductBrand": "Asus",
        "ProductFilters": "",
        "Created": as_dt("2025-01-10 12:10:29.289034"),
        "LastUpdate": as_dt("2025-01-10 12:11:29.289034"),
    },
    {
        "Id": 2,
        "NameId": 1,
        "ProductName": "Geforce Rtx 3050",
        "ProductModel": "Stormx",
        "ProductBrand": "Palit",
        "ProductFilters": "",
        "Created": as_dt("2025-01-10 12:13:29.289034"),
        "LastUpdate": as_dt("2025-01-10 14:10:29.289034"),
    },
    {
        "Id": 3,
        "NameId": 3,
        "ProductName": "Geforce Rtx 4060 Ti",
        "ProductModel": "Dual",
        "ProductBrand": "Asus",
        "ProductFilters": "",
        "Created": as_dt("2025-01-10 12:12:39.289034"),
        "LastUpdate": as_dt("2025-01-10 13:14:29.289034"),
    },
    {
        "Id": 4,
        "NameId": 4,
        "ProductName": "SSD 1Tb",
        "ProductModel": "Red WDS100T1R0A",
        "ProductBrand": "WD",
        "ProductFilters": "",
        "Created": as_dt("2025-01-12 12:12:39.289034"),
        "LastUpdate": as_dt("2025-01-12 13:14:29.289034"),
    },
    {
        "Id": 5,
        "NameId": 5,
        "ProductName": "SSD 500Gb",
        "ProductModel": "Blue WDS500G3B0A",
        "ProductBrand": "WD",
        "ProductFilters": "",
        "Created": as_dt("2025-01-12 12:12:39.289034"),
        "LastUpdate": as_dt("2025-01-12 13:14:29.289034"),
    },
    {
        "Id": 6,
        "NameId": 8,
        "ProductName": "SSD 240Gb",
        "ProductModel": "Green WDS250G2G0C ",
        "ProductBrand": "WD",
        "ProductFilters": "",
        "Created": as_dt("2025-01-12 12:13:31.289034"),
        "LastUpdate": None,
    },
]


products_data2 = [
    {
        "Id": 1,
        "NameId": 1,
        "ProductName": "Geforce Rtx 3050",
        "ProductModel": "Dual",
        "ProductBrand": "Asus",
        "ProductFilters": "",
        "Created": as_dt("2025-01-10 12:10:29.289034"),
        "LastUpdate": as_dt("2025-01-10 12:11:29.289034"),
    },
    {
        "Id": 2,
        "NameId": 1,
        "ProductName": "Geforce Rtx 3050",
        "ProductModel": "Stormx",
        "ProductBrand": "Palit",
        "ProductFilters": "",
        "Created": as_dt("2025-01-10 12:13:29.289034"),
        "LastUpdate": as_dt("2025-01-10 14:10:29.289034"),
    },
    {
        "Id": 3,
        "NameId": 3,
        "ProductName": "Geforce Rtx 4060 Ti",
        "ProductModel": "Dual",
        "ProductBrand": "Asus",
        "ProductFilters": "",
        "Created": as_dt("2025-01-10 12:12:39.289034"),
        "LastUpdate": as_dt("2025-01-10 13:14:29.289034"),
    },
    {
        "Id": 4,
        "NameId": 4,
        "ProductName": "SSD 1Tb",
        "ProductModel": "Red WDS100T1R0A",
        "ProductBrand": "WD",
        "ProductFilters": "",
        "Created": as_dt("2025-01-12 12:12:39.289034"),
        "LastUpdate": as_dt("2025-01-12 13:14:29.289034"),
    },
    {
        "Id": 5,
        "NameId": 5,
        "ProductName": "SSD 500Gb",
        "ProductModel": "Blue WDS500G3B0A",
        "ProductBrand": "WD",
        "ProductFilters": "",
        "Created": as_dt("2025-01-12 12:12:39.289034"),
        "LastUpdate": None,
    },
    {
        "Id": 6,
        "NameId": 8,
        "ProductName": "SSD 240Gb",
        "ProductModel": "Green WDS250G2G0C ",
        "ProductBrand": "WD",
        "ProductFilters": "",
        "Created": as_dt("2025-01-12 12:13:31.289034"),
        "LastUpdate": as_dt("2025-01-12 13:14:29.289034"),
    },
]


prices_data = [
    {
        "Id": 1,
        "ProductId": 1,
        "Date": as_dt("2025-01-10 12:11:29.289034"),
        "Currency": "R$",
        "Price": 1199.99,
        "Name": "Placa de Vídeo Asus Dual NVIDIA GeForce RTX 3050 2X, 6GB, GDDR6, DLSS, Ray Tracing",
        "Store": "Terabyteshop",
        "Url": "https://www.terabyteshop.com.br/produto/33039/placa-de-video-asus-dual-nvidia-geforce-rtx-3050-2x-6gb-gddr6-dlss-ray-tracing?srsltid=AfmBOooiPeKj0KIVD1n1PrZs9ydZ0Ur8FXF1fYE4DkHJZqgCXAiQyguh",
    },
    {
        "Id": 2,
        "ProductId": 2,
        "Date": as_dt("2025-01-12 12:10:29.289034"),
        "Currency": "R$",
        "Price": 1279.99,
        "Name": "Placa de Video Palit GeForce RTX 3050 StormX, 6GB, GDDR6, 96-bit, NE63050018JE-1070F",
        "Store": "Pichau",
        "Url": "https://www.pichau.com.br/placa-de-video-palit-geforce-rtx-3050-stormx-6gb-gddr6-96-bit-ne63050018je-1070f?srsltid=AfmBOoqEYYDgcjZtQOiyuU-iclPTONBb8MZbhxn4TlYUJa-m8znha4E-",
    },
    {
        "Id": 3,
        "ProductId": 3,
        "Date": as_dt("2025-01-12 12:35:26.418760"),
        "Currency": "R$",
        "Price": 2999.9,
        "Name": "Placa De Video Asus GeForce RTX 4060 Ti Oc Evo 8GB GDDR6 128 Bits - Dual ...",
        "Store": "Terabyteshop",
        "Url": "https://www.terabyteshop.com.br/produto/29271/placa-de-video-asus-dual-nvidia-geforce-rtx-4060-ti-evo-oc-8gb-gddr6-dlss-ray-tracing-dual-rtx4060ti-o8g-evo?srsltid=AfmBOorCGAuHRbnkGwscI4cIKTYzur8aWL1gT0SiZxhjc5XrDmSDI7DN",
    },
    {
        "Id": 4,
        "ProductId": 4,
        "Date": as_dt("2025-01-12 12:35:52.944107"),
        "Currency": "R$",
        "Price": 1088.21,
        "Name": 'Ssd Wd 1TB Sata III Red Nas Sa500 2,5" - WDS100T1R0A',
        "Store": "Amazon.com.br - Seller",
        "Url": "https://www.amazon.com.br/Red-SA500-NAS-NAND-interno/dp/B07YFG3R5N?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&psc=1&smid=A3LXIKUF05VWWL",
    },
    {
        "Id": 5,
        "ProductId": 5,
        "Date": as_dt("2025-01-12 12:36:31.407773"),
        "Currency": "R$",
        "Price": 475,
        "Name": 'Ssd Wd Blue SA510 500GB, Sata 2,5" - WDS500G3B0A',
        "Store": "Mercado Livre",
        "Url": "https://www.mercadolivre.com.br/disco-solido-interno-western-digital-sa510-wds500g3b0a-500gb-azul/p/MLB19900731?matt_tool=18956390&utm_source=google_shopping&utm_medium=organic&pdp_filters=item_id%3AMLB5068612076&from=gshop",
    },
]
