from features.nlp.routers import router as NlpRouter
from features.pipeline.routers import router as PipeLineRouter
from features.job.routers import router as JobRouter

ROUTE_LIST = [
    {"route": JobRouter, "tags": ["Job"], "prefix": "/Job"},
    {"route": PipeLineRouter, "tags": ["Pipeline"], "prefix": "/Pipeline"},
    {"route": NlpRouter, "tags": ["Nlp"], "prefix": "/Nlp"}
]