import requests
from core.config import settings
import json

def get_sentiment(title, content):
    try:
        sentiment_req = requests.post(settings.SENTIMENT_API, data = json.dumps({
            'title': title, 
            'content': content,
            'description': 'string'
        }))
        if not sentiment_req.ok:
            raise Exception(sentiment_req.json())
        sentiments = sentiment_req.json().get("result")
        if len(sentiments) == 0:
            raise Exception()
        
        if sentiments[0] == "tieu_cuc":
            kq = "2"
        elif sentiments[0] == "trung_tinh":
            kq = "0"
        elif sentiments[0] == "tich_cuc":
            kq = "1"
        else:
            kq = ""
        return kq
    except Exception as e:
        raise e
    

def get_keywords(content):
    try:
        extkey_request = requests.post(settings.EXTRACT_KEYWORD_API, data=json.dumps({
            "number_keyword": 6,
            "text": content
        }))
        if not extkey_request.ok:
            raise Exception(extkey_request.json())
        result = extkey_request.json().get("translate_text")
        return result
    except Exception as e:
        raise e