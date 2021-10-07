from src.centralsystem.centralsystem import ChargePoint
import asyncio
from src.centralsystem.centralsystem import CentralSystem, create_websocket_server
from src.httpserver.server import create_http_server
from ocpp.v16 import call, ChargePoint as cp
from ocpp.v16.enums import AuthorizationStatus, RegistrationStatus

async def main():
    csms = CentralSystem()
    websocket_server = await create_websocket_server(csms)
    http_server = await create_http_server(csms)

    asyncio.create_task(background(csms))

    await asyncio.wait([websocket_server.wait_closed(), http_server.start()])


async def background(csms):
        await asyncio.sleep(2)
        while 1:
            await asyncio.sleep(1)
            a = input(">> ")
            if a == "1":
                await asyncio.gather(csms.reserve_now("CP_1", "MyID"))

if __name__ == "__main__":
    asyncio.run(main())