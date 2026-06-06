import json

from mitmproxy import http
from utils import defs
from handlers import filters


@defs.isFortniteAgent
def response(self, flow: http.HTTPFlow):
    url = flow.request.pretty_url
    method = flow.request.method

    if url.endswith("/api/v1/fortnite-br/channel/motd/target") and method == "POST":
        requestData = json.loads(flow.request.text)
        tags = requestData.get("tags", [])

        placements = []
        for i, tag in enumerate(tags):
            placements.append({
                "trackingId": "Xyro",
                "tag": tag,
                "locations": [],
                "position": 0
            })

        responseData = {
    "contentItems": [
        {
            "contentHash": "Xyro",
            "contentSchemaName": "DynamicMotd",
            "contentFields": {
                "fullScreenTitle": "Xyro",
                "body": "Made by @xyro.py\nhttps://github.com/Just-Xyro",
                "teaserTitle": "Xyro",
                "fullScreenBackground": {
                    "image": [
                        {
                            "width": 1920,
                            "height": 1080
                        },
                        {
                            "width": 960,
                            "height": 540
                        }
                    ],
                    "type": "FullScreenBackground"
                },
                "teaserBackground": {
                    "image": [
                        {
                            "width": 720,
                            "height": 400
                        }
                    ],
                    "type": "TeaserBackground"
                },
                "verticalTextLayout": False
            },
            "placements": placements
        }
    ],
    "tcId": "Xyro"
}


        flow.response.text = json.dumps(responseData)
        flow.response.headers["contentType"] = "application/json"