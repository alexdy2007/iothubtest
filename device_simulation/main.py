from device_simulation.temperature_device import TemperatureDevice
from device_simulation.pump_device import PumpDevice
from device_simulation.device_runner import DeviceRunner
import asyncio

if __name__ == '__main__':

    device1=PumpDevice(device_id='sample-pump-1', model_id='dtmi:com:example:PumpData;1', conn_str='HostName=iothub-we-water-dev-2.azure-devices.net;DeviceId=sample-pump-1;SharedAccessKey=Bbjtndt/d4vaYUDAlhpasJiLwI1M/1wiPYz83VpFF+U=',
     reading_epoch=5,device_name='pumpexample',location='SewagePlant1',site_point_id=1)

    device_list =[device1]

    device_runner = DeviceRunner(device_list)
    try:
        asyncio.run(device_runner.run())
    except asyncio.CancelledError as e:
        print(e)
        print('Program Shutting Down')