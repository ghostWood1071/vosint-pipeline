import datetime
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
from .utils import *
from dateutil import parser

def get_article_data(article_raw:Locator, crawl_social_id):
    try:
        # check pinned
        social_context_tag = select(article_raw,'//*[@data-testid="socialContext"]')
        if len(social_context_tag) != 0: is_pinned = social_context_tag[0].inner_text()== "Pinned"
        else: is_pinned = False
        # kiem tra tin co phai trong ngay khong
        footer_date = convert_utc_to_utcp7(select(article_raw, 'time')[0].get_attribute('datetime'))
        post_date = parser.parse(footer_date)
        current_date = datetime.today().date()
        # if post_date.date() < current_date and not is_pinned:
        #     print('post_date: ', post_date)
        #     print('current_date: ', current_date)
        #     return None

        print('post_date: ', post_date)
        print('current_date: ', current_date)


        header_tag = select(article_raw, '//*[@data-testid="User-Name"]/div[1]')[0]

        post_link = select(article_raw, '//a[time]')[0].get_attribute('href')
        post_id = post_link.split('/')[3]
        user_id = post_link.split('/')[1]
        header = select(header_tag, 'div')[0].text_content()
        content = select(article_raw, '//*[@data-testid="tweetText"]')[0].text_content().replace('Show more', '')


        try:
            like = select(article_raw, '//*[@data-testid="like"]')[0].text_content()
            like = process_like(like)
        except:
            like = 0

        try:
            comment = select(article_raw, '//*[@data-testid="reply"]')[0].text_content()
            comment = process_like(comment)
        except:
            comment = 0

        try:
            share = select(article_raw, '//*[@data-testid="reply"]')[0].text_content()
            share = process_like(share)
        except:
            share = 0

        sentiment = get_sentiment(header, content)
        keywords = get_keywords(content)

        data = {
            "post_link": post_link,
            "header": header,
            "content": content,
            "footer_date": footer_date,
            "like": like,
            "comment": comment,
            "share": share,
            "post_id": post_id,
            "user_id": user_id,
            "sentiment": sentiment,
            "keywords": keywords,
            "id_social": crawl_social_id,
            "is_pinned": is_pinned
        }
        return data



    except Exception as e:
        raise Exception("post none")

def get_articles(page:Page, got_article:int, crawl_social_id)->bool:
    articles = select(page, "article")
    subset_articles = articles[got_article:len(articles)]
    for article in subset_articles:
        try:
            data = get_article_data(article, crawl_social_id)
            print('data: ', data)
            if data is None:
                print("is old news")
                return 0
            success = check_and_insert_to_db(data)
            if not success and not data["is_pinned"]:
                print("success: ", success)
                print("is_existed")
                return 0
            else:
                return len(articles) + 1
        except Exception as e:
            continue
    return len(articles)

def twitter_account(browser, cookies,link_person, account, password, source_acc_id,crawl_acc_id):
    page:Page = authenticate(browser, cookies, link_person, account, password, source_acc_id)
    scroll_loop(get_articles, page=page, crawl_social_id=crawl_acc_id)