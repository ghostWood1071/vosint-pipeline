import json
import time
import random
import traceback
import langdetect

time_waiting = random.randint(1,7)
import re
from .nlp import get_sentiment, get_keywords
from bson.objectid import ObjectId
from playwright.sync_api import sync_playwright
from playwright.sync_api import Browser, Page, Locator
from .authenticate import login
from typing import *
from .utils import *
from .cookies_expire_exception import CookiesExpireException


def tiktok_channel(page: Page, cookies,link_person, crawl_acc_id, max_news):
    video_links = []
    try:
        page.context.add_cookies(cookies)
    except Exception as e:
        print(e)
    print(link_person)
    page.goto(link_person)
    scroll_loop(get_videos, page=page, crawl_social_id= crawl_acc_id, cookies= cookies, max_news=max_news, video_links=video_links)

def get_video_data(page: Page, url: str, cookies, data: Dict[str, Any]) -> bool:
    page.goto(url)
    time.sleep(10)
    try:
        content_tag = select(page, '//*[@data-e2e="browse-video-desc"]')[0]
        content = content_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        content = ''

    if content == '':
        print('video has no text content')
        page.close()
        return None

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
        like_tag = select(page, '//*[@data-e2e="like-count"]')[0]
        like = like_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        like = 0

    try:
        comment_tag = select(page, '//*[@data-e2e="comment-count"]')[0]
        comments = comment_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        comments = 0

    try:
        share_tag = select(page, '//*[@data-e2e="share-count"]')[0]
        share = share_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        share  = 0

    try:
        sentiment = get_sentiment(header, content)
    except Exception as e:
        traceback.print_exc()
        sentiment = '0'

    try:
        lang = langdetect.detect(content)
        keywords = get_keywords(content, lang)
        print('lang: ', lang)
    except Exception as e:
        traceback.print_exc()
        keywords = []


    data.update({
        "header": header,
        "footer_date": footer_date,
        "content": content,
        "like": process_like(like),
        "comments": process_like(comments),
        "share": process_like(share),
        "video_link": url,
        "sentiment": sentiment,
        "keywords": keywords
    })

    print("data: ", data)
    return data

def get_videos(page: Page, got_videos: int, crawl_social_id, cookies, max_news, video_links)-> bool:
    time.sleep(10)
    videos = select(page, '//*[@data-e2e="user-post-item-list"]/div')
    if len(videos) == 0:
        raise CookiesExpireException('Cannot find any videos. Cookies may be expired.')
    subset_videos = videos[got_videos:len(videos)]
    links = []
    for video in subset_videos:
        link_tag = video.locator('//*[@data-e2e="user-post-item-desc"]/a[1]')
        link = link_tag.get_attribute('href')
        links.append(link)

    for link in links:
        try:
            if link not in video_links:
                video_links.append(link)
            if len(video_links) > max_news:
                return -1
            link_arr = link.split('/')
            social_id = link_arr[3]
            video_id = link_arr[5]
            data= {
                "social_id": social_id,
                "video_id": video_id,
                "id_social": crawl_social_id
            }
            check = is_existed(data)
            if not check:
                data= get_video_data(page, url=link, cookies=cookies, data= data)
                if data is not None:
                    check_and_insert_to_db(data)
            else:
                return 0
        except Exception as e:
            traceback.print_exc()








