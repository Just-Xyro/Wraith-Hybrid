import json
import xml.etree.ElementTree as ET

from mitmproxy import http
from handlers import filters


def websocket_message(proxy, flow: http.HTTPFlow):
    url = flow.request.pretty_url

    if "//xmpp-service-prod.ol.epicgames.com/" in url:
        for currentMsg in flow.websocket.messages:
            if not currentMsg.from_client:
                continue
            load = currentMsg.content.decode('utf-8', errors='ignore') if isinstance(currentMsg.content, bytes) else str(currentMsg.content)
            
            try:
                xmlRoot = ET.fromstring(load)
                statusNode = xmlRoot.find(".//status") or xmlRoot.find("status")
                
                if statusNode is not None and statusNode.text:
                    try:
                        jsonData = json.loads(statusNode.text)
                        jsonData["Status"] = "SHADOW"
                        statusNode.text = json.dumps(jsonData, separators=(',', ':'))
                        
                        updatedXml = ET.tostring(xmlRoot, encoding='unicode')
                        currentMsg.content = updatedXml.encode('utf-8')
                    except:
                        pass
            except:
                pass