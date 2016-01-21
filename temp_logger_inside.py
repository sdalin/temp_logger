#!/usr/bin/python
#Record the temperature from our raspberry pi
tfile = open("/sys/bus/w1/devices/28-03159138f4ff/w1_slave")
text = tfile.read()
tfile.close()
secondline = text.split("\n")[1]
temperaturedata = secondline.split(" ")[9]
temperature = float(temperaturedata[2:])
temperature = temperature/1000
print temperature
