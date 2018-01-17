import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from functions import p2f
import time

DEBUG = True

dir = 'mountpoint/logs/'

def importData(file, column_names=[]):
    if DEBUG:
        print('Reading ' + file)
    df = pd.read_table(file, sep='[ \t]', header=None, names=column_names, engine='python', converters={'Humidity': p2f})
    #df.Temperature = df.Temperature.apply(lambda x: float(x) if str(x).replace('.', '').isdigit() else np.nan)
    df.Temperature = pd.to_numeric(df.Temperature, errors='coerce')
    df = df.dropna()
    if 'UnixTime' in column_names:
        df['DateTime'] = pd.to_datetime(df.UnixTime, unit='s')
    return df



column_names = ["Date","Time","UnixTime","NodeID","MessageIndex","Temperature","Humidity","Temperature2","Humidity2"]
radio = pd.read_table(dir + 'temp_hum.txt', sep='[ \t]', header=None, names=column_names[2:7], usecols=range(2,7), engine='python')
radio = radio.dropna()
#radio.Temperature = radio.Temperature.apply(lambda x: float(x) if str(x).replace('.', '').isdigit() else np.nan)
radio.Temperature = pd.to_numeric(radio.Temperature, errors='coerce')
radio.Humidity = radio.Humidity.apply(p2f)
radio['DateTime'] = pd.to_datetime(radio.UnixTime, unit='s')
bedroom = radio[radio.NodeID == 'E2']
basement = radio[radio.NodeID == 'E1']


column_names2 = ["Date","Time","UnixTime","Temperature","Humidity"]
diningroom = importData(dir + 'inside_temp.txt', column_names2)


outside = importData(dir + 'outside_temp.txt', column_names2)


varList = [bedroom, diningroom, outside, basement]
varStringsList = ['bedroom', 'diningroom', 'outside', 'basement']
fig1 = plt.figure()
for var in varList:
    varTemp = var
    #varTemp = var[var.UnixTime > time.time()-2*24*60*60]
    plt.plot(varTemp.DateTime, varTemp.Temperature)
plt.legend(varStringsList)
plt.ylim(0, 100)

fig2 = plt.figure()
for var in varList:
    plt.plot(var.DateTime, var.Humidity)
plt.legend(varStringsList)
plt.ylim((0, 100))

print True