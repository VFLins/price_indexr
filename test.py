from typing import List
import os
from sqlalchemy import ForeignKey, Integer, create_engine, DateTime, insert
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, sessionmaker
from typing import Optional
from datetime import date, datetime

SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))

class dec_base(DeclarativeBase): pass
DB_ENGINE = create_engine(f"sqlite:///{SCRIPT_FOLDER}\data\database.sqlite", echo=True)
#DB_SESSION = sessionmaker(bind=DB_ENGINE)
#DB_MSESSION = DB_SESSION()

class prices(dec_base):
    __tablename__ = "prices"
    Id: Mapped[int] = mapped_column(primary_key=True)
    ProductId: Mapped[int] = mapped_column(ForeignKey("products.Id"))
    Product: Mapped[List["products"]] = relationship(back_populates="Product")
    Model: Mapped[str] = mapped_column()
    Date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    Currency: Mapped[str] = mapped_column()
    Price: Mapped[float] = mapped_column()
    Name: Mapped[str] = mapped_column()
    Store: Mapped[str] = mapped_column()
    Url: Mapped[str] = mapped_column()

class products(dec_base):
    __tablename__ = "products"
    Id: Mapped[int] = mapped_column(primary_key=True)
    Product: Mapped["prices"] = relationship(back_populates="Product")
    Created: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    LastUpdate: Mapped[datetime] = mapped_column(DateTime(timezone=True))


dec_base.metadata.create_all(DB_ENGINE)

stmt = (
    insert(prices).
    values(
        Product='geforce rtx 3050', 
        Model='galax ex',
        Date=datetime.now(),
        Currency="R$",
        Price=1720.59,
        Name="Placa De Vídeo Galax Geforce RTX 3050 Ex 8GB GDDR6",
        Store="KaBuM!",
        Url="https://www.kabum.com.br/produto/320250/placa-de-video-galax-nvidia-geforce-rtx-3050-ex-oc-8gb-gddr6-lhr-1-click-128-bits-35nsl8md6yex?srsltid=Ad5pg_E93vNYIyyNwSwnn5Vm7KG2F1dCN33aqOb-c2uw65qxlW761FCmP6U"))

DB_MSESSION.execute(stmt)
