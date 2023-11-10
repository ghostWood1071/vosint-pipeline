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
    get_videos(page, 0, crawl_acc_id, cookies, max_news, video_links)
    # scroll_loop(get_videos, page=page, crawl_social_id= crawl_acc_id, cookies= cookies, max_news=max_news, video_links=video_links)

def get_video_data(page: Page, url: str, cookies, data: Dict[str, Any], content) -> bool:
    if content == '':
        print('video has no text content')
        return None
    page.goto(url)
    time.sleep(5)
    try:
        content_tag = select(page, '//*[@data-e2e="browse-video-desc"]')[0]
        content = content_tag.inner_text()
    except Exception as e:
        traceback.print_exc()
        content = ''

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
    time.sleep(5)
    page.wait_for_selector('body')
    page.wait_for_selector('//*[@data-e2e="user-post-item-list"]/div')
    videos = select(page, '//*[@data-e2e="user-post-item-list"]/div')

    # videos = select(page, 'div[data-e2e="user-post-item-list"] > div')
    if len(videos) == 0:
        raise CookiesExpireException('Cannot find any videos. Cookies may be expired.')
    subset_videos = videos[got_videos:len(videos)]
    links = []
    contents = []
    for video in subset_videos:
        # xpath = '//*[@id="main-content-others_homepage"]/div/div[2]/div[3]/div/div[1]/div[1]/div/div/a'
        # link_tag = video.locator(xpath)
        # link_tag = video.locator('//div[data-e2e="user-post-item-desc"]/a[1]')
        link_tag = video.locator('//*[@data-e2e="user-post-item-desc"]/a[1]')
        link = link_tag.get_attribute('href')
        links.append(link)

        try:
            # content_tag = select(video, '//*[@data-e2e="user-post-item-desc"]/a')[0]
            content = link_tag.get_attribute('title')
        except Exception as e:
            traceback.print_exc()
            content = ''
        contents.append(content)

    for i in range(len(links)):
        try:
            link = links[i]
            content = contents[i]
            if link not in video_links:
                video_links.append(link)
            # if len(video_links) > max_news:
            #     return -1
            if i >= max_news:
                return -1
            link_arr = link.split('/')
            social_id = link_arr[3]
            video_id = link_arr[5]
            data= {
                "social_id": social_id,
                "video_id": video_id,
                "id_social": crawl_social_id,
                "content": content
            }
            check = is_existed(data)
            if not check:
                data= get_video_data(page, url=link, cookies=cookies, data= data, content=content)
                if data is not None:
                    check_and_insert_to_db(data)
            else:
                return 0
        except Exception as e:
            traceback.print_exc()

def tiktok_channel_test(page: Page, cookies,link_persons, max_news):
    video_links = []
    try:
        page.context.add_cookies(cookies)
    except Exception as e:
        print(e)
    links = []
    contents = []
    datum = []
    for link_person in link_persons:
        page.goto(link_person)
        video_info_arr = get_video_info_on_channel(page, 0, link_person.get("_id"), cookies, max_news, video_links)
        for info in video_info_arr:
            links.extend(info['links'])
            contents.extend(info['contents'])
            datum.extend(info['datum'])
    for i in len(links):
        link = links[i]
        content = contents[i]
        data = datum[i]
        data = get_video_data(page, link, cookies, data, content)
        check_and_insert_to_db(data)

def get_video_info_on_channel(page: Page, got_videos: int, crawl_social_id, cookies, max_news, video_links):
    time.sleep(5)
    page.wait_for_selector('body')
    page.wait_for_selector('//*[@data-e2e="user-post-item-list"]/div')
    videos = select(page, '//*[@data-e2e="user-post-item-list"]/div')
    if len(videos) == 0:
        raise CookiesExpireException('Cannot find any videos. Cookies may be expired.')
    subset_videos = videos[got_videos:len(videos)]
    links = []
    contents = []
    datum = []
    for i in range(len(subset_videos)):
        video = subset_videos[i]
        link_tag = video.locator('//*[@data-e2e="user-post-item-desc"]/a[1]')
        link = link_tag.get_attribute('href')
        try:
            # content_tag = select(video, '//*[@data-e2e="user-post-item-desc"]/a')[0]
            content = link_tag.get_attribute('title')
        except Exception as e:
            traceback.print_exc()
            content = ''
        if i >=max_news:
            break

        link_arr = link.split('/')
        social_id = link_arr[3]
        video_id = link_arr[5]
        data = {
            "social_id": social_id,
            "video_id": video_id,
            "id_social": crawl_social_id,
            "content": content
        }
        check = is_existed(data)
        if not check:
            links.append(link)
            contents.append(content)
            datum.append(data)
    return {
        "links": links,
        "contents": contents,
        "datum": datum
    }











