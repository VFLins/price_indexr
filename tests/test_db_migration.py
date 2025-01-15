import pytest
from pathlib import Path
from sqlalchemy import (
    Engine,
    MetaData,
    create_engine,
    select,
    insert,
)
from synthetic_data import (
    product_categories_data,
    product_names_data,
    products_data,
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
    _columns_are_identical,
    _create_backup_table,
    _recreate_updated_tables,
    _reset_table_schema_in_db,
    _table_missing_columns,
    _table_update_migration,
    _table_with_same_columns,
    _tables_are_identical,
    _tables_have_same_data,
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


def test_create_backup(new_populated_db_engine):
    """Test if backup table in being created."""
    engine = new_populated_db_engine
    meta = MetaData()
    meta.reflect(engine)
    mapped_tables = [prices, products, product_names, product_categories]
    for tbl in mapped_tables:
        tblname = tbl.__tablename__
        orm_backup_tbl = _create_backup_table(
            table_mapping=tbl, engine=engine, metadata=meta
        )
        db_backup_tbl = meta.tables[tblname]
        assert orm_backup_tbl.__table__ == db_backup_tbl
