from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.routes.chat import router as chat_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.search import router as search_router
from app.config.settings import settings

load_dotenv()  # Load environment variables from .env file at startup
# Create the FastAPI application instance.
# This object is what Uvicorn imports and runs.
# App metadata comes from environment-backed settings, so it can change
# between environments without editing application code.

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)


# Configure CORS (Cross-Origin Resource Sharing) to allow browser requests.
#
# When the frontend (running on localhost:5173) makes a POST request to the
# backend (localhost:8000), the browser first sends an automatic OPTIONS preflight
# request to check if the server allows cross-origin requests. This happens
# automatically before the actual POST request is sent—it's a browser security
# feature to prevent cross-origin attacks.
#
# Without CORS configuration, the backend returns 405 Method Not Allowed for
# the OPTIONS request, and the browser blocks the subsequent POST request.
# This appears as a network error in the frontend, even though the backend
# endpoint is working correctly.
#
# CORS middleware solves this by:
# 1. Listening for OPTIONS requests from different origins
# 2. Responding with headers that tell the browser which methods/headers are allowed
# 3. Allowing the subsequent actual requests (POST, GET, etc.) to proceed
app.add_middleware(
    CORSMiddleware,
    # List of origins that are allowed to make cross-origin requests.
    # In development, we allow localhost:5173 (Vite dev server default port).
    # In production, this would be restricted to specific frontend domains.
    # allow_origins=[
    #     "http://localhost:5173",
    #     "http://localhost:5174",
    #     "http://localhost:3000",
    #     "http://localhost:8000",
    # ],
    allow_origins=[
        "https://similar-incidents-temp-2.vercel.app",
    ],  # don't add / at the end of the url
    # HTTP methods that are allowed for cross-origin requests.
    # OPTIONS is required for preflight requests; GET/POST/etc. are for actual requests.
    allow_methods=["GET", "POST", "OPTIONS"],
    # HTTP headers that are allowed in cross-origin requests.
    # * means allow any headers sent by the frontend.
    allow_headers=["*"],
    # Allow cookies/credentials to be sent with cross-origin requests.
    # Set to False if your frontend doesn't need to send authentication cookies.
    allow_credentials=False,
)


# Register route modules here so main.py stays focused on application setup.
app.include_router(health_router)
app.include_router(incidents_router)
app.include_router(ingestion_router)
app.include_router(search_router)
app.include_router(chat_router)


# Run the development server with:
# uvicorn app.main:app --reload