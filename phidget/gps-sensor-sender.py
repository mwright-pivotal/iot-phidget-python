#!/usr/bin/env python

"""Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""
from logging import INFO

__author__ = 'Adam Stelmack'
__revised__= 'Mike Wright'
__version__ = '2.2.0'
__date__ = 'Jan 5, 2015'

#Basic imports
from ctypes import *
import sys, logging
import datetime
import time
import simplejson as json
from flask import jsonify
#Phidget specific imports
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import SpatialDataEventArgs, AttachEventArgs, DetachEventArgs, ErrorEventArgs
from Phidgets.Devices.Spatial import Spatial, SpatialEventData, TimeSpan
from Phidgets.Devices.GPS import GPS
import urllib, httplib2

gps_url = 'http://gps-synapse.south.fe.pivotal.io/api/gps'

h = httplib2.Http(".cache") # WAT?
h.add_credentials("user", "******", "http://accelerometer-synapse.south.fe.pivotal.io")
FORMAT = '%(asctime)-15s %(lineno)d %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('gps-sender')
logger.setLevel(INFO)

#Create an accelerometer object
try:
    gps = GPS()
except RuntimeError as e:
    print("Runtime Exception: %s" % e.details)
    print("Exiting....")
    exit(1)

def GPSAttached(e):
    attached = e.device
    print("GPS %i Attached!" % (attached.getSerialNum()))

def GPSDetached(e):
    detached = e.device
    print("GPS %i Detached!" % (detached.getSerialNum()))

def GPSError(e):
    try:
        source = e.device
        print("GPS %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))

def GPSPositionChanged(e):
	global prev_lat
	global prev_long
	global prev_alt
	source = e.device
	serialnum = source.getSerialNum()
	if (abs(e.latitude - prev_lat) > .001 or abs(e.longitude - prev_long) > .001 or abs(e.altitude - prev_alt) > .001):
            data = {'type' : 'gps', 'device' : str(serialnum), 'rcvts' : str(datetime.datetime.now()), 'lat' : str(e.latitude), 'long' : str(e.longitude), 'alt' : str(e.altitude)}
            obj = json.dumps(data)
            resp, content = h.request(uri=accleration_url + "/" + str(serialnum), method='POST', headers={'Content-Type': 'application/json; charset=UTF-8'}, body=obj)
            prev_lat = e.latitude
            prev_long = e.longitude
            prev_alt = e.altitude
    #print("GPS %i: Latitude: %F, Longitude: %F, Altitude: %F, Date: %s, Time: %s" % (source.getSerialNum(), e.latitude, e.longitude, e.altitude, source.getDate().toString(), source.getTime().toString()))

def GPSPositionFixStatusChanged(e):
    source = e.device
    if e.positionFixStatus:
        status = "FIXED"
    else:
        status = "NOT FIXED"
    print("GPS %i: Position Fix Status: %s" % (source.getSerialNum(), status))
#Main Program Code
try:
    gps.setOnAttachHandler(GPSAttached)
    gps.setOnDetachHandler(GPSDetached)
    gps.setOnErrorhandler(GPSError)
    gps.setOnPositionChangeHandler(GPSPositionChanged)
    gps.setOnPositionFixStatusChangeHandler(GPSPositionFixStatusChanged)
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

print("Opening phidget object....")

try:
    gps.openPhidget()
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

print("Waiting for attach....")

try:
    print("Waiting for GPS attach....")
    gps.waitForAttach(10000)
    print("GPS attached....")
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    try:
        gps.closePhidget()
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Exiting....")
        #raise SystemExit(1)
        exit(1)

while True:
    time.sleep(10)

print("Closing...")

try:
    gps.closePhidget()
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

print("Done.")
