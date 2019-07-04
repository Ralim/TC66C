from bluepy.btle import Scanner, DefaultDelegate, Peripheral
from time import sleep
class ScanDelegate (DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print ("Discovered device", dev.addr)
        elif isNewData:
            print ("Received new data from", dev.addr)

class MyDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        # ... perhaps check cHandle
        # ... process 'data'
        print(cHandle)
        print(data)


def scanAndFind():
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(3.0)

    for dev in devices:
        if(dev.connectable):
            devName = dev.getValueText(9)
            if devName == "TC66C":
                print ("Found Device %s - [%s] (%s), RSSI=%d dB" % (devName,dev.addr, dev.addrType, dev.rssi))
                for (adtype, desc, value) in dev.getScanData():
                    print ("[%s]  %s = %s" % (adtype,desc, value))
                return Peripheral(dev)
                

SlaveDevice = scanAndFind()

if SlaveDevice is not None:
    print('Connected')
    SlaveDevice.setMTU(250)
    services = SlaveDevice.getServices()
    # To enable the data streaming through from the device, is actually a polling loop /me facepalms
    # They dont actually use notifications for anything useful except as a slightly lower delay read
    devWriteService = SlaveDevice.getServiceByUUID('0000ffe5-0000-1000-8000-00805f9b34fb')
    devWriteChar = devWriteService.getCharacteristics('0000ffe9-0000-1000-8000-00805f9b34fb')
    devWriteChar = devWriteChar[0]
    devReadService  = SlaveDevice.getServiceByUUID('0000ffe0-0000-1000-8000-00805f9b34fb')
    # Hook notifications
    SlaveDevice.setDelegate( MyDelegate() )

    # Setup polling loop
    rotateScreen = bytearray.fromhex('62726f7461740d0a')
    BackScreen = bytearray.fromhex('626c617374700d0a')
    ForwScreen = bytearray.fromhex('626e657874700d0a')
    print(BackScreen)
    print(rotateScreen)
    print(ForwScreen)    
    while True:
        print('Polling')
        devWriteChar.write(rotateScreen)#rotate screen
       # devWriteChar.write(bytearray.fromhex('6267657476610d0a'))
        SlaveDevice.waitForNotifications(1.0)
else:
    print('No Devices Found')