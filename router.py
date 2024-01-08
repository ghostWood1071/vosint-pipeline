
from features.job.routers import router as JobRouter
ROUTE_LIST = [
    {"route": JobRouter, "tags": ["Job"], "prefix": "/Job"},
]