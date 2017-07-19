import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

DEBUG = True

def p2f(x):
    try:
        return float(x.rstrip('%'))
    except:
        return np.nan

def importData(file, column_names=[]):
    if DEBUG:
        print('Reading ' + file)
    df = pd.read_table(file, sep='[ \t]', header=None, names=column_names, engine='python') #, converters={'Humidity': p2f})
    #df.Temperature = df.Temperature.apply(lambda x: float(x) if str(x).replace('.', '').isdigit() else np.nan)
    df.Temperature = pd.to_numeric(df.Temperature, errors='coerce')
    df = df.dropna()
    if 'UnixTime' in column_names:
        df['DateTime'] = pd.to_datetime(df.UnixTime, unit='s')
    return df



column_names = ["Date","Time","UnixTime","NodeID","MessageIndex","Temperature","Humidity","Temperature2","Humidity2"]
radio = pd.read_table('logs/temp_hum.txt', sep='[ \t]', header=None, names=column_names[2:7], usecols=range(2,7), engine='python')
radio = radio.dropna()
#radio.Temperature = radio.Temperature.apply(lambda x: float(x) if str(x).replace('.', '').isdigit() else np.nan)
radio.Temperature = pd.to_numeric(radio.Temperature, errors='coerce')
radio['DateTime'] = pd.to_datetime(radio.UnixTime, unit='s')
bedroom = radio[radio.NodeID == 'E2']
basement = radio[radio.NodeID == 'E1']


column_names2 = ["Date","Time","UnixTime","Temperature","Humidity"]
diningroom = importData('logs/inside_temp.txt', column_names2)


outside = importData('logs/outside_temp.txt', column_names2)


varList = [bedroom, diningroom, outside, basement]
varStringsList = ['bedroom', 'diningroom', 'outside', 'basement']
fig1 = plt.figure()
for var in varList:
    plt.plot(var.DateTime, var.Temperature)
plt.legend(varStringsList)


fig2 = plt.figure()
for var in varList:
    # This doesn't work in debug mode.
    # Can generate the following warning, which may or may not be relevant
    # A value is trying to be set on a copy of a slice from a DataFrame.
    #Try using .loc[row_indexer,col_indexer] = value instead
    # See the caveats in the documentation: http://pandas.pydata.org/pandas-docs/stable/indexing.html#indexing-view-versus-copy
    # self[name] = value
    a = var.Humidity.apply(p2f)
    var.Humidity = a
    plt.plot(var.DateTime, var.Humidity)
plt.legend(varStringsList)

print True