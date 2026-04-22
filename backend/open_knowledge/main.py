import logging
import pathlib
import sys

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

from open_knowledge.routers import files, knowledge
from open_knowledge.env import ENV, GLOBAL_LOG_LEVEL, SRC_LOG_LEVELS


logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

app = FastAPI(
    title="Open Knowledge",
    docs_url="/api/docs" if ENV == "dev" else None,
    openapi_url="/api/openapi.json" if ENV == "dev" else None,
    redoc_url=None,
    # lifespan=lifespan,
)


# For integrations
# app.state.config = AppConfig()

app.state.MODELS = {}

########################################
#
# Frontend
#
########################################


def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

    if not build_path.is_dir or not (build_path / "index.html").is_file():
        log.warn(
            f"Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )

        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm/pnpm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        # This creates a `catch-all` route:
        #   - Match **Any Path** under this route handler
        #   - Pass the full path to `dummy_frontend`
        #   - Return a 503 error saying 'frontend not built'
        return Route("/{path:path}", endpoint=dummy_frontend)

    return StaticFiles(directory=build_path, html=True)


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount("/app", create_frontend_router(), name="frontend")


########################################
#
# API
#
########################################

app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
