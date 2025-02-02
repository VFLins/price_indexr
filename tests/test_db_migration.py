import pytest
from copy import copy
from pathlib import Path
from typing import Type
from sqlalchemy import (
    Engine,
    MetaData,
    Table,
    create_engine,
    select,
    insert,
)
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
    engine = new_populated_db_engine
    meta = MetaData()
    meta.reflect(engine)

    class prices_copy(prices_model, TableMapping):
        __tablename__ = "prices_copy"

    TableMapping.metadata.create_all(engine, tables=[prices_copy.__table__])
    with Session(engine) as ses:
        ses.execute(insert(prices_copy).values(prices_data))
        ses.commit()
    yield prices_copy
    TableMapping.metadata.drop_all(engine, tables=[prices_copy.__table__])


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
    engine = new_populated_db_engine

    meta = MetaData()
    meta.reflect(engine)

    class products_copy2(products_model, TableMapping):
        __tablename__ = "products_copy2"

    TableMapping.metadata.create_all(engine, tables=[products_copy2.__table__])
    with Session(engine) as ses:
        ses.execute(insert(products_copy2).values(products_data2))
        ses.commit()
    yield products_copy2
    TableMapping.metadata.drop_all(engine, tables=[products_copy2.__table__])


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


def test_columns_are_identical_empty(new_empty_db_engine):
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


def test_success_columns_are_identical_populated(
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


def test_edge_case_columns_are_identical(new_populated_db_engine, copy_table_products2):
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


def not_test_create_backup(new_populated_db_engine):
    """Test if backup table in being created. No ready to run yet"""
    engine, meta = new_populated_db_engine, MetaData()
    meta.reflect(engine)
    mapped_tables = [prices, products, product_names, product_categories]
    for tbl in mapped_tables:
        tblname = tbl.__tablename__
        orm_backup_tbl = _create_backup_table(
            table_mapping=tbl, engine=engine, metadata=meta
        )
        db_backup_tbl = meta.tables[tblname]
        assert orm_backup_tbl.__table__ == db_backup_tbl


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


def test__table_with_same_columns(new_populated_db_engine):
    engine = new_populated_db_engine
    assert _tables_with_same_columns("prices", "prices_copy", engine=engine)
    assert not _tables_with_same_columns("prices", "products", engine=engine)
