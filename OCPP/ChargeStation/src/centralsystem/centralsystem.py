import asyncio
import websockets
from aiohttp import web
from functools import partial
from datetime import datetime
from src.centralsystem.chargepoint import ChargePoint

from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, RegistrationStatus
from ocpp.v16 import call_result, call
from aioconsole import ainput


class CentralSystem:

    def __init__(self):
        self._chargers = {}

    def register_charger(self, cp: ChargePoint) -> asyncio.Queue:
        """ Register a new ChargePoint at the CSMS. The function returns a
        queue.  The CSMS will put a message on the queue if the CSMS wants to
        close the connection. 
        """
        queue = asyncio.Queue(maxsize=1)

        # Store a reference to the task so we can cancel it later if needed.
        task = asyncio.create_task(self.start_charger(cp, queue))

        self.charger = task

        self._chargers[cp] = task

        return queue

    #This function runs when a connection is established.
    async def start_charger(self, cp, queue):
        """ Start listening for message of charger. """
        try:
            await cp.start()    #Seems to remain in this function until disconnect.
        except Exception as e:
            print(f"Charger {cp.id} disconnected: {repr(e)}")
        finally:
            # Make sure to remove reference to charger after it disconnected.
            del self._chargers[cp]
            
            # This will unblock the `on_connect()` handler and the connection
            # will be destroyed.
            await queue.put(True)
 
    async def start_transaction(self, id:str, tag:str):
        cp, _  = self._get_cp(id)
        print("Start")
        await cp.remote_start_transaction(tag)

    def disconnect_charger(self, id: str):
        _, task = self._get_cp(id)
        task.cancel()

    def _get_cp(self, id):
        for cp, task in self._chargers.items():
            if cp.id == id:
                return cp, task

        raise ValueError(f"Charger {id} not connected.")



async def on_connect(websocket, path, csms):
    """ For every new charge point that connects, create a ChargePoint instance
    and start listening for messages.

    The ChargePoint is registered at the CSMS.

    """
    charge_point_id = path.strip("/")
    cp = ChargePoint(charge_point_id, websocket)

    print(f"Charger {cp.id} connected.")

    # If this handler returns the connection will be destroyed. Therefore we need some
    # synchronization mechanism that blocks until CSMS wants to close the connection.
    # An `asyncio.Queue` is used for that.
    queue = csms.register_charger(cp)
    await queue.get()



async def create_websocket_server(csms: CentralSystem):
    handler = partial(on_connect, csms=csms)
    return await websockets.serve(handler, "0.0.0.0", 9000, subprotocols=["ocpp1.6"])
