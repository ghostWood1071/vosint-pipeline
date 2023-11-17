import json
import time
import random
time_waiting = random.randint(1,7)
from playwright.sync_api import sync_playwright, Page, Browser
from typing import *
from models.mongorepository import MongoRepository
import json
import traceback

def login(page:Page, account, password):
    print("login ....")
    page.context.clear_cookies()
    page.goto("https://m.facebook.com/login")
    page.type("input#m_login_email", account)
    page.type('input#m_login_password', password)
    page.press('input#m_login_password', "Enter")
    time.sleep(15)
    return page.context.cookies()

def authenticate(browser:Browser, cookies:Any, link, account, password, source_acc_id):
    user_agent = (
        "Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1"
    )
    context = browser.new_context(user_agent=user_agent)
    browser.contexts[0].close()
    context.add_cookies(cookies)
    page:Page = context.new_page()
    page.set_viewport_size({"width": 768, "height": 1024})
    
    page.goto(link)
    try:
        print(page.title())
        print(page.url)
        if page.title() in ["Log in to Facebook | Facebook", "Facebook – log in or sign up"] or "login" in page.url or "| Facebook" in page.title():
            print("need to login")
            cookies = login(page, account, password)
            print("cookies after login: ", cookies)
            context.clear_cookies()
            context.add_cookies(cookies)
            page.goto(link)
            MongoRepository().update_one('socials', {"_id": source_acc_id, "cookie":json.dumps(cookies)})
    except Exception as e:
        raise e
    return page