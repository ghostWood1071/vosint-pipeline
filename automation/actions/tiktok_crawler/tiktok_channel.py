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
from ...common import ActionInfo, ActionType, ParamInfo, ActionStatus




def get_video_data(page: Page, url: str, cookies, data: Dict[str, Any], content) -> bool:
    time.sleep(5)
    if content == '':
        print('video has no text content')
        return None
    page.goto(url)
    time.sleep(5)

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
        traceback.print_exc()
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
        share = 0

    try:
        lang = langdetect.detect(content)
    except Exception as e:
        print('Detect language error')
        lang = ''

    try:
        languages = ['cn', 'ru', 'en']
        if lang in languages:
            translated_content = translate(lang, content)
            sentiment = get_sentiment(header, translated_content)
        elif lang == 'vi':
            sentiment = get_sentiment(header, content)
        else:
            sentiment = "0"
    except Exception as e:
        traceback.print_exc()
        sentiment = '0'

    try:
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


def tiktok_channel(page: Page, cookies,accounts, max_news, create_log, pipeline_id):
    try:
        page.context.add_cookies(cookies)
    except Exception as e:
        print(e)
    # links = []
    # contents = []
    # datum = []
    account_dict = {}
    for account in accounts:
        page.goto(account.get('account_link'))
        time.sleep(10)
        info = get_video_info_on_channel(page, 0, account.get("_id"), max_news)
        links = info['links']
        contents = info['contents']
        datum = info['datum']
        account_dict[account.get('account_link')] = {
            "links": links,
            "contents": contents,
            "datum": datum
        }
        # links.extend(info['links'])
        # contents.extend(info['contents'])
        # datum.extend(info['datum'])
    for account in accounts:
        account_info = account_dict.get(account.get('account_link'))
        links = account_info.get('links')
        contents = account_info.get('contents')
        datum = account_info.get('datum')
        for i in range(len(links)):
            link = links[i]
            content = contents[i]
            data = datum[i]
            data = get_video_data(page, link, cookies, data, content)
            if data is not None:
                check = is_existed(data)
                if check:
                    check_and_update(data)
                else:
                    check_and_insert_to_db(data)
        create_log(ActionStatus.COMPLETED, account.get('account_link'), pipeline_id)

    # for i in range(len(links)):
    #     link = links[i]
    #     content = contents[i]
    #     data = datum[i]
    #     data = get_video_data(page, link, cookies, data, content)
    #     if data is not None:
    #         check = is_existed(data)
    #         if check:
    #             check_and_update(data)
    #         else:
    #             check_and_insert_to_db(data)


def get_video_info_on_channel(page: Page, got_videos: int, crawl_social_id, max_news):
    links = []
    contents = []
    datum = []
    try:
        time.sleep(10)
        page.wait_for_selector('body')
        videos = select(page, '//*[@data-e2e="user-post-item-list"]/div')
        if len(videos) == 0:
            raise CookiesExpireException('Cannot find any videos. Cookies may be expired.')
        subset_videos = videos[got_videos:len(videos)]
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
            if i >= max_news:
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
            links.append(link)
            contents.append(content)
            datum.append(data)
        return {
            "links": links,
            "contents": contents,
            "datum": datum
        }
    except CookiesExpireException as e:
        raise e
    except Exception as e:
        print(e)
        return {
            "links": links,
            "contents": contents,
            "datum": datum
        }












