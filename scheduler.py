from typing import List
from price_indexr import *
from sqlalchemy import ForeignKey, Integer, create_engine, DateTime, insert, update, select
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, Session
from datetime import date, datetime

def scan_products() -> list:
    """Read products table to get pairs of Id and LastUpdate"""
    output = []
    with Session(DB_ENGINE) as ses:
        stmt = select(products)
        result = ses.execute(stmt).scalars()

        for i in result:
                output.append((i.Id, i.LastUpdate))
    return output


if __name__ == "__main__":
    print(scan_products())