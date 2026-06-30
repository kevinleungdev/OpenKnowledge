import logging
from logging.handlers import RotatingFileHandler
import pathlib
import sys

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from open_knowledge.routers import files, knowledge
from open_knowledge.env import DATA_DIR, ENV, GLOBAL_LOG_LEVEL, SRC_LOG_LEVELS


logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

# In dev mode, mirror exceptions/errors to a rotating log file so tracebacks
# survive console scrollback. WARNING and above only; INFO logs (incl. the
# sqlalchemy.engine SQL echo) still go to the console alone. Off in every
# other environment.
if ENV == "dev":
    _log_dir = DATA_DIR / "logs"
    _log_dir.mkdir(parents=True, exist_ok=True)
    _file_handler = RotatingFileHandler(
        _log_dir / "open_knowledge.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    _file_handler.setLevel(logging.WARNING)
    _file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logging.getLogger().addHandler(_file_handler)
    log.info(f"Dev error log enabled at {_log_dir / 'open_knowledge.log'}")

app = FastAPI(
    title="Open Knowledge",
    docs_url="/api/docs" if ENV == "dev" else None,
    openapi_url="/api/openapi.json" if ENV == "dev" else None,
    redoc_url=None,
    # lifespan=lifespan,
)


# In dev mode, log every unhandled exception with its full traceback via the app
# logger so it reaches both the console and the dev error log file. Registered
# for the base Exception so it only catches genuinely unhandled errors;
# HTTPException and RequestValidationError keep their built-in handlers.
if ENV == "dev":

    @app.exception_handler(Exception)
    async def _log_unhandled_exception(request: Request, exc: Exception):
        log.error(
            "Unhandled exception on %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "message": str(exc)},
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
