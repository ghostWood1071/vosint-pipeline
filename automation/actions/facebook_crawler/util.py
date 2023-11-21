import time
import random
time_waiting = random.randint(1,7)
import re
from playwright.sync_api import  Page, Locator
from typing import *
from datetime import datetime, timedelta
from dateutil import parser
from models import MongoRepository

def scroll_loop(action: Any, max_news:int ,**kwargs:Dict[str, Any]):
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
            if real_got >= max_news:
                print("i'm break")
                break
            got_quantity = real_got

def check_and_insert_to_db(data):
    is_exists  = MongoRepository().get_one("facebook", {"post_id": data.get("post_id")})
    if is_exists == None:
        post_id = MongoRepository().insert_one("facebook", data)
        print("inserted: ", post_id)
        return True
    return False

def update_interact(data):
    MongoRepository().update_many("facebook", 
                                  {"post_id": data.get("post_id")}, 
                                  {"$set": {"like": data.get("like"),
                                            "share":data.get("share"),
                                            "comments": data.get("comments")
                                            }
                                  }
                                )

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

def get_image_links(elems):
    img_links = []
    for elem in elems:
        try:
            computed_style = elem.evaluate('(element) => getComputedStyle(element)', elem)
            background_image_url = computed_style['backgroundImage']
            background_image_url = background_image_url.replace('url("', '').replace('")', '')
            img_links.append(background_image_url)
        except Exception as e:
            continue
    return img_links

def get_video_links(elems):
    video_links = []
    for elem in elems:
        try:
            elem.click()
            time.sleep(0.1)
            video_tags = select(elem, "video")
            if len(video_tags)>0:
                video_links.append(video_tags[0].get_attribute("src"))
        except Exception as e:
            continue
    return video_links

def get_other_links(elems: List[Locator]):
    other_links = []
    for elem in elems:
        try:
            other_links.append(elem.get_attribute("href"))
        except Exception as e:
            continue
    return other_links
