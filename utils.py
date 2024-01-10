import uuid
from datetime import datetime

import pytz
import unidecode
import re

value_pattern = [
    "***",
    "dd",
    "mm",
    "yyyy"
]

spliters = [
    ",",
    ".",
    "/",
    "_",
    "-",
    " "
]

def get_time_now_string(
    tz: str = "Asia/Ho_Chi_Minh", fmt: str = "%Y/%m/%d %H:%M:%S"
) -> str:
    return datetime.now(pytz.timezone(tz)).strftime(fmt)

def get_time_now_string_y_m_d(
    tz: str = "Asia/Ho_Chi_Minh", fmt: str = "%Y/%m/%d"
) -> str:
    return datetime.now(pytz.timezone(tz)).strftime(fmt)

def get_time_now_string_y_m_now(
    tz: str = "Asia/Ho_Chi_Minh", fmt: str = "%Y/%m/%d"
) -> str:
    return datetime.strptime(str(get_time_now_string_y_m_d()), "%Y/%m/%d")
    
def gen_id(length: int = 12) -> str:
    return str(uuid.uuid4().hex[-length:])

def norm_text(text: str) -> str:
    text_lower = text.lower()
    text_removed_accent = unidecode.unidecode(text_lower)
    return text_removed_accent

def get_time_string_zone(
    date: datetime, tz: str = "Asia/Ho_Chi_Minh", fmt: str = "%Y/%m/%d"
):
    zone = pytz.timezone(tz)
    return zone.localize(date).strftime(fmt)

def format_date_pattern(pattern:str):
    pattern = pattern.replace("dd", "D")
    pattern = pattern.replace("mm", "M")
    pattern = pattern.replace("yyyy","Y")
    pattern = pattern.replace("***", "*")
    return pattern #=> D/M/Y *

def get_date_part(date_str:str, spliters):
    date_tmp = date_str
    for item in date_str:
        if item in spliters:
            date_tmp = date_tmp.replace(item, "$")
    return date_tmp

def find_remove_index(date_part:list[str], remove_values:list[str]):
    indices = [x for x, val in enumerate(date_part) if val in remove_values]
    return indices

def month_to_number(month_name, language='en', abbreviated=False):
    # Chuyển đổi tên tháng sang số dựa vào ngôn ngữ và viết tắt
    if language == 'en':
        if abbreviated:
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        else:
            months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    elif language == 'ru':
        if abbreviated:
            months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        else:
            months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    elif language == 'cn':
        if abbreviated:
            months = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
        else:
            months = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    else:
        return None  # Ngôn ngữ không hỗ trợ

    try:
        # Tìm vị trí của tháng trong danh sách và trả về số tương ứng
        month_number = months.index(month_name) + 1
        return month_number
    except ValueError:
        return None  # Nếu tên tháng không hợp lệ
    
def parse_string_time(input_date:str, date_pattern:str, lang:str):
    date_pattern = format_date_pattern(date_pattern)
    parttern_part = get_date_part(date_pattern, spliters).split("$")
    input_date_part = get_date_part(input_date, spliters).split("$")
    remove_index = find_remove_index(parttern_part, ["*"])

    for index in reversed(remove_index):
        parttern_part.pop(index)

    for index in reversed(remove_index):
        input_date_part.pop(index)

    if not set(["D", "M", "Y"]).issubset(parttern_part):
        parttern_part = date_pattern.split("*")
        input_date_part = re.findall(r"\d+", input_date_part[0])

    data = dict(zip(parttern_part, input_date_part))
    year = int(data.get("Y"))
    try:
        month = int(data.get("M"))
    except:
        month_val = re.findall(r"\d+", data.get("M")) 
        if len(month_val)>0:
            month = int(month_val[0])
        else:
            month = month_to_number(data.get("M"), lang)
            if month is None:
                month = month_to_number(data.get("M"), lang, abbreviated=True)
    day = int(data.get("D"))
    time_return = datetime(year, month, day)
    return time_return