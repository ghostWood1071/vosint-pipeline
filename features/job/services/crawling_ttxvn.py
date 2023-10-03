from playwright.sync_api import sync_playwright, Page, Browser
import time
from models import MongoRepository
import requests
import json

def select(from_element, expr, by = "css="):
        element = from_element.locator(f"{by}{expr}")
        element = [element.nth(i) for i in range(element.count())]
        return element
            

# def check_proxy(proxy):
#     url = "https://news.vnanet.vn/"
#     requests.get(a)

# def get_proxies():
#     proxies,_ = MongoRepository().get_many("proxy", {})
#     for proxy in proxies:
#         pass

def login_ttxvn(page:Page, username, password):
    page.goto('https://news.vnanet.vn/')
    page.click('#btnSignIn')
    page.fill('#username', username)
    page.fill('#password', password)
    page.click('#login')
    time.sleep(1)
    cookies = page.context.cookies() 
    account = MongoRepository().get_one("config_ttxvn", {"user": username, "password": password})
    MongoRepository().update_many("config_ttxvn", {"_id": account["_id"]}, {"$set": {"cookies": cookies}})
    return cookies

def crawl_ttxvn(data, username,password, cookies):
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page()
        if cookies == None:
            cookies = login_ttxvn(page, username, password)
        
        page.context.add_cookies(cookies)
        for row in data:
            try:
                link  = 'https://news.vnanet.vn/FrontEnd/PostDetail.aspx?id='+ str(row.get("ID"))
                page.goto(link)
                time.sleep(2)
                if "https://vnaid.vnanet.vn/core/login" in page.url:
                    cookies = login_ttxvn(page, username, password)
                    page.context.add_cookies(cookies)
                    page.goto(link)
                content = select(page,".post-content")[0].inner_text()
                row["content"] = str(content).replace(row["Title"], "", 1)
            except Exception as e:
                raise e
        page.close()
        playwright.stop()
    except Exception as e:
        page.close()
        playwright.stop()
    
    return data
    
