from fastapi import APIRouter

router = APIRouter(tags=["monitoreo"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
