import asyncio
import time
import json
import os

from pypresence import AioPresence

config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(config_path, "r") as f:
    config = json.load(f)

rpc_config = config.get("rpc", {})
enabled = rpc_config.get("enabled", True)
client_id = rpc_config.get("client_id", "1512746861457576037")
large_image = rpc_config.get("large_image", "https://github.com/Just-Xyro/Xyro-Hybrid/blob/main/rpc.jpeg?raw=true")
large_text = rpc_config.get("large_text", "Xyro Hybrid")

class DiscordRPC:
    
    def __init__(self):
        self.rpc: AioPresence | None = None
        self.connected = False
        self.start_time = time.time()
        self._current_state: str | None = None

    async def connect(self):
        if not enabled or self.connected:
            return

        loop = asyncio.get_event_loop()
        self.rpc = AioPresence(client_id, loop=loop)
        try:
            await self.rpc.connect()
            self.connected = True

            await self.rpc.update(
                large_image=large_image,
                large_text=large_text,
                start=self.start_time
            )
        except Exception:
            self.connected = False

    async def update(self, state: str = None, details: str = None, displayName: str = None):
        if not self.connected or self.rpc is None:
            return

        update_kwargs = {
            "large_image": large_image,
            "large_text": large_text,
            "start": self.start_time
        }
        
        if displayName:
            self._current_state = f"Logged in as {displayName}"
        
        if state:
            update_kwargs["state"] = state
            
        elif self._current_state:
            update_kwargs["state"] = self._current_state
                
        try:
            await self.rpc.update(**update_kwargs)
        except Exception:
            self.connected = False

    async def close(self):
        if self.rpc is None:
            return
            
        try:
            await self.rpc.close()
        except Exception:
            pass
        finally:
            self.rpc = None
            self.connected = False
            self._current_state = None

async def create_and_start_rpc() -> DiscordRPC:
    rpc_manager = DiscordRPC()
    await rpc_manager.connect()
    return rpc_manager

async def stop_rpc_connection(rpc_manager: DiscordRPC | None):
    if rpc_manager:
        await rpc_manager.close()