import network


def connect():
    ssid = "DataMiner"
    password = "Perovskite"

    station = network.WLAN(network.STA_IF)

    if station.isconnected():
        print("Already connected")
        return station

    station.active(True)
    station.connect(ssid, password)

    while not station.isconnected():
        pass

    print("Connection successful")
    print(station.ifconfig())
    return station
