from typing import List
from price_indexr import *
from sqlalchemy import ForeignKey, Integer, create_engine, DateTime, insert, update, select
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, Session
from datetime import date, datetime

def scan_products() -> list:
    output = []
    with Session(DB_ENGINE) as ses:
        stmt = select(products)
        result = ses.execute(stmt).scalars()

        for i in result:
                output.append([i.Id, i.LastUpdate])

if __name__ == "__main__":
    print(scan_products())