import time

programFile = "./thermostatProgram.txt"
dateTime = time.ctime()
dateTimeSplit = dateTime.split()

#Determine time and day of week
day = dateTimeSplit[0]
time = dateTimeSplit[3]

if day == "Sat,Sun":
    dayType = 'end'
else:
    dayType = 'week'

#Load thermostat program into nested dict
with open(programFile) as f:
    program = list(f)
    for line in 1:len(program):

        here extract 'outer keys' aka week & end
        then extract 'inner keys' aka dateTimeSplit
        then load temps and rooms into those keys

    outerKeys = (line.split(',')[0] for line in f)

use dict to access day/time to get thresh and room