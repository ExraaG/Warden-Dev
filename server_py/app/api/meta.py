import httpx
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query

router = APIRouter(prefix="/v1/meta", tags=["meta"])

def format_sublabel(v: str, is_first: bool = False, is_stable: bool = True) -> Optional[str]:
    if not is_stable or any(x in v.lower() for x in ["snapshot", "-pre", "-rc", "w"]):
        return "Snapshot / Experimental"
    if is_first:
        return "Latest Release"
    if v == "26.2":
        return "Latest Release"
    if v == "1.21.1":
        return "Popular Release"
    if v == "1.20.1":
        return "LTS Modding Standard"
    if v == "1.16.5":
        return "Nether Update"
    return None

def fallback_versions() -> List[Dict[str, Any]]:
    versions = [
        ("26.2", "Latest Release"),
        ("26.1.2", None),
        ("26.1.1", None),
        ("26.1", None),
        ("1.21.4", "Latest Stable"),
        ("1.21.3", None),
        ("1.21.1", "Popular Release"),
        ("1.21", "Tricky Trials"),
        ("1.20.6", "Armored Paws"),
        ("1.20.4", "Popular Modding Standard"),
        ("1.20.2", None),
        ("1.20.1", "LTS Modding Standard"),
        ("1.19.4", "Trails & Tales"),
        ("1.19.2", "The Wild Update"),
        ("1.18.2", "Caves & Cliffs II"),
        ("1.16.5", "Nether Update"),
        ("1.12.2", "Classic Modding"),
        ("1.8.9", "Classic Combat"),
    ]
    return [{"id": v, "label": v, "sublabel": sub, "isStable": True} for v, sub in versions]

@router.get("/versions")
async def get_meta_versions(loader: str = Query("paper")):
    loader_lower = loader.lower()
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            if loader_lower == "paper":
                res = await client.get("https://api.papermc.io/v2/projects/paper")
                if res.is_success:
                    raw_versions = res.json().get("versions", [])
                    rev = list(reversed(raw_versions))
                    return {
                        "success": True,
                        "data": [
                            {
                                "id": v,
                                "label": v,
                                "sublabel": format_sublabel(v, i == 0),
                                "isStable": True,
                            }
                            for i, v in enumerate(rev)
                        ]
                    }
            elif loader_lower == "purpur":
                res = await client.get("https://api.purpurmc.org/v2/purpur")
                if res.is_success:
                    raw_versions = res.json().get("versions", [])
                    rev = list(reversed(raw_versions))
                    return {
                        "success": True,
                        "data": [
                            {
                                "id": v,
                                "label": v,
                                "sublabel": format_sublabel(v, i == 0),
                                "isStable": True,
                            }
                            for i, v in enumerate(rev)
                        ]
                    }
            elif loader_lower in ["fabric", "quilt"]:
                res = await client.get("https://meta.fabricmc.net/v2/versions/game")
                if res.is_success:
                    data = res.json()
                    releases = [item for item in data if item.get("stable")]
                    return {
                        "success": True,
                        "data": [
                            {
                                "id": item["version"],
                                "label": item["version"],
                                "sublabel": format_sublabel(item["version"], i == 0, True),
                                "isStable": True,
                            }
                            for i, item in enumerate(releases)
                        ]
                    }
            else:
                # Vanilla / default Mojang
                res = await client.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
                if res.is_success:
                    data = res.json()
                    releases = [v for v in data.get("versions", []) if v.get("type") == "release"]
                    return {
                        "success": True,
                        "data": [
                            {
                                "id": v["id"],
                                "label": v["id"],
                                "sublabel": format_sublabel(v["id"], i == 0, True),
                                "isStable": True,
                            }
                            for i, v in enumerate(releases)
                        ]
                    }
        except Exception:
            pass

    return {"success": True, "data": fallback_versions()}
