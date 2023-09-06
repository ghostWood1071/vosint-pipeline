import datetime
import sys

# sys.path.insert(0, "/home/ghost/Desktop/vosint/vosint_pipeline/vosint_ingestion")

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import settings
from db import init_db

app = FastAPI(title=settings.APP_TITLE, root_path=settings.ROOT_PATH)

if settings.APP_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.APP_ORIGINS],
        #allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class Settings(BaseModel):
    expires = datetime.timedelta(days=1)
    authjwt_algorithm: str = "RS512"
    authjwt_public_key: str = settings.PUBLIC_KEY
    authjwt_private_key: str = settings.PRIVATE_KEY
    authjwt_access_token_expires: datetime.timedelta = expires
    authjwt_refresh_token_expires: datetime.timedelta = expires
    authjwt_token_location: set = {"cookies"}
    # Disable CSRF Protection for this example. default is True
    authjwt_cookie_csrf_protect: bool = False


@app.on_event("startup")
async def on_startup():
    await init_db.connect_db()


@app.on_event("shutdown")
async def on_shutdown():
    await init_db.close_db()


# """
#     Start file server for downloading static files.
# """
# app.mount("/static", StaticFiles(directory=settings.APP_STATIC_DIR), name="static")
"""
    Import and init route list
"""
from router import ROUTE_LIST
for route in ROUTE_LIST:
    app.include_router(route["route"], tags=route["tags"], prefix=route["prefix"])

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
