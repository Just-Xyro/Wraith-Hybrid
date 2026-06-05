import json
from datetime import datetime

from mitmproxy import http
from utils import defs


@defs.isFortniteAgent
def response(self, flow: http.HTTPFlow):
    url = flow.request.pretty_url
    method = flow.request.method

    if url.endswith("/content/api/pages/fortnite-game/") and method == "GET":
        data = json.loads(flow.response.get_text())

        data["emergencynoticev2"] = {
            "_title": "emergencynoticev2",
            "_noIndex": False,
            "emergencynotices": {
                "_type": "Emergency Notices",
                "emergencynotices": [
                    {
                        "gamemodes": [],
                        "hidden": False,
                        "_type": "CommonUI Emergency Notice Base",
                        "title": "Xyro",
                        "body": "Made by @xyro.py\nhttps://github.com/Just-Xyro",

                    }
                ],
            },
            "_activeDate": "2023-09-26T03:00:00.000Z",
            "lastModified": datetime.utcnow().isoformat() + "Z",
            "_locale": "en",
            "_templateName": "FortniteGameMOTD",
        }

        flow.response.text = json.dumps(data)