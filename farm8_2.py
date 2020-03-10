# farm9 [use "Try" with si7021]
import threading
from time import sleep
import RPi.GPIO as GPIO
import os
import time
import spidev
import smbus
import Adafruit_DHT
import adafruit_si7021
import math
import board
import busio
import requests
from datetime import datetime
from datetime import timedelta  # timer
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode

spi = spidev.SpiDev()
spi.open(0, 0)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

bus = smbus.SMBus(1)  # (512 MB or MB or 1024 MB)
addr = 0x23  # i2c address BH1750
i2c = busio.I2C(board.SCL, board.SDA)  # si7021
sensor = adafruit_si7021.SI7021(i2c)

# servo
GPIO.setup(26, GPIO.OUT)
servoPIN = 26
p = GPIO.PWM(servoPIN, 50) # GPIO 26 for PWM with 50Hz
p.start(7.5)

def analog_read(channel):  # mcp3208

    r = spi.xfer2([4 | 2 | (channel >> 2), (channel & 3) << 6, 0], 500000, 1000)

    adc_out = ((r[1] & 15) << 8) + r[2]

    return adc_out

def fgas(x):
    i = (x * 5000) / 2048
    return i

def fec(x):
    i = (20 * x) / 2785
    return i

def pcw(x):
    i = (100*x)/3000
    return i

buf = 0.0
buf1 = 0.0
buf2 = 0.0
buf3 = 0.0
buf4 = 0.0
buf5 = 0.0
buf6 = 0.0
buf7 = 0.0
buf8 = 0.0
buf9 = 0.0

def movafilter(x):
    global buf
    global buf1
    global buf2
    global buf3
    global buf4
    global buf5
    global buf6
    global buf7
    global buf8
    global buf9
    buf9 = buf8
    buf8 = buf7
    buf7 = buf6
    buf6 = buf5
    buf5 = buf4
    buf4 = buf3
    buf3 = buf2
    buf2 = buf1
    buf1 = buf
    buf = x
    xbar = (buf + buf1 + buf2 + buf3 + buf4 + buf5 + buf6 + buf7 + buf8 + buf9) / 10
    return xbar

def insertPythonVaribleInTable(time,water,waste,gasp,gasm ,humid,temp,light,ec,cput ):
    try:
        connection = mysql.connector.connect(host='localhost',
                             database='plantae',
                             user='root',
                             password='admin')
        cursor = connection.cursor(prepared=True)
        sql_insert_query = """ INSERT INTO `allplant`
                          (`time`, `water`, `waste`, `gasp` , `gasm` ,`humid`,`temp`,`light`,`ec`,`cput` ) 
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        insert_tuple = (time,water,waste,gasp,gasm ,humid,temp,light,ec,cput )
        result  = cursor.execute(sql_insert_query, insert_tuple)
        connection.commit()
        #print ("Record inserted successfully into python_users table")
    except mysql.connector.Error as error :
        connection.rollback()
        print("Failed to insert into MySQL table {}".format(error))
    finally:
        #closing database connection.
        if(connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

def func1(): # send to database
    while True:
        nowt = datetime.now()
        nowtt = ("{:d}-{:d}-{:d} {:d}:{:d}:{:d}".format(nowt.year, nowt.month, nowt.day, \
                                                        nowt.hour, nowt.minute, nowt.second))

        waterlevel = analog_read(0)
        soil1 = analog_read(1)
        soil2 = analog_read(2)
        wastewater = analog_read(4)
        gas1 = analog_read(5)
        gas2 = analog_read(6)
        ec = analog_read(7)
        reading = (soil1 + soil2) / 2  # mushroom
        i = int(reading)
        j = int(waterlevel)

        gass1 = movafilter(fgas(gas1))
        gass2 = movafilter(fgas(gas2))
        deltag = math.fabs(gass1 - gass2)

        light = bus.read_i2c_block_data(addr, 0x10)
        lightconversed = (light[1] + (256 * light[0] / 1.2))
        # use Try for prevent i2c error of si7021
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            sensor = adafruit_si7021.SI7021(i2c)
            temp = sensor.temperature
            humid = sensor.relative_humidity
        except:
            temp = 0
            humid = 0


        insertPythonVaribleInTable(nowtt, j, pcw(wastewater), gass2, gass1, humid, temp, lightconversed,
                                   movafilter(fec(ec)), tempC)

        sleep(60)

def func2(): #work
    mstt1 = 15  # mix step time(sec)   water
    mstt2 = 2  # A
    mstt3 = 9  # delay 1  900
    mstt4 = 2  # B
    mstt5 = 6  # delay 2  300
    mstt6 = 2  # keep finish water
    mstt8 = 3  # keep finish ab

    flagsimwater = 0
    flagtime = 0
    flagreserve = 0
    flagdowater = 0
    flagdoab = 0
    #watermode = 1  # 1 = ab , 0 = water
    #ec = 1.7  # test for flagreserve

    while True:
        nowt = datetime.now()

        waterlevel = analog_read(0)
        soil1 = analog_read(1)
        soil2 = analog_read(2)
        # soil3 = analog_read(3)
        wastewater = analog_read(4)
        gas1 = analog_read(5)
        gas2 = analog_read(6)
        ec = analog_read(7)
        reading = (soil1 + soil2) / 2  # mushroom
        i = float(reading)
        j = float(waterlevel)

        gass1 = movafilter(fgas(gas1))
        gass2 = movafilter(fgas(gas2))
        deltag = math.fabs(gass1 - gass2)

        #   light = bus.read_i2c_block_data(addr, 0x10)
        #  lightconversed = (light[1] + (256 * light[0] / 1.2))

        GPIO.output(ge, 1)  # 12 16 20 21 13 14 15
        GPIO.output(gf, 1)
        GPIO.output(gg, 1)
        # GPIO.output(gh, 1)
        GPIO.output(gj, 1)
        GPIO.output(gk, 1)
        GPIO.output(gl, 1)
        # if  reading < 1000:  # mushroom water
        if nowt.second <= 9 and nowt.minute == 0 and (nowt.hour == 7 or nowt.hour == 18):
            # print("active mush pump")
            GPIO.output(gc, 0)
            GPIO.output(gh, 0)
        else:
            #    print("High Humidity mush")
            GPIO.output(gc, 1)
            GPIO.output(gh, 1)

        # pump from stock input plant water + fertilizer AB
        #    if waterlevel < 1000:
        #        print("active relay 21 water plant")  # uncomplete yet   +  mixwater1sub.py
        #        GPIO.output(gh, 1)
        #    else:
        #        GPIO.output(gh, 0)

        # light
        if 6 <= nowt.hour <= 19 and nowt.minute >= 5:
            #   if lightconversed < 3000:
            #        print("active LED")
            GPIO.output(gb, 1)
        #     else:
        #        GPIO.output(gb, 0)
        else:
            # print("LED rest time")
            GPIO.output(gb, 0)

        # CO2 fan
        if nowt.hour % 2 == 0:  # deltag > 250 or
            GPIO.output(ga, 0)
        else:
            GPIO.output(ga, 1)

        # cpu cooler
        if nowt.minute > 25:
            GPIO.output(gd, 0)
        else:
            GPIO.output(gd, 1)

        # mixwatersub2---------------------------------------------------
        if nowt.minute == 50 and 0 <= nowt.second <= 1 and nowt.hour != 24 and nowt.hour != 0 and nowt.hour % 1 == 0:
                #        if waterlevel < 250:  # pump from stock input plant water + fertilizer AB
                flagtime = 1
                flagsimwater = 1
            #        else:
            #           print ("waterfull")
            # GPIO.output(W, 0)

        if flagtime == 1:
                mstep1 = datetime.now() + timedelta(seconds=mstt1)  # add water
                mstep2 = datetime.now() + timedelta(seconds=mstt2)  # A
                mstep3 = datetime.now() + timedelta(seconds=mstt2 + mstt3)  # delay1
                mstep4 = datetime.now() + timedelta(seconds=mstt2 + mstt3 + mstt4)  # B
                mstep5 = datetime.now() + timedelta(seconds=mstt2 + mstt3 + mstt4 + mstt5)  # delay 2
                mstep6 = datetime.now() + timedelta(seconds=mstt1 + mstt6)  # finish water
                mstep8 = datetime.now() + timedelta(seconds=mstt2 + mstt3 + mstt4 + mstt5 + mstt8)  # finish ab
                flagtime = 0
                # flaginmix = 1

        if flagsimwater == 1:
                # swiftservo
                p.ChangeDutyCycle(2.5)
                print("step1")
                flagdowater = 1
                # flagreserve = 1
                flagsimwater = 0

            # maybe pour water only in flaginmix and pour ab later here and check ec(flagreserve) one or two times a day
            # don't forget to check wastewater
        if flagreserve == 1:
            if watermode == 1:  # ec
                if 1.5 <= ec <= 2:
                        print("complete")
                        # swiftbackservo
                        p.ChangeDutyCycle(7.5)
                        flagreserve = 0
                elif ec > 2:  # pour water
                        flagdowter = 1
                        flagtime = 1
                elif ec < 1.5:  # pour ab
                        flagdoab = 1
                        flagtime = 1

            if watermode == 0:
                if ec < 0.5:
                        print("complete")
                        # swiftbackservo
                        p.ChangeDutyCycle(7.5)
                        flagreserve = 0
                elif ec > 0.5:  # and waterlevel <= 1000/pour water
                        flagdowter = 1
                        flagtime = 1

        if flagdowater == 1:  # in water mode, don't swift back servo since waterlevel250 until complete
                flagreserve = 0

            if nowt.second <= mstep1.second and nowt.minute <= mstep1.minute and nowt.hour <= mstep1.hour and nowt.day <= mstep1.day:
                    print("step1 water")
                    # GPIO.output(W, 1)
            if mstep1.second <= nowt.second <= mstep6.second and mstep1.minute <= nowt.minute <= mstep6.minute \
                        and mstep1.hour <= nowt.hour <= mstep6.hour and mstep1.day <= nowt.day <= mstep6.day:
                    print("finish water")
                    flagreserve = 1
                    flagdowater = 0

        if flagdoab == 1:
                flagreserve = 0
                # swiftbackservo from water250 and swift again later when waiting b
                p.ChangeDutyCycle(7.5)
            if nowt.second <= mstep2.second and nowt.minute <= mstep2.minute \
                        and nowt.hour <= mstep2.hour and nowt.day <= mstep2.day:
                    print("step2 A")
                    # GPIO.output(A, 1)
                # else:
                # all gpio in do ab except a =0

            if mstep2.second <= nowt.second <= mstep3.second and mstep2.minute <= nowt.minute <= mstep3.minute \
                        and mstep2.hour <= nowt.hour <= mstep3.hour and mstep2.day <= nowt.day <= mstep3.day:
                    print("step3 wait a")

            if mstep3.second <= nowt.second <= mstep4.second and mstep3.minute <= nowt.minute <= mstep4.minute \
                        and mstep3.hour <= nowt.hour <= mstep4.hour and mstep3.day <= nowt.day <= mstep4.day:
                    print("step4 B")
                    # GPIO.output(B, 1)
                    # swiftservo
                    p.ChangeDutyCycle(2.5)
            if mstep4.second <= nowt.second <= mstep5.second and mstep4.minute <= nowt.minute <= mstep5.minute \
                        and mstep4.hour <= nowt.hour <= mstep5.hour and mstep4.day <= nowt.day <= mstep5.day:
                    print("step5 wait b")

            if mstep5.second <= nowt.second <= mstep8.second and mstep5.minute <= nowt.minute <= mstep8.minute \
                        and mstep5.hour <= nowt.hour <= mstep8.hour and mstep5.day <= nowt.day <= mstep8.day:
                    print("finish step")
                    # all gpio = 0

                    flagreserve = 1
                    flagdoab = 0
            # GPIO.clear()
            # if nowt.minute == 41 and (nowt.second  == 10 or nowt.second == 15):
            #    print("ok")


        # fOR SERVO  12.5 /   -7.5-   \ 2.5

        sleep(1)
    
if __name__ == '__main__':

    proc1 = threading.Thread(target=func1)
    proc1.start()
    proc2 = threading.Thread(target=func2)
    proc2.start()
