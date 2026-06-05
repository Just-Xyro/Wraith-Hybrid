import requests
import json
from typing import Dict, Any, List, Optional, Tuple


def fetchVariants(apiVariants: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    variants = []
    if not isinstance(apiVariants, list):
        return variants

    for variantDetail in apiVariants:
        channel = variantDetail.get("channel")
        optionsList = variantDetail.get("options")

        if channel and isinstance(optionsList, list) and optionsList:
            active = optionsList[0].get("tag")
            owned = [option.get("tag") for option in optionsList if option.get("tag")]

            if active and owned:
                variants.append({
                    "channel": channel,
                    "active": active,
                    "owned": owned
                })

    return variants


def fetchAthenaCosmetics() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    backendValueMap = {
        "AthenaEmoji": "AthenaDance",
        "AthenaSpray": "AthenaDance",
        "AthenaToy": "AthenaDance",
        "AthenaPetCarrier": "AthenaBackpack",
        "AthenaPet": "AthenaBackpack",
        "SparksDrum": "SparksDrums",
        "SparksMic": "SparksMicrophone",
        "CosmeticCompanion": "CosmeticMimosa",
        "SparksTrack": "SparksSong"
    }

    categories = [
        "br",
        "lego",
        "beans",
        "tracks",
        "instruments",
        "cars",
        "legoKits"
    ]

    athena: Dict[str, Any] = {
        "AthenaCharacter:CID_BeanCharacter_TEST": {
            "templateId": "AthenaCharacter:CID_BeanCharacter_TEST",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        },
        "AthenaCharacter:CID_BeanCharacter_Original": {
            "templateId": "AthenaCharacter:CID_BeanCharacter_Original",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        },
        "AthenaCharacter:Bean_ZombieJonesy": {
            "templateId": "AthenaCharacter:Bean_ZombieJonesy",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        },
        "AthenaCharacter:Bean_ZombieElasticEB": {
            "templateId": "AthenaCharacter:Bean_ZombieElasticEB",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        },
        "AthenaCharacter:Bean_RenegadeSkull": {
            "templateId": "AthenaCharacter:Bean_RenegadeSkull",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        },
        "SparksBass:Sparks_Bass_Generic": {
            "templateId": "SparksBass:Sparks_Bass_Generic",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        },
        "SparksGuitar:Sparks_Guitar_Generic": {
            "templateId": "SparksGuitar:Sparks_Guitar_Generic",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        },
        "SparksDrums:Sparks_Drum_Generic": {
            "templateId": "SparksDrums:Sparks_Drum_Generic",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        },
        "SparksMicrophone:Sparks_Mic_Generic": {
            "templateId": "SparksMicrophone:Sparks_Mic_Generic",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        },
        "SparksKeyboard:Sparks_Keytar_Generic": {
            "templateId": "SparksKeyboard:Sparks_Keytar_Generic",
            "attributes": {
                "max_level_bonus": 0,
                "archived": False,
                "level": 1,
                "item_seen": True,
                "xp": 0,
                "variants": [],
                "favorite": False
            },
            "quantity": 1
        }
    }

    commonCore: Dict[str, Any] = {}

    try:
        response = requests.get("https://fortnite-api.com/v2/cosmetics")
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200 or "data" not in data:
            return athena, commonCore

        for categoryName in categories:
            cosmeticsData = data["data"].get(categoryName, [])

            for item in cosmeticsData:
                itemId = item.get("id")
                if not itemId:
                    continue

                variants: List[Dict[str, Any]] = []
                prefix: Optional[str] = None

                if categoryName == "tracks":
                    prefix = "SparksSong"

                elif categoryName in ["br", "instruments", "cars", "legoKits"]:
                    originalPrefix = item.get("type", {}).get("backendValue")
                    if originalPrefix:
                        prefix = backendValueMap.get(originalPrefix, originalPrefix)

                if categoryName == "br":
                    apiVariants = item.get("variants")
                    variants = fetchVariants(apiVariants)

                if prefix:
                    templateId = f"{prefix}:{itemId}"
                elif itemId:
                    templateId = itemId
                else:
                    continue

                athena[templateId] = {
                    "templateId": templateId,
                    "attributes": {
                        "max_level_bonus": 0,
                        "archived": False,
                        "level": 1,
                        "item_seen": True,
                        "xp": 0,
                        "variants": variants,
                        "favorite": False
                    },
                    "quantity": 1
                }

    except (requests.exceptions.RequestException, json.JSONDecodeError):
        pass

    try:
        bannerResponse = requests.get("https://fortnite-api.com/v1/banners")
        bannerResponse.raise_for_status()
        bannerData = bannerResponse.json()

        for banner in bannerData.get("data", []):
            bannerId = banner.get("id")
            if bannerId:
                templateId = f"HomebaseBannerIcon:{bannerId}"
                commonCore[templateId] = {
                    "templateId": templateId,
                    "quantity": 1,
                    "attributes": {
                        "item_seen": True
                    }
                }
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        pass

    try:
        colorResponse = requests.get("https://fortnite-api.com/v1/banners/colors")
        colorResponse.raise_for_status()
        colorData = colorResponse.json()

        for color in colorData.get("data", []):
            colorId = color.get("id")
            if colorId:
                templateId = f"HomebaseBannerColor:{colorId}"
                commonCore[templateId] = {
                    "templateId": templateId,
                    "quantity": 1,
                    "attributes": {
                        "item_seen": True
                    }
                }
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        pass

    return athena, commonCore