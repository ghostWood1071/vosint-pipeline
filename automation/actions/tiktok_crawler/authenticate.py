import json
import time
import random
time_waiting = random.randint(1,7)
from playwright.sync_api import sync_playwright, Page, Browser
from typing import *
from models.mongorepository import MongoRepository
import json


def login(page, account, password):
    # page.type("input#m_login_email", account)
    # page.type('input#m_login_password', password)
    # page.press('input#m_login_password', "Enter")
    # time.sleep(5)
    cookie = [
        {'name': 'tt_csrf_token', 'value': 'DAMQ9m7Q-_c1jkbZ-_vxfB6ziYkbFcU0L93w', 'domain': '.tiktok.com', 'path': '/',
         'expires': -1, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'}, {'name': '__tea_cache_tokens_1988',
                                                                               'value': '{%22_type_%22:%22default%22%2C%22user_unique_id%22:%227291906976681297416%22%2C%22timestamp%22:1697779408744}',
                                                                               'domain': '.www.tiktok.com', 'path': '/',
                                                                               'expires': 1698384242, 'httpOnly': False,
                                                                               'secure': False, 'sameSite': 'Lax'},
        {'name': 'passport_csrf_token', 'value': 'b9cb3cc5dba3876def227d1430930572', 'domain': '.tiktok.com',
         'path': '/', 'expires': 1702963409.580471, 'httpOnly': False, 'secure': True, 'sameSite': 'None'},
        {'name': 'passport_csrf_token_default', 'value': 'b9cb3cc5dba3876def227d1430930572', 'domain': '.tiktok.com',
         'path': '/', 'expires': 1702963409.580535, 'httpOnly': False, 'secure': False, 'sameSite': 'Lax'},
        {'name': 's_v_web_id', 'value': 'verify_lny61ae6_m5hnfID5_qi1s_4pJI_AwW5_RzS3HqjRqUHW', 'domain': '.tiktok.com',
         'path': '/', 'expires': -1, 'httpOnly': False, 'secure': True, 'sameSite': 'None'},
        {'name': 'multi_sids', 'value': '7290765131746362376%3A688bc30409786d19088d08c475e8f72a',
         'domain': '.tiktok.com', 'path': '/', 'expires': 1702963437.482018, 'httpOnly': True, 'secure': True,
         'sameSite': 'Lax'},
        {'name': 'cmpl_token', 'value': 'AgQQAPOFF-RO0rUQ7uXSuR0x_1OX8XfXP4oOYMxcdw', 'domain': '.tiktok.com',
         'path': '/', 'expires': 1702963437.482218, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'},
        {'name': 'sid_guard',
         'value': '688bc30409786d19088d08c475e8f72a%7C1697779437%7C15552000%7CWed%2C+17-Apr-2024+05%3A23%3A57+GMT',
         'domain': '.tiktok.com', 'path': '/', 'expires': 1728883437.482328, 'httpOnly': True, 'secure': True,
         'sameSite': 'Lax'},
        {'name': 'uid_tt', 'value': '6e57974f6fd58063412d7e43d8af0934bb7c42832f7f28d155d732fbba80ffed',
         'domain': '.tiktok.com', 'path': '/', 'expires': 1713331437.48238, 'httpOnly': True, 'secure': True,
         'sameSite': 'Lax'},
        {'name': 'uid_tt_ss', 'value': '6e57974f6fd58063412d7e43d8af0934bb7c42832f7f28d155d732fbba80ffed',
         'domain': '.tiktok.com', 'path': '/', 'expires': 1713331437.482408, 'httpOnly': True, 'secure': True,
         'sameSite': 'None'},
        {'name': 'sid_tt', 'value': '688bc30409786d19088d08c475e8f72a', 'domain': '.tiktok.com', 'path': '/',
         'expires': 1713331437.482432, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'},
        {'name': 'sessionid', 'value': '688bc30409786d19088d08c475e8f72a', 'domain': '.tiktok.com', 'path': '/',
         'expires': 1713331437.482456, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'},
        {'name': 'sessionid_ss', 'value': '688bc30409786d19088d08c475e8f72a', 'domain': '.tiktok.com', 'path': '/',
         'expires': 1713331437.482479, 'httpOnly': True, 'secure': True, 'sameSite': 'None'}, {'name': 'sid_ucp_v1',
                                                                                               'value': '1.0.0-KDU3ZTAxMTE3OGI5ODkwOWNjZjg3ZjdmOTk5YmE4MmIxMDdiNGUxNTYKIAiIiK_UpYiAl2UQ7Z3IqQYYswsgDDD4gLipBjgEQOoHEAMaBm1hbGl2YSIgNjg4YmMzMDQwOTc4NmQxOTA4OGQwOGM0NzVlOGY3MmE',
                                                                                               'domain': '.tiktok.com',
                                                                                               'path': '/',
                                                                                               'expires': 1713331437.482502,
                                                                                               'httpOnly': True,
                                                                                               'secure': True,
                                                                                               'sameSite': 'Lax'},
        {'name': 'ssid_ucp_v1',
         'value': '1.0.0-KDU3ZTAxMTE3OGI5ODkwOWNjZjg3ZjdmOTk5YmE4MmIxMDdiNGUxNTYKIAiIiK_UpYiAl2UQ7Z3IqQYYswsgDDD4gLipBjgEQOoHEAMaBm1hbGl2YSIgNjg4YmMzMDQwOTc4NmQxOTA4OGQwOGM0NzVlOGY3MmE',
         'domain': '.tiktok.com', 'path': '/', 'expires': 1713331437.482526, 'httpOnly': True, 'secure': True,
         'sameSite': 'None'},
        {'name': 'store-idc', 'value': 'alisg', 'domain': '.tiktok.com', 'path': '/', 'expires': 1713331437.87966,
         'httpOnly': True, 'secure': False, 'sameSite': 'Lax'},
        {'name': 'store-country-code', 'value': 'vn', 'domain': '.tiktok.com', 'path': '/',
         'expires': 1713331437.879731, 'httpOnly': True, 'secure': False, 'sameSite': 'Lax'},
        {'name': 'store-country-code-src', 'value': 'uid', 'domain': '.tiktok.com', 'path': '/',
         'expires': 1713331437.879762, 'httpOnly': True, 'secure': False, 'sameSite': 'Lax'},
        {'name': 'tt-target-idc', 'value': 'alisg', 'domain': '.tiktok.com', 'path': '/', 'expires': 1713331437.879788,
         'httpOnly': True, 'secure': False, 'sameSite': 'Lax'}, {'name': 'tt-target-idc-sign',
                                                                 'value': 'k3kzue1bA_6TQRy3m1ZpHtnsLjkRdixuEzIxXeLZlDDFRSaXDixs_Vzaj2wbyXe0YMkT_MSLgGR7XRvvjC1uLlKVRXij0o7vLP7G46VCOEi_XvDhqPo9QO_YIeeZ_rCx65PzeVMmfUJM8tW2CYxU_H9yANESysiJ_fWH-exXSLLBFc-S-4leKwOWEUym9OPoTULEtEa3VCylb4v1HNL6leXvFkMQ1zw-r80mnoxKPHDY-lwKiLRn3TwOu4cgra11snxwa3LY_aIde9ZXITFAZh-lWtGIlWaVGMqXkg5Q14KXbkoYAf-al2sbrHig8mHzC1Ujb83gnNJSGBhxxxVSiqwAchER9cpGF0Y7Sc0j8DtraMTXGUPmT7sQePy6_scH1MO-nnXjgZrSueO85jfOfm-XIav_ca2nLh6WNRwKCKgPHshrJYZcuJJrlP4z1_ricM8emKLwWEv65hQvrxXzhuJ2YynX2uVJaNEnJ1ua0mDcTZwUaYKsp9OEruvpTeer',
                                                                 'domain': '.tiktok.com', 'path': '/',
                                                                 'expires': 1729315438.254679, 'httpOnly': True,
                                                                 'secure': False, 'sameSite': 'Lax'},
        {'name': 'tt_chain_token', 'value': 'oXV/D06YyOVPJuNAdSClWQ==', 'domain': '.tiktok.com', 'path': '/',
         'expires': 1713331440.011643, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'},
        {'name': 'passport_fe_beating_status', 'value': 'true', 'domain': '.www.tiktok.com', 'path': '/', 'expires': -1,
         'httpOnly': False, 'secure': False, 'sameSite': 'Lax'},
        {'name': 'tiktok_webapp_theme', 'value': 'dark', 'domain': '.www.tiktok.com', 'path': '/',
         'expires': 1723699443, 'httpOnly': False, 'secure': True, 'sameSite': 'Lax'}, {'name': 'ttwid',
                                                                                        'value': '1%7C4nYnYZI9TD4i0VmfJM8RYXhWgSfvHVWRYnd9alIgqLo%7C1697779443%7C6c14298da225f0c2db3f347cf648321b7bdc60edce651796d75538ffc987b687',
                                                                                        'domain': '.tiktok.com',
                                                                                        'path': '/',
                                                                                        'expires': 1729315443.665631,
                                                                                        'httpOnly': True,
                                                                                        'secure': True,
                                                                                        'sameSite': 'None'},
        {'name': 'odin_tt',
         'value': '34d3550204b4c6f8a7aee84b6719b74d142056e546ccc73fb1770db7dec69e67d58ce17d67130e1e335a3722ca0bc8ab5eb6e420f99e95f327e188a8182a9e7b012fb7b0cecec300255d860aeaf768ab',
         'domain': '.tiktok.com', 'path': '/', 'expires': 1729315444.14918, 'httpOnly': True, 'secure': False,
         'sameSite': 'Lax'},
        {'name': 'csrf_session_id', 'value': '15ae21cc95a5aeef87dcc999035f7edc', 'domain': 'webcast.tiktok.com',
         'path': '/', 'expires': -1, 'httpOnly': False, 'secure': True, 'sameSite': 'None'}, {'name': 'msToken',
                                                                                              'value': 'Nrj3E_0wKKDXQo6b3WcoYr0aOVvRm5gKAyuzc2p4bWsgV8vNI0O7IXWPT5J7vPg4IMZruzgonZEadXu_vOmPKNK0fbbMeeSDpxWx-b7phBwMaIzToJnj2DaQOJY2GgL53SyXY5DYGkOyJtEE',
                                                                                              'domain': '.tiktok.com',
                                                                                              'path': '/',
                                                                                              'expires': 1698643447.858034,
                                                                                              'httpOnly': False,
                                                                                              'secure': True,
                                                                                              'sameSite': 'None'},
        {'name': 'msToken',
         'value': 'Nrj3E_0wKKDXQo6b3WcoYr0aOVvRm5gKAyuzc2p4bWsgV8vNI0O7IXWPT5J7vPg4IMZruzgonZEadXu_vOmPKNK0fbbMeeSDpxWx-b7phBwMaIzToJnj2DaQOJY2GgL53SyXY5DYGkOyJtEE',
         'domain': 'www.tiktok.com', 'path': '/', 'expires': 1705555447, 'httpOnly': False, 'secure': False,
         'sameSite': 'Lax'}]

    return cookie

def authenticate(browser: Browser, cookies: Any, link, account, password, source_acc_id):
    user_agent = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) "
        "AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
    )
    context = browser.new_context(user_agent=user_agent)
    context.add_cookies(cookies)
    page: Page = context.new_page()

    page.goto(link)
    # try:
    #     if page.title() == "Facebook – log in or sign up" in page.url:
    #         cookies = login(page, account, password)
    #         context.clear_cookies()
    #         context.add_cookies(cookies)
    #         page = context.new_page()
    #         page.goto(link)
    #         MongoRepository().update_one('socials', {"_id": source_acc_id, "cookie": json.dumps(cookies)})
    # except Exception as e:
    #     pass
    return page