from device_simulation.device import Device
import asyncio
import numpy as np
from typing import List, Dict
from datetime import datetime
import uuid

class PumpDevice(Device):

    """
    Device that returns a random temperture from a uniform distrubition
    """

    def __init__(self, device_id:str=str(uuid.uuid4()), model_id=None, id_scope=None, sas_key=None, conn_str=None, reading_epoch:int=10, device_name:int='temperature_device' ,location:int='Leeds',site_point_id:int=1):

        self.device_readings:List[Dict[str:datetime, str:int, str:int, str:int]] = []
        self.last_value:int = None
        super().__init__(device_id=device_id, model_id=model_id, id_scope=id_scope, sas_key=sas_key, conn_str=conn_str, device_name=device_name, reading_epoch=reading_epoch, site_point_id=site_point_id, location=location)

    def _generate_measures(self):
        
        """
        schema
        {
            "watts":
            "flow"
            "temp"
        }
        """

        measures = {}

        measures['watts']= np.random.uniform(60, 100)
        # measures['volumneFlowRate'] = np.random.uniform(0, 70)
        # measures['temperture'] = np.random.uniform(0, 70)

        self.last_value = measures

        self.device_readings.append(measures)
        self.logger.debug(f'Sleeping {self.reading_epoch} for device {self.device_name}')
        self.logger.info('(f"{self.device_name} - measures : {self.last_value}")')
        print(self.last_value)

    async def start(self):
        print("here")
        device_client = await self.connect_to_device(registration_id=self.device_id, 
                                                    id_scope=self.id_scope, 
                                                    symmetric_key=self.sas_key, 
                                                    model_id=uuid.uuid4(),
                                                    conn_str=self.conn_str)

        self.device_client = device_client
        await device_client.connect()
        while self.is_started:
            try:
                measures = self._generate_measures()   
            except Exception as e:
                print(e)
                raise e
            
            await self.send_telemetry_message(measures)
            await asyncio.sleep(self.reading_epoch) 

    async def stop(self):
        self.is_started=False
        self.logger.info(f'Stopping devive {self.id}')
 
    
