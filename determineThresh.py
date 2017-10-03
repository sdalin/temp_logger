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
    for line in range(1,len(program)):
        lineData = program[line]
        if program[1].split()[0] in programDict:
            lineArray = lineData.split()
            programDict[lineArray[0]][lineArray[1]] = lineArray[2]
            programDict[lineArray[0]][lineArray[1]].append(lineArray[3])
        else:
            lineArray = lineData.split()
            programDict[lineArray[0]] = {}
            programDict[lineArray[0]][lineArray[1]] = lineArray[2]
            programDict[lineArray[0]][lineArray[1]].append(lineArray[3])


#use dict to access day/time to get thresh and room
thresh = programDict[dayType]
