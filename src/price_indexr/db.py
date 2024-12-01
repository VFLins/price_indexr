from sqlalchemy import  ForeignKey, Integer, create_engine, DateTime, insert, update, select
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, Session
from typing import List
from datetime import datetime
import os

SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))

# ===================== #
# DATABASE ARCHITECTURE #
# ===================== #

DB_ENGINE = create_engine(f"sqlite:///{SCRIPT_FOLDER}\\data\\database.db", echo=False)
class dec_base(DeclarativeBase):
    pass

class product_categories(dec_base):
    __tablename__ = "product_categories"
    Category: Mapped["product_names"] = relationship(back_populates="Category")

    Id: Mapped[int] = mapped_column(primary_key=True)
    CategoryName: Mapped[str] = mapped_column()

class product_names(dec_base):
    __tablename__ = "product_names"
    Category: Mapped[List["product_categories"]] = relationship(back_populates="Category")
    Name: Mapped["products"] = relationship(back_populates="Name")

    Id: Mapped[int] = mapped_column(primary_key=True)
    CategoryId: Mapped[int] = mapped_column(ForeignKey("product_categories.Id"), nullable=True)
    ProductName: Mapped[str] = mapped_column()

class prices(dec_base):
    __tablename__ = "prices"
    Product: Mapped[List["products"]] = relationship(back_populates="Product")

    Id: Mapped[int] = mapped_column(primary_key=True)
    ProductId: Mapped[int] = mapped_column(ForeignKey("products.Id"))
    Date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    Currency: Mapped[str] = mapped_column()
    Price: Mapped[float] = mapped_column()
    Name: Mapped[str] = mapped_column()
    Store: Mapped[str] = mapped_column()
    Url: Mapped[str] = mapped_column()

class products(dec_base):
    __tablename__ = "products"
    Product: Mapped["prices"] = relationship(back_populates="Product")
    Name: Mapped[List["product_names"]] = relationship(back_populates="Name")

    Id: Mapped[int] = mapped_column(primary_key=True)
    NameId: Mapped[int] = mapped_column(ForeignKey("product_names.Id"))
    ProductName: Mapped[str] = mapped_column()
    ProductModel: Mapped[str] = mapped_column()
    ProductBrand: Mapped[str] = mapped_column()
    ProductFilters: Mapped[str] = mapped_column()
    Created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    LastUpdate: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
dec_base.metadata.create_all(DB_ENGINE)

