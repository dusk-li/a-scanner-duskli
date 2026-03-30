import http.client
from pathlib import Path
from datetime import date
import datetime
import requests
import os
import json
import validators
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import concurrent.futures
import io
import zipfile
import csv