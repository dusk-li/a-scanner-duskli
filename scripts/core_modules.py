from requests_html import HTMLSession
from pathlib import Path
import requests
import wget
import time
import sys
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options