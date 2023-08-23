from typing import List

from pydantic import AnyHttpUrl, BaseSettings

import sys
import os
script_path = os.path.abspath(sys.argv[0])
script_directory = os.path.dirname(script_path)

class Settings(BaseSettings):
    # APP_TITLE: str = "V-OSINT API"
    APP_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:5173",
        "http://127.0.0.1:2000",
        "http://118.70.48.144:2000",
        "http://192.168.1.101:2000",
        "http://118.70.52.237:2000",
    ]
    APP_TITLE: str = "V-OSINT INGESTION"
    # APP_ORIGINS: List[AnyHttpUrl] =["*"]

    APP_HOST: str
    APP_PORT: int
    APP_STATIC_DIR: str = script_directory+"/static"

    PRIVATE_KEY: str
    PUBLIC_KEY: str

    MONGO_DETAILS: str 
    DATABASE_NAME: str 

    #Mongo
    MONGO_DETAILS: str
    DATABASE_NAME: str
    
    mong_host:str
    mongo_port: int
    mongo_username: str
    mongo_passwd: str
    mongo_db_name: str

    ROOT_PATH: str 

    # APP_HOST: str = "0.0.0.0"
    # APP_PORT: int = 3100
    # APP_STATIC_DIR: str = "/home/ds1/vosint/v-osint-backend/static"

    # PRIVATE_KEY: str
    # PUBLIC_KEY: str

    # MONGO_DETAILS: str = "mongodb://127.0.0.1:27017"
    # DATABASE_NAME: str = "v-osint"

    # ROOT_PATH: str = "./"

    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"
    #     secrets_dir = "/home/ds1/vosint/v-osint-backend/secrets"
    #     case_sensitive = True

    class Config:
        # print('ddddddddddddddddddddddddd',script_directory)
        env_file = script_directory+"/.env"
        env_file_encoding = "utf-8"
        secrets_dir = script_directory+"/secrets"
        case_sensitive = False

    #
    API_PIPELINE: str
    #kafka
    KAFKA_CONNECT: str
    #elastic
    ELASTIC_CONNECT: str
    #trans
    TRANS_CONNECT_EN: str
    TRANS_CONNECT_RU: str
    TRANS_CONNECT_CN: str

    EXTRACT_KEYWORD_API: str
    DOCUMENT_CLUSTERING_API: str
    SENTIMENT_API: str


settings = Settings()
