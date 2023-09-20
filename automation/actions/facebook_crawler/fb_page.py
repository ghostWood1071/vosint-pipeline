import json
import time
import random
time_waiting = random.randint(1,7)
from .authenticate import authenticate
import re
from .nlp import get_sentiment, get_keywords
from bson.objectid import ObjectId
from playwright.sync_api import sync_playwright
from playwright.sync_api import Browser, Page

def select(from_element, expr, by = "css="):
        element = from_element.locator(f"{by}{expr}")
        element = [element.nth(i) for i in range(element.count())]
        return element

def fb_page(browser:Browser, cookies,link_person, account, password, source_acc_id, crawl_acc_id):
    data = {}

    page:Page = authenticate(browser, cookies, link_person, account, password, source_acc_id) 
    page.keyboard.press('End')
    page.wait_for_selector('body')
    time.sleep(10)
    content = page.inner_html("body")
    datas = []
    return datas

#fb_groups(link_person="https://mbasic.facebook.com/thanh.bi.73")     
