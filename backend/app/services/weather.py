import httpx
import re
from datetime import datetime, date, timedelta
from typing import Optional

MEMPHIS_LAT = 35.1495
MEMPHIS_LON = -90.0490
NWS_USER_AGENT = "MemphisMeatScout/1.0 contact@memphismeatscout.com"
CACHE_TTL_SECONDS = 3 * 60 * 60  # 3 hours

_cache: dict = {"data": None, "fetched_at": None}


def _day_label(d: date) -> str:
    today = date.today()
    if d == today:
        return "Today"
    if d == today + timedelta(days=1):
        return "Tomorrow"
    return d.strftime("%A")


def _parse_wind(wind_str: str) -> int:
    nums = re.findall(r"\d+", str(wind_str))
    return max(int(n) for n in nums) if nums else 0


async def _fetch_nws() -> Optional[list]:
    try:
        headers = {"User-Agent": NWS_USER_AGENT, "Accept": "application/geo+json"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            points = await client.get(
                f"https://api.weather.gov/points/{MEMPHIS_LAT},{MEMPHIS_LON}",
                headers=headers,
            )
            points.raise_for_status()
            forecast_url = points.json()["properties"]["forecast"]

            forecast = await client.get(forecast_url, headers=headers)
            forecast.raise_for_status()
            periods = forecast.json()["properties"]["periods"]

        daytime = [p for p in periods if p.get("isDaytime", True)][:3]
        result = []
        for p in daytime:
            d = date.fromisoformat(p["startTime"][:10])
            precip = p.get("probabilityOfPrecipitation") or {}
            precip_val = precip.get("value") if isinstance(precip, dict) else None
            result.append({
                "label": _day_label(d),
                "high": p["temperature"],
                "precip_pct": precip_val if precip_val is not None else 0,
                "wind_mph": _parse_wind(p.get("windSpeed", "0 mph")),
            })
        return result
    except Exception:
        return None


async def _fetch_open_meteo() -> Optional[list]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": MEMPHIS_LAT,
                    "longitude": MEMPHIS_LON,
                    "daily": "temperature_2m_max,precipitation_probability_max,windspeed_10m_max",
                    "temperature_unit": "fahrenheit",
                    "timezone": "America/Chicago",
                    "forecast_days": 3,
                },
            )
            resp.raise_for_status()
            daily = resp.json()["daily"]

        result = []
        for i in range(3):
            d = date.fromisoformat(daily["time"][i])
            result.append({
                "label": _day_label(d),
                "high": round(daily["temperature_2m_max"][i]),
                "precip_pct": int(daily["precipitation_probability_max"][i] or 0),
                "wind_mph": round(daily["windspeed_10m_max"][i]),
            })
        return result
    except Exception:
        return None


async def get_forecast() -> Optional[dict]:
    now = datetime.utcnow()
    if _cache["data"] and _cache["fetched_at"]:
        age = (now - _cache["fetched_at"]).total_seconds()
        if age < CACHE_TTL_SECONDS:
            return _cache["data"]

    days = await _fetch_nws()
    if not days:
        days = await _fetch_open_meteo()

    if days:
        _cache["data"] = {"days": days}
        _cache["fetched_at"] = now
        return _cache["data"]

    return None
