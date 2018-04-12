import wifi
try:
    import picoweb
except ModuleNotFoundError:
    import upip
    upip.install('utemplate')
    upip.install('picoweb')
    import picoweb
try:
    import ujson
except ModuleNotFoundError:
    import upip
    upip.install('ujson')
    import ujson
import machine
import dht

sensor = dht.DHT22(machine.Pin(25, machine.Pin.IN, machine.Pin.PULL_UP))

station = wifi.connect()
app = picoweb.WebApp(None)


@app.route("/")
def html(req, resp):
    sensor.measure()
    t = sensor.temperature()
    h = sensor.humidity()
    jsonData = {"temperature": t, "humidity": h}
    encoded = ujson.dumps(jsonData)
    msg = (b'{0:g} {1:g}'.format(t, h))
    print(msg)
    yield from picoweb.start_response(resp, content_type="application/json")
    yield from resp.awrite(encoded)


app.run(debug=True, host=station.ifconfig()[0])



#
#
#
#
#
# html = """
# <!DOCTYPE HTML>
# <html lang="en">
#   <head>
#     <meta charset="utf-8">
#     <title>Picoweb on ESP32 PICO Core</title>
#   </head>
#   <body>
#     <p>Hello World!!!</p>
#     <p><b>Hello World in Bold!!!</b></p>
#   </body>
# </html>
# """
#
#
#
# app = picoweb.WebApp(__name__)
#
#
# @app.route("/")
# def index(req, resp):
#     yield from picoweb.start_response(resp, content_type="text/html")
#
#     htmlFile = open('index.html', 'r')
#     for line in htmlFile:
#         yield from resp.awrite(line)
#
#
# @app.route("/temp")
# def html(req, resp):
#     sensor.measure()
#     t = sensor.temperature()
#     h = sensor.humidity()
#     sensor = {"tmpr": t, "hmdty": h}
#     msg = (b'{0:3.1f} {1:3.1f}'.format(t, h))
#     print(msg)
#     yield from picoweb.start_response(resp, content_type="text/html")
#     yield from app.render_template(resp, "sensor.tpl", (sensor,))
#
#
