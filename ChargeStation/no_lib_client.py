import asyncio
from asyncio.events import get_event_loop
import websockets
from datetime import datetime
import json
import asyncio
import concurrent.futures
import sys
import time
import threading

class ChargePoint():
    my_websocket = None
    my_id = ""
    def __init__(self, id, connection):
        self.my_websocket = connection
        self.my_id = id
        _thread = threading.Thread(target=self.between_callback, args=("some text"))
        _thread.start()
            

    async def some_callback(args):
        await 

    def between_callback(args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.some_callback(args))
        loop.close()

    _thread = threading.Thread(target=between_callback, args=("some text"))
    _thread.start()



    async def check_for_message(self):
        while 1:
            await self.my_websocket.recv()
            asyncio.sleep(2)

    async def send_boot_notification(self):
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "BootNotification", {
            "chargePointVendor": "AVT-Company",
            "chargePointModel": "AVT-Express",
            "chargePointSerialNumber": "avt.001.13.1",
            "chargeBoxSerialNumber": "avt.001.13.1.01",
            "firmwareVersion": "0.9.87",
            "iccid": "",
            "imsi": "",
            "meterType": "AVT NQC-ACDC",
            "meterSerialNumber": "avt.001.13.1.01" }]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        #response = await self.my_websocket.recv()
        #print(json.loads(response))
        #await asyncio.sleep(1)

    async def send_data_transfer_req(self):
        msg = [1]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        #response = await self.my_websocket.recv()
        #print(json.loads(response))
        #await asyncio.sleep(1)




async def user_input_task(cp):
    while 1:
        a = int(input(">> "))
        if a == 1:
            print("Testing boot notification")
            await asyncio.gather(cp.send_boot_notification())
        elif a == 9:
            await asyncio.sleep(2)
    
async def main():
    async with websockets.connect(
        'ws://54.220.194.65:1337/chargerplus',
         subprotocols=['ocpp1.6']
    ) as ws:
        chargePoint = ChargePoint("chargerplus", ws)
        await chargePoint.send_boot_notification()
        await chargePoint.check_for_message()
        await user_input_task(chargePoint)

if __name__ == '__main__':
    asyncio.run(main())