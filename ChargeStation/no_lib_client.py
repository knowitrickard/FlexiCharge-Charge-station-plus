import asyncio
from asyncio.events import get_event_loop
import threading
import websockets
from datetime import datetime
import time
import json
import asyncio
from threading import Thread

class ChargePoint():
    my_websocket = None
    my_id = ""

    reserve_now_timer = 0

    #Define enums for status and error_code (or use the onses in OCPP library)
    status = "Available"
    error_code = "NoError"

    hardcoded_connector_id = 1
    hardcoded_vendor_id = "Flexicharge"

    transaction_id = 123

    #Wont't be used in the final product. It is here until back-end is done with thier implementation (then we know what to send instead)
    id_tag = 123456

    charger_id = 00000

    timestamp_at_last_heartbeat : float = time.perf_counter()
    time_between_heartbeats = 60 * 60 * 24 #In seconds (heartbeat should be sent once every 24h)

    def __init__(self, id, connection):
        self.my_websocket = connection
        self.my_id = id

    async def get_message(self):
        print("Check messages")
        try:
            msg = await asyncio.wait_for(self.my_websocket.recv(), 1)
            #async for msg in self.my_websocket: #Takes latest message
            print("Check for message")
            message = json.loads(msg)
            print(message)

            if message[2] == "ReserveNow":
                await asyncio.gather(self.reserve_now(message))
            elif message[2] == "BootNotification":
                self.charger_id = message[3]["chargerId"] #This is the id number we get from the server (100001)
                print(self.charger_id)
            elif message[2] == "RemoteStart":
                await asyncio.gather(self.remote_start_transaction(message[1]))
        except:
            pass


    async def remote_start_transaction(self, unique_message_id):
        msg = [3, 
            unique_message_id, 
            "RemoteStartTransaction", 
            {"status": "Accepted"}
        ]
        response = json.dumps(msg)
        await self.my_websocket.send(response)

    #Will count down every second
    def timer_countdown_reservation(self):
        if self.reserve_now_timer <= 0:
            print("Reservation is up!")
            return
        self.reserve_now_timer = self.reserve_now_timer - 1
        print(self.reserve_now_timer)
        threading.Timer(1, self.timer_countdown_reservation).start()


    async def reserve_now(self, message):
        timestamp = message[3]["expiryDate"]   #Given in ms since epoch
        reserved_for_ms = int(timestamp - (int(time.time()*1000)))
        self.reserve_now_timer = int(reserved_for_ms/100)   #This should be changed to seconds. Time received is too short to test

        threading.Timer(1, self.timer_countdown_reservation).start()

        msg = [3, 
            message[1], #Have to use the unique message id received from server
            "ReserveNow", 
            {"status": "Accepted"}
        ]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

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
        await asyncio.sleep(1)

    async def send_data_transfer_req(self):
        msg = [1]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        #response = await self.my_websocket.recv()
        #print(json.loads(response))
        #await asyncio.sleep(1)

    #Gets no response, is this an error in back-end? Seems to be the case (Update: No response seems to be expected)
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
        #No response expected
        #response = await self.my_websocket.recv()
        #print(json.loads(response))

    #Depricated in backend
    async def send_heartbeat(self):
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "Heartbeat", {}]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        #print(await self.my_websocket.recv())
        #await asyncio.sleep(1)
        self.timestamp_at_last_heartbeat = time.perf_counter()

    async def check_if_time_for_heartbeat(self):
        seconds_since_last_heartbeat = time.perf_counter() - (self.timestamp_at_last_heartbeat)
        if seconds_since_last_heartbeat >= self.time_between_heartbeats:
            return True
        else:
            return False

    #Depricated in back-end
    async def send_meter_values(self):
        current_time = datetime.now()
        timestamp = current_time.timestamp() #Can be removed if back-end does want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ") #Can be removed if back-end does not want the time-stamp formated

        #Should be replace with "real" sampled values (this is just for testing)
        sample_value = "12345"
        sample_context = "Sample.Clock"
        sample_format = "Raw"
        sample_measurand = "Energy.Active.Export.Register"
        sample_phase = "L1"
        sample_location = "Cable"
        sample_unit = "kWh"

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "MeterValues",{
                "connectorId" : self.hardcoded_connector_id,
                "transactionId" : self.transaction_id,
                "meterValue" : [{
                    "timestamp": formated_timestamp,
                    "sampledValue":[
                        {"value" : sample_value,
                        "context" : sample_context,
                        "format" : sample_format,
                        "measurand": sample_measurand,
                        "phase": sample_phase,
                        "location" : sample_location,
                        "unit": sample_unit},
                        ]
                    },],
        }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        response = await self.my_websocket.recv()
        print(json.loads(response))
        await asyncio.sleep(1)

    #This is a test function to initiate communication from server side
    async def send_data_transfer_req(self):
        msg = ["chargerplus", "ReserveNow"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    #Will need changes when back-end is done!
    async def stop_transaction(self):
        meter_stop = 123
        reason = "Remote"

        current_time = datetime.now()
        timestamp = current_time.timestamp() #Can be removed if back-end does want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ") #Can be removed if back-end does not want the time-stamp formated
        
        #Back-end won't use samapled values, instead (I beleave) that they only want the charged level
        sample_value = "12345"
        sample_context = "Sample.Clock"
        sample_format = "Raw"
        sample_measurand = "Energy.Active.Export.Register"
        sample_phase = "L1"
        sample_location = "Cable"
        sample_unit = "kWh"

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction",{
                "idTag" : self.id_tag,
                "meterStop" : meter_stop,
                "timestamp" : formated_timestamp,
                "transactionId" : self.transaction_id,
                "reason" : reason,
                "transactionData" : [{
                    "timestamp": formated_timestamp,
                    "sampledValue":[
                        {"value" : sample_value,
                        "context" : sample_context,
                        "format" : sample_format,
                        "measurand": sample_measurand,
                        "phase": sample_phase,
                        "location" : sample_location,
                        "unit": sample_unit},
                        ]
                    },],
        }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        response = await self.my_websocket.recv()
        response_parsed = json.loads(response)
        stop_status = response_parsed[3]['status']
        print("Stap status: " + stop_status)
        await asyncio.sleep(1)

async def user_input_task(cp):
    while 1:
        msg = await asyncio.gather(cp.get_message())    #Check if there is any incoming message pending

        #Maybe not the best solution to generate a periodic heartbeat but using Threads togheter with websocket results in big problems. Time is not enough to solve that now.
        if await cp.check_if_time_for_heartbeat():
            await asyncio.gather(cp.send_heartbeat())
            print("Heartbeat")

        a = int(input(">> "))

        if a == 1:
            print("Testing boot notification")
            await asyncio.gather(cp.send_boot_notification())
        elif a == 2:
            print("Testing status notification")
            await asyncio.gather(cp.send_status_notification())
        elif a == 3:
            print("Testing status notification")
            await asyncio.gather(cp.send_heartbeat())
        elif a == 4:
            print("Testing status notification")
            await asyncio.gather(cp.send_meter_values())
        elif a == 5:
            print("Testing reserve now")
            await asyncio.gather(cp.send_data_transfer_req())
        elif a == 9:
            await asyncio.sleep(0.1)

async def main():
    async with websockets.connect(
        'ws://54.220.194.65:1337/chargerplus',
         subprotocols=['ocpp1.6']
    ) as ws:
        chargePoint = ChargePoint("chargerplus", ws)

        await chargePoint.send_boot_notification()
        #await chargePoint.send_heartbeat()
        
        await user_input_task(chargePoint)

if __name__ == '__main__':
    asyncio.run(main())