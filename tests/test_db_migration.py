import pytest
from copy import copy
from pathlib import Path
from typing import Type
from sqlalchemy import (
    Engine,
    MetaData,
    Table,
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    create_engine,
    select,
    insert,
)
from sqlalchemy.orm import Mapped, mapped_column
from .synthetic_data import (
    GENERIC_PRICES_COLS,
    product_categories_data,
    product_names_data,
    products_data,
    products_data2,
    prices_data,
)
from price_indexr.db import (
    DATA_DIR,
    TableMapping,
    Session,
    product_categories,
    product_names,
    products,
    prices,
    prices_model,
    products_model,
    _columns_are_identical,
    _table_missing_columns,
    _tables_with_same_columns,
    _tables_are_identical,
    _tables_have_same_data,
    _recreate_updated_tables,
    _create_backup_table,
    _reset_table_schema_in_db,
    _table_update_migration,
)


POPULATED_DB_FILE = Path(DATA_DIR, "test_populated.db")
EMPTY_DB_FILE = Path(DATA_DIR, "test_empty.db")
BLANK_DB_FILE = Path(DATA_DIR, "test_blank.db")


@pytest.fixture
def new_populated_db_engine(scope="session"):
    """Yields an engine from a new database with every mapped table and all populated with data."""
    engine = create_engine(f"sqlite:///{POPULATED_DB_FILE}", echo=False)
    TableMapping.metadata.create_all(engine)
    with Session(engine) as ses:
        ses.execute(insert(product_categories).values(product_categories_data))
        ses.execute(insert(product_names), product_names_data)
        ses.execute(insert(products).values(products_data))
        ses.execute(insert(prices).values(prices_data))
        ses.commit()
    yield engine
    engine.dispose()
    POPULATED_DB_FILE.unlink(missing_ok=True)


@pytest.fixture
def new_empty_db_engine(scope="session"):
    """Yields an engine from a new database with every mapped table but all empty."""
    engine = create_engine(f"sqlite:///{EMPTY_DB_FILE}", echo=False)
    TableMapping.metadata.create_all(engine)
    yield engine
    engine.dispose()
    EMPTY_DB_FILE.unlink(missing_ok=True)


@pytest.fixture
def new_blank_db_engine(scope="session"):
    """Yields an engine from a new database with no tables."""
    engine = create_engine(f"sqlite:///{BLANK_DB_FILE}", echo=False)
    yield engine
    engine.dispose()
    BLANK_DB_FILE.unlink(missing_ok=True)


@pytest.fixture
def copy_table_prices(new_populated_db_engine, scope="function"):
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)

    if "prices_copy" not in TableMapping.mapped_tables().keys():

        class prices_copy(prices_model, TableMapping):
            __tablename__ = "prices_copy"

    prices_copy_cls = TableMapping.mapped_tables()["prices_copy"]
    TableMapping.metadata.create_all(engine, tables=[prices_copy_cls.__table__])
    with Session(engine) as ses:
        ses.execute(insert(prices_copy_cls).values(prices_data))
        ses.commit()
    yield prices_copy_cls
    TableMapping.metadata.drop_all(engine, tables=[prices_copy_cls.__table__])


@pytest.fixture
def copy_table_products(new_populated_db_engine, scope="function"):
    engine = new_populated_db_engine
    meta = MetaData()
    meta.reflect(engine)

    class products_copy(products_model, TableMapping):
        __tablename__ = "products_copy"

    TableMapping.metadata.create_all(engine, tables=[products_copy.__table__])
    with Session(engine) as ses:
        ses.execute(insert(products_copy).values(products_data))
        ses.commit()
    yield products_copy
    TableMapping.metadata.drop_all(engine, tables=[products_copy.__table__])


@pytest.fixture
def copy_table_products2(new_populated_db_engine, scope="function"):
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)

    class products_copy2(products_model, TableMapping):
        __tablename__ = "products_copy2"

    meta.create_all(engine, tables=[products_copy2.__table__])
    with Session(engine) as ses:
        ses.execute(insert(products_copy2).values(products_data2))
        ses.commit()
    yield products_copy2
    meta.drop_all(engine, tables=[products_copy2.__table__])


@pytest.fixture
def products_table_extra_col(new_populated_db_engine, scope="function"):
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)

    tbl_products_extra_col = Table(
        "products_extra_col",
        meta,
        Column("Id", Integer, primary_key=True),
        Column("NameId", Integer, ForeignKey("product_names.Id"), nullable=False),
        Column("ProductName", String),
        Column("ProductModel", String),
        Column("ProductBrand", String),
        Column("ProductFilters", String),
        Column("Created", DateTime),
        Column("LastUpdate", DateTime),
        Column("NewEmptyColumn", String, nullable=True),
    )

    if "products_extra_col" not in TableMapping.mapped_tables().keys():

        # class products_extra_col(products_model, TableMapping):
        #    __tablename__ = "products_extra_col",
        #    extra_col: Mapped[str] = mapped_column(nullable=True)
        TableMapping.metadata.create_all(engine, tables=[tbl_products_extra_col])
    with Session(engine) as ses:
        ses.execute(insert(tbl_products_extra_col).values(products_data))
        ses.commit()
    yield tbl_products_extra_col
    TableMapping.metadata.drop_all(engine, tables=[tbl_products_extra_col])


def test_table_creation(new_empty_db_engine):
    """Test if the new database file exists,
    this is testing if future tests will behave normally.
    """
    assert EMPTY_DB_FILE.exists()
    engine = new_empty_db_engine
    metadata = MetaData()
    metadata.reflect(engine)
    expected_tables = ("product_categories", "product_names", "products", "prices")
    for tablename in expected_tables:
        assert tablename in metadata.tables.keys()


def test_data_insertion(new_populated_db_engine):
    """Test if data is inserted during creation of populated database,
    this is testing if future tests will behave normally.
    """
    assert POPULATED_DB_FILE.exists()
    engine = new_populated_db_engine
    with Session(engine) as ses:
        result1 = ses.execute(select(product_categories)).all()
        assert len(result1) == len(product_categories_data)
        result2 = ses.execute(select(product_names)).all()
        assert len(result2) == len(product_names_data)
        result3 = ses.execute(select(products)).all()
        assert len(result3) == len(products_data)
        result4 = ses.execute(select(prices)).all()
        assert len(result4) == len(prices_data)
        ses.close()


def test__columns_are_identical_empty(new_empty_db_engine):
    """Test if `_columns_are_identical()` performs as expected in empty tables."""
    engine, meta = new_empty_db_engine, MetaData()
    meta.reflect(engine)
    # Same column on the same table should always return True
    col1 = meta.tables["prices"].columns["Id"]
    assert _columns_are_identical(col1, col1, engine=engine)
    # Empty columns with same colname should always return True
    col2 = meta.tables["product_names"].columns["Id"]
    assert _columns_are_identical(col1, col2, engine=engine)
    # Empty columns with different colnames should always return False
    col3 = meta.tables["prices"].columns["ProductId"]
    assert _columns_are_identical(col1, col3, engine=engine) == False


def test_success__columns_are_identical_populated(
    new_populated_db_engine, copy_table_prices, copy_table_products
):
    """Test success cases of `_columns_are_identical()` in populated tables."""
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)
    prices_copy: Table = copy_table_prices
    for colname in prices_copy.mapped_colnames():
        col1 = prices.__table__.c[colname]
        col2 = prices_copy.__table__.c[colname]
        assert _columns_are_identical(col1, col2, engine=engine)
    products_copy: Table = copy_table_products
    for colname in products_copy.mapped_colnames():
        col1 = products.__table__.c[colname]
        col2 = products_copy.__table__.c[colname]
        assert _columns_are_identical(col1, col2, engine=engine)


def test_edge_case__columns_are_identical(
    new_populated_db_engine, copy_table_products2
):
    """Test if _columns_are_identical will evaluate correctly when columns with
    NULL values are identical when NULL values are omitted and not otherwise.
    """
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)
    products_copy: Table = copy_table_products2
    for colname in products_copy.mapped_colnames():
        col1 = products.__table__.c[colname]
        col2 = products_copy.__table__.c[colname]
        if colname == "LastUpdate":
            assert _columns_are_identical(col1, col2, engine=engine) == False
        else:
            assert _columns_are_identical(col1, col2, engine=engine)


def not_test_fail_columns_are_identical_populated(
    new_populated_db_engine, copy_table_prices
):
    """Test fail cases of `_columns_are_identical()` in populated tables."""


@pytest.mark.parametrize(
    "expected_missing_colnames",
    [(["Price", "Date"]), (["Name"]), (["Url", "Store", "Currency"])],
)
def test__table_missing_columns(
    expected_missing_colnames: list[str], new_blank_db_engine
):
    """Test whether _table_missing_columns returns the correct list of columns."""
    engine, meta = new_blank_db_engine, MetaData()
    meta.reflect(engine)
    sel_colnames = [
        name
        for name in GENERIC_PRICES_COLS.keys()
        if name not in expected_missing_colnames
    ]
    sel_prices_cols = [copy(GENERIC_PRICES_COLS[colname]) for colname in sel_colnames]
    new_table = Table("test_missing_cols", meta, *sel_prices_cols)
    meta.create_all(engine, tables=[new_table])
    missing_cols = _table_missing_columns(
        table_name="test_missing_cols", table_declared=prices, meta_data=meta
    )
    missing_colnames = [col.name for col in missing_cols]
    # Check all expected are present
    for name in expected_missing_colnames:
        assert name in missing_colnames
    # Check ONLY expected are present
    assert len(missing_colnames) == len(expected_missing_colnames)
    meta.drop_all(engine, tables=[new_table])


def test__table_with_same_columns(new_populated_db_engine, copy_table_prices):
    engine = new_populated_db_engine
    _ = copy_table_prices
    assert _tables_with_same_columns("prices", "prices_copy", engine=engine)
    assert not _tables_with_same_columns("prices", "products", engine=engine)


def test__tables_are_identical(new_populated_db_engine, copy_table_prices):
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)
    # return True comparing a table with itself
    for tablename in meta.tables.keys():
        table_obj = meta.tables[tablename]
        assert _tables_are_identical(table_obj, table_obj, engine=engine)
    # return True comparing different tables with the exact same data
    _ = copy_table_prices
    prices_table = meta.tables["prices"]
    prices_copy_table = meta.tables["prices_copy"]
    assert _tables_are_identical(
        prices_table, prices_copy_table, warn_=True, engine=engine
    )
    # return False comparing tables with different data
    products_table = meta.tables["products"]
    for tablename in meta.tables.keys():
        if tablename != "products":
            table_obj = meta.tables[tablename]
            assert not _tables_are_identical(products_table, table_obj, engine=engine)


def test__tables_have_same_data(new_populated_db_engine, copy_table_prices):
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)
    # return True comparing a table with itself
    for tablename in meta.tables.keys():
        table_obj = meta.tables[tablename]
        assert _tables_have_same_data(table_obj, table_obj, engine=engine)
    # return True comparing different tables with the exact same data
    _ = copy_table_prices
    prices_table = meta.tables["prices"]
    prices_copy_table = meta.tables["prices_copy"]
    assert _tables_have_same_data(prices_table, prices_copy_table, engine=engine)
    # return False comparing tables with different data
    products_table = meta.tables["products"]
    for tablename in meta.tables.keys():
        if tablename != "products":
            table_obj = meta.tables[tablename]
            assert not _tables_are_identical(products_table, table_obj, engine=engine)


def test_tables_coparison_edge_case(new_populated_db_engine, products_table_extra_col):
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)
    # create a copy of 'products' with an extra column
    _ = products_table_extra_col
    products_tbl = meta.tables["products"]
    products_tbl_extra_col = meta.tables["products_extra_col"]
    # should return True when testing if they have the same data
    assert _tables_have_same_data(products_tbl, products_tbl_extra_col, engine=engine)
    # should return False when testing if they are identical
    assert not _tables_are_identical(
        products_tbl, products_tbl_extra_col, engine=engine
    )


def test__create_backup_table(new_populated_db_engine):
    """Test if backup table in being created correctly and returns the correct table object."""
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)
    mapped_tables = [prices, products, product_names, product_categories]
    for tbl in mapped_tables:
        orm_backup_tbl = _create_backup_table(table_mapping=tbl, engine=engine)
        db_backup_tbl = meta.tables[orm_backup_tbl.__tablename__]
        assert orm_backup_tbl.__table__ == db_backup_tbl
