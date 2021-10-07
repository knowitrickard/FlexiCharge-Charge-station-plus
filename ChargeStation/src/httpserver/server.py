import asyncio
import websockets
from aiohttp import web
from functools import partial
from datetime import datetime
from src.centralsystem.centralsystem import CentralSystem

from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, RegistrationStatus
from ocpp.v16 import call_result, call

async def hello(request):
    return web.Response(text="hello world")

async def start_charge(request):
    """ HTTP handler for remotely starting a chargring session. """
    data = await request.json()
    csms = request.app["csms"]

    try:
        await csms.start_transaction(data["id"], data["tag"])
    except ValueError as e:
        print(f"Failed to start transaction: {e}")
        return web.Response(status=404)

    return web.Response()

async def disconnect_charger(request):
    """ HTTP handler for disconnecting a charger. """
    data = await request.json()
    csms = request.app["csms"]

    try:
        csms.disconnect_charger(data["id"])
    except ValueError as e:
        print(f"Failed to disconnect charger: {e}")
        return web.Response(status=404)

    return web.Response()

async def create_http_server(csms: CentralSystem):
    app = web.Application()
    #Also possible to use decorators instead
    app.add_routes([web.get("/", hello)])
    app.add_routes([web.post("/disconnect", disconnect_charger)])
    app.add_routes([web.post("/startcharge", start_charge)])

    # Put CSMS in app so it can be accessed from request handlers.
    # https://docs.aiohttp.org/en/stable/faq.html#where-do-i-put-my-database-connection-so-handlers-can-access-it
    app["csms"] = csms

    # https://docs.aiohttp.org/en/stable/web_advanced.html#application-runners
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "localhost", 8080)
    return site
