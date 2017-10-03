#!/usr/local/bin/python

#reads thermostatProgram.txt to output a threshold temperature and
#room to read temp from, based on current day/time

def determineThreshRoom():
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
    programDict = {}
    with open(programFile) as f:
        program = list(f)
        for line in program:
            lineArray = line.split()
            if line[0] == '#':
                continue
            if lineArray[0] in programDict:
                programDict[lineArray[0]][lineArray[1]] = [lineArray[2]]
                programDict[lineArray[0]][lineArray[1]].append(lineArray[3])
            else:
                programDict[lineArray[0]] = {}
                programDict[lineArray[0]][lineArray[1]] = [lineArray[2]]
                programDict[lineArray[0]][lineArray[1]].append(lineArray[3])


    #use dict to access day/time to get thresh and room
    dayTimes = programDict[dayType].keys()

    #list all time keys less than the current time, sort then select biggest
    #to find most recent time
    list = [x for x in dayTimes if x < time]
    list.sort()
    timeType = list[-1]

    #access the threshold temp and room to read from
    thresh = programDict[dayType][timeType][0]
    readRoom = programDict[dayType][timeType][1]

    #return threshhold temp and room to read from
    return thresh, readRoom

