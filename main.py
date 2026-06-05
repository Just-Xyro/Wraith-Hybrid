import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings('ignore', category=CryptographyDeprecationWarning)
import asyncio
import json
import os
import psutil
import ssl
import subprocess
import sys
import win32api
import winreg
import signal
import webbrowser
from typing import Dict, Any
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from mitmproxy import certs, http, options
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.tools.web.master import WebMaster
from modifications import cloudstorage, contentpages, mcp, motd, xmpp
from utils import cosmetics

debugMode = '-debug' in sys.argv
shutdownEvent = asyncio.Event()
FORTNITE_LOCAL_CAPTURE_SPEC = ','.join(['FortniteClient-Win64-Shipping.exe', 'FortniteClient-Win64-Shipping_EAC_EOS.exe', 'FortniteLauncher.exe'])
LOCAL_IGNORE_HOSTS = ['.*iostore.*\\.epicgames\\.com:443', '.*download.*\\.epicgames\\.com:443', '.*cdn.*\\.epicgames\\.com:443']
FORTNITE_LAUNCH_ARGS = ['-HIGH', '-USEALLAVAILABLECORES', '-NOSPLASH', '-PREFERREDPROCESSOR 8', '-NOTEXTURESTREAMING', '-NORHITHREAD']

def killProcessByName(processName: str):
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if processName.lower() in proc.info['name'].lower():
                try:
                    proc.kill()
                except:
                    pass
    except:
        return None

def onExit(signalType=None):
    processNames = ['FortniteClient-Win64-Shipping_EAC_EOS.exe', 'FortniteClient-Win64-Shipping.exe', 'FortniteLauncher.exe', 'EpicGamesLauncher.exe']
    for name in processNames:
        killProcessByName(name)
    proxy_toggle(False)
    if signalType is not None:
        shutdownEvent.set()
        return True


def proxy_toggle(enable: bool = True):
    try:
        INTERNET_SETTINGS = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            0,
            winreg.KEY_ALL_ACCESS,
        )

        def set_key(name: str, value):
            try:
                _, reg_type = winreg.QueryValueEx(INTERNET_SETTINGS, name)
                winreg.SetValueEx(INTERNET_SETTINGS, name, 0, reg_type, value)
            except FileNotFoundError:
                winreg.SetValueEx(INTERNET_SETTINGS, name, 0, winreg.REG_SZ, value)

        proxy_enable = winreg.QueryValueEx(INTERNET_SETTINGS, "ProxyEnable")[0]
        if proxy_enable == 0 and enable:
            set_key("ProxyServer", "127.0.0.1:1942")
            set_key("ProxyEnable", 1)
        elif proxy_enable == 1 and not enable:
            set_key("ProxyEnable", 0)
            set_key("ProxyServer", "")
    except Exception:
        pass

class Xyro:
    def __init__(self, athenaItems, commonCoreItems):
        self.athenaItems = athenaItems
        self.commonCoreItems = commonCoreItems
        self.athena = {}
        self.athenaStats = {}
        self.profileRevision = 1
        self.seasonNum = 0

    def response(self, flow: http.HTTPFlow):
        cloudstorage.response(self, flow)
        contentpages.response(self, flow)
        mcp.response(self, flow)
        motd.response(self, flow)

        if (
            flow.request.url.startswith(
                "https://catalog-public-service-prod.ak.epicgames.com/catalog/api/shared/bulk/namespaces/items"
            )
            and flow.request.method == "POST"
        ):
            try:
                responseBody = json.loads(flow.response.get_text())

                if "fn:4fe75bbc5a674f4f9b356b5c90567da5" in responseBody:
                    if "customAttributes" in responseBody["fn:4fe75bbc5a674f4f9b356b5c90567da5"]:
                        if "AllowUriCmdArgsSanitized" in responseBody["fn:4fe75bbc5a674f4f9b356b5c90567da5"]["customAttributes"]:
                            del responseBody["fn:4fe75bbc5a674f4f9b356b5c90567da5"]["customAttributes"]["AllowUriCmdArgsSanitized"]

                    responseBody["fn:4fe75bbc5a674f4f9b356b5c90567da5"]["title"] += " - Xyro Enhanced"

                    if "customAttributes" not in responseBody["fn:4fe75bbc5a674f4f9b356b5c90567da5"]:
                        responseBody["fn:4fe75bbc5a674f4f9b356b5c90567da5"]["customAttributes"] = {}

                    responseBody["fn:4fe75bbc5a674f4f9b356b5c90567da5"]["customAttributes"]["AllowUriCmdArgs"] = {"value": "true"}

                    print("[Xyro] Enabled Fortnite Arguments.")
                    flow.response.text = json.dumps(responseBody)
            except (json.JSONDecodeError, KeyError):
                pass

        if (
            flow.request.url
            == "https://library-service.live.use1a.on.epicgames.com/library/api/public/items/namespace/fn/catalogItem/4fe75bbc5a674f4f9b356b5c90567da5/source"
        ):
            killProcessByName('EpicGamesLauncher.exe')
            proxy_toggle(False)
            os._exit(0)

    def websocket_message(self, flow: http.HTTPFlow):
        xmpp.websocket_message(self, flow)

def isCertificateInstalled() -> bool:
    try:
        caCertStore = certs.CertStore.from_store(path=os.path.expanduser('~/.mitmproxy/'), basename='mitmproxy', key_size=2048)
        mitmFingerprint = caCertStore.default_ca.fingerprint(hashes.SHA256())
        
        for certDer, _, _ in ssl.enum_certificates('ROOT'):
            certObj = x509.load_der_x509_certificate(certDer)
            if certObj.fingerprint(hashes.SHA256()) == mitmFingerprint:
                return True
    except:
        pass
    return False

async def installCertificate():
    certPath = os.path.expanduser('~/.mitmproxy/mitmproxy-ca-cert.cer')
    attempts = 0
    while not isCertificateInstalled() and attempts < 5:
        try:
            subprocess.run(['certutil.exe', '-f', '-addstore', 'Root', certPath], check=True, capture_output=True)
            if isCertificateInstalled():
                break
        except:
            attempts += 1
            await asyncio.sleep(1)

async def runMitmproxy(proxy: Xyro):
    opts = options.Options(listen_host='127.0.0.1', listen_port=1942, mode=[f'local:{FORTNITE_LOCAL_CAPTURE_SPEC}'], ignore_hosts=LOCAL_IGNORE_HOSTS)
    master = WebMaster(opts, with_termlog=True) if debugMode else DumpMaster(opts)
    if debugMode:
        master.options.web_open_browser = True
    master.addons.add(proxy)
    await master.run()

async def runProxy():
    athena, commonCore = cosmetics.fetchAthenaCosmetics()
    proxyInstance = Xyro(athena, commonCore)
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, lambda s, f: shutdownEvent.set())
    if hasattr(win32api, 'SetConsoleCtrlHandler'):
        win32api.SetConsoleCtrlHandler(onExit, True)
    killProcessByName('EpicGamesLauncher.exe')
    await installCertificate()
    print(f'[Xyro] Local proxy capture enabled via mitmproxy local mode for: {FORTNITE_LOCAL_CAPTURE_SPEC}')
    proxy_toggle(True)
    asyncio.create_task(runMitmproxy(proxyInstance))

    args = ['action=launch', 'silent=true'] + [f'arg={arg}' for arg in FORTNITE_LAUNCH_ARGS]
    launch_cmd = f"com.epicgames.launcher://apps/fn:4fe75bbc5a674f4f9b356b5c90567da5:Fortnite?{'&'.join(args)}"

    print(f'[Xyro] Launching Fortnite with performance arguments...')
    os.system(f'start "" "{launch_cmd}"')
    
    await shutdownEvent.wait()
    onExit()

if __name__ == '__main__':
    try:
        asyncio.run(runProxy())
    except KeyboardInterrupt:
        pass