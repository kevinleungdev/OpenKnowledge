import logging
import sys

from fastapi import FastAPI

from open_knowledge.routers import files, knowledge
from open_knowledge.config import AppConfig
from open_knowledge.env import ENV, GLOBAL_LOG_LEVEL, SRC_LOG_LEVELS


logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])


print(
    rf"""
 ██████╗ ██████╗ ███████╗███╗   ██╗    ██╗  ██╗███╗   ██╗ ██████╗ ██╗    ██╗██╗     ███████╗██████╗  ██████╗ ███████╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ██║ ██╔╝████╗  ██║██╔═══██╗██║    ██║██║     ██╔════╝██╔══██╗██╔════╝ ██╔════╝
██║   ██║██████╔╝█████╗  ██╔██╗ ██║    █████╔╝ ██╔██╗ ██║██║   ██║██║ █╗ ██║██║     █████╗  ██║  ██║██║  ███╗█████╗  
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║    ██╔═██╗ ██║╚██╗██║██║   ██║██║███╗██║██║     ██╔══╝  ██║  ██║██║   ██║██╔══╝  
╚██████╔╝██║     ███████╗██║ ╚████║    ██║  ██╗██║ ╚████║╚██████╔╝╚███╔███╔╝███████╗███████╗██████╔╝╚██████╔╝███████╗
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝
"""
)

app = FastAPI(
    title="Open Knowledge",
    docs_url="/docs" if ENV == "dev" else None,
    openapi_url="/openapi.json" if ENV == "dev" else None,
    redoc_url=None,
    # lifespan=lifespan,
)


# For integrations
# app.state.config = AppConfig()


########################################
#
# WEBUI
#
########################################

app.state.MODELS = {}

app.include_router(
    knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])

app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
