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

    #Define enums for status and error_code (or use the onses in OCPP library)
    status = "Available"
    error_code = "NoError"

    hardcoded_connector_id = 1
    hardcoded_vendor_id = "Flexicharge"


    def __init__(self, id, connection):
        self.my_websocket = connection
        self.my_id = id
        """
        _thread = threading.Thread(target=self.between_callback, args=("some text"))
        _thread.start()
        """ 

    """
    async def some_callback(args):
        return

    def between_callback(args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.some_callback(args))
        loop.close()

    _thread = threading.Thread(target=between_callback, args=("some text"))
    _thread.start()
    """


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
        response = await self.my_websocket.recv()
        print(json.loads(response))
        await asyncio.sleep(1)

    async def send_data_transfer_req(self):
        msg = [1]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        #response = await self.my_websocket.recv()
        #print(json.loads(response))
        #await asyncio.sleep(1)

    #Gets no response, is this an error in back-end? Seems to be the case
    async def send_status_notification(self):
        current_time = datetime.now()
        timestamp = current_time.timestamp() #Can be removed if back-end does want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ") #Can be removed if back-end does not want the time-stamp formated
        
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StatusNotification",{
            "connectorId" : self.hardcoded_connector_id,
            "errorCode" : self.error_code,
            "info" : None, #Optional according to official OCPP-documentation
            "status" : self.status,
            "timestamp" : formated_timestamp, #Optional according to official OCPP-documentation
            "vendorId" : self.hardcoded_vendor_id, #Optional according to official OCPP-documentation
            "vendorErrorCode" : None #Optional according to official OCPP-documentation
            }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        response = await self.my_websocket.recv()
        print(json.loads(response))
        await asyncio.sleep(1)

async def user_input_task(cp):
    while 1:
        a = int(input(">> "))
        if a == 1:
            print("Testing boot notification")
            await asyncio.gather(cp.send_boot_notification())
        if a == 2:
            print("Testing status notification")
            await asyncio.gather(cp.send_status_notification())
        elif a == 9:
            await asyncio.sleep(2)
    
async def main():
    async with websockets.connect(
        'ws://54.220.194.65:1337/chargerplus',
         subprotocols=['ocpp1.6']
    ) as ws:
        chargePoint = ChargePoint("chargerplus", ws)
        await chargePoint.send_boot_notification()
        #await chargePoint.check_for_message()
        await user_input_task(chargePoint)

if __name__ == '__main__':
    asyncio.run(main())