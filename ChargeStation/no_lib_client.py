#Note! A message starting with the number 2 means we (chargpoint) are starting a communication. The number 3 means we are responding.

import asyncio
from asyncio.events import get_event_loop
from asyncio.tasks import gather
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

    meter_value_total = 0   #Send this to server at start and stop. It will calculate cost. Incremented during charging.

    #Reservation related variables
    reserve_now_timer = 0
    is_reserved = False
    reservation_id_tag = None
    reservation_id = None
    reserved_connector = None
    ReserveConnectorZeroSupported = True

    #Transaction related variables
    is_charging = False
    charging_id_tag = None
    charging_connector = None
    charging_Wh = 0 #I think this is how many Wh have been used to charge
    transaction_id = None

    #Define enums for status and error_code (or use the onses in OCPP library)
    status = "Available"
    error_code = "NoError"

    hardcoded_connector_id = 1
    hardcoded_vendor_id = "com.flexicharge"

    hardcoded_id_tag = 1

    charger_id = 00000

    timestamp_at_last_heartbeat : float = time.perf_counter()
    time_between_heartbeats = 60 * 60 * 24 #In seconds (heartbeat should be sent once every 24h)


    def __init__(self, id, connection):
        self.my_websocket = connection
        self.my_id = id

    async def get_message(self):
        try:
            msg = await asyncio.wait_for(self.my_websocket.recv(), 1)
            #async for msg in self.my_websocket: #Takes latest message
            print("Check for message")
            message = json.loads(msg)
            print(message)

            if message[2] == "ReserveNow":
                await asyncio.gather(self.reserve_now(message))
            elif message[2] == "BootNotification":
                self.status = "Available"
                await asyncio.gather(self.send_status_notification(None)) #Status notification should be sent after a boot
                #Should change state here!
            elif message[2] == "RemoteStartTransaction":
                await asyncio.gather(self.remote_start_transaction(message))
            elif message[2] == "RemoteStopTransaction":
                await asyncio.gather(self.remote_stop_transaction(message))
            elif message[2] == "DataTransfer":
                await asyncio.gather(self.recive_data_transfer(message))
            elif message[2] == "StartTransaction":
                self.transactionId = message[3]["transactionId"]    #Store transaction id from server
        except:
            pass

    #AuthorizeRemoteTxRequests is always false since no authorize function exists in backend(?)
    #TODO - Change when multiple connectors exists. Add parent id tag.
    #       No handling for connectorID = 0 since only a single connector will exist in mvp
    #       No status_notification is sent since it does not get a response and locks the program
    async def remote_start_transaction(self, message):
        if int(message[3]["idTag"]) == self.reservation_id_tag: #If the idTag has a reservation
            self.start_charging_from_reservation()
            print("Remote transaction started")

            msg = [3, 
                message[1], #Unique message id
                "RemoteStartTransaction", 
                {"status": "Accepted"}
            ]
            response = json.dumps(msg)
            await self.my_websocket.send(response)

            await self.start_transaction(is_remote=True)
            await self.send_status_notification(None)   #Notify central system that connector is now available
            print("Charge should be started")
        else:   #A non reserved tag tries to use the connector
            print("This tag does not have a reservation")
            msg = [3, 
                message[1], #Unique message id
                "RemoteStartTransaction", 
                {"status": "Rejected"}
            ]
            response = json.dumps(msg)
            await self.my_websocket.send(response)

    async def remote_stop_transaction(self, message):
        #message[3]["transactionID"]
        if self.is_charging == True:# and message[3]["transactionId"] == self.transaction_id:
            print("Remote stop charging")
            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "RemoteStopTransaction", 
                {"status": "Accepted"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
            await self.stop_transaction(is_remote=True) #Stop transaction and inform server
        else:
            print("Charging cannot be stopped")
            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "RemoteStopTransaction", 
                {"status": "Rejected"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)

    #Will count down every second
    def timer_countdown_reservation(self):
        if self.reserve_now_timer <= 0:
            print("Reservation is canceled!")
            self.hard_reset_reservation()
            self.status = "Available"
            asyncio.run(self.send_status_notification(None)) #Notify back-end that we are availiable again
            return
        self.reserve_now_timer = self.reserve_now_timer - 1
        print(self.reserve_now_timer)
        threading.Timer(1, self.timer_countdown_reservation).start()    #Countdown every second
##########################################################################################################################
    def meter_counter_charging(self):
        if self.is_charging == True:
            self.meter_value_total = self.meter_value_total + 1
            print(self.meter_value_total)
            threading.Timer(1, self.meter_counter_charging).start()
        else:
            print("{}{}".format("Total charge: ", self.meter_value_total))

    
    def hard_reset_reservation(self):
        self.is_reserved = False
        self.reserve_now_timer = 0
        self.reservation_id_tag = None
        self.reservation_id = None
        print("Hard reset reservation")

    def hard_reset_charging(self):
        self.is_charging = False
        self.charging_id_tag = None
        self.charging_connector = None
        print("Hard reset charging")
    
    def start_charging_from_reservation(self):
        self.is_charging = True
        self.charging_id_tag = self.reservation_id_tag
        self.charging_connector = self.reserved_connector
        threading.Timer(1, self.meter_counter_charging).start()

    def start_charging(self, connector_id, id_tag):
        self.is_charging = True
        self.charging_id_tag = id_tag
        self.charging_connector = connector_id
        threading.Timer(1, self.meter_counter_charging).start()

    async def reserve_now(self, message):
        if self.reservation_id == None or self.reservation_id == message[3]["reservationID"]:
            if self.ReserveConnectorZeroSupported == False and message[3]["connectorID"] == 0:
                print("Connector zero not allowed")
                msg = [3, 
                    message[1], #Have to use the unique message id received from server
                    "ReserveNow", 
                    {"status": "Rejected"}
                ]
                msg_send = json.dumps(msg)
                await self.my_websocket.send(msg_send)
                return
            self.hard_reset_reservation()
            self.is_reserved = True
            self.reservation_id_tag = message[3]["idTag"]
            self.reservation_id = message[3]["reservationID"]
            self.reserved_connector = message[3]["connectorID"]
            timestamp = message[3]["expiryDate"]   #Given in ms since epoch
            reserved_for_ms = int(timestamp - (int(time.time()*1000)))
            self.reserve_now_timer = int(10)#reserved_for_ms/1000)   #Reservation time in seconds
            threading.Timer(1, self.timer_countdown_reservation).start()    #Countdown every second

            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "ReserveNow", 
                {"status": "Accepted"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
        elif self.reserved_connector == message[3]["connectorID"]:
            print("Connector occupied")
            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "ReserveNow", 
                {"status": "Occupied"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
        else:
            print("Implement other messages for non accepted reservations")
            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "ReserveNow", 
                {"status": "Occupied"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
###################################################################################################################
    #Tells server we have started a transaction (charging)
    async def start_transaction(self, is_remote):
        current_time = datetime.now()
        timestamp = current_time.timestamp()

        if is_remote == True:
            #If remote then charging have started in remote_start_transaction. Notify server here.
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StartTransaction", {
            "connectorId" : self.charging_connector,
            "id_tag": self.charging_id_tag,
            "meterStart":self.meter_value_total,
            "timestamp" : timestamp,
            "reservationId": self.reservation_id,
             }]
        
            self.hard_reset_reservation()
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
        else:   #No reservation
            self.start_charging(self.hardcoded_connector_id, self.hardcoded_id_tag)

            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StartTransaction", {
            "connectorId" : self.charging_connector,
            "id_tag": self.charging_id_tag ,
            "meterStart":self.meter_value_total,
            "timestamp" : timestamp,
            "reservationId": None,  #If here, no reservation was made
             }]

            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)

    #TODO - Adjust to multiple connectors when added. Assumes a single connector
    async def stop_transaction(self, is_remote):
        current_time = datetime.now()
        timestamp = current_time.timestamp()
        if is_remote == True:
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
                "idTag": self.charging_id_tag,
                "meterStop": self.meter_value_total,
                "timestamp": timestamp,
                "transactionId": self.transaction_id,
                "reason": "Remote",
                "transactionData": None#[
                    #{
                    #Can place timestamp here. (Optional)
                    #},
                    #Can place meterValues here. (Optional)
                #]
                }]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
            self.hard_reset_charging()
        else:
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
                "idTag": self.charging_id_tag,
                "meterStop": self.meter_value_total,
                "timestamp": timestamp,
                "transactionId": self.transaction_id,
                "reason": "Remote",
                "transactionData": None#[
                    #{
                    #Can place timestamp here. (Optional)
                    #},
                    #Can place meterValues here. (Optional)
                #]
                }]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
            self.hard_reset_charging()

        response = await self.my_websocket.recv()
        print(json.loads(response))

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

    #Gets no response, is this an error in back-end? Seems to be the case
    async def send_status_notification(self, info):
        current_time = datetime.now()
        timestamp = current_time.timestamp() #Can be removed if back-end does want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ") #Can be removed if back-end does not want the time-stamp formated
        
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StatusNotification",{
            "connectorId" : self.hardcoded_connector_id,
            "errorCode" : self.error_code,
            "info" : info, #Optional according to official OCPP-documentation
            "status" : self.status,
            "timestamp" : timestamp, #Optional according to official OCPP-documentation
            "vendorId" : self.hardcoded_vendor_id, #Optional according to official OCPP-documentation
            "vendorErrorCode" : "None" #Optional according to official OCPP-documentation
            }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        print("Status notification sent with message: ")
        print(msg)
        self.timestamp_at_last_status_notification = time.perf_counter()

    #Depricated in back-end
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

    async def send_data_transfer(self, message_id, message_data):
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "DataTransfer",{
                "vendorId" : self.hardcoded_vendor_id,
                "messageId" : message_id,
                "data" : message_data
        }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def recive_data_transfer(self, message):
        status = "Rejected"
        if message[3]["vendorId"] == self.hardcoded_vendor_id:
            if message[3]["messageId"] == "BootData":
                parsed_data = json.loads(message[3]["data"])
                self.charger_id = parsed_data["chargerId"]
                print("Charger ID is set to: " + str(self.charger_id))
                status = "Accepted"
            else:
                status = "UnknownMessageId"
        else:
            status = "UnknownVenorId"

        #Send a conf
        conf_msg = [3, 
                    message[1],
                    "DataTransfer", 
                    {"status": status}]

        conf_send = json.dumps(conf_msg)
        print("Sending confirmation: " + conf_send)
        await self.my_websocket.send(conf_send)


    async def send_data_reserve(self):
        msg = ["chargerplus", "ReserveNow"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def send_data_remote_start(self):
        msg = ["chargerplus", "RemoteStart"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def send_data_remote_stop(self):
        msg = ["chargerplus", "RemoteStop"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

async def user_input_task(cp):
    while 1:
        msg = await asyncio.gather(cp.get_message())    #Check if there is any incoming message pending

        """
        #Maybe not the best solution to generate a periodic heartbeat but using Threads togheter with websocket results in big problems. Time is not enough to solve that now.
        #Depricated in back-end
        if await cp.check_if_time_for_heartbeat():
            await asyncio.gather(cp.send_heartbeat())
            print("Heartbeat")
        """

        a = int(input(">> "))
        if a == 1:
            print("Testing boot notification")
            await asyncio.gather(cp.send_data_transfer("ChargeLevelUpdate","{\"transactionId\":32\"latestMeterValue\":1,\"CurrentChargePercentage\":1}"))
        elif a == 2:
            print("Testing status notification")
            await asyncio.gather(cp.send_status_notification())
        elif a == 3:
            print("Testing status notification")
            await asyncio.gather(cp.send_heartbeat())
        elif a == 4:
            print("Testing status notification")
            await asyncio.gather(cp.send_status_notification(None))
        elif a == 5:
            print("Testing reserve now")
            await asyncio.gather(cp.send_data_reserve())
        elif a == 6:
            print("Testing remote start")
            await asyncio.gather(cp.send_data_remote_start())
        elif a == 7:
            print("Testing remote stop")
            await asyncio.gather(cp.send_data_remote_stop())
        elif a == 8:
            print("Testing stop transaction")
            await asyncio.gather(cp.stop_transaction(False))
        elif a == 9:
            print("Reset reservation")
            cp.hard_reset_reservation()
        elif a == 10:
            print("Testing start transaction")
            await asyncio.gather(cp.start_transaction(is_remote = False))
        elif a == 0:
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