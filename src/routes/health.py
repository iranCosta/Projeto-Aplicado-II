from fastapi import APIRouter

from src.controllers.health_controller import checar_saude

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return checar_saude()
