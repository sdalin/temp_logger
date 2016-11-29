#!/usr/local/bin/python
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
import time
from sensors import *
from logger import Logger

try:
    sensor = DS18B20()
except IndexError:     # list index out of range, i.e. no DS18B20 plugged in
    sensor = DHT()


log = Logger('logs/thermostat.txt')
thresh = 68     # temperature setting in Farenheit

GPIO.setmode(GPIO.BCM)
pin = 21
GPIO.setup(pin, GPIO.OUT, initial=False)
while True:
    startTime = time.time()
    data = sensor.read()
    if type(data) is tuple:
        temperature = data[0]
        humidity = data[1]
    elif type(data) is float:
        temperature = data
        humidity = None
    if temperature != None:
        temperature = float(temperature)*1.8+32
        if temperature < thresh:
            GPIO.output(pin, True)
            log.write('Heat on: %.1f degrees is below %i degree threshold.' % (temperature, thresh))
        else:
            GPIO.output(pin, False)
            log.write('Heat off: %.1f degrees is above %i degree threshold.' % (temperature, thresh))
    else:
        log.write(time.asctime() + ": thermostat.py sensor read failed.")
    endTime = time.time()
    elapsedTime = endTime - startTime
    print(time.asctime() + ": thermostat.py elapsed time: " + str(elapsedTime))
    time.sleep(max(1*60 - elapsedTime, 0))

GPIO.cleanup()
