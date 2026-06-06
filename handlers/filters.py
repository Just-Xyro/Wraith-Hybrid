from mitmproxy import http
from functools import wraps

def is_fortnite_agent(func):
    @wraps(func)
    def wrapper(self, flow: http.HTTPFlow):
        agent = flow.request.headers.get("User-Agent", "")
        
        agents = ("Fortnite", "EOS-SDK", "UELauncher", "UnrealEngine")

        if not any(tag in agent for tag in agents):
            return
        
        return func(self, flow)
        
    return wrapper

def clean_loadout_items(loadouts):
    for loadout_schema_id, loadout in loadouts.items():
        try:
            for slot in loadout.get("loadoutSlots", []):
                item_id = slot.get("equippedItemId")
                if item_id and isinstance(item_id, str):
                    parts = item_id.split(':')
                    if len(parts) > 2:
                        cleaned_id = f"{parts[0]}:{parts[1]}"
                        slot["equippedItemId"] = cleaned_id
        except Exception:
            pass
    return loadouts