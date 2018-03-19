
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
        self.devices = [s for s in dirlist if s.startswith(hex(0x28)[2:])]
        self.device = directory + self.devices[0] + "/w1_slave"

    def read(self, units='C'):
        tfile = open(self.device)
        text = tfile.read()
        tfile.close()
        retries = 0
        while not text and retries < 10:
            print(time.asctime() + ': couldn''t read from "' + self.device + '". Trying again. ')
            time.sleep(1)
            tfile = open(self.device)
            text = tfile.read()
            tfile.close()
            retries += 1
        secondline = text.split("\n")[1]
        temperaturedata = secondline.split("=")[1]
        temp = float(temperaturedata)/1000
        if units[0].upper() == 'F':
            return temp*1.8+32
        elif units[0].upper() == 'C':
            return temp
        else:
            return None


class DHT:
    def __init__(self, sensor=Adafruit_DHT.DHT22, pin=26):
        self.sensor = sensor
        self.pin = pin

    def read(self, units='C'):
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        if units[0].upper() == 'F':
            return temperature * 1.8 + 32, humidity
        elif units[0].upper() == 'C':
            return temperature, humidity
        else:
            return None, None

