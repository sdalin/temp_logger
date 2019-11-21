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
