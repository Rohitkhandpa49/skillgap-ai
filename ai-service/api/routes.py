from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["analytics"])

@router.get("/health")
def health():
    return {"status": "ok"}
