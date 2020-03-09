# farm6 real code   wait for combine with nodered       + ,step motor ,ec ,water change+combine+waste+servo reuse , line sent ,
import RPi.GPIO as GPIO
import os
import time
import spidev
import smbus
#import Adafruit_DHT
import adafruit_si7021
import math
import board
import busio
import requests
from time import sleep
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

# input value all from sensoe
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
    i = pcw(int(reading))
    j = pcw(int(waterlevel))


    gass1 = movafilter(fgas(gas1))
    gass2 = movafilter(fgas(gas2))
    deltag = math.fabs(gass1 - gass2)

    tFile = open('/sys/class/thermal/thermal_zone0/temp')
    temp = float(tFile.read())
    tempC = temp / 1000


    light = bus.read_i2c_block_data(addr, 0x10)
    lightconversed = (light[1] + (256 * light[0] / 1.2))
    temp = sensor.temperature
    humid = sensor.relative_humidity
    print("------------------------------------------------------------------------------------------")
    print("This time is ", datetime.now())
    print("Luminoisity= ", "%.2f" % lightconversed, "lx")
    print("Soil Moisture= {:.2f}".format(i))
    print("water level= {:.2f}".format(j))
     # print("Humidity = {} %; Temperature = {} c".format(humidity, temperature))
    print("Temperature: %0.1f C" % temp)
    print("Humidity: %0.1f %%" % humid)
    print("EC = ",movafilter(fec(ec)))
    print(" -delta- = ", deltag, "ppm", "\nmush gas = ", gass1 , "ppm", " plantgas = ", gass2, "ppm",)
     # print(" -delta- = {:.2f} ppm","mush gas = {:.2f} ppm"," plantgas = {:.2f} ppm".format(deltag,gascon2,gascon1))
    #print("cputemp = ",measure_temp())
    print(tempC)
    #(time, water, waste, gasp, gasm, humid, temp, light, ec,cput):
    insertPythonVaribleInTable(nowtt,j,pcw(wastewater),gass2,gass1,humid,temp,lightconversed,movafilter(fec(ec)),tempC)

    time.sleep(10)