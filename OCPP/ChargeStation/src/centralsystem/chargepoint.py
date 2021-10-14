import logging
import asyncio
import random
import json
from datetime import datetime
from ocpp.routing import on, after
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, ClearCacheStatus, RegistrationStatus, AuthorizationStatus, DataTransferStatus, ChargePointStatus
from ocpp.v16 import call_result, call

class ChargePoint(cp):
    def __init__(self, _id, connection):
        cp.__init__(self,  _id, connection)
        self.status = ChargePointStatus.available
        self.transaction_id = None

    async def remote_start_transaction(self, id_tag:str):
        """
        Tell chargepoint to start a transaction with the given id_tag.
        """
        
        print("Remote start transaction")
        payload = call.RemoteStartTransactionPayload(id_tag = id_tag )
        response = await self.call(payload)
        print(response)

    @on(Action.Authorize)
    def on_authorize(self, id_tag:str, **kwargs):
        """
        Verifies a tag and responds with a status
        """
        print("On authorize")

        tag_info =  {
           "status": AuthorizationStatus.accepted
        }
        print(f"Charger {self.id}: Authorized with {id_tag}")

        return call_result.AuthorizePayload(
            id_tag_info = tag_info
        )

    @on(Action.BootNotification)
    def on_boot_notification(self, charge_point_vendor: str, charge_point_model: str, **kwargs):
        """
        Init message beteween server and chargepoint
        """
        print("On boot notification")
        return call_result.BootNotificationPayload(
            current_time =datetime.utcnow().isoformat(),
            interval     =10,
            status       =RegistrationStatus.accepted
        )

    @on(Action.StartTransaction)
    def on_start_transaction(self, connector_id: int, id_tag: int, meter_start:int, reservation_id:int , timestamp:datetime):
        """
        If chargepoint is avaiable and the tag is correct/authorized start charging/transacting 
        """
        print("On start transaction")
        if self.status != ChargePointStatus.available:
            status = AuthorizationStatus.blocked
            
        else:
            status = AuthorizationStatus.accepted
            print("Charger {self.id}: Charging Started")

        tag_info =  {
            "status": status
        }
        self.transaction_id = random.randint(1,1000)
        
        return call_result.StartTransactionPayload(
            id_tag_info    = tag_info,
            transaction_id = self.transaction_id
        )

    #example use of after decorator
    @after(Action.StartTransaction)
    def after_start_transaction(self, connector_id: int, id_tag: int, meter_start:int, reservation_id:int , timestamp:datetime):
        """
        updates charger status and database afer a transaction has been started
        """
        print("After start transaction")
        self.status = ChargePointStatus.charging 

    @on(Action.StopTransaction)
    def on_stop_transaction(self, id_tag: int, meter_stop:int , timestamp:datetime, transaction_id:int):
        """
        validates transaction id, accepts and stops charging if valid
        """
        print("On stop transaction")
        if transaction_id != self.transaction_id:
            status = AuthorizationStatus.invalid
        else:
            status = AuthorizationStatus.accepted
            print("Charger {self.id}: Charging Stopped")
        tag_info =  {
            "status": status
        }
        self.status = ChargePointStatus.available
        return call_result.StopTransactionPayload(
            id_tag_info    = tag_info,
        )
        
    @on(Action.Heartbeat)
    def on_heartbeat(self):
        print("Heartbeat")
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().isoformat(),
        )

    #transact own logic here, only used if ocpp does not support the message
    @on(Action.DataTransfer)
    def on_data_transfer(self, vendor_id:str, message_id:str, data:str):
        print("On data transfer")
        return call_result.DataTransferPayload(
            status=DataTransferStatus.accepted
        )


