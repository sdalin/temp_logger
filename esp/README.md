download ch340

for loading micropython follow instructions here if necessary https://micropython.org/download#esp32

`pip install adafruit-ampy`

to load new code, connect usb

```
screen /dev/tty.wchusbserialfa130 115200
Ctrl-C
import os
os.remove('main.py’)
Ctl-A Ctl-\
```
reset esp
```
ampy --port /dev/tty.wchusbserialfa130 put dht22webpage.py
ampy --port /dev/tty.wchusbserialfa130 put main.py
```
reset esp


btw, had to do `upip.install('micropython-logging')`
and add `time.sleep` in ampy https://github.com/adafruit/ampy/issues/19

or from https://github.com/scientifichackers/ampy:
To set these variables automatically each time you run ampy, copy them into a file named .ampy:
```
# Example .ampy file
# Fix for macOS users' "Could not enter raw repl"; try 2.0 and lower from there:
AMPY_DELAY=0.5
```
