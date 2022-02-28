import sqlalchemy
import requests
import json
import sys
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

DB_CON = sys.argv[1]
SERACH_FIELD = sys.argv[2]
SEARCH_KEYWORDS = SERACH_FIELD.split(" ")

print(DB_CON, SERACH_FIELD)
