#!/usr/bin/python
from logger import Logger
import time
import os

class DS18B20:
    def __init__(self):
        directory = '/sys/bus/w1/devices/'
        dirlist = os.listdir(directory)
        devices = [s for s in dirlist if s.startswith(hex(0x28)[2:])]
        self.device = directory + devices[0] + "/w1_slave"

    def read(self):
        tfile = open(self.device)
        text = tfile.read()
        tfile.close()
        while not text:         # TODO: include max retries
            print time.asctime() + ': couldn''t read from "' + self.device + '". Trying again. '
            time.sleep(1)
            tfile = open(self.device)
            text = tfile.read()
            tfile.close()
        secondline = text.split("\n")[1]
        temperaturedata = secondline.split("=")[1]
        return temperaturedata/1000, None


#Record the temperature from our raspberry pi
try:
    sensor = DS18B20()
except OSError:     # no such file or directory, i.e. no DS18B20 plugged in
    import Adafruit_DHT

    class DHT:
        def __init__(self, sensor=Adafruit_DHT.DHT22, pin=4):
            self.sensor = sensor
            self.pin = pin

        def read(self):
            humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
            return temperature, humidity

    sensor = DHT()


tempLog = Logger('inside_temp_log.txt')
while True:
    startTime = time.time()
    data = sensor.read()
    temperature = float(data[0])*1.8+32
    humidity = float(data[1])
    if humidity != None:
        tempLog.write('%.1f %.1f%%' % (temperature, humidity))
    else:
        tempLog.write('%.1f' % temperature)
    endTime = time.time()
    elapsedTime = endTime - startTime
    print time.asctime() + ": temp_logger_inside.py elapsed time: " + str(elapsedTime)
    time.sleep(max(1*60 - elapsedTime, 0))
