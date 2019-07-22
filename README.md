# TC66C
Messing around with the TC66C from RDK from python

The TC66C is a really capable USB-C power meter that is made by RDK.
The "C" version comes with a bluetooth interface, which uses a Dialog Semi BLE chipset.

This python code is "MVP", in that it will connect to the first TC66C it can find, and print out the data.
Its not amazing, and it doesnt handle re-connection overly well, but its a good grounds for it to evolve if anyone has interest.
1000% happy if anyone has pull requests / ideas for this.

This is a work of my own interest and time, mostly spurred on by the low quality of the provided app and its very slow interface.
For how nice this hardware is, I *really* wish the manufacturer would have released this instead.


## Details

The main chipset is a small ARM micro, a GD103 I believe. However, its of low relivence here.

The BLE protocol this device uses is not documented anywhere I can find online, so all of this is based on my reverse engineering work.

It exposes one characteristic that can be written to, to control the device.

The commands that are sent are in plain ascii, with not encryption. So these can be easily captured and figured out.

By observing the messages that are sent by the app, the following strings have been found:

* "brotat\n\r"  --> Rotates the device screen
* "blastp\n\r"  --> Goes back one screen
* "bnextp\n\r"  --> Goes forward one screen
* "bgetva\n\r"  --> Asks for measurements to be sent

There are no ACK's for these messages, except that sending the latter (getva), 
which results in the device sending a series of notifications that contain the measured data.

The general operation is mostly just send the request as often as possible and wait for the data to come back

## Recieving data

Recieving data from this unit is a little harder. The data is sent in blocks of 192 bytes, which start with a known constant. 
However, all of this data is AES encrypted. Thankfully the key can be recovered by the fact that they released an Android app for this unit.

The AES is running in ECB mode, which is nice and simple :grin:
The key is noted in the python code, which was extracted from the application.
It did hold me up a bit because Java smali uses signed bytes.





## BLE Details

### Exposed services


