from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.observability.http_logging import add_http_logging_middleware
from app.api import rou


def create_app()-> FastAPI:
    app = FastAPI(docs_url="/swagger",)
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
    app.include_router(rou)

    return app
