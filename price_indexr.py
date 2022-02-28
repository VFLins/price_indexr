import sqlalchemy
import requests
import json
import sys
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

search_field = sys.argv[1]
search_keywords = search_field.split(" ")

