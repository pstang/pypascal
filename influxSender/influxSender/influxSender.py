#!/usr/bin/env python3

"""
InfluxDB Sender helper library.
Copyright (c) 2021 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

This module is an InfluxDB client implementation targeted towards sending
structured data.

The module can also be run as a console tool, but only as a test.

TODO(pstang): Refine API to be more object-oriented.

Example Usage:

  import influxSender

  # Create sender.
  db = InfluxSender(loglevel=logging.DEBUG)
  # Open database client.
  db.open(host='localhost', port=8086, database='demo')
  # Sent data.
  kvdict = {'myvalue1': 123, 'myvalue2': 456}
  db.sendDict(measurement='SenderTest', tags=None, recorddict=kvdict, time=None)
  # Done.
  db.close()
"""

# system
import datetime
import logging
import sys
# package
from influxdb import InfluxDBClient

class InfluxSender:
  def __init__(self, loglevel=logging.ERROR):
    """Create and initialize InfluxSender object."""
    # Initialize state.
    self.database = ''
    logging.basicConfig(format = '%(levelname)s:%(name)s:%(message)s', level=loglevel)
    self._log = logging.getLogger(__name__)

  def open(self, host, port, database):
    """Open access to the database."""
    self._log.info("Open Host={:s}:{:d} db=\'{:s}\'".format(host, port, database))
    # Create instance.
    #client = InfluxDBClient(host='mydomain.com', port=8086, username='myuser', password='mypass' ssl=True, verify_ssl=True)
    self.dbclient = InfluxDBClient(host=host, port=port, database=database)
    self.database = database

  def close(self):
    """Close access to the database."""
    self._log.info("Close db=\'{:s}\'".format(self.database))
    self.dbclient.close()
    self.database = ''
    return

  def sendPoints(self, measurement, tags, linestring, time=None):
    """Send a set of data points to database (data in linestring 'key1=value1,key2=value2' format)."""
    # Formulate influxDB line protocol.
    tagstring = InfluxSender.dict2lineformat(tags, string_use_quotes=False)
    timestamp_ns = InfluxSender.timestamp_ns(time)
    if tagstring is None:
      dbstring = "{:s} {:s} {:d}".format(measurement, linestring, timestamp_ns)
    else:
      dbstring = "{:s},{:s} {:s} {:d}".format(measurement, tagstring, linestring, timestamp_ns)
    self._log.debug("Sending: " + dbstring)
    # Send it to the database.
    return self.dbclient.write_points(dbstring, database=self.database, protocol=u'line')

  def sendDict(self, measurement, tags, recorddict, time=None):
    """Send a set of data points to database (data in dict key:value format)."""
    return self.sendPoints(measurement=measurement, tags=tags, linestring=InfluxSender.dict2lineformat(recorddict), time=time)

  def timestamp(t=None):
    """Generate an influxdb timestamp from datetime object (if None, timestamp is generated for now)."""
    if t == None:
      t = datetime.datetime.utcnow()
    return (t - datetime.datetime.utcfromtimestamp(0)).total_seconds()

  def timestamp_ns(t=None):
    """Generate an influxdb nanoseconds timestamp from datetime object (if None, timestamp is generated for now)."""
    return int(InfluxSender.timestamp(t)*1e9)

  def dict2lineformat(d, string_use_quotes=True):
    report = ""
    if d is None:
      return None
    for key in sorted(d):
      if isinstance(d[key], float):
        report = report + "{:s}={:0.7f},".format(key, d[key])
      elif isinstance(d[key], int):
        report = report + "{:s}={:d},".format(key, d[key])
      elif isinstance(d[key], str):
        if string_use_quotes:
          report = report + "{:s}=\"{:s}\",".format(key, d[key])
        else:
          report = report + "{:s}={:s},".format(key, d[key])
      elif d[key] is not None:
        report = report + "{:s}={:},".format(key, d[key])
      else:
        # d[key] is None so leave it out of dataset.
        pass
    # Trim trailing comma.
    report = report[0:-1]
    return report

def main(argv):
  # test operation
  db = InfluxSender(loglevel=logging.DEBUG)
  db.open(host='localhost', port=8086, database='demo')
  kvdict = {'myvalue1': 123, 'myvalue2': 456}
  db.sendDict(measurement='SenderTest', tags=None, recorddict=kvdict, time=None)
  db.close()

if __name__ == "__main__":
  main(sys.argv)
