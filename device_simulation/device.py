import uuid
from abc import ABC, abstractmethod
from numbers import Number
import logging
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message, MethodResponse
import json
import os

class Device(ABC):

    def __init__(self, device_id:str=str(uuid.uuid4()), id_scope=None, model_id=None, sas_key=None, conn_str=None, 
    reading_epoch:int=30, device_name:str=None, location:str='Leeds', site_point_id:int=1):
        self.device_id=device_id
        self.device_name = device_name
        self.model_id=model_id
        self.location=location
        self.site_point_id=site_point_id
        self.reading_epoch = reading_epoch
        self.logger = logging.getLogger(f"Device_{self.device_id}")
        self.is_started=True
        self.measure_task = None
        self.report_task = None
        self.id_scope = id_scope
        self.conn_str = conn_str
        self.sas_key = sas_key
     
    def __str__(self):
        return f"device_name : {self.device_name} \n location : {self.location} \n site_point_id {self.site_point_id} \n reading_epoch : {self.reading_epoch} \n device_id {self.device_id}"


    @abstractmethod
    async def _generate_measures(self) -> Number:
        return NotImplementedError

    @abstractmethod
    async def start(self):
        return NotImplementedError

    @abstractmethod
    async def stop(self):
        return NotImplementedError

    async def send_iothub(self):
        pass

    async def execute_command_listener(self, method_name, user_command_handler, create_user_response_handler):
        while True:
            if method_name:
                command_name = method_name
            else:
                command_name = None

            command_request = await self.device_client.receive_method_request(command_name)
            print("Command request received with payload")
            print(command_request.payload)

            values = {}
            if not command_request.payload:
                print("Payload was empty.")
            else:
                values = command_request.payload

            await user_command_handler(values)

            response_status = 200
            response_payload = create_user_response_handler(values)

            command_response = MethodResponse.create_from_method_request(
                command_request, response_status, response_payload
            )

            try:
                await self.device_client.send_method_response(command_response)
            except Exception:
                print("responding to the {command} command failed".format(command=method_name))


    async def execute_property_listener(device_client):
        ignore_keys = ["__t", "$version"]
        while True:
            patch = await device_client.receive_twin_desired_properties_patch()  # blocking call

            print("the data in the desired properties patch was: {}".format(patch))

            version = patch["$version"]
            prop_dict = {}

            for prop_name, prop_value in patch.items():
                if prop_name in ignore_keys:
                    continue
                else:
                    prop_dict[prop_name] = {
                        "ac": 200,
                        "ad": "Successfully executed patch",
                        "av": version,
                        "value": prop_value,
                    }

            await device_client.patch_twin_reported_properties(prop_dict)


    async def connect_to_device(self, conn_str=None, id_scope=None, registration_id=None, symmetric_key=None, model_id=None, provisioning_host='global.azure-devices-provisioning.net'):

        async def provision_device(provisioning_host, id_scope, registration_id, symmetric_key, model_id):
            provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
                provisioning_host=provisioning_host,
                registration_id=registration_id,
                id_scope=id_scope,
                symmetric_key=symmetric_key,
            )


            provisioning_device_client.provisioning_payload = {"modelId": model_id}
            return await provisioning_device_client.register()


        switch = "connectionString"

        if switch == "DPS":
            provisioning_host = (
                os.getenv("IOTHUB_DEVICE_DPS_ENDPOINT")
                if os.getenv("IOTHUB_DEVICE_DPS_ENDPOINT")
                else "global.azure-devices-provisioning.net"
            )
            id_scope = id_scope
            registration_id = registration_id
            symmetric_key = symmetric_key

            registration_result = await provision_device(
                provisioning_host, id_scope, registration_id, symmetric_key, model_id
            )

            if registration_result.status == "assigned":
                print("Device was assigned")
                print(registration_result.registration_state.assigned_hub)
                print(registration_result.registration_state.device_id)
                device_client = IoTHubDeviceClient.create_from_symmetric_key(
                    symmetric_key=symmetric_key,
                    hostname=registration_result.registration_state.assigned_hub,
                    device_id=registration_result.registration_state.device_id,
                    product_info=model_id,
                )
                return device_client
            else:
                raise RuntimeError(
                    "Could not provision device. Aborting Plug and Play device connection."
                )

        elif switch == "connectionString":
            print("Connecting using Connection String " + self.conn_str)
            device_client = IoTHubDeviceClient.create_from_connection_string(
                self.conn_str
            )

            return device_client

        else:
            raise RuntimeError(
                "At least one choice needs to be made for complete functioning of this sample."
            )
    async def send_telemetry_message(self, telemetry_msg):
        msg = Message(json.dumps(telemetry_msg))
        msg.content_encoding = "utf-8"
        msg.content_type = "application/json"
        print("Sent message")
        await self.device_client.send_message(msg)


