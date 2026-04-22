from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

# from app.core.rag_middleware import request_context_middleware
from app.api import rou
from app.core.http_logging import add_http_logging_middleware


def create_app() -> FastAPI:
    app = FastAPI(
        docs_url="/swagger",
        redoc_url="/swagger_redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=settings.ALLOWED_ORIGINS,
        # allow_credentials=True,
        allow_origins=["*"],
        allow_credentials=False,  # MUST be False when origins="*"
        allow_methods=["*"],
        allow_headers=["*"],
    )

    add_http_logging_middleware(app)

    # app.middleware("http")(request_context_middleware)

    app.include_router(rou)

    return app
