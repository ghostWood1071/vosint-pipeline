import json
import time
import random

time_waiting = random.randint(1, 7)
from playwright.sync_api import sync_playwright, Page, Browser
from typing import *
from models.mongorepository import MongoRepository
import json
from .utils import *


def login(page, account, password):
    link = 'https://twitter.com/i/flow/login'
    page.goto(link)
    page.wait_for_selector('//input[@autocomplete="username"]').type(account)
    page.get_by_text('Next').click()
    page.wait_for_selector('//input[@name="password"]').type(password)
    page.get_by_text('Log in').click()
    time.sleep(30)
    return page.context.cookies()

def authenticate(browser: Browser, cookies: Any, link, account, password, source_acc_id):
    user_agent = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) "
        "AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
    )
    context = browser.new_context(user_agent=user_agent)
    page: Page = browser.new_page()
    page.context.add_cookies(cookies)

    page.goto(link)
    account_menu_tags = select(page, '//*[@aria-label="Account menu"]')
    try:
        if len(account_menu_tags) == 0:
            cookies = login(page, account, password)
            context.clear_cookies()
            context.add_cookies(cookies)
            page = context.new_page()
            page.goto(link)
            MongoRepository().update_one('socials', {"_id": source_acc_id, "cookie":json.dumps(cookies)})
    except Exception as e:
        pass
    return page