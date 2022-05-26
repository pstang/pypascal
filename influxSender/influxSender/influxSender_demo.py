#!/usr/bin/env python3

"""
InfluxSender library demonstration.
Copyright (c) 2021 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.
"""

# system
import logging
import datetime
import random
import sys
import time
# package
import influxSender

# Configuration options.
Config = {
  'Influx': {
    # Host/Database options.
    'Host': 'localhost',
    'Port': 8086,
    'Database': 'demo',
    # Record options.
    'TimeStamp': 'host',
    # Logging options.
    'LogLevel': logging.INFO,
  },
}

def main(argv):
  global Config
  global db

  print("InfluxSender demo")
  print("-----------------")

  # Influx database connection
  if Config['Influx']['Host']:
    print("Initializing InfluxDB Sender")
    # Create instance.
    db = influxSender.InfluxSender(loglevel=Config['Influx']['LogLevel'])
    db.open(host=Config['Influx']['Host'], port=Config['Influx']['Port'], database=Config['Influx']['Database'])
  else:
    db = None

  # Send some stuff
  print("Sending data to database")
  for n in range(10):
    # Create a dict of key:value pairs to send.
    # (this allows us to record several measurement values at once)
    valueDict = {'loopNum': n, 'rampdata': 50+n, 'randomdata': random.random()}
    print(valueDict)
    # Send the data to the database.
    # If passing time=None, the timestamp is automatically recorded as "now".
    db.sendDict(measurement='influxSender', tags=None, recorddict=valueDict, time=None)
    # Wait a moment to simulate passage of real time between measurements
    time.sleep(1)

  # Close database sender instance
  db.close()

if __name__ == "__main__":
  main(sys.argv)
