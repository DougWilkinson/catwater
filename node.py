from sensorclass import Sensor
from machine import Pin
import time
from hx import HX711

# catwater with weight sensor for food
# using new sensorclass with MQTT built in
# Updated 9/12/2019
# Started 7/9/2019

# water delay for auto-shutoff and control
wdelay = Sensor("wdelay", initval=90)

water = Sensor("water", "OUT", 12)

# motion sensor
motion = Sensor("motion", "IN", 14, onname="motion detected", offname="standby")
lastmotion = time.time()

# feedstatus is either ok or empty
feedstatus = Sensor("feedstatus", "VS", initval="ok" )
hxmin = Sensor("hxmin", initval=-1300)
hxmax = Sensor("hxmax", initval=-700)
hxk = Sensor("constant", initval=1155)
hx = HX711(5,4)
rawhx = Sensor("rawhx", initval=0, diff=5)

# Stores actual feed level value as a percentage
feedlevel = Sensor("feedlevel", initval=0, diff=2)

# read hx711 callback
def hxread(x):
    lastsumhx = sum(rawhx.values)
    newhx = int(hx.raw_read())
    if abs(newhx - rawhx.value) < rawhx.diff:
        newhx = rawhx.value
    rawhx.values.pop()
    rawhx.values.insert(0,newhx)
    if lastsumhx != sum(rawhx.values):
        rawhx.setvalue(int(sum(rawhx.values)/len(rawhx.values)))
        newstatus = "ok"
        level = 0.53 * (rawhx.value + hxk.value)  
        if level < -9 or level > 109:
            newstatus = "error"
        if level < 0:
            level = 0
        if level > 100:
            level = 100
        feedlevel.setvalue(int(level))
        if newstatus != feedstatus.value:
            feedstatus.setvalue(newstatus)

# Sensor to poll for readings only
checklevel = Sensor("checklevel", poll=1000, callback=hxread)
checklevel.pubneeded = False

print(feedlevel.value)
time.sleep(2)
print(feedlevel.value)

statusled = Sensor("led", "OUT", 2)
statusled.setstate(True)


def main():
    Sensor.MQTTSetup("catwater")
    while True:
        Sensor.Spin()
        if (wdelay.triggered or motion.pin.value()) and wdelay.value > 0:
            if not water.state:
                #print("water on")
                water.setstate(True)
            lastmotion = time.time()
            wdelay.triggered = False
            motion.triggered = False
        if water.state and (time.time() - lastmotion > wdelay.value):
            #print("water off")
            water.setstate(False)
            
