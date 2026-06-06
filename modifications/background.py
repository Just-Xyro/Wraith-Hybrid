import json
import os

from mitmproxy import http

from handlers import filters

config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(config_path, "r") as f:
    config = json.load(f)

background_config = config.get("exploits", {}).get("custom_background", {})
enabled = background_config.get("enabled", True)
background_url = background_config.get("url", "https://github.com/Just-Xyro/Xyro-Hybrid/blob/main/lobby.png?raw=true")

@filters.is_fortnite_agent
def request(self, flow: http.HTTPFlow):
    if not enabled:
        return
    url = flow.request.pretty_url
    method = flow.request.method

    if ("//cdn-0001.qstv.on.epicgames.com/" in url or "//cdn2.unrealengine.com/" in url) and ("lobby" in url.lower()) and method == "GET":
        flow.request.url = background_url

@filters.is_fortnite_agent
def response(self, flow: http.HTTPFlow):
    if not enabled:
        return
    url = flow.request.pretty_url
    method = flow.request.method

    if "/api/fn/mnemonic/" in url and method == "GET":
        if flow.response.headers.get("Content-Type", "").startswith("application/json"):
            try:
                content_bytes = flow.response.content
                data = json.loads(content_bytes.decode("utf-8"))
                
                custom_image_url_data = {"url": background_url}
                
                if "parentLinks" in data and isinstance(data["parentLinks"], list):
                    for parent_link in data["parentLinks"]:
                        metadata = parent_link.get("metadata")
                        if (
                            isinstance(metadata, dict) and 
                            "lobby_background_image_urls" in metadata and
                            isinstance(metadata["lobby_background_image_urls"], dict)
                        ):
                            metadata["lobby_background_image_urls"] = custom_image_url_data

                if "links" in data and isinstance(data["links"], dict):
                    for link_data in data["links"].values():
                        metadata = link_data.get("metadata")
                        if (
                            isinstance(metadata, dict) and 
                            "lobby_background_image_urls" in metadata and
                            isinstance(metadata["lobby_background_image_urls"], dict)
                        ):
                            metadata["lobby_background_image_urls"] = custom_image_url_data
                        
                flow.response.content = json.dumps(data).encode("utf-8")
                
                flow.response.headers["Content-Length"] = str(len(flow.response.content))

            except json.JSONDecodeError:
                pass
            except Exception:
                pass