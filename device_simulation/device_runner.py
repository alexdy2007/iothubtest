from typing import List
from device_simulation.device import Device
import logging
import asyncio
from signal import SIGINT, SIGTERM
import sys

class DeviceRunner():

    def __init__(self, device_list:List[Device]):
        self.device_list = device_list
        self.logger = self.create_logger()
        self.loop = None

    @staticmethod
    def create_logger():
        h1 = logging.StreamHandler()
        h1.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        h1.setFormatter(formatter)
        logger = logging.getLogger('DeviceRunner')
        return logger

    def shutdown(self):
        all_running_tasks = asyncio.all_tasks(self.loop)
        self.logger.info(f'number of active tasks {len(all_running_tasks)}')

        if len(all_running_tasks)>0:
            self.logger.info('Shutting down all tasks')
            for t in all_running_tasks:
                t.cancel()
        return True

    def shutdown_listener(self):
        """
        Listener for quitting the sample
        """
        while True:
            selection = input("Press Q to quit\n")
            if selection == "Q" or selection == "q":
                print("Quitting...")
                break

    async def run(self):

        self.loop = asyncio.get_event_loop()
        background_devices = set()
        try:
            for d in self.device_list:
                device_task = asyncio.create_task(d.start(), name=str(d.device_id)) 
                background_devices.add(device_task)

            for signal in [SIGINT, SIGTERM]:
                self.loop.add_signal_handler(signal, self.shutdown)
        
            try:
                user_finished = self.loop.run_in_executor(None, self.shutdown_listener)
                await user_finished
                self.shutdown()
            except Exception as e:
                raise e

        except Exception as e:            
            self.logger.info(f'Stopping due to error {e}')
            raise e

    async def stop_task(self, id):
        pass
