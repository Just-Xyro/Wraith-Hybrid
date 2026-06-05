from mitmproxy import http
from functools import wraps


def isFortniteAgent(func):
    @wraps(func)
    def wrapper(self, flow: http.HTTPFlow):
        userAgent = flow.request.headers.get("User-Agent", "")

        allowedAgents = ("Fortnite", "EOS-SDK", "UELauncher", "UnrealEngine")

        if not any(tag in userAgent for tag in allowedAgents):
            return

        return func(self, flow)

    return wrapper


def cleanLoadoutItems(loadouts):
    for loadoutSchemaId, loadout in loadouts.items():
        try:
            for slot in loadout.get("loadoutSlots", []):
                itemId = slot.get("equippedItemId")
                if itemId and isinstance(itemId, str):
                    idParts = itemId.split(":")
                    if len(idParts) > 2:
                        cleanedId = f"{idParts[0]}:{idParts[1]}"
                        slot["equippedItemId"] = cleanedId
        except Exception:
            pass
    return loadouts