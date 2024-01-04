import json
import time
import random
time_waiting = random.randint(1,7)
from playwright.sync_api import sync_playwright, Page, Browser, Playwright
from typing import *
from models.mongorepository import MongoRepository
import json
import traceback

def login(page:Page, account, password):
    print("login ....")
    page.context.clear_cookies()
    page.goto("https://mobile.facebook.com/login")
    page.type("input#m_login_email", account)
    page.type('input[type="password"]', password)
    # page.type('input#m_login_password', password)
    page.press('input[type="password"]', "Enter")
    time.sleep(15)
    try:    
        confirm = page.locator('button[value="OK"]')
        confirm.click()
    except:
        pass
    return page.context.cookies()

def authenticate(browser:Browser, cookies:Any, link, account, password, source_acc_id, device):
    user_agent = (
        "Mozilla/5.0 (Linux; Android 12; Pixel 6 Build/SQ3A.220705.004; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/115.0.0.0 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/407.0.0.0.65;]"
    )
    context = browser.new_context(user_agent=user_agent)
    browser.contexts[0].close()
    context.add_cookies(cookies)
    page:Page = context.new_page()
    # page.set_viewport_size({"width": 768, "height": 1024})
    
    page.goto(link)
    try:
        print(page.title())
        print(page.url)
        if page.title() in ["Log in to Facebook | Facebook", "Facebook – log in or sign up"] or "login" in page.url or "| Facebook" in page.title() or page.title() == "Error Facebook":
            print("need to login")
            cookies = login(page, account, password)
            if page.title() in ["Log in to Facebook | Facebook", "Facebook – log in or sign up"] or "login" in page.url or "| Facebook" in page.title():
                MongoRepository().update_one('socials', {"_id": source_acc_id, "error":True, "cookie": json.dumps(cookies)})
                raise Exception("login failed")
            else:
                print("cookies after login: ", cookies)
                page.goto(link)
                MongoRepository().update_one('socials', {"_id": source_acc_id, "cookie":json.dumps(cookies), "error": False})
    except Exception as e:
        raise e
    return page