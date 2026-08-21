import httpx
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query

router = APIRouter(prefix="/v1/meta", tags=["meta"])

@router.get("/versions")
async def get_meta_versions(loader: str = Query("paper")):
    loader_lower = loader.lower()
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            if loader_lower == "paper":
                res = await client.get("https://api.papermc.io/v2/projects/paper")
                if res.is_success:
                    versions = res.json().get("versions", [])
                    return {"success": True, "data": list(reversed(versions))}
            elif loader_lower == "purpur":
                res = await client.get("https://api.purpurmc.org/v2/purpur")
                if res.is_success:
                    versions = res.json().get("versions", [])
                    return {"success": True, "data": list(reversed(versions))}
            else:
                # Vanilla / default
                res = await client.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
                if res.is_success:
                    versions = [
                        v["id"] for v in res.json().get("versions", [])
                        if v.get("type") == "release"
                    ]
                    return {"success": True, "data": versions}
        except Exception:
            pass

    # Safe fallback list
    fallback = ["1.21.4", "1.21.3", "1.21.1", "1.20.6", "1.20.4", "1.20.2", "1.20.1", "1.19.4", "1.18.2", "1.16.5", "1.12.2", "1.8.9"]
    return {"success": True, "data": fallback}
