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
        post_id = get_post_id(article_raw, crawl_social_id)
        data_ft = article_raw.get_attribute("data-store")
        content_div_tag = select(article_raw, ".story_body_container")[0]
        header = select(content_div_tag, "header")[0]
        info = select(header, "a")[1].text_content()
        footer_date = select(header, 'div[data-sigil="m-feed-voice-subtitle"]')[0].text_content()
        data = {
            "header":info,
            "footer_date": convert_to_std_date(footer_date.split('·')[0].strip()).strftime("%d/%m/%Y"),
        }
        content_div_child_tag = select(content_div_tag, ">:nth-child(3)")[0]
        continue_content = select(content_div_child_tag, 'span[data-sigil="more"]')
        if len(continue_content) > 0:
            continue_a_tag = select(continue_content[0], "a")[0]
            continue_a_tag.click()
        content_div_child_tag = select(content_div_tag, ">:nth-child(2)")[0]
        data["content"] = content_div_child_tag.text_content().replace("… More","").replace("See Translation","")
        data["link"] = "http://m.facebook.com" + select(content_div_child_tag, "a")[0].get_attribute("href")
        media_elems = select(content_div_tag, ">:nth-child(3)")
        data["video_link"] = []
        data["image_link"] = []
        data["other_link"] = []
        if len(media_elems) > 0:
            media_div = media_elems[0]
            data["image_link"] = get_image_links(select(media_div, 'i.img[role="img"]'))
            data["video_link"] = get_video_links(select(media_div, 'div[data-sigil="inlineVideo"]'))
            data["other_link"] = get_other_links(select(media_div, 'a.touchable'))
        footer_tag = select(article_raw,"footer>:nth-child(1)>:nth-child(1)>:nth-child(1)>:nth-child(1)")[0]
        try:
            data["like"] = process_like(select(footer_tag, 'div[data-sigil="reactions-sentence-container"]')[0].text_content())
        except:
            data["like"] = 0
        try:
            comments = select(footer_tag,'span[data-sigil="comments-token"]')[0]
            data["comments"] = re.findall(r'\d+', comments.text_content())[0]
        except:
            data["comments"] = "0"
        try:
            data["share"] =re.findall(r'\d+',select(footer_tag,">:nth-child(2)>:nth-child(2)")[0].text_content())[0]
        except Exception as e:
            data["share"] = "0"
        data["id_data_ft"] = ""
        data["post_id"] = post_id #json.loads(data_ft).get("share_id")
        data["footer_type"] = "page"
        data["id_social"] = crawl_social_id
        data["sentiment"] = get_sentiment(data["header"], data["content"])
        data["keywords"] = get_keywords(data["content"])
        print(data)
        return data
    except Exception as e:
        raise Exception("post none")
#this is action
def get_articles(page:Page, got_article:int, crawl_social_id, mode_test)->bool:
    articles = select(page, "#m_group_stories_container> section > article")
    subset_articles = articles[got_article:len(articles)]
    collected_data = []
    for article in subset_articles:
        try: 
            data = get_article_data(article, crawl_social_id)
            if mode_test == False:
                success = check_and_insert_to_db(data)
                if not success:
                    print("is_existed")
                    update_interact(data)
            collected_data.append(data)
        except:
            continue
    return len(articles), collected_data

def fb_groups(browser, cookies,link_person, account, password, source_acc_id,crawl_acc_id, max_news, device, mode_test):
    page:Page = authenticate(browser, cookies, link_person, account, password, source_acc_id, device) 
    collected = scroll_loop(get_articles, max_news, page=page, crawl_social_id=crawl_acc_id, mode_test = mode_test)
    return collected