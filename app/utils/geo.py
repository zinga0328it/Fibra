"""
app/utils/geo.py - Utility geografiche per la Centrale Operativa FTTH.

Contiene:
- haversine(): calcola distanza tra due punti GPS in km
- geocode_address(): converte indirizzo in lat/lng via Nominatim (OSM, gratis)
- find_nearest_technicians(): trova i tecnici più vicini a un punto
"""

import math
import logging
import httpx
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.models import Technician

logger = logging.getLogger("app.utils.geo")

# ── Haversine ─────────────────────────────────────────────────────
EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcola la distanza in km tra due punti (lat/lng) usando la formula di Haversine.

    Args:
        lat1, lng1: coordinate punto 1 (gradi decimali)
        lat2, lng2: coordinate punto 2 (gradi decimali)

    Returns:
        Distanza in chilometri.
    """
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = math.sin(dlat / 2) ** 2 + \
        math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


# ── Geocoding (Nominatim / OpenStreetMap) ─────────────────────────

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "FTTH-Gestionale/1.0 (admin@servicess.net)"}


def _build_geocode_queries(address: str) -> List[str]:
    queries = []
    cleaned = address.strip()
    if cleaned:
        queries.append(cleaned)
        queries.append(f"{cleaned}, Italia")

    if "," in cleaned:
        first_part = cleaned.split(",", 1)[0].strip()
        if first_part:
            queries.append(first_part)
            queries.append(f"{first_part}, Emilia-Romagna, Italia")

    deduped = []
    for q in queries:
        if q and q not in deduped:
            deduped.append(q)
    return deduped


def _pick_best_candidate(results: list) -> Optional[Tuple[float, float]]:
    if not results:
        return None

    for item in results:
        display_name = (item.get("display_name") or "").lower()
        if "emilia-romagna" in display_name:
            return (float(item["lat"]), float(item["lon"]))

    first = results[0]
    return (float(first["lat"]), float(first["lon"]))


async def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Converte un indirizzo testuale in coordinate (lat, lng) via Nominatim.

    Nominatim è gratuito con limite di 1 req/sec.
    Ritorna None se non trova risultati.
    """
    if not address or len(address.strip()) < 5:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for query in _build_geocode_queries(address):
                params = {
                    "q": query,
                    "format": "json",
                    "limit": 5,
                    "countrycodes": "it",
                }
                resp = await client.get(
                    NOMINATIM_URL,
                    params=params,
                    headers=NOMINATIM_HEADERS,
                )
                resp.raise_for_status()
                data = resp.json()
                best = _pick_best_candidate(data)
                if best:
                    lat, lng = best
                    logger.info("Geocoded '%s' (query='%s') → (%.6f, %.6f)", address, query, lat, lng)
                    return (lat, lng)

        logger.warning("Geocoding: nessun risultato per '%s'", address)
        return None

    except Exception as e:
        logger.error("Geocoding error per '%s': %s", address, e)
        return None


def geocode_address_sync(address: str) -> Optional[Tuple[float, float]]:
    """
    Versione sincrona di geocode_address (per uso in contesti non-async).
    """
    if not address or len(address.strip()) < 5:
        return None

    try:
        with httpx.Client(timeout=10.0) as client:
            for query in _build_geocode_queries(address):
                params = {
                    "q": query,
                    "format": "json",
                    "limit": 5,
                    "countrycodes": "it",
                }
                resp = client.get(
                    NOMINATIM_URL,
                    params=params,
                    headers=NOMINATIM_HEADERS,
                )
                resp.raise_for_status()
                data = resp.json()
                best = _pick_best_candidate(data)
                if best:
                    lat, lng = best
                    logger.info("Geocoded (sync) '%s' (query='%s') → (%.6f, %.6f)", address, query, lat, lng)
                    return (lat, lng)

        logger.warning("Geocoding sync: nessun risultato per '%s'", address)
        return None

    except Exception as e:
        logger.error("Geocoding sync error per '%s': %s", address, e)
        return None


# ── Trova tecnici più vicini ──────────────────────────────────────

def find_nearest_technicians(
    db: Session,
    target_lat: float,
    target_lng: float,
    limit: int = 3,
    exclude_id: Optional[int] = None,
) -> List[dict]:
    """
    Trova i tecnici disponibili più vicini a un punto.

    Filtra solo tecnici con:
    - stato_posizione = 'disponibile'
    - tracking_attivo = True
    - lat/lng non nulli

    Returns:
        Lista di dict ordinata per distanza crescente:
        [{"technician": Technician, "distance_km": float}, ...]
    """
    query = db.query(Technician).filter(
        Technician.stato_posizione == "disponibile",
        Technician.tracking_attivo == True,
        Technician.lat.isnot(None),
        Technician.lng.isnot(None),
    )
    if exclude_id:
        query = query.filter(Technician.id != exclude_id)

    tecnici = query.all()

    results = []
    for tech in tecnici:
        dist = haversine(target_lat, target_lng, tech.lat, tech.lng)
        results.append({
            "technician": tech,
            "distance_km": round(dist, 2),
        })

    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]
