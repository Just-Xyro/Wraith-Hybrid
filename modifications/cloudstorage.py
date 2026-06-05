import json
import hashlib
from pathlib import Path
from datetime import datetime

from mitmproxy import http
from utils import defs


def getFileHashes(content: bytes):
    sha1 = hashlib.sha1(content).hexdigest()
    sha256 = hashlib.sha256(content).hexdigest()
    return sha1, sha256


@defs.isFortniteAgent
def response(self, flow: http.HTTPFlow):
    url = flow.request.pretty_url
    method = flow.request.method
    hotfixesDir = Path("hotfixes")

    if url.endswith("/fortnite/api/cloudstorage/system/config") and method == "GET":
        configData = {
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
            "disableV2": False,
            "isAuthenticated": False,
            "enumerateFilesPath": "/fortnite/api/cloudstorage/system",
            "enableMigration": False,
            "enableWrites": False,
            "epicAppName": "Live",
            "transports": {
                "mcpProxyTransport": {
                    "name": "McpProxyTransport",
                    "type": "ProxyStreamingFile",
                    "appName": "fortnite",
                    "isEnabled": True,
                    "isRequired": True,
                    "isPrimary": True,
                    "timeoutSeconds": 30,
                    "priority": 10,
                },
                "mcpSignatoryTransport": {
                    "name": "McpSignatoryTransport",
                    "type": "ProxySignatory",
                    "appName": "fortnite",
                    "isEnabled": False,
                    "isRequired": False,
                    "isPrimary": False,
                    "timeoutSeconds": 30,
                    "priority": 20,
                },
                "dssDirectTransport": {
                    "name": "DssDirectTransport",
                    "type": "DirectDss",
                    "appName": "fortnite",
                    "isEnabled": True,
                    "isRequired": False,
                    "isPrimary": False,
                    "timeoutSeconds": 30,
                    "priority": 30,
                },
            },
        }

        flow.response = http.Response.make(
            200,
            json.dumps(configData),
            {"Content-Type": "application/json"},
        )

    if url.endswith("/fortnite/api/cloudstorage/system") and method == "GET":
        fileList = []
        if hotfixesDir.exists():
            for filePath in hotfixesDir.iterdir():
                if filePath.is_file() and not filePath.name.startswith("."):
                    fileContent = filePath.read_bytes()
                    sha1, sha256 = getFileHashes(fileContent)
                    fileList.append(
                        {
                            "uniqueFilename": filePath.name,
                            "filename": filePath.name,
                            "hash": sha1,
                            "hash256": sha256,
                            "length": len(fileContent),
                            "contentType": "application/json"
                            if filePath.name.endswith(".json")
                            else "text/plain",
                            "uploaded": datetime.utcnow().isoformat() + "Z",
                            "storageType": "S3",
                            "doNotCache": True,
                        }
                    )

        flow.response = http.Response.make(
            200,
            json.dumps(fileList),
            {"Content-Type": "application/json"},
        )

    if "/fortnite/api/cloudstorage/system/" in url and method == "GET":
        fileName = url.split("/")[-1]
        targetFile = hotfixesDir / fileName
        if targetFile.is_file():
            fileData = targetFile.read_bytes()
            contentType = (
                "application/json" if fileName.endswith(".json") else "text/plain"
            )

            flow.response = http.Response.make(
                200,
                fileData,
                {"Content-Type": contentType},
            )