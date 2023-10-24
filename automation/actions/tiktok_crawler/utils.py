import time
import random
time_waiting = random.randint(1,7)
import re
from playwright.sync_api import  Page, Locator
from typing import *
from datetime import datetime, timedelta
from dateutil import parser
from models import MongoRepository

def scroll_loop(action: Any ,**kwargs:Dict[str, Any]):
    kwargs.update({'got_videos': 0})
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
    is_exists  = MongoRepository().get_one("tiktok", {"social_id": data.get("social_id"), "video_id": data.get("video_id")})
    if is_exists == None:
        MongoRepository().insert_one("tiktok", data)
        return True
    return False

def is_existed(data):
    is_exists = MongoRepository().get_one("tiktok",
                                          {"social_id": data.get("social_id"), "video_id": data.get("video_id")})
    if is_exists == None:
        return False
    return True

def select(from_element: Union[Locator, Page], expr:str):
        element = from_element.locator(f"{expr}")
        element = [element.nth(i) for i in range(element.count())]
        return element

def convert_to_std_date(date_str:str):
    result = datetime.now()
    try:
        if 'h' in date_str:
            hour = int(re.findall(r"\d+", date_str)[0])
            result = result - timedelta(hours=hour)
        elif 'm' in date_str:
            mins = int(re.findall(r"\d+", date_str)[0])
            result = result - timedelta(minutes=mins)
        # else:
        #     result = parser.parse(date_str, fuzzy=True)
        return result
    except Exception as e:
        print(e)
        return result
