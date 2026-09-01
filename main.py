import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings('ignore', category=CryptographyDeprecationWarning)

import os
import sys
import time
import signal
import json
import asyncio
import logging
import ssl
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock, Thread
from datetime import datetime

import psutil
import winreg
import colorama
import subprocess
from cryptography import x509
from cryptography.hazmat.primitives import hashes

try:
    import webview as pywebview
except ImportError as e:
    print(f"pywebview import failed: {e}")
    print("Attempting to install pywebview...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pywebview"], check=True)
        import webview as pywebview
        print("pywebview installed successfully!")
    except Exception as install_error:
        print(f"Failed to install pywebview: {install_error}")
        print("Please manually install: pip install pywebview")
        sys.exit(1)

try:
    from mitmproxy import http
    from mitmproxy.tools.dump import DumpMaster
    from mitmproxy.tools.web.master import WebMaster
    from mitmproxy import options
    from mitmproxy.certs import CertStore
except ImportError:
    print("mitmproxy not installed. Please install it first.")
    sys.exit(1)

os.system('')
colorama.init()

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
hwnd = kernel32.GetConsoleWindow()
if hwnd:
    user32.ShowWindow(hwnd, 5)
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    char_width = 8
    char_height = 16
    window_width = 80 * char_width
    window_height = 25 * char_height
    center_x = (screen_width - window_width) // 2
    center_y = (screen_height - window_height) // 2
    user32.SetWindowPos(hwnd, 0, center_x, center_y, window_width, window_height, 1)
    
    current_style = user32.GetWindowLongW(hwnd, -16)
    new_style = current_style & -262145
    new_style = new_style & -65537
    new_style = new_style & -131073
    user32.SetWindowLongW(hwnd, -16, new_style)
    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 295)

shutdown_event = None
_mitmproxy_task = None
_mitm_master = None
athena_items: Dict[str, Any] = {}
common_core_items: Dict[str, Any] = {}
_shutdown_executed = False
main_loop = None
_shutdown_started = False
_gui_window = None
_fortnite_detected = False

if getattr(sys, 'frozen', False):
    INTERNAL_ASSETS_DIR = Path(sys._MEIPASS)
else:
    INTERNAL_ASSETS_DIR = Path(__file__).parent

try:
    import config
except ImportError:
    class Config:
        QUIET_STARTUP_LOGS = False
        debug = False
    config = Config()

debug = getattr(config, 'debug', False) or '-debug' in sys.argv

try:
    from handlers import cache_manager
    from handlers import cosmetics
    from handlers import filters
    from handlers import fortnite_api
    from handlers.cosmetics import fetch_athena_cosmetics_fast, update_cosmetics_cache
    from handlers.cache_manager import cosmetic_cache
    from handlers.local_emotes import get_local_emotes as get_local_emotes_data, create_emote_template_simple
except ImportError:
    print("Warning: Some handlers could not be imported")

try:
    from modifications import mcp
    from modifications import storefront
    from modifications import cloudstorage_universal
    from modifications import contentpages
    from modifications import lightswitch
    from modifications import cloudstorage, friends, habanero, account, versioncheck
except ImportError:
    print("Warning: Some modifications could not be imported")

def center_text(text: str, width: int = 80) -> str:
    """Center text within specified width."""
    if '\n' in text:
        lines = text.split('\n')
        centered_lines = []
        for line in lines:
            if line.strip():
                centered_lines.append(line.center(width))
            else:
                centered_lines.append(line)
        return '\n'.join(centered_lines)
    else:
        return text.center(width)

def print_centered(text: str, color: str = ''):
    """Print centered text with optional color."""
    if '\n' in text:
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                centered_line = line.center(80)
                if color:
                    print(color + centered_line + '\033[0m')
                else:
                    print(centered_line)
            else:
                print()
    else:
        if text.strip():
            centered_line = text.center(80)
            if color:
                print(color + centered_line + '\033[0m')
            else:
                print(centered_line)
        else:
            print()

def print_ascii_art_centered(text: str, color: str = ''):
    """Print ASCII art centered with optional color."""
    lines = text.strip().split('\n')
    centered_lines = []
    for line in lines:
        if line.strip():
            centered_line = line.center(80)
            centered_lines.append(centered_line)
        else:
            centered_lines.append('')
    centered_text = '\n'.join(centered_lines)
    if color:
        print(color + centered_text + '\033[0m')
    else:
        print(centered_text)

def set_proxy_settings(proxy_server: str, enable_proxy: int):
    """Set Windows proxy settings."""
    reg_path = 'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, 'ProxyServer', 0, winreg.REG_SZ, proxy_server)
            winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, enable_proxy)
        
        # Notify system of proxy change
        user32.SendMessageTimeoutW(65535, 26, 0, 'Environment', 0, 5000, None)
        wininet = ctypes.windll.wininet
        wininet.InternetSetOptionW(0, 39, None, 0)
        wininet.InternetSetOptionW(0, 37, None, 0)
    except Exception as e:
        print_centered(f'Error setting proxy: {e}', '\033[91m')

def kill_process_by_name(name: str):
    """Kill processes by name."""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == name.lower():
                try:
                    proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    except Exception:
        pass

def kill_processes_on_port(port: int):
    """Kill processes using a specific port."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            if proc.info['connections']:
                for conn in proc.info['connections']:
                    if conn.laddr and conn.laddr.port == port:
                        try:
                            proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            pass
    except Exception:
        pass

def on_exit():
    """Cleanup on exit."""
    set_proxy_settings('', 0)
    processes_to_kill = [
        'FortniteClient-Win64-Shipping_EAC_EOS.exe',
        'FortniteClient-Win64-Shipping.exe',
        'FortniteLauncher.exe'
    ]
    for process_name in processes_to_kill:
        kill_process_by_name(process_name)

def _run_quiet(cmd: list):
    """Run command quietly without output."""
    try:
        subprocess.run(cmd, check=False, capture_output=True, text=True)
    except Exception:
        pass

def force_stop_everything_windows():
    """Force stop all related processes and clear proxy settings."""
    global _shutdown_executed
    if _shutdown_executed:
        return
    
    _shutdown_executed = True
    print_centered('Stopping all processes...', '\033[95m')
    
    # Kill processes
    _run_quiet(['taskkill', '/f', '/im', 'python.exe', '/fi', 'WINDOWTITLE eq *proxy*'])
    _run_quiet(['taskkill', '/f', '/im', 'mitmproxy.exe'])
    _run_quiet(['taskkill', '/f', '/im', 'mitmdump.exe'])
    _run_quiet(['taskkill', '/f', '/im', 'FortniteClient-Win64-Shipping.exe'])
    _run_quiet(['taskkill', '/f', '/im', 'EpicGamesLauncher.exe'])
    _run_quiet(['taskkill', '/f', '/im', 'EasyAntiCheat.exe'])
    _run_quiet(['taskkill', '/f', '/im', 'EasyAntiCheat_EOS.exe'])
    _run_quiet(['taskkill', '/f', '/im', 'BEService.exe'])
    _run_quiet(['taskkill', '/f', '/im', 'BEClient_x64.exe'])
    _run_quiet(['wmic', 'process', 'where', "name='FortniteClient-Win64-Shipping.exe'", 'delete'])
    _run_quiet(['wmic', 'process', 'where', "name='EpicGamesLauncher.exe'", 'delete'])
    _run_quiet(['wmic', 'process', 'where', "name='EasyAntiCheat.exe'", 'delete'])
    _run_quiet(['wmic', 'process', 'where', "name='EasyAntiCheat_EOS.exe'", 'delete'])
    
    # Clear proxy settings
    for reg_path in [
        'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings',
        'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Connections',
        'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\LAN Proxy'
    ]:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                for value_name in ['ProxyServer', 'ProxyEnable', 'ProxyOverride', 'AutoConfigURL', 'ProxySettings']:
                    try:
                        winreg.DeleteValue(key, value_name)
                    except FileNotFoundError:
                        pass
        except (OSError, FileNotFoundError):
            continue
    
    # Reset proxy enable
    try:
        reg_path = 'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
    except (OSError, FileNotFoundError):
        pass
    
    # Reset connection settings
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Connections', 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, 'DefaultConnectionSettings', 0, winreg.REG_BINARY, b'\x00')
    except (OSError, FileNotFoundError):
        pass
    
    _run_quiet(['ipconfig', '/flushdns'])
    print_centered('Done.', '\033[95m')

def _sigint_handler(_signum, _frame):
    """Handle SIGINT signal."""
    global _shutdown_started
    if _shutdown_started:
        return
    
    _shutdown_started = True
    try:
        shutdown_event.set()
    except Exception:
        pass
    
    try:
        if main_loop is not None:
            def _cancel_tasks_and_shutdown_master():
                try:
                    if _mitmproxy_task is not None:
                        _mitmproxy_task.cancel()
                except Exception:
                    pass
                master = _mitm_master
                if master is not None:
                    shutdown_fn = getattr(master, 'shutdown', None)
                    if callable(shutdown_fn):
                        shutdown_fn()
            
            main_loop.call_soon_threadsafe(_cancel_tasks_and_shutdown_master)
    except Exception:
        pass
    
    if os.name == 'nt':
        force_stop_everything_windows()

class Proxy:
    """MITM Proxy addon for Fortnite."""
    
    def __init__(self, athena_items: Dict[str, Any], common_core_items: Dict[str, Any]):
        self.athena_items = athena_items
        self.common_core_items = common_core_items
        self.last_fortnite_request_time = 0
        self.fortnite_detected_count = 0
    
    async def request(self, flow: http.HTTPFlow) -> None:
        """Handle incoming requests."""
        url = flow.request.pretty_url
        method = flow.request.method
        
        if any(domain in url for domain in ['epicgames.com', 'fortnite.com', 'eonfn.dev']) and method in ['GET', 'POST', 'PUT', 'PATCH']:
            self.last_fortnite_request_time = time.time()
            self.fortnite_detected_count += 1
    
    def response(self, flow: http.HTTPFlow):
        """Handle responses."""
        url = flow.request.pretty_url
        
        # Call various handlers
        try:
            if 'account' in globals():
                account.response(self, flow)
            if 'cloudstorage' in globals():
                cloudstorage.response(self, flow)
            if 'contentpages' in globals():
                contentpages.response(self, flow)
            if 'friends' in globals():
                friends.response(self, flow)
            if 'habanero' in globals():
                habanero.response(self, flow)
            if 'mcp' in globals():
                mcp.response(self, flow)
            if 'storefront' in globals():
                storefront.response(self, flow)
            if 'versioncheck' in globals():
                versioncheck.response(self, flow)
        except Exception:
            pass
    
    def websocket_message(self, flow: http.HTTPFlow):
        """Handle websocket messages."""
        return

def is_certificate_installed() -> bool:
    """Check if mitmproxy certificate is installed."""
    try:
        ca_cert = CertStore.from_store(path=os.path.expanduser('~/.mitmproxy/'), basename='mitmproxy', key_size=2048).default_ca
        if not ca_cert:
            return False
        
        mitm_fingerprint = ca_cert.fingerprint()
        for cert_der, _, _ in ssl.enum_certificates('ROOT'):
            cert_obj = x509.load_der_x509_certificate(cert_der)
            if cert_obj.fingerprint(hashes.SHA256()) == mitm_fingerprint:
                return True
        return False
    except Exception:
        return False

async def install_certificate():
    """Install mitmproxy certificate."""
    cert_path = os.path.expanduser('~/.mitmproxy/mitmproxy-ca-cert.cer')
    max_attempts = 5
    attempts = 0
    
    if not is_certificate_installed():
        while attempts < max_attempts:
            try:
                subprocess.run(['certutil.exe', '-user', '-addstore', 'Root', cert_path], check=True, capture_output=True)
                break
            except subprocess.CalledProcessError:
                attempts += 1
                await asyncio.sleep(1)
            except FileNotFoundError:
                return
            except Exception:
                attempts += 1
                await asyncio.sleep(1)

async def is_fortnite_running() -> bool:
    """Check if Fortnite is running."""
    fortnite_processes = [
        'FortniteClient-Win64-Shipping_EAC_EOS.exe',
        'FortniteClient-Win64-Shipping_EAC.exe',
        'FortniteClient-Win64-Shipping.exe',
        'FortniteLauncher.exe',
        'EpicGamesLauncher.exe',
        'FortniteClient-Win64-Shipping.exe',
        'FortniteClient-Win64.exe',
        'EasyAntiCheat_EOS.exe',
        'EasyAntiCheat.exe'
    ]
    try:
        for proc in psutil.process_iter(['name', 'exe']):
            proc_name = proc.info['name']
            # Check exact match first
            if proc_name in fortnite_processes:
                return True
            # Check partial match for Fortnite processes
            if 'Fortnite' in proc_name or 'EpicGames' in proc_name:
                return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

async def run_mitmproxy(proxy: Proxy):
    """Run the mitmproxy server."""
    global _mitm_master
    
    # Suppress mitmproxy logging
    logging.getLogger('mitmproxy').setLevel(logging.CRITICAL)
    logging.getLogger('mitmproxy.websocket').setLevel(logging.CRITICAL)
    logging.getLogger('websockets').setLevel(logging.CRITICAL)
    logging.getLogger('mitmproxy.proxy').setLevel(logging.CRITICAL)
    logging.getLogger('mitmproxy.server').setLevel(logging.CRITICAL)
    
    try:
        opts = options.Options(listen_host='127.0.0.1', listen_port=1942)
        if debug:
            master = WebMaster(opts, with_termlog=True)
            master.options.web_open_browser = True
        else:
            master = DumpMaster(opts, with_termlog=False, with_dumper=False)
        
        _mitm_master = master
        master.addons.add(proxy)
        await master.run()
        return master
    except asyncio.CancelledError:
        raise
    except Exception as e:
        print_centered(f'Mitmproxy error: {e}', '\033[91m')
        raise

class Api:
    """API class for communicating with the GUI."""
    
    def __init__(self):
        self.fortnite_detected = False
    
    def update_gui_status(self, status):
        """Update the status in the GUI."""
        global _gui_window, _fortnite_detected
        
        if status == 'active' and not _fortnite_detected:
            _fortnite_detected = True
            if _gui_window:
                _gui_window.evaluate_js("updateStatus('active')")
        elif status == 'waiting':
            _fortnite_detected = False
            if _gui_window:
                _gui_window.evaluate_js("updateStatus('waiting')")
    
    def minimize_window(self):
        """Minimize the window."""
        global _gui_window
        if _gui_window:
            _gui_window.minimize()
    
    def close_window(self):
        """Close the window and cleanup all processes."""
        global _gui_window, _shutdown_started
        
        if _shutdown_started:
            return
        
        _shutdown_started = True
        
        # Turn off proxy first
        set_proxy_settings('', 0)
        
        # Trigger shutdown event
        try:
            if shutdown_event:
                shutdown_event.set()
        except Exception:
            pass
        
        # Cancel mitmproxy task
        try:
            if _mitmproxy_task:
                _mitmproxy_task.cancel()
        except Exception:
            pass
        
        # Shutdown mitmproxy master
        try:
            master = _mitm_master
            if master is not None:
                shutdown_fn = getattr(master, 'shutdown', None)
                if callable(shutdown_fn):
                    shutdown_fn()
        except Exception:
            pass
        
        # Force stop everything on Windows
        if os.name == 'nt':
            force_stop_everything_windows()
        else:
            on_exit()
        
        # Destroy window
        if _gui_window:
            _gui_window.destroy()
        
        # Exit
        sys.exit(0)
    
    # Expose methods for JavaScript
    def call(self, method, *args, **kwargs):
        """Call method by name for JavaScript API."""
        if hasattr(self, method):
            return getattr(self, method)(*args, **kwargs)
        return None

async def run_proxy(api):
    """Main proxy execution loop."""
    global _mitmproxy_task, athena_items, common_core_items, main_loop, shutdown_event
    
    shutdown_event = asyncio.Event()
    main_loop = asyncio.get_running_loop()
    
    # Print startup message
    print_centered('Starting proxy...', '\033[96m')
    print_centered('Fetching cosmetics...', '\033[96m')
    
    # Fetch cosmetics
    try:
        if cosmetic_cache and cosmetic_cache.pre_fetch_all_cosmetics():
            athena, common_core = cosmetic_cache.load_cached_athena_cosmetics()
            if not getattr(config, 'QUIET_STARTUP_LOGS', False):
                pass
        else:
            if not getattr(config, 'QUIET_STARTUP_LOGS', False):
                pass
            athena, common_core = {}, {}
        
        athena_items.update(athena)
        common_core_items.update(common_core)
        
        try:
            update_cosmetics_cache()
        except Exception:
            pass
        
        try:
            athena_items, common_core_items = fetch_athena_cosmetics_fast()
        except Exception:
            athena_items, common_core_items = {}, {}
    except Exception:
        athena_items, common_core_items = {}, {}
    
    # Create proxy instance
    proxy = Proxy(athena_items=athena_items, common_core_items=common_core_items)
    
    # Clear line and wait for Fortnite
    print('\033[1A\033[2K', end='')
    print_centered('Waiting for Fortnite...', '\033[96m')
    
    fortnite_detected = False
    mitmproxy_task = None
    
    try:
        while not shutdown_event.is_set():
            is_running = await is_fortnite_running()
            
            if is_running and not fortnite_detected:
                fortnite_detected = True
                print('\033[1A\033[2K', end='')
                print_centered('Fortnite detected!', '\033[95m')
                kill_processes_on_port(1942)
                
                # Set proxy settings BEFORE starting mitmproxy
                set_proxy_settings('127.0.0.1:1942', 1)
                
                # Update GUI status
                api.update_gui_status('active')
                
                try:
                    mitmproxy_task = asyncio.create_task(run_mitmproxy(proxy))
                    _mitmproxy_task = mitmproxy_task
                except Exception as e:
                    print_centered(f'Error starting proxy: {e}', '\033[91m')
            elif not is_running and fortnite_detected:
                fortnite_detected = False
                # Disable proxy settings when Fortnite is not running
                set_proxy_settings('', 0)
                # Update GUI status
                api.update_gui_status('waiting')
                print('\033[1A\033[2K', end='')
                print_centered('Waiting for Fortnite...', '\033[96m')
            
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        pass
    finally:
        # Cleanup
        if mitmproxy_task:
            mitmproxy_task.cancel()
        
        try:
            master = _mitm_master
            if master is not None:
                shutdown_fn = getattr(master, 'shutdown', None)
                if callable(shutdown_fn):
                    shutdown_fn()
        except Exception:
            pass
        
        if os.name == 'nt':
            force_stop_everything_windows()
        else:
            on_exit()

def start_async_loop(api):
    """Start the async event loop in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Install certificate first
    async def install_cert():
        await install_certificate()
    
    loop.run_until_complete(install_cert())
    
    # Start the proxy
    loop.run_until_complete(run_proxy(api))

def show_splash_screen():
    """Show splash screen for 2.5 seconds using tkinter with PIL."""
    try:
        import tkinter as tk
        from PIL import Image, ImageTk
    except ImportError:
        return  # Skip splash screen if PIL or tkinter is not available
    
    try:
        root = tk.Tk()
        root.overrideredirect(True)  # Remove window decorations
        root.attributes('-topmost', True)  # Keep on top
        
        # Get screen dimensions for centering
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Load and display image
        splash_path = os.path.join(os.path.dirname(__file__), 'splash.jpeg')
        image = Image.open(splash_path)
        photo = ImageTk.PhotoImage(image)
        
        label = tk.Label(root, image=photo)
        label.pack()
        
        # Set window size to image size
        img_width, img_height = image.size
        x = (screen_width - img_width) // 2
        y = (screen_height - img_height) // 2
        root.geometry(f'{img_width}x{img_height}+{x}+{y}')
        
        root.update()
        
        # Show for 2.5 seconds
        root.after(2500, root.destroy)
        root.mainloop()
    except Exception as e:
        print(f"Error showing splash screen: {e}")
        return

def setup_console():
    """Setup console colors."""
    try:
        handle = kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, 15)
    except Exception:
        pass

if __name__ == '__main__':
    # Setup console
    setup_console()
    
    # Setup signal handler
    try:
        signal.signal(signal.SIGINT, _sigint_handler)
    except Exception:
        pass
    
    # Show splash screen
    try:
        show_splash_screen()
    except Exception:
        pass
    
    # Create API instance
    api = Api()
    
    # Start async loop in thread
    proxy_thread = Thread(target=start_async_loop, args=(api,), daemon=True)
    proxy_thread.start()
    
    # Create GUI window
    try:
        gui_path = os.path.join(os.path.dirname(__file__), 'gui.html')
        _gui_window = pywebview.create_window(
            'Wraith',
            gui_path,
            width=500,
            height=400,
            resizable=False,
            frameless=True,
            easy_drag=True,
            background_color='#1a1a2e',
            js_api=api
        )
        pywebview.start(debug=debug)
    except Exception as e:
        print_centered(f'GUI error: {e}', '\033[91m')
        # Fallback to console mode if GUI fails
        try:
            asyncio.run(run_proxy())
        except KeyboardInterrupt:
            _sigint_handler(None, None)
        except Exception as e:
            print_centered(f'Fatal error: {e}', '\033[91m')