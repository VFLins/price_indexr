from typing import Tuple, Dict
import logging
from sqlalchemy import update, select
from sqlalchemy.orm import Session
from httpx import AsyncClient
import asyncio
import re
import os
from datetime import datetime
from bs4 import BeautifulSoup
from price_indexr import db


SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(SCRIPT_PATH, "data")
LOG_PATH = os.path.join(SCRIPT_PATH, "log")

for dirpath in [DATA_PATH, LOG_PATH]:
    os.makedirs(dirpath, exist_ok=True)

SEARCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}

# =============== #
# LOGGING HANDLER #
# =============== #


class LocalLogger:
    """Generate an ephemeral logger inside the function scope."""

    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        self.handler = logging.FileHandler(
            filename=os.path.join(LOG_PATH, f"{name}.log")
        )
        self.formatter = logging.Formatter(
            fmt="%(levelname)s [%(asctime)s] - %(name)s :: %(message)s"
        )

        self.handler.setFormatter(self.formatter)
        self.handler.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)
        self.logger.propagate = False

    def debug(self, context, message):
        """Log a `debug` level message"""
        self.logger.debug(msg=f"{context}: {message}")

    def info(self, context, message):
        """Log a `info` level message"""
        self.logger.info(msg=f"{context}: {message}")

    def warn(self, context, message):
        """Log a `warning` level message"""
        self.logger.warning(msg=f"{context}: {message}")

    def error(self, context, message):
        """Log a `error` level message"""
        self.logger.error(msg=f"{context}: {message}")

    def critical(self, context, message):
        """Log a `critical` level message"""
        self.logger.critical(msg=f"{context}: {message}")


log = LocalLogger("price_indexr")


# ========== #
# EXCEPTIONS #
# ========== #


class HtmlParseError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


# ================ #
# MANAGE RESPONSES #
# ================ #


class SearchResponses:
    def __init__(
        self,
        soup_bing: BeautifulSoup | None,
        soup_google: BeautifulSoup | None,
        product: db.products,
        filter_kws: dict,
    ):
        self.soup_bing = soup_bing
        self.soup_google = soup_google

        if soup_google:
            self.google_inline = soup_google.find_all("div", {"data-dtld": True})
            self.google_grid = soup_google.find_all("g-inner-card", {"jscontroller": True})
            self.google_highlight = soup_google.find("div", {"class": "_-oX"})
        else:
            self.google_inline, self.google_grid, self.google_highlight = (
                None,
                None,
                None,
            )

        if soup_bing:
            self.bing_inline = soup_bing.find_all(
                "div", {"class": "slide", "data-appns": "commerce", "tabindex": True}
            )
            self.bing_inline = [
                res for res in self.bing_inline if res.find("div", class_="br-gOffCard")
            ]
            self.bing_grid = soup_bing.find_all(
                "div", {"class": "br-wholeCardClickable"}
            )
        else:
            self.bing_inline, self.bing_grid = (None, None)

        self.product = product
        self.filter_kws = filter_kws

        self.product_name = (
            f"{product.ProductBrand} {product.ProductModel} {product.ProductName}"
        )
        self.Date = datetime.now()
        self.results = []

    def parse_and_save(self):
        self._parse_all()
        self._save_data()

    def _parse_all(self):
        _context = "SearchResponses.parse_all"
        parsers = (
            self._parse_google_inline,
            self._parse_google_grid,
            self._parse_google_highlight,
            self._parse_bing_inline,
            self._parse_bing_grid,
        )

        _max_errors: int = 5
        _errors: int = 0
        for parser in parsers:
            try:
                parser()
            except HtmlParseError:
                _errors = _errors + 1

                if _errors == _max_errors:
                    results_amount = len(self.results)
                    log.error(
                        _context,
                        f"Skipping data parsing for '{self.product_name}', too many errors",
                    )

                    if results_amount == 0:
                        log.error(
                            _context, f"No data collected for '{self.product_name}'"
                        )

                else:
                    continue

    def _save_data(self):
        _context = "SearchResponses._save_data"

        n_results = len(self.results)
        if n_results == 0:
            log.info(_context, f"No valid results for '{self.product_name}'")

        else:
            try:
                write_results(
                    results=self.results, CURR_PROD_ID=self.product.Id, date=self.Date
                )
                log.info(
                    _context, f"Saved {n_results} results for '{self.product_name}'"
                )
            except Exception as unexpected_save_exception:
                log.critical(
                    _context,
                    f"Unexpected error for '{self.product_name}': {unexpected_save_exception}",
                )

    def _parse_google_inline(self):
        """Dedicated parser for google inline (promoted) elements"""
        _context = "SearchResponses._parse_google_inline"
        if not self.google_inline:
            log.warn(_context, f"No `google_inline` element found, skipping...")
            return

        for result in self.google_inline:
            try:
                line = {}
                Name = result.find("span", {"class": "pymv4e"}).get_text()

                if not filtered_by_name(Name, self.filter_kws):
                    continue

                Price = strip_price_str(
                    result.find("span", {"class": "e10twf"}).get_text()
                )

                line["Url"] = result.find("a", {"data-impdclcc": True})["href"]
                line["Name"] = Name
                line["Date"] = self.Date
                line["Store"] = result.find("span", {"aria-label": True}).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = self.product.Id

                self.results.append(db.prices(**line))

            except Exception as google_inline_faliure:
                log.critical(
                    _context,
                    f"Prod. ID: {self.product.Id}. Could not parse:\n{result}"
                    + f"\nReason: {google_inline_faliure}",
                )

                raise HtmlParseError(f"Error in _parse_google_inline")

    def _parse_google_grid(self):
        """Dedicated parser for the first page of the google shopping grid of results"""
        _context = "SearchResponses._parse_google_grid"

        if not self.google_grid:
            log.warn(_context, f"No `google_grid` element found, skipping...")
            return

        for result in self.google_grid:
            try:
                line = {}
                Name = result.find("h3", {"class": "tAxDx"}).get_text()

                if not filtered_by_name(Name, self.filter_kws):
                    continue

                Price = strip_price_str(
                    result.find("span", {"class": "a8Pemb"}).get_text()
                )

                line["Url"] = (
                    f"https://www.google.com{result.find('a', {'class' : 'xCpuod'})['href']}"
                )
                line["Name"] = Name
                line["Date"] = self.Date
                line["Store"] = result.find(
                    "div", {"class": "aULzUe IuHnof"}
                ).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = self.product.Id

                self.results.append(db.prices(**line))

            except Exception as google_grid_faliure:
                log.critical(
                    _context,
                    f"Prod. ID - {self.product.Id}. Could not parse:\n{result}"
                    + f"\nReason: {google_grid_faliure}",
                )

                raise HtmlParseError("Error in _parse_google_grid")

    def _parse_google_highlight(self):
        """Dedicated parser for google's 'best match' section"""
        _context = "SearchResponses._parse_google_highlight"

        if self.google_highlight:
            try:
                Name = self.google_highlight.find(
                    "a",
                    {
                        "class": " _-lC sh-t__title sh-t__title-popout shntl translate-content"
                    },
                ).get_text()

                if not filtered_by_name(Name, self.filter_kws):
                    for result in self.google_highlight.find_all(
                        "div", {"class": "_-oB"}
                    ):
                        line = {}

                        line["Name"] = Name
                        Price = strip_price_str(
                            result.find("span", {"class": "_-p5 _-p1"}).get_text()
                        )
                        line["Url"] = (
                            f"https://google.com/{result.find('a', {'href': True})['href']}"
                        )
                        line["Date"] = self.Date
                        line["Store"] = result.find(
                            "div", {"class": "_-oH _-oF"}
                        ).get_text()
                        line["Price"] = Price[1]
                        line["Currency"] = Price[0]
                        line["ProductId"] = self.product.Id

                        self.results.append(db.prices(**line))

            except Exception as google_highlight_faliure:
                log.critical(
                    _context,
                    f"Prod. ID - {self.product.Id}. Could not parse:\n{result}"
                    + f"\nReason: {google_highlight_faliure}",
                )

                raise HtmlParseError("Error in _parse_google_higlight")

    def _parse_bing_inline(self):
        """Dedicated parser for bing's promoted results"""
        _context = "SearchResponses._parse_bing_inline"

        if not self.bing_inline:
            log.warn(_context, f"No `bing_inline` element found, skipping...")
            return

        for result in self.bing_inline:
            try:
                line = {}
                name_block = result.find("span", {"title": True})
                Name = name_block["title"]

                if not filtered_by_name(Name, self.filter_kws):
                    continue

                Price = strip_price_str(
                    result.find("div", {"class": "br-price"}).get_text()
                )

                line["Url"] = result.find("a", {"class": "br-offLink"})["href"]
                line["Name"] = Name
                line["Date"] = self.Date
                line["Store"] = result.find(
                    "span", {"class": "br-offSlrTxt"}
                ).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = self.product.Id

                self.results.append(db.prices(**line))

            except Exception as bing_inline_faliure:
                log.critical(
                    _context,
                    f"Prod. ID - {self.product.Id}. Could not parse:\n{result}"
                    + f"\nReason: {bing_inline_faliure}",
                )

                raise HtmlParseError("Error in _parse_bing_inline")

    def _parse_bing_grid(self):
        """Dedicated parser for the first page of the bing grid of results"""
        _context = "SearchResponses._parse_bing_grid"

        if not self.bing_grid:
            log.warn(_context, f"No `bing_inline` element found, skipping...")
            return

        for result in self.bing_grid:
            try:
                line = {}
                name_block = result.find("span", {"title": True})
                Name = name_block["title"]

                if not filtered_by_name(Name, self.filter_kws):
                    continue

                Price = strip_price_str(
                    result.find("div", {"class": "pd-price"}).get_text()
                )

                line["Url"] = result.find("a", {"class": "br-compareSellers"})["href"]
                line["Name"] = Name
                line["Date"] = self.Date
                line["Store"] = result.find(
                    "span", {"class": "br-sellersCite"}
                ).get_text()
                line["Price"] = Price[1]
                line["Currency"] = Price[0]
                line["ProductId"] = self.product.Id

                self.results.append(db.prices(**line))

            except Exception as bing_grid_faliure:
                log.critical(
                    _context,
                    f"Prod. ID - {self.product.Id}. Could not parse:\n{result}"
                    + f"\nReason: {bing_grid_faliure}",
                )

                raise HtmlParseError("Error in _parse_bing_grid")


# ===== #
# UTILS #
# ===== #


def validate_integer_input(inp: int) -> db.products:
    """
    Validates an integer input and retrieves a product from the database.

    ### Args:
        inp (`int`): The input value to validate.

    ### Returns:
        `products`: The product retrieved from the database.

    ### Raises:
        `ValueError`: If the input cannot be converted to an integer.
        `IndexError`: If the specified ID is not found in the database.
    """
    _context = f"validate_integer_input '{inp}'"

    try:
        inp = int(inp)
    except ValueError:
        log.error("{_context}: Input must be of type `int` or coercible to `int`")
        raise ValueError

    try:
        with Session(db.DB_ENGINE) as ses:
            stmt = select(db.products).where(db.products.Id == inp)
            curr_product = ses.execute(stmt).scalar_one()
    except Exception as not_found_id_error:
        log.error(_context, f"Database returned an error: {not_found_id_error}")
        raise IndexError

    return curr_product


def generate_filters(product: db.products) -> Tuple[str, Dict[str, list]]:
    """
    ### Filters handling:

    1. retrieve from tables:
        product_categories: `'pc,personal_computer'`
        product_names: `'something,foo'`
        products: `'foo_bar,baz'`

    2. split on commas and append:
        `['pc','personal_computer','something','foo','foo_bar','baz']`

    3. underscores become spaces:
        `['pc','personal computer','something','foo','foo bar','baz']`

    ### Args:
        product (`products`): A row retrieved from database of class `products`

    ### Returns:
        A `tuple` containing:
            `str` the product's full name (brand, name, and model)
            `dict` of filters with two keys: `'negative'` and `'positive'`
    """
    _context = f"generate_filters {product}"

    try:
        negf = set(re.split(",", product.ProductFilters.replace(" ", "")))
        product_name = db.product_name_by_id(product.NameId)
        if product_name.NameFilters not in [None, ""]:
            negf.update(re.split(",", product_name.NameFilters.replace(" ", "")))
        product_category = db.product_category_by_id(product_name.CategoryId)
        if product_category.CategoryFilters not in [None, ""]:
            negf.update(
                re.split(",", product_category.CategoryFilters.replace(" ", ""))
            )

        product_fullname = (
            f"{product.ProductBrand} {product_name.ProductName} {product.ProductModel}"
        )
        posf = re.split(" ", product_fullname)

        keywords = dict(
            negative=[x.replace("_", " ") for x in negf if x not in ["", "_"]],
            positive=[x.replace("_", " ") for x in posf],
        )
    except Exception as generate_filters_error:
        log.error(_context, f"{generate_filters_error}")
        raise Exception

    return product_fullname, keywords


# =========== #
# GATHER DATA #
# =========== #


def collect_search(q: str, product: db.products, keywords: dict) -> SearchResponses:
    _context = f"collect_search: {q}"

    bing_params = {"q": q}
    google_params = {"q": q, "tbm": "shop"}

    urls = ["https://www.bing.com/shop", "https://www.google.com/search"]
    params = [bing_params, google_params]
    metas = zip(urls, params)

    async def get_webpage(url, params):
        try:
            async with AsyncClient() as client:
                return await client.get(
                    url=url,
                    params=params,
                    headers=SEARCH_HEADERS,
                    follow_redirects=True,
                )
        except Exception as err:
            log.error(_context, f"Could not get {url} contents: {err}")
            return None

    async def request_webpage():
        tasks = (get_webpage(url, param) for url, param in metas)
        return await asyncio.gather(*tasks)

    bing_response, google_response = asyncio.run(request_webpage())

    if (bing_response is None) and (google_response is None):
        log.error(_context, "Could not get responses from any webpage. Exiting...")
        raise Exception

    soup_bing, soup_google = None, None
    if bing_response:
        soup_bing = BeautifulSoup(bing_response.text, "lxml")
    if google_response:
        soup_google = BeautifulSoup(google_response.text, "lxml")

    return SearchResponses(
        soup_bing=soup_bing,
        soup_google=soup_google,
        product=product,
        filter_kws=keywords,
    )


def collect_prices(CURR_PROD_ID):
    _context = "collect_prices"

    try:
        curr_product = validate_integer_input(CURR_PROD_ID)
        search_field, search_kewords = generate_filters(curr_product)
        responses = collect_search(
            q=search_field, keywords=search_kewords, product=curr_product
        )
        responses.parse_and_save()

    except Exception as uncaught_exception:
        log.critical(
            _context, f"Uncaught exception with '{search_field}': {uncaught_exception}"
        )
        return


# ERROR MANAGEMENT AND RESULTS FILTERING
def filtered_by_name(name_to_filter: str, filters: dict) -> bool:
    """
    Checks if the product title has every keyword it is supposed to have,
    and if it does NOT have the keywords it isn't supposed to have,
    with every test passed, return 'True'.
    """

    pos_filters = filters["positive"]
    neg_filters = filters["negative"]

    checks_up = False
    for word in pos_filters:
        # skip when word is an empty string
        if word == "":
            continue
        # checks_up when the positive filter is found
        pos_filter_check = re.search(rf"\b{word.lower()}\b", name_to_filter.lower())
        if bool(pos_filter_check):
            checks_up = True
        else:
            checks_up = False
        if not checks_up:
            break

    if len(neg_filters) > 0 and checks_up:
        for word in neg_filters:
            if word == "":
                continue
            neg_filter_fail = re.search(rf"\b{word.lower()}\b", name_to_filter.lower())
            if not bool(neg_filter_fail):
                checks_up = True
            else:
                checks_up = False
            if not checks_up:
                break
    return checks_up


def strip_price_str(price_str):
    price_str = price_str.replace("\xa0", " ")
    price_expr = r"[\d.,]*[,.]\d*"
    curr_expr = r"[^\d., ]*"
    dec_expr = r"[,.](?=[^,.]*$)"

    price = re.search(price_expr, price_str).group(0)
    curr = re.search(curr_expr, price_str).group(0)
    dec = re.search(dec_expr, price_str).group(0)

    if dec == ",":
        price = float(price.replace(".", "").replace(",", "."))
    elif dec == ".":
        price = float(price.replace(",", ""))
    return [curr, price]


def write_results(results: list, CURR_PROD_ID: int, date: datetime):
    time_stmt = (
        update(db.products)
        .where(db.products.Id == CURR_PROD_ID)
        .values(LastUpdate=datetime.now())
    )
    with Session(db.DB_ENGINE) as ses:
        ses.add_all(results)
        ses.commit()
        ses.execute(time_stmt)
        ses.commit()
