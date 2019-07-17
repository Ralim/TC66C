#!/usr/bin/env python3
from bluepy.btle import Scanner, DefaultDelegate, Peripheral
from time import sleep
from Crypto.Cipher import AES
import itertools


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
        IncomingDataBuffer.extend(data)


def scanAndFind():
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(1.0)

    for dev in devices:
        if (dev.connectable):
            devName = dev.getValueText(9)
            if devName == "TC66C":
                print("Found Device %s - [%s] (%s), RSSI=%d dB" %
                      (devName, dev.addr, dev.addrType, dev.rssi))
                # for (adtype, desc, value) in dev.getScanData():
                #     print("[%s]  %s = %s" % (adtype, desc, value))
                return Peripheral(dev)


def decrypt(data):
    AESKeySource = [
        0x58, 0x21, -0x6, 0x56, 0x1, -0x4e, -0x10, 0x26, -0x79, -0x1, 0x12,
        0x4, 0x62, 0x2a, 0x4f, -0x50, -0x7a, -0xc, 0x2, 0x60, -0x7f, 0x6f,
        -0x66, 0xb, -0x59, -0xf, 0x6, 0x61, -0x66, -0x48, 0x72, -0x78
    ]

    AESKey = []
    for b in AESKeySource:
        AESKey.append(b & 0xFF)  # Handle negative numbers
    AESKey = bytes(AESKey)
    cipher = AES.new(bytes(AESKey), AES.MODE_ECB)
    rawData = cipher.decrypt(bytes(data))
    return rawData


def printHex(array):
    output = 'Hex: '
    for b in array:
        output = output + '%2.2X' % b
    print(output)


def handleDataPacket(data):
    if (data[0] == 112):
        voltageReading = int.from_bytes(data[48:48 + 4:1], "little")
        voltageReading = float(voltageReading) / 10000
        print(f'V In : {voltageReading}')
    # else :
    #     print(data[0])
    #     print(data[1])
    #     print(data[2])
    #     print(data[3])


def decodeDataBuffer(IncomingDataBuffer):
    while len(IncomingDataBuffer) >= 192:
        #decode the readings
        buffer = IncomingDataBuffer[0:192]  # grab the first 192
        searchpattern = [112, 97, 99, 49]
        aeskeything = buffer[48:64]
        # printHex(aeskeything)
        decodedData = decrypt(buffer)

        # First 4 bytes of the message are always 'pac1'
        # This is hinted by a consant of 'pac1TC66' in the apk
        if (decodedData[0] == 112 and decodedData[1] == 97 and decodedData[2] == 99 and decodedData[3] == 49):
            
            handleDataPacket(decodedData)
            IncomingDataBuffer = IncomingDataBuffer[192:]
        else:
            IncomingDataBuffer = IncomingDataBuffer[1:]
    return IncomingDataBuffer


# Main
SlaveDevice = None
while SlaveDevice is None:
    SlaveDevice = scanAndFind()

if SlaveDevice is not None:
    print('Connected')
    SlaveDevice.setMTU(200)
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
    print(bytearray.fromhex(
        '706163315443363631'))  # This appears to be the message marker?

    while True:
        print('Polling')
        devWriteChar.write(AskForData,
                           True)  #Ask for data to be sent in a notification
        while (len(IncomingDataBuffer) < 192):
            SlaveDevice.waitForNotifications(0.2)

        IncomingDataBuffer = decodeDataBuffer(IncomingDataBuffer)

else:
    print('No Devices Found')