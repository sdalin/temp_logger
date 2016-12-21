
import time
import os
import Adafruit_DHT

class DS18B20:
    def __init__(self):
        os.system('sudo modprobe w1-gpio && sudo modprobe w1-therm')    # refresh device listing
        directory = '/sys/bus/w1/devices/'
        dirlist = os.listdir(directory)
        if dirlist == []:
            print('You need to add "dtoverlay=w1-gpio" to /boot/config.txt and reboot if you want to use ds18b20.')
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
        return float(temperaturedata)/1000


class DHT:
    def __init__(self, sensor=Adafruit_DHT.DHT22, pin=4):
        self.sensor = sensor
        self.pin = pin

    def read(self):
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        return temperature, humidity

