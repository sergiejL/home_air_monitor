#!/usr/bin/python3.4
# coding: utf-8

import serial
import datetime
import time
from configparser import ConfigParser
import urllib3
import requests
import json

parser = ConfigParser(allow_no_value=False)
parser.read('/boot/configuration.data')
sensor_model = (parser.get('airmonitor', 'sensor_model'))
lat = (parser.get('airmonitor', 'lat'))
long = (parser.get('airmonitor', 'long'))
urllib3.disable_warnings()

port = serial.Serial('/dev/ttyAMA0', baudrate=9600, timeout=2.0)


def read_pm_line(_port):
    rv = b''
    while True:
        ch1 = _port.read()
        if ch1 == b'\x42':
            ch2 = _port.read()
            if ch2 == b'\x4d':
                rv += ch1 + ch2
                rv += _port.read(28)
                return rv


count = 0
rcv_list = []
pm10_values = []
pm25_values = []
pm100_values = []
FACTOR = 1.5

while count < 9:
    try:
        rcv = read_pm_line(port)
        res = {'timestamp': datetime.datetime.now(),
               'apm10': rcv[4] * 256 + rcv[5],
               'apm25': rcv[6] * 256 + rcv[7],
               'apm100': rcv[8] * 256 + rcv[9],
               'pm10': rcv[10] * 256 + rcv[11],
               'pm25': rcv[12] * 256 + rcv[13],
               'pm100': rcv[14] * 256 + rcv[15],
               'gt03um': rcv[16] * 256 + rcv[17],
               'gt05um': rcv[18] * 256 + rcv[19],
               'gt10um': rcv[20] * 256 + rcv[21],
               'gt25um': rcv[22] * 256 + rcv[23],
               'gt50um': rcv[24] * 256 + rcv[25],
               'gt100um': rcv[26] * 256 + rcv[27]
               }
        print('===============\n'
              'PM1.0(CF=1): {}\n'
              'PM2.5(CF=1): {}\n'
              'PM10 (CF=1): {}\n'
              'PM1.0 (STD): {}\n'
              'PM2.5 (STD): {}\n'
              'PM10  (STD): {}\n'
              '>0.3um     : {}\n'
              '>0.5um     : {}\n'
              '>1.0um     : {}\n'
              '>2.5um     : {}\n'
              '>5.0um     : {}\n'
              '>10um      : {}'.format(res['apm10'], res['apm25'], res['apm100'],
                                       res['pm10'], res['pm25'], res['pm100'],
                                       res['gt03um'], res['gt05um'], res['gt10um'],
                                       res['gt25um'], res['gt50um'], res['gt100um']))

        pm10_values.append(res['pm10'])
        pm25_values.append(res['pm25'])
        pm100_values.append(res['pm100'])

        rcv_list.append(res.copy())

        print(''.format(len(rcv_list)))
        count += 1
        time.sleep(1)
    except KeyboardInterrupt:
        break


print("List of PM1 values from sensor", pm10_values)
pm10_values_avg = (sum(pm10_values) / len(pm10_values))
print("PM1 Average", pm10_values_avg)

for i in pm10_values:
    if pm10_values_avg > i * FACTOR:
        pm10_values.remove(max(pm10_values))
        pm10_values_avg = (sum(pm10_values) / len(pm10_values))
        print("Something is not quite right, some PM1 value is by 50% than average from last 9 measurements\n")
    elif pm10_values_avg < i * FACTOR:
        print("OK")
print(pm10_values)

print("List of PM2,5 values from sensor", pm25_values)
pm25_values_avg = (sum(pm25_values) / len(pm25_values))
print("PM2,5 Average", pm25_values_avg)

for i in pm25_values:
    if pm25_values_avg > i * 1.5:
        pm25_values.remove(max(pm25_values))
        pm25_values_avg = (sum(pm25_values) / len(pm25_values))
        print("Something is not quite right, some PM2,5 value is by 50% than average from last 9 measurements\n")
    elif pm25_values_avg < i * FACTOR:
        print("OK")
print(pm25_values)

print("List of PM10 values from sensor", pm100_values)
pm100_values_avg = (sum(pm100_values) / len(pm100_values))
print("PM10 Average", pm100_values_avg)

for i in pm100_values:
    if pm100_values_avg > i * FACTOR:
        pm100_values.remove(max(pm100_values))
        pm100_values_avg = (sum(pm100_values) / len(pm100_values))
        print("Something is not quite right, some value PM10 value is by 50% than average from last 9 measurements\n")
    elif pm100_values_avg < i * FACTOR:
        print("OK")
print(pm100_values)


data = '{"lat": "' + str(lat) + '", ' \
        '"long": "'+ str(long) + '", ' \
        '"pm1":' + str(float('%.2f' % pm10_values_avg)) + ', ' \
        '"pm25": ' + str(float('%.2f' % pm25_values_avg)) + ', ' \
        '"pm10":' + str(float('%.2f' % pm100_values_avg)) + ', ' \
        '"sensor": "' + str(sensor_model) + '"}'

url = 'http://api.airmonitor.pl:5000/api'
resp = requests.post(url,
                     timeout=10,
                     data=json.dumps(data),
                     headers={"Content-Type": "application/json"})

