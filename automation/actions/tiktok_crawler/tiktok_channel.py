import json
import time
import random
import traceback

time_waiting = random.randint(1,7)
import re
from .nlp import get_sentiment, get_keywords
from bson.objectid import ObjectId
from playwright.sync_api import sync_playwright
from playwright.sync_api import Browser, Page, Locator
from .authenticate import authenticate
from typing import *
from .utils import *


def tiktok_channel(browser, cookies,link_person, account, password, source_acc_id,crawl_acc_id):
    page:Page = browser.new_page()
    try:
        page.context.add_cookies(cookies)
    except Exception as e:
        print(e)
    print(link_person)
    page.goto(link_person)
    scroll_loop(get_videos, page=page, crawl_social_id= 1, browser= browser, cookies= cookies)

def get_video_data(browser: Browser, url: str, cookies, data: Dict[str, Any]) -> bool:
    page = browser.new_page()
    page.context.add_cookies(cookies)
    page.goto(url)
    time.sleep(10)
    try:
        header_tag = select(page, '//*[@data-e2e="browser-nickname"]/span[1]')[0]
        header = header_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        header = ''

    try:
        footer_date_tag = select(page, '//*[@data-e2e="browser-nickname"]/span[3]')[0]
        footer_date = footer_date_tag.inner_text()
    except Exception as e:
        footer_date= ''

    try:
        content_tag = select(page, '//*[@data-e2e="browse-video-desc"]')[0]
        content = content_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        content = ''

    try:
        like_tag = select(page, '//*[@data-e2e="like-count"]')[0]
        like = like_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        like = 0

    try:
        comment_tag = select(page, '//*[@data-e2e="comment-count"]')[0]
        comment = comment_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        comment = 0

    try:
        share_tag = select(page, '//*[@data-e2e="share-count"]')[0]
        share = share_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        share  = 0

    sentiment = get_sentiment(header, content)
    keywords = get_keywords(content)

    print('header: ', header)
    print('footer_date: ', footer_date)
    print('content: ', content)
    print('like: ', like)
    print('comment: ', comment)
    print('share: ', share)
    data.update({
        "header": header,
        "footer_date": footer_date,
        "content": content,
        "like": process_like(like),
        "comment": process_like(comment),
        "share": process_like(share),
        "video_link": url,
        "sentiment": sentiment,
        "keywords": keywords
    })

    page.close()
    return data

def get_videos(page: Page, got_videos: int, crawl_social_id, browser: Browser, cookies)-> bool:
    time.sleep(10)
    videos = select(page, '//*[@data-e2e="user-post-item-list"]/div')
    subset_videos = videos[got_videos:len(videos)]
    for video in subset_videos:
        try:
            link_tag = video.locator('//*[@data-e2e="user-post-item-desc"]/a[1]')
            link = link_tag.get_attribute('href')
            link_arr = link.split('/')
            social_id = link_arr[3]
            video_id = link_arr[5]
            data= {
                "social_id": social_id,
                "video_id": video_id
            }
            check = is_existed(data)
            if not check:
                data= get_video_data(browser, url=link, cookies=cookies, data= data)
                check_and_insert_to_db(data)
            else:
                return 0

            # get_video_data(browser, url=link, cookies=cookies)
        except Exception as e:
            traceback.print_exc()
            browser.close()
    browser.close()







