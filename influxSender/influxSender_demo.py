#!/usr/bin/env python3

# system
import datetime
import random
import sys
import time
# internal
import influxSender

# Configuration options.
Config = {
  'Influx': {
    # Host/Database options.
    #'Host': '192.168.2.40',
    'Host': 'localhost',
    'Port': 8086,
    'Database': 'demo',
    # Record options.
    'TimeStamp': 'host',
    # Debug.
    'Debug': True,
  },
}

def main(argv):
  global Config
  global db

  print("InfluxDB demo")
  print("-------------")

  # Influx database connection
  if Config['Influx']['Host']:
    print("Initializing InfluxDB Sender")
    # Create instance.
    db = influxSender.InfluxSender(debugflag=Config['Influx']['Debug'])
    db.open(host=Config['Influx']['Host'], port=Config['Influx']['Port'], database=Config['Influx']['Database'])
  else:
    db = None

  # Send some stuff
  print("Sending data to database")
  for n in range(10):
    # Create a dict of key:values to send.
    # (this allows us to record several measurement values at once)
    valueDict = {'loopNum': n, 'setpoint': 50+n, 'temperature': random.random()}
    print(valueDict)
    # Send the data to the database.
    # If passing time=None, the timestamp is automatically recorded as "now".
    db.sendDict(measurement='thermalchamber', tags=None, recorddict=valueDict, time=None)
    # Wait a moment to simulate passage of real time between measurements
    time.sleep(1)

  # Close database sender instance
  db.close()

if __name__ == "__main__":
  main(sys.argv)
