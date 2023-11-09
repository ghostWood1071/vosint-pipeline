import json
import time
import random
time_waiting = random.randint(1,7)
from playwright.sync_api import sync_playwright, Page, Browser
from typing import *
from models.mongorepository import MongoRepository
import json


def login():
    pass

def authenticate(browser: Browser, cookies: Any, link, account, password, source_acc_id):
    pass