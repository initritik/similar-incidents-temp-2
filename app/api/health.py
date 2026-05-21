from fastapi import APIRouter


# APIRouter lets us keep related endpoints in their own module.
# main.py imports this router and attaches it to the FastAPI app.
router = APIRouter()


@router.get("/health")
def health_check():
    """Return a simple status response for uptime checks."""
    return {"status": "ok"}
