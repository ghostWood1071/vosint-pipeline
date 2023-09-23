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
from .util import *


        
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
        data["id_social"] = crawl_social_id
        data["sentiment"] = get_sentiment(data["header"], data["content"])
        data["keywords"] = get_keywords(data["content"])
        return data
    except:
        raise Exception("post none")
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
    page:Page = authenticate(browser, cookies, link_person, account, password, source_acc_id) 
    # articles = select(page, "article")
    # for article in articles:
    #      get_article_data(article) 
    scroll_loop(get_articles, page=page, crawl_social_id=crawl_acc_id)
    
         

#fb_groups(link_person="https://mbasic.facebook.com/thanh.bi.73")     
