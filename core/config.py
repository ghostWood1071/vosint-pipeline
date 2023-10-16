from typing import List

from pydantic import AnyHttpUrl, BaseSettings

import sys
import os
script_path = os.path.abspath(sys.argv[0])
script_directory = os.path.dirname(script_path)

class Settings(BaseSettings):
    # APP_TITLE: str = "V-OSINT API"
    class Config:
        env_file = script_directory+"/.env"
        env_file_encoding = "utf-8"
        secrets_dir = script_directory+"/secrets"
        case_sensitive = False

    APP_ORIGINS = [
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

    #
    API_PIPELINE: str
    #kafka
    KAFKA_CONNECT: str
    #elastic
    ELASTIC_CONNECT: str
  
    EXTRACT_KEYWORD_API: str
    DOCUMENT_CLUSTERING_API: str
    KEYWORD_CLUSTERING_API: str
    SENTIMENT_API: str
    TRANSLATE_API: str


settings = Settings()
setting_dict = settings.dict()
for env_name in list(settings.__annotations__.keys()):
    type_obj = settings.__annotations__[env_name]
    if type_obj != List[str]:
        env_val = type_obj(os.environ.get(env_name, setting_dict.get(env_name)))
    else:
        env_val = os.environ.get(env_name, str(setting_dict.get(env_name)))
    settings.__setattr__(env_name, env_val)
