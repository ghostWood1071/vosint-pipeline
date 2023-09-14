import json
import time
import random
time_waiting = random.randint(1,7)
from playwright.sync_api import sync_playwright
from typing import *
from models.mongorepository import MongoRepository
import json

def login(page, account, password):
    page.type("input#m_login_email", account)
    page.type('input[name="pass"]', password)
    page.press('input[name="pass"]', "Enter")
    time.sleep(5)
    return page.context.cookies()

def authenticate(browser, cookies:Any, link, account, password, source_acc_id):
    context = browser.new_context()
    page = context.new_page()
    # Add cookies to the browser context
    context.add_cookies(cookies)
    # Navigate to a page that requires authentication
    page = context.new_page()
    # Navigate to the login page
    page.goto(link)
    try:
        if 'https://mbasic.facebook.com/login.php' in page.url:
            cookies = login(page, account, password)
            context.clear_cookies()
            context.add_cookies(cookies)
            page = context.new_page()
            page.goto(link)
            MongoRepository().update_one('socials', {"_id": source_acc_id, "cookie":json.dumps(cookies)})
    except Exception as e:
        pass
    return page