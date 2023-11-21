import time
import random
time_waiting = random.randint(1,7)
import re
from playwright.sync_api import  Page, Locator
from typing import *
from datetime import datetime, timedelta
import dateutil
from models import MongoRepository
import requests
from core.config import settings
import json

def scroll_loop(action: Any ,**kwargs:Dict[str, Any]):
    kwargs.update({'got_article': 0})
    page:Page = kwargs.get("page")
    check = True
    while check:
        page.keyboard.press("End")
        page.wait_for_selector("body")
        time.sleep(10)
        pre_link_len = len(kwargs['post_links'])
        kwargs.update({'pre_link_len': pre_link_len})
        check = action(**kwargs)
        # if(real_got==0):
        #     break
        # else:
        #     got_quantity = real_got

def check_and_insert_to_db(data):
    record  = MongoRepository().get_one("twitter", {"post_id": data.get("post_id"), "user_id": data.get("user_id"), "id_social": data.get("id_social")})
    if record is None:
        MongoRepository().insert_one("twitter", data)
        return 1 # insert
    else:
        record.update({"like": data['like']})
        record.update({"comments": data['comments']})
        record.update({"share": data['share']})
        record.update({"content": data['content']})
        record.update({"sentiment": data['sentiment']})
        MongoRepository().update_one("twitter", record)
    return 2 # update

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
            result = dateutil.parser.parse(date_str, fuzzy=True)
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

def translate(language:str, content:str):
    result = ""
    try:
        lang_dict = {
            'cn': 'chinese',
            'ru': 'russia',
            'en': 'english'
        }
        lang_code = lang_dict.get(language)
        if lang_code is None:
            return ""
        req = requests.post(settings.TRANSLATE_API, data=json.dumps(
            {
                "language": lang_code,
                "text": content
            }
        ))
        result = req.json().get("translate_text")
        if not req.ok:
            raise Exception()
    except:
        result = ""
    return result