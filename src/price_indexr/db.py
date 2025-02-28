from sqlalchemy import (
    Table,
    Column,
    MetaData,
    Engine,
    ForeignKey,
    DateTime,
    create_engine,
    update,
    delete,
    insert,
    case,
    select,
    text,
    table,
    func,
    and_,
    or_,
    literal_column,
)
from sqlalchemy.orm import (
    Mapped,
    MappedColumn,
    mapped_column,
    DeclarativeBase,
    relationship,
    Session,
    declared_attr,
)
from warnings import warn
from sqlalchemy.exc import AmbiguousForeignKeysError, InvalidRequestError
from typing import List, Literal, Type, final
from datetime import datetime
import os
import re


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
DATABASE_FILE = os.path.join(DATA_DIR, "price_indexr.db")

os.makedirs(DATA_DIR, exist_ok=True)

# ===================== #
# DATABASE ARCHITECTURE #
# ===================== #

DB_ENGINE = create_engine(f"sqlite:///{DATABASE_FILE}", echo=False)
DB_METADATA = MetaData()
"""Metadata from the database's state upon startup."""
DB_METADATA.reflect(DB_ENGINE)


class TableMapping(DeclarativeBase):
    """Base class for table objects using SQLAlchemy's ORM capabilities."""

    @classmethod
    @final
    def mapped_colnames(cls) -> tuple[str]:
        return tuple(col.name for col in cls.__table__.c)

    @classmethod
    @final
    def mapped_tables(cls) -> dict[str, Type[DeclarativeBase]]:
        subclasses = cls.__subclasses__()
        return {cls.__tablename__: cls for cls in subclasses}


class product_categories_model:
    @declared_attr
    def Category(cls) -> Mapped["product_names"]:
        return relationship(back_populates="Category")

    Id: Mapped[int] = mapped_column(primary_key=True)
    CategoryName: Mapped[str] = mapped_column()
    CategoryFilters: Mapped[str] = mapped_column(nullable=True)


class product_names_model:
    @declared_attr
    def Category(cls) -> Mapped[List["product_categories"]]:
        return relationship(back_populates="Category")

    @declared_attr
    def RelName(cls) -> Mapped["products"]:
        return relationship(back_populates="RelName")

    Id: Mapped[int] = mapped_column(primary_key=True)
    CategoryId: Mapped[int] = mapped_column(
        ForeignKey("product_categories.Id"), nullable=True
    )
    ProductName: Mapped[str] = mapped_column()


class products_model:
    @declared_attr
    def Product(cls) -> Mapped["prices"]:
        return relationship(back_populates="Product")

    @declared_attr
    def RelName(cls) -> Mapped[List["product_names"]]:
        return relationship(back_populates="RelName")

    Id: Mapped[int] = mapped_column(primary_key=True)
    NameId: Mapped[int] = mapped_column(ForeignKey("product_names.Id"))
    ProductName: Mapped[str] = mapped_column()
    ProductModel: Mapped[str] = mapped_column()
    ProductBrand: Mapped[str] = mapped_column()
    ProductFilters: Mapped[str] = mapped_column()
    Created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    LastUpdate: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class prices_model:
    @declared_attr
    def Product(cls) -> Mapped[List["products"]]:
        return relationship(back_populates="Product")

    Id: Mapped[int] = mapped_column(primary_key=True)
    ProductId: Mapped[int] = mapped_column(ForeignKey("products.Id"))
    Date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    Currency: Mapped[str] = mapped_column()
    Price: Mapped[float] = mapped_column()
    Name: Mapped[str] = mapped_column()
    Store: Mapped[str] = mapped_column()
    Url: Mapped[str] = mapped_column()


class product_categories(product_categories_model, TableMapping):
    __tablename__ = "product_categories"


class product_names(product_names_model, TableMapping):
    __tablename__ = "product_names"


class products(products_model, TableMapping):
    __tablename__ = "products"


class prices(prices_model, TableMapping):
    __tablename__ = "prices"


def _different_null_vals_positions(
    column_obj1: Column, column_obj2: Column, engine: Engine = DB_ENGINE
) -> bool:
    """Compares position of every NULL value between `column_obj1` and `column_obj2`,
    will return `False` only if they both have the same same amount of NULL values
    and all in the same positions.
    """
    if column_obj1 == column_obj2:
        return False
    cond1 = and_(column_obj1.is_(None), column_obj2.is_not(None))
    cond2 = and_(column_obj1.is_not(None), column_obj2.is_(None))
    with Session(engine) as ses:
        stmt = (
            select(func.count())
            .select_from(column_obj1.table)
            .join(
                column_obj2.table,
                column_obj1.table.c["Id"] == column_obj2.table.c["Id"],
            )
            .where(or_(cond1, cond2))
        )
        result = ses.execute(stmt)
        return bool(result.scalar())


def _table_missing_columns(
    table_name: str,
    table_declared: Type[TableMapping],
    meta_data: MetaData = DB_METADATA,
) -> list[Column]:
    """Return a list of SQLAlchemy `Column` that are missing in the database.

    **Args**
        `table_name`: the table to look for in the database
        `table_declared`: must be a table declared in sqlalchemy ORM
        `meta_data`: metadata reflecting the desired database
    """
    try:
        _ = table_declared.__tablename__
        table_in_code = table_declared.__table__
    except AttributeError:
        raise ValueError(f"{table_declared=} does not inherit from `TableMapping`.")
    colnames_in_db = [col.name for col in meta_data.tables[table_name].c]
    return [col for col in table_in_code.c if col.name not in colnames_in_db]


def _column_length(column_obj: Column, engine: Engine = DB_ENGINE) -> int:
    """Return number of rows in a column, compatible with databases with COUNT function."""
    with Session(engine) as ses:
        return ses.scalar(select(func.count(column_obj)))


def _columns_are_identical(
    column_obj1: Column, column_obj2: Column, engine: Engine = DB_ENGINE
) -> bool:
    colname1, tablename1 = column_obj1.name, column_obj1.table.name
    colname2, tablename2 = column_obj2.name, column_obj2.table.name
    if colname1 != colname2:
        return False
    if tablename1 == tablename2:
        return True
    col1_empty = _column_length(column_obj1, engine=engine) == 0
    col2_empty = _column_length(column_obj2, engine=engine) == 0
    if col1_empty and col2_empty:
        return True
    if _different_null_vals_positions(column_obj1, column_obj2, engine):
        return False
    with Session(engine) as ses:
        stmt = (
            select(
                case(
                    (
                        func.coalesce(column_obj1, "")
                        == func.coalesce(column_obj2, ""),
                        1,
                    ),
                    else_=0,
                )
            )
            .select_from(column_obj1.table)
            .join(
                column_obj2.table,
                column_obj1.table.c["Id"] == column_obj2.table.c["Id"],
            )
        )
        result = ses.execute(stmt)
        return bool(result.scalar())


def _tables_are_identical(
    table_obj1: Table,
    table_obj2: Table,
    warn_: bool = False,
    engine: Engine = DB_ENGINE,
) -> bool:
    """Check if two tables have the *exact* same columns and same data across those columns."""
    tablename1, tablename2 = table_obj1.name, table_obj2.name
    if not _tables_with_same_columns(tablename1, tablename2, engine=engine):
        return False
    column_set = [col.name for col in table_obj1.columns]
    for colname in column_set:
        if not _columns_are_identical(
            table_obj1.c[colname], table_obj2.c[colname], engine=engine
        ):
            if warn_:
                warn(
                    f"Data not identical in column {colname}, evaluation order={column_set}"
                )
            return False
    return True


def _tables_have_same_data(
    table_obj1: Table, table_obj2: Table, engine: Engine = DB_ENGINE
) -> bool:
    """Checks if all data found in `table_obj1` can be found in `table_obj2`."""
    meta = MetaData()
    meta.reflect(engine)
    # use table from metadata instead
    tablename1, tablename2 = table_obj1.name, table_obj2.name
    table_obj1, table_obj2 = meta.tables[tablename1], meta.tables[tablename2]
    # compare cols presence before comparing contents
    expected_colnames = [col.name for col in table_obj1.columns]
    table2_colnames = [col.name for col in table_obj2.columns]
    if not all(colname in table2_colnames for colname in expected_colnames):
        print(f"Not all columns of '{table_obj1.name}' are present in '{table_obj2.name}'.")
        return False
    for col2 in table_obj2.columns:
        if col2.name in expected_colnames:
            col1 = table_obj1.columns[col2.name]
            if not _columns_are_identical(col1, col2, engine=engine):
                print(
                    f"Data in '{col1.name}' not the same across tables '{table_obj1.name}' and '{table_obj2.name}'"
                )
                return False
    return True


def _tables_with_same_columns(*tablenames: str, engine: Engine = DB_ENGINE) -> bool:
    """Boolean value indicating if tables with `tablenames` in the database have the same column set.
    Raises `KeyError` if one of the `tablenames` are not present in the database."""
    meta = MetaData()
    meta.reflect(engine)
    tables_in_db = [meta.tables[tbl_name] for tbl_name in tablenames]
    tables_colnames = [set(col.name for col in tbl.columns) for tbl in tables_in_db]
    return all(col_name == tables_colnames[0] for col_name in tables_colnames)


def _create_backup_table(
    table_mapping: Type[TableMapping],
    engine: Engine = DB_ENGINE,
    mapper: Type[DeclarativeBase] = TableMapping
) -> Table:
    """Create a backup table from `table_mapping`'s table if it's present in the database.
    Returns a `Table` object from the backup table generated.
    Raises a `RuntimeError` if the data cannot be loaded to the backup table,
    or if `table_mapping`'s table isn't present in the database.
    """
    metadata, tablename = mapper.metadata, table_mapping.__tablename__

    if tablename not in metadata.tables.keys():
        raise RuntimeError("Could not find table to be backed-up in the database.")
    table_model_obj = table_mapping.__mro__[1]

    existing_backup_table = metadata.tables.get("ephemeral_backup_table")
    if existing_backup_table is not None:
        metadata.drop_all(bind=engine, tables=[existing_backup_table])
        metadata._remove_table(name="ephemeral_backup_table", schema=None)

    class ephemeral_backup_table(table_model_obj, mapper):
        __tablename__ = "ephemeral_backup_table"
        # __table_args__ = {"extend_existing": True}

    colnames_in_db = tuple(col.name for col in metadata.tables[tablename].c)
    with Session(engine) as ses:
        metadata.create_all(bind=engine, tables=[ephemeral_backup_table.__table__])
        metadata._add_table(
            name="ephemeral_backup_table", schema=None,
            table=ephemeral_backup_table.__table__
        )
        stmt = insert(ephemeral_backup_table).from_select(
            colnames_in_db, select(*metadata.tables[tablename].c)
        )
        ses.execute(stmt)
        ses.commit()

    if not _tables_have_same_data(
        metadata.tables[tablename],
        metadata.tables["ephemeral_backup_table"],
        engine=engine
    ):
        raise RuntimeError(
            "Could not load data to a backup table before migration."
        )
    return metadata.tables["ephemeral_backup_table"]


def _reset_table_schema_in_db(table_mapping: Type[TableMapping]):
    """Backs up data from `table_mapping`, then recreates it's table restoring
    data from the backup. Expects new columns to be nullable."""
    backup_table = _create_backup_table(table_mapping)
    backup_tablename = backup_table.__tablename__
    TableMapping.metadata.drop_all(DB_ENGINE, tables=[table_mapping.__table__])
    TableMapping.metadata.create_all(DB_ENGINE, tables=[table_mapping.__table__])

    colnames_in_db = tuple(col.name for col in DB_METADATA.tables[backup_tablename].c)
    with Session(DB_ENGINE) as ses:
        stmt = insert(table_mapping).from_select(
            colnames_in_db, select(*backup_table.__table__.c)
        )
        ses.execute(stmt)
        ses.commit()


def _table_update_migration(table_mapping: Type[TableMapping]):
    tablename = table_mapping.__tablename__
    missing_cols = _table_missing_columns(
        table_name=tablename, table_declared=table_mapping
    )
    if len(missing_cols) == 0:
        return
    for col in missing_cols:
        if not col.nullable:
            raise NotImplementedError(
                f"Column {col} is not nullable, can only create new nullable columns."
            )

    with Session(DB_ENGINE) as ses:
        # turn foreign key restraint off before recreating tables
        ses.execute(text("PRAGMA foreign_keys = 0;"))
        _reset_table_schema_in_db(table_mapping)
        ses.execute(text("PRAGMA foreign_keys = 1;"))
        ses.commit()
    return


def _recreate_updated_tables(table_mapping: TableMapping):
    tablename: str = table_mapping.__tablename__
    # https://stackoverflow.com/questions/21310549/list-database-tables-with-sqlalchemy
    table_metadata = DB_METADATA.tables[tablename]
    columns_expected: tuple = table_mapping.mapped_colnames()
    for col in columns_expected:
        if col not in [col.name for col in table_metadata.c]:
            _table_update_migration(table_mapping)


TableMapping.metadata.create_all(DB_ENGINE)
# refresh metadata
DB_METADATA.reflect(DB_ENGINE)
for mapped_table in [prices, products, product_names, product_categories]:
    _recreate_updated_tables(mapped_table)


def format_name(name: str) -> str:
    """Returns `name` in the format it should be retrieved from/inserted to the database."""
    return re.sub(" +", " ", name.title())


def table_has_data(tablename: Literal["prices", "product_names", "product_categories"]):
    stmt = select(func.count()).select_from(
        select(literal_column("1")).select_from(table(tablename)).limit(1).subquery()
    )
    with Session(DB_ENGINE) as ses:
        return bool(ses.execute(stmt).scalar())


def scan_categories() -> list[product_categories]:
    """Read *product_categories* table to get a list of rows."""
    with Session(DB_ENGINE) as ses:
        stmt = select(product_categories)
        result = ses.execute(stmt).scalars()
        return [row for row in result]


def scan_names() -> list[product_names]:
    """Read *product_names* table to get a list of rows."""
    with Session(DB_ENGINE) as ses:
        stmt = select(product_names)
        result = ses.execute(stmt).scalars()
        return [row for row in result]


def scan_products(name_id: int | None = None) -> list[products]:
    """
    Read *products* table to get a list of rows.

    **Args**
        `name_id`: ID number of the desired name. `None`, if should get all products.
    """
    stmt = select(products)
    if name_id:
        stmt = stmt.where(products.NameId == name_id)
    with Session(DB_ENGINE) as ses:
        result = ses.execute(stmt).scalars()
        return [row for row in result]


def scan_prices(
    product_ids: list[int] | None = None,
    date_max: datetime | None = None,
    date_min: datetime | None = None,
    price_max: float | None = None,
    price_min: float | None = None,
) -> list[prices]:
    """Read *prices* table to get a list of rows.

    **Args**
        `product_ids`: list of ID numbers of the desired products. `None` if should get from all products.
        `date_max`: Maximum date to retrieve prices. `None` if should get up to the latest.
        `date_min`: Minimum date to retrieve prices. `None` if should get down to the first.
    """
    stmt = select(prices)
    if product_ids:
        stmt = stmt.where(prices.ProductId.in_(product_ids))
    if date_max:
        stmt = stmt.where(prices.Date <= date_max)
    if date_min:
        stmt = stmt.where(prices.Date >= date_min)
    if price_max:
        stmt = stmt.where(prices.Price <= price_max)
    if price_min:
        stmt = stmt.where(prices.Price >= price_min)
    with Session(DB_ENGINE) as ses:
        result = ses.execute(stmt).scalars()
        return [row for row in result]


def delete_price_rows(rows: list[prices]):
    """
    Delete a list of rows from *prices* table.

    **Args**
        `rows`: list of rows to be deleted.
    """
    rows_id = [r.Id for r in rows]
    stmt = delete(prices).where(prices.Id.in_(rows_id))
    with Session(DB_ENGINE) as ses:
        ses.execute(stmt)
        ses.commit()


def product_category_by_id(id: int) -> product_categories | None:
    """Return an entry from *product_categories* table with the specified `id`. `None` if it doesn't exist."""
    with Session(DB_ENGINE) as ses:
        stmt = select(product_categories).where(product_categories.Id == id)
        return ses.execute(stmt).scalar_one_or_none()


def product_name_by_id(id: int) -> product_names | None:
    """Return an entry from *product_names* table with the specified `id`. `None` if it doesn't exist."""
    with Session(DB_ENGINE) as ses:
        stmt = select(product_names).where(product_names.Id == id)
        return ses.execute(stmt).scalar_one_or_none()


def product_by_id(id: int) -> products | None:
    """Return an entry from products table with the specified `id`. `None` if it doesn't exist."""
    with Session(DB_ENGINE) as ses:
        stmt = select(products).where(products.Id == id)
        return ses.execute(stmt).scalar_one_or_none()


def price_by_id(id: int) -> prices | None:
    """Return an entry from prices table with the specified `id`. `None` if it doesn't exist."""
    with Session(DB_ENGINE) as ses:
        stmt = select(prices).where(prices.Id == id)
        result = ses.execute(stmt).scalar_one_or_none()
    return result


def title_category_exists(name: str) -> bool:
    """Returns a boolean value indicating wether `name` exist in *product_categories* table or not."""
    name = format_name(name)
    with Session(DB_ENGINE) as ses:
        stmt = select(product_categories).where(product_categories.CategoryName == name)
        result = tuple(ses.execute(stmt).scalars())
    return bool(len(result))


def title_name_exists(name: str) -> bool:
    """Returns a boolean value indicating wether `name` exist in *product_names* table or not."""
    name = re.sub(" +", " ", name.title())
    with Session(DB_ENGINE) as ses:
        stmt = select(product_names).where(product_names.ProductName == name)
        result = tuple(ses.execute(stmt).scalars())
    return bool(len(result))


def product_exists(product_obj: products) -> bool:
    stmt = (
        select(products)
        .where(products.ProductBrand == product_obj.ProductBrand)
        .where(products.ProductName == product_obj.ProductName)
        .where(products.ProductModel == product_obj.ProductModel)
    )
    with Session(DB_ENGINE) as ses:
        result = tuple(ses.execute(stmt).scalars())
    return bool(len(result))


def id_by_category_name(name: str) -> int | None:
    """Returns the ID number of the corresponding `name` in *product_categories*
    table, or `None` if not present.
    """
    name = format_name(name)
    stmt = select(product_categories.Id).where(product_categories.CategoryName == name)
    with Session(DB_ENGINE) as ses:
        result = ses.execute(stmt).scalar_one_or_none()
    return int(result)


def id_by_product_name(name: str) -> int | None:
    """Returns the ID number of the corresponding `name` in *product_categories*
    table, or `None` if not present.
    """
    name = format_name(name)
    stmt = select(product_names.Id).where(product_names.ProductName == name)
    with Session(DB_ENGINE) as ses:
        result = ses.execute(stmt).scalar_one_or_none()
    return result


def id_product_by_created_time(dt: datetime) -> int:
    with Session(DB_ENGINE) as ses:
        stmt = select(products.Id).where(products.Created == dt)
        return ses.execute(stmt).scalar_one_or_none()


def id_category_exists(category_id: int) -> bool:
    """Returns a boolean value indicating wether `category_id` exist or not."""
    stmt = select(product_categories).where(product_categories.Id == category_id)
    with Session(DB_ENGINE) as ses:
        result = tuple(ses.execute(stmt).scalars())
    return bool(len(result))


def id_name_exists(name_id: int) -> bool:
    """Returns a boolean value indicating wether `name_id` exist or not."""
    stmt = select(product_names).where(product_names.Id == name_id)
    with Session(DB_ENGINE) as ses:
        result = tuple(ses.execute(stmt).scalars())
    return bool(len(result))


def id_product_exists(product_id: int) -> bool:
    """Returns a boolean value indicating wether `product_id` exist or not."""
    with Session(DB_ENGINE) as ses:
        stmt = select(products).where(products.Id == product_id)
        result = tuple(ses.execute(stmt).scalars())
    return bool(len(result))


def id_price_exists(price_id: int) -> bool:
    """Returns a boolean value indicating wether `price_id` exist or not."""
    with Session(DB_ENGINE) as ses:
        stmt = select(prices).where(prices.Id == price_id)
        result = tuple(ses.execute(stmt).scalars())
    return bool(len(result))


def product_name_has_category(name_id: int) -> bool:
    """Returns a boolean value indicating wether `name_id` has a category ID
    associated to it or not.
    """
    if not id_name_exists(name_id):
        print("This name ID is not in database.")
        return None
    stmt = select(product_names.CategoryId).where(product_names.Id == name_id)
    with Session(DB_ENGINE) as ses:
        result = ses.execute(stmt).scalar_one_or_none()
    return bool(result)


def add_product_category_to_db(product_category_obj: product_categories) -> int | None:
    """Creates an entry in *product_categories* table, returns the ID of the
    entry created or `None` if `category_name` already exists.
    """
    category_name = product_category_obj.CategoryName
    if title_category_exists(name=category_name):
        return None
    with Session(DB_ENGINE) as ses:
        ses.add(product_category_obj)
        ses.commit()
        new_id = id_by_category_name(category_name)
    return new_id


def add_product_name_to_db(product_name_obj: product_names):
    """Creates an entry in *product_names* table, returns the ID of the entry
    created or `None` if `category_name` already exists.
    """
    product_name = product_name_obj.ProductName
    if title_name_exists(name=product_name):
        return None
    with Session(DB_ENGINE) as ses:
        ses.add(product_name_obj)
        ses.commit()
        new_id = id_by_product_name(product_name)
    return new_id


def add_product_to_db(product_obj: products):
    """Creates an entry in *products* table, returns the ID of the entry
    created or `None` if `product_obj` already exists.
    """
    if product_exists(product_obj):
        return None
    with Session(DB_ENGINE) as ses:
        ses.add(product_obj)
        ses.commit()
        new_id = id_product_by_created_time(product_obj.Created)
    return new_id


def set_category_to_name(name_id: int, category_id: int):
    """Set `category_id` to *CategoryId* column in *product_names* table for
    the specified `name_id`.
    """
    stmt = (
        update(product_names)
        .where(product_names.Id == name_id)
        .values(CategoryId=category_id)
    )
    with Session(DB_ENGINE) as ses:
        ses.execute(stmt)
        ses.commit()
