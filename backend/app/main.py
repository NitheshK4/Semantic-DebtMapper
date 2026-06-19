import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import (routes_audits, routes_ingest, routes_projects,
                     routes_reports, routes_auth)
from app.sandbox import routes_sandbox
from app.core.db import engine
from app.models.db_models import Base
from app.models.user import User  # Ensure User is in Base metadata

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Initializing database and enabling vector extension...")
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}", exc_info=True)
    yield


app = FastAPI(
    title="Semantic Debt Mapper (SDM)",
    description="Production AI reliability tool to map and detect semantic debt in ML/LLM pipelines",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
api_prefix = "/api/v1"
app.include_router(routes_projects.router, prefix=api_prefix)
app.include_router(routes_ingest.router, prefix=api_prefix)
app.include_router(routes_audits.router, prefix=api_prefix)
app.include_router(routes_reports.router, prefix=api_prefix)
app.include_router(routes_sandbox.router, prefix=api_prefix)
app.include_router(routes_auth.router, prefix=api_prefix)


@app.get("/health", tags=["Health"])
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}
