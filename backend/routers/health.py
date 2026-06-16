from fastapi import APIRouter

router = APIRouter()


@router.get("/api/test", response_model=dict)
async def test_endpoint():
    return {
        "status": "ok",
        "message": "API is running",
        "version": "0.1.0",
    }
