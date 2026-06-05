import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from mitmproxy import http
from utils import defs


def getProfileDir(accountId):
    return Path("profiles") / accountId


def getTemplateDir():
    return Path("profiles") / "templateId"


def getFilePath(accountId, filename, useTemplate=False):
    if useTemplate:
        return getTemplateDir() / filename
    return getProfileDir(accountId) / filename


def copyTemplateFiles(accountId, deploymentId, currentTime):
    templateDir = getTemplateDir()
    accountDir = getProfileDir(accountId)
    accountDir.mkdir(parents=True, exist_ok=True)
    loadout = "activeLoadoutGroup.json"

    try:
        if templateDir.is_dir():
            for item in os.listdir(templateDir):
                if item != loadout:
                    sourcePath = templateDir / item
                    destinationPath = accountDir / item
                    if sourcePath.is_file():
                        shutil.copy2(sourcePath, destinationPath)

        loadoutAccountPath = accountDir / loadout

        if templateDir.is_dir() and (templateDir / loadout).is_file():
            shutil.copy2(templateDir / loadout, loadoutAccountPath)

        if loadoutAccountPath.exists():
            with open(loadoutAccountPath, "r") as f:
                loadoutData = json.load(f)

            if loadoutData.get("deploymentId") in ["", None]:
                loadoutData["deploymentId"] = deploymentId
            if loadoutData.get("accountId") in ["", None]:
                loadoutData["accountId"] = accountId
            if loadoutData.get("creationTime") in ["", None]:
                loadoutData["creationTime"] = currentTime

            loadoutData["updatedTime"] = currentTime

            with open(loadoutAccountPath, mode="w") as fs:
                json.dump(loadoutData, fs, indent=2)
            return True
        return False
    except Exception:
        return False


def loadDataFile(accountId, filename, defaultData, deploymentId=None, currentTime=None):
    accountDir = getProfileDir(accountId)
    accountConfigPath = accountDir / filename

    if filename == "activeLoadoutGroup.json" and not accountConfigPath.is_file():
        copyTemplateFiles(accountId, deploymentId, currentTime)

    if not accountConfigPath.is_file() and filename != "activeLoadoutGroup.json":
        if not accountDir.is_dir():
            accountDir.mkdir(parents=True, exist_ok=True)

    try:
        with open(accountConfigPath, "r") as f:
            data = json.load(f)
        return data, True
    except (FileNotFoundError, json.JSONDecodeError):
        return defaultData.copy(), False


def saveDataFile(data, accountId, filename, fileExists=True):
    configPath = getFilePath(accountId, filename)
    configPath.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(configPath, mode="w") as fs:
            json.dump(data, fs, indent=2)
        return True
    except Exception:
        return False


def loadAllConfig(accountId, deploymentId, currentTime):
    activeLoadoutGroup, _ = loadDataFile(
        accountId,
        "activeLoadoutGroup.json",
        {"loadouts": {}, "shuffleType": "DISABLED"},
        deploymentId,
        currentTime,
    )
    savedStatus, _ = loadDataFile(
        accountId, "savedStatus.json", {"favorite": [], "archived": []}
    )

    return {
        "activeLoadoutGroup": activeLoadoutGroup,
        "archived": savedStatus,
    }


def buildAthenaProfileItems(self, accountId, deploymentId, currentTime):
    if not hasattr(self, "athenaStats") or not self.athenaStats:
        pastSeasons = []
        for i in range(1, 101):
            pastSeasons.append(
                {
                    "seasonNumber": i,
                    "numWins": 10000,
                    "seasonXp": 1000000,
                    "seasonLevel": 500,
                    "bookXp": 1000000,
                    "bookLevel": 500,
                    "purchasedVIP": True,
                }
            )
        self.athenaStats = {
            "attributes": {
                "level": 67,
                "xp": 0,
                "season_num": self.seasonNum,
                "past_seasons": pastSeasons,
            }
        }
    else:
        self.athenaStats["attributes"]["seasonNum"] = self.seasonNum

    allConfig = loadAllConfig(accountId, deploymentId, currentTime)
    favorites = allConfig["archived"]["favorite"]
    archived = allConfig["archived"]["archived"]

    items = {}

    if hasattr(self, "athenaItems") and self.athenaItems:
        items.update(self.athenaItems)

    if self.seasonNum > 0:
        athenaSeasonId = f"AthenaSeason:athenaseason{self.seasonNum}"
        items[athenaSeasonId] = {
            "templateId": f"AthenaSeason:athenaseason{self.seasonNum}",
            "attributes": {
                "level": 67,
                "currency_season_total": 67,
                "purchase_date": "min",
                "purchase_context": "None",
            },
            "quantity": 1,
        }

    for itemId in items:
        itemAttrs = items[itemId].setdefault("attributes", {})
        itemAttrs["favorite"] = itemId in favorites
        itemAttrs["archived"] = itemId in archived

    items["VictoryCrown_defaultvictorycrown"] = {
        "templateId": "VictoryCrown:defaultvictorycrown",
        "attributes": {
            "victory_crown_account_data": {
                "has_victory_crown": True,
                "data_is_valid_for_mcp": True,
                "total_victory_crowns_bestowed_count": 500,
                "total_royal_royales_achieved_count": 69420
            },
            "max_level_bonus": 0,
            "archived": False,
            "level": 1,
            "item_seen": True,
            "xp": 0,
            "favorite": False
        },
        "quantity": 1
    }

    self.athena = items
    return items


@defs.isFortniteAgent
def response(self, flow: http.HTTPFlow):
    url = flow.request.pretty_url
    method = flow.request.method
    userAgent = flow.request.headers.get("User-Agent", "")

    if userAgent.startswith("Fortnite/"):
        try:
            versionString = userAgent.split("+Release-")[1].split("-")[0]
            self.seasonNum = int(versionString.split(".")[0])
        except Exception:
            self.seasonNum = 0

    def extractUrlParts(url):
        parts = url.split("/")
        try:
            if len(parts) > 8 and parts[7] == "locker":
                return parts[6], parts[8]
            if len(parts) > 6:
                return parts[6], parts[8] if len(parts) > 8 else None
        except Exception:
            return None, None
        return None, None

    deploymentId, accountId = extractUrlParts(url)

    if not accountId:
        return

    currentTime = datetime.utcnow().isoformat() + "Z"

    if (
        "/api/locker/v4/" in url
        and url.endswith("/active-loadout-group")
        and method == "PUT"
    ):
        data = json.loads(flow.request.get_text())
        loadouts = defs.cleanLoadoutItems(data.get("loadouts", {}))
        config, exists = loadDataFile(
            accountId,
            "activeLoadoutGroup.json",
            {"loadouts": {}, "shuffleType": "DISABLED"},
            deploymentId,
            currentTime,
        )

        newConfig = {
            "deploymentId": deploymentId,
            "accountId": accountId,
            "athenaItemId": "Xyro",
            "creationTime": config.get("creationTime", currentTime),
            "updatedTime": currentTime,
            "loadouts": loadouts,
            "shuffleType": data.get("shuffleType", "DISABLED"),
        }

        saveDataFile(newConfig, accountId, "activeLoadoutGroup.json", exists)

        flow.response = http.Response.make(
            200, json.dumps(newConfig), {"Content-Type": "application/json"}
        )
        return

    if "/api/locker/v4/" in url and url.endswith("/items") and method == "GET":
        cfg = loadAllConfig(accountId, deploymentId, currentTime)
        
        responseData = {
            "activeLoadoutGroup": cfg["activeLoadoutGroup"],
            "loadoutGroupPresets": [],
        }

        flow.response = http.Response.make(
            200, json.dumps(responseData), {"Content-Type": "application/json"}
        )
        return

    if "/QueryProfile?profileId=athena" in url and method == "POST":
        try:
            data = json.loads(flow.response.get_text())
            profile = data["profileChanges"][0]["profile"]
            profile["items"] = buildAthenaProfileItems(
                self, accountId, deploymentId, currentTime
            )
            profile["stats"] = self.athenaStats
            flow.response.set_text(json.dumps(data))
        except Exception:
            pass
        return

    if "/ClientQuestLogin?profileId=athena" in url and method == "POST":
        try:
            data = json.loads(flow.response.get_text())
            self.profileRevision += 1
            items = buildAthenaProfileItems(self, accountId, deploymentId, currentTime)

            profile = {
                "created": currentTime,
                "updated": currentTime,
                "rvn": self.profileRevision,
                "wipeNumber": 1,
                "accountId": accountId,
                "profileId": "athena",
                "version": "no_version",
                "items": items,
                "commandRevision": self.profileRevision,
                "profileCommandRevision": self.profileRevision,
                "profileChangesBaseRevision": self.profileRevision,
                "stats": self.athenaStats,
            }

            data["profileChanges"] = [
                {"changeType": "fullProfileUpdate", "profile": profile}
            ]
            data["profileRevision"] = self.profileRevision

            flow.response.set_text(json.dumps(data))
        except Exception:
            pass
        return

    if "/QueryProfile?profileId=common_core" in url and method == "POST":
        try:
            data = json.loads(flow.response.get_text())
            profile = data["profileChanges"][0]["profile"]

            profile["items"] = {
                "Currency:MtxPurchased": {
                    "templateId": "Currency:MtxPurchased",
                    "attributes": {"platform": "EpicPC"},
                    "quantity": 1000000,
                }
            }

            if hasattr(self, "commonCoreItems"):
                profile["items"].update(self.commonCoreItems)

            flow.response.set_text(json.dumps(data))
        except Exception:
            pass
        return