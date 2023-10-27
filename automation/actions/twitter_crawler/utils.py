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
    is_exists  = MongoRepository().get_one("twitter", {"post_id": data.get("post_id"), "user_id": data.get("user_id"), "id_social": data.get("id_social")})
    if is_exists == None:
        MongoRepository().insert_one("twitter", data)
        return True
    return False

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

def convert_utc_to_utcp7(datetime_str: str):
    datetime_object = parser.parse(datetime_str) + timedelta(hours=7)
    return datetime_object.strftime("%Y-%m-%d %H:%M:%S")