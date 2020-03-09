# farm6 real code   wait for combine with nodered       + ,step motor ,ec ,water change+combine+waste+servo reuse , line sent ,
import RPi.GPIO as GPIO
import time
import spidev
import smbus
import math
from time import sleep
from datetime import datetime
from datetime import timedelta  # timer

spi = spidev.SpiDev()
spi.open(0, 0)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
ga = 18
gb = 23
gc = 24
gd = 25
ge = 12
gf = 16
gg = 20  # this number is fig with relay already
gh = 21
gj = 13
gk = 14
gl = 15

GPIO.setup(ga, GPIO.OUT)  # fan
GPIO.setup(gb, GPIO.OUT)  # LED
GPIO.setup(gc, GPIO.OUT)  # water mush
GPIO.setup(gd, GPIO.OUT)  # cpu cooler
GPIO.setup(ge, GPIO.OUT)  # solenoid  waste
GPIO.setup(gf, GPIO.OUT)  # pump A
GPIO.setup(gg, GPIO.OUT)  # pump B
GPIO.setup(gh, GPIO.OUT)  # water plant
GPIO.setup(gj, GPIO.OUT)  # water flow2
GPIO.setup(gk, GPIO.OUT)  # mixer motor
GPIO.setup(gl, GPIO.OUT)  # dc waste




while True:
    nowt = datetime.now()

    GPIO.output(ge, 1)  # 12 16 20 21 13 14 15
    #GPIO.output(gf, 1)   A
    #GPIO.output(gg, 1)   B
    #GPIO.output(gh, 1)   mush
    GPIO.output(gj, 1)
    GPIO.output(gk, 1)
    GPIO.output(gl, 1)

    if nowt.second <= 8 and nowt.minute == 0 and (nowt.hour == 7 or nowt.hour == 18):
        #print("active mush pump")
        GPIO.output(gc, 1)         # mush pump (1) is blocked
        GPIO.output(gh, 0)
    else:
    #    print("High Humidity mush")
        GPIO.output(gc, 1)
        GPIO.output(gh, 1)

    # EC
    if nowt.day % 2 == 0 and nowt.hour == 9 and nowt.minute == 1 and 0 < nowt.second <= 3:
        dayeven = nowt.day / 2
        if dayeven % 2 == 0:
            GPIO.output(gf, 0)

        if dayeven % 2 == 1:
            GPIO.output(gg, 0)

    else:
        GPIO.output(gf, 1)
        GPIO.output(gg, 1)

    # light
    if 6 <= nowt.hour <= 20 and nowt.minute >= 5:
        GPIO.output(gb, 1)
    else:
        #print("LED rest time")
        GPIO.output(gb, 0)

    # CO2 fan
    if  nowt.hour % 2 == 0: #deltag > 250 or
        GPIO.output(ga, 0)
    else:
        GPIO.output(ga, 1)

    #cpu cooler
    if nowt.minute >25:
        GPIO.output(gd, 0)
    else:
        GPIO.output(gd, 1)


    time.sleep(1)
