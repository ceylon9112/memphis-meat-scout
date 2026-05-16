from fastapi import APIRouter
from ..services.weather import get_forecast

router = APIRouter()


@router.get("/weather")
async def weather():
    data = await get_forecast()
    if not data:
        return {"error": "unavailable"}
    return data
