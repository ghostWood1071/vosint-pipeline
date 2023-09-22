import json
import time
import random
time_waiting = random.randint(1,7)
from .authenticate import authenticate
import re
from .nlp import get_sentiment, get_keywords
from bson.objectid import ObjectId
from playwright.sync_api import sync_playwright
from playwright.sync_api import Browser, Page, Locator
from typing import *
from datetime import datetime, timedelta
from dateutil import parser
from models import MongoRepository

def select(from_element: Union[Locator, Page], expr:str):
        element = from_element.locator(f"{expr}")
        element = [element.nth(i) for i in range(element.count())]
        return element

def convert_to_std_date(date_str:str):
    result = datetime.now()
    try:
        if 'hrs' in date_str:
            hour = int(re.findall(r"\d+", date_str)[0])
            result = result - timedelta(hours=hour)
        elif 'mins' in date_str:
            mins = int(re.findall(r"\d+", date_str)[0])
            result = result - timedelta(minutes=mins)
        else:
            result = parser.parse(date_str, fuzzy=True)
        return result
    except Exception as e:
        print(e)
        return result

def process_like(likes_string:str):       
    suffixes = {
        'K': 1000,
        'M': 1000000,
        'B': 1000000000,
        'T': 1000000000000,
    }
    matches = re.search(r'(\d+(\.\d+)?)', likes_string)
    if matches:
        number_str = matches.group(1)
        likes_quantity = float(number_str)
        remaining_text = likes_string.replace(number_str, '').strip()
        if remaining_text:
            for suffix in remaining_text.split(" "):
                multiplier = suffixes.get(suffix)
                if multiplier != None:
                    likes_quantity *= multiplier
                    break
        return likes_quantity
    else:
        return 0
        
def get_article_data(article_raw:Locator, crawl_social_id):
    try:
        data_ft = article_raw.get_attribute("data-ft")
        content_div_tag = select(article_raw, ">:nth-child(1)")[0]
        header = select(content_div_tag, "header")[0]
        info = select(header, "a")[1].text_content()
        footer_date = select(header, 'div[data-sigil="m-feed-voice-subtitle"]')[0].text_content()
        data = {
            "header":info,
            "footer_date": convert_to_std_date(footer_date.split('·')[0].strip()).strftime("%d/%m/%Y"),
        }
        content_div_child_tag = select(content_div_tag, ">:nth-child(2)")[0]
        continue_content = select(content_div_child_tag, 'span[data-sigil="more"]')
        if len(continue_content) > 0:
            continue_a_tag = select(continue_content[0], "a")[0]
            continue_a_tag.click()
        content_div_child_tag = select(content_div_tag, ">:nth-child(2)")[0]
        data["content"] = content_div_child_tag.text_content().replace("… Xem thêm","").replace("See Translation","")
        footer_tag = select(article_raw,"footer>:nth-child(1)>:nth-child(1)>:nth-child(1)>:nth-child(1)")[0]
        try:
            data["like"] = process_like(select(footer_tag, ">:nth-child(1)")[0].text_content())
        except:
            data["like"] = 0
        try:
            data["comments"] = re.findall(r'\d+',select(footer_tag,">:nth-child(2)>:nth-child(1)")[0].text_content())[0]
        except:
            data["comments"] = "0"
        try:
            data["share"] =re.findall(r'\d+',select(footer_tag,">:nth-child(2)>:nth-child(2)")[0].text_content())[0]
        except Exception as e:
            data["share"] = "0"
        data["id_data_ft"] = data_ft
        data["post_id"] = json.loads(data_ft).get("mf_story_key")
        data["footer_type"] = "page"
        data["social_id"] = crawl_social_id
        return data
    except:
        raise Exception("post none")
    
def scroll_loop(action: Any ,**kwargs:Dict[str, Any]):
    kwargs.update({'got_article': 0})
    page:Page = kwargs.get("page")
    got_quantity = 1
    while got_quantity>0:
        page.keyboard.press("End")
        page.wait_for_selector("body")
        time.sleep(10)
        real_got = action(**kwargs)
        if(real_got==0):
            break
        else:
            got_quantity = real_got

def check_and_insert_to_db(data):
    is_exists  = MongoRepository().get_one("facebook", {"post_id": data.get("post_id")})
    if is_exists == None:
        MongoRepository().insert_one("facebook", data)
        return True
    return False

#this is action
def get_articles(page:Page, got_article:int, crawl_social_id)->bool:
    articles = select(page, "article")
    subset_articles = articles[got_article:len(articles)]
    for article in subset_articles:
        try: 
            data = get_article_data(article, crawl_social_id)
            success = check_and_insert_to_db(data)
            if not success:
                print("is_existed")
                return 0
        except:
            continue
    return len(articles)

def fb_page(browser:Browser, cookies,link_person, account, password, source_acc_id, crawl_acc_id):
    data = {}
    page:Page = authenticate(browser, cookies, link_person, account, password, source_acc_id) 
    # articles = select(page, "article")
    # for article in articles:
    #      get_article_data(article) 
    scroll_loop(get_articles, page=page, crawl_social_id=crawl_acc_id)
    
         

#fb_groups(link_person="https://mbasic.facebook.com/thanh.bi.73")     
