from bluepy.btle import Scanner, DefaultDelegate, Peripheral
from time import sleep
from Crypto.Cipher import AES


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        name = dev.getValueText(9)
        if isNewDev:
            if name is not None:
                if name is not 'None':
                    print(f'Discovered device \t{ dev.addr} | {name}')


IncomingDataBuffer = []


class MyDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        # ... perhaps check cHandle
        # ... process 'data'
        IncomingDataBuffer.extend(data)
        print(f'Recieved {len(data)} bytes')


def scanAndFind():
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(4.0)

    for dev in devices:
        if (dev.connectable):
            devName = dev.getValueText(9)
            if devName == "TC66C":
                print("Found Device %s - [%s] (%s), RSSI=%d dB" %
                      (devName, dev.addr, dev.addrType, dev.rssi))
                for (adtype, desc, value) in dev.getScanData():
                    print("[%s]  %s = %s" % (adtype, desc, value))
                return Peripheral(dev)


def decrypt(data):
    if len(data) != 192:
        return None
    AESKey = b'X!\xf9V\x01\xb1\xef&\x86\xfe\x12\x04b*O\xaf\x85\xf3\x02`\x80o\x99\x0b\xa6\xf0\x06a\x99\xb7r\x87'
    cipher = AES.new(AESKey, AES.MODE_ECB)
    rawData = cipher.decrypt(bytes(data))
    return rawData


def decodeDataBuffer(inputBuffer):
    while len(inputBuffer) >= 192:
        #decode the readings
        buffer = inputBuffer[0:193:1]
        inputBuffer = inputBuffer[193::]
        aesIV = ""
        for i in range(48, 64):
            aesIV = aesIV + "%2.2X" % buffer[i]
        decodedData = decrypt(buffer)
        print(decodedData)

        sleep(0.5)


# Main
SlaveDevice = scanAndFind()
if SlaveDevice is not None:
    print('Connected')
    SlaveDevice.setMTU(250)
    services = SlaveDevice.getServices()
    # To enable the data streaming through from the device, is actually a polling loop /me facepalms
    # They dont actually use notifications for anything useful except as a slightly lower delay read
    devWriteService = SlaveDevice.getServiceByUUID(
        '0000ffe5-0000-1000-8000-00805f9b34fb')
    devWriteChar = devWriteService.getCharacteristics(
        '0000ffe9-0000-1000-8000-00805f9b34fb')
    devWriteChar = devWriteChar[0]
    devReadService = SlaveDevice.getServiceByUUID(
        '0000ffe0-0000-1000-8000-00805f9b34fb')
    devReadChar = devReadService.getCharacteristics(
        '0000ffe4-0000-1000-8000-00805f9b34fb')[0]
    # Hook notifications
    SlaveDevice.setDelegate(MyDelegate())

    # Setup polling loop
    rotateScreen = bytearray.fromhex('62726f7461740d0a')
    BackScreen = bytearray.fromhex('626c617374700d0a')
    ForwScreen = bytearray.fromhex('626e657874700d0a')
    AskForData = bytearray.fromhex('6267657476610d0a')
    print(BackScreen)
    print(rotateScreen)
    print(ForwScreen)
    print(AskForData)
    while True:
        print('Polling')
        devWriteChar.write(AskForData, True)  #rotate screen
        SlaveDevice.waitForNotifications(0.5)
        SlaveDevice.waitForNotifications(0.5)
        sleep(0.5)
        decodeDataBuffer(IncomingDataBuffer)
else:
    print('No Devices Found')