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
import signal
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
    if signalType is not None:
        shutdownEvent.set()
        return True

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
    asyncio.create_task(runMitmproxy(proxyInstance))
    os.system('start com.epicgames.launcher://apps/Fortnite?action=launch')
    await shutdownEvent.wait()
    onExit()

if __name__ == '__main__':
    try:
        asyncio.run(runProxy())
    except KeyboardInterrupt:
        pass