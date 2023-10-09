from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError
import time
from models import MongoRepository
import requests
from requests.auth import HTTPProxyAuth
import json

def select(from_element, expr, by = "css="):
        element = from_element.locator(f"{by}{expr}")
        element = [element.nth(i) for i in range(element.count())]
        return element     

def test_proxy(url, proxy):
    try:
        username = proxy.get("username")
        password = proxy.get("password")
        port = proxy.get("port")
        ip = proxy.get("ip")
        auth = None
        if username != "" and password != "":
            auth = HTTPProxyAuth(proxy.get("username"), proxy.get("password"))
        if auth != None:
            response = response = requests.get(url, proxies={'http': f'{ip}:{port}', 'https': f'{ip}:{port}'}, timeout=10, auth=auth)
        else:
            response = requests.get(url, proxies={'http': f'{ip}:{port}', 'https': f'{ip}:{port}'}, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_active_proxy_index(url, proxies, index = 0):
    active_index = -1
    for i in range (index, len(proxies)):
        if test_proxy(url, proxies[i]):
            return i
    return active_index

def login_ttxvn(page:Page, username, password):
    try: 
        page.goto('https://news.vnanet.vn')
        page.click('#btnSignIn')
        page.fill('#username', username)
        page.fill('#password', password)
        page.click('#login')
        time.sleep(1)
        cookies = page.context.cookies() 
        account = MongoRepository().get_one("user_config", {"username": username, "password": password})
        MongoRepository().update_many("user_config", {"_id": account["_id"]}, {"$set": {"cookies": cookies}})
        return cookies
    except TimeoutError as e:
        raise e



def crawl_ttxvn(data, username,password, cookies, proxies):
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(channel="chrome")
        context = browser.new_context()
        page = context.new_page()
        proxy_index = 0
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
            except TimeoutError as e:
                proxy_index = get_active_proxy_index("https://news.vnanet.vn", proxies ,proxy_index)
                page.close()
                context.close()
                if proxy_index < 0:
                    raise Exception("there are no proxy work")
                proxy = proxies[proxy_index]
                context = browser.new_context(proxy={
                    'server': f"{proxy.get('ip_address')}:{proxy.get('port')}",
                    'username': proxy.get("username"),
                    'password': proxy.get("password")})
            except Exception as e:
                raise e
        page.close()
        playwright.stop()
    except Exception as e:
        page.close()
        playwright.stop()
    return data
    
