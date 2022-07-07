#!/usr/bin/env python3

"""
Serial Key-Value reader demonstration.
Copyright (c) 2020-2022 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.
"""

# system
import logging
import sys
import time
# package
import serialkv

PORT = '/dev/ttyUSB0'

def main():
  # Create instance.
  skv = serialkv.serialkv(serialport=PORT,
                          baudrate=115200,
                          timeout=1,
                          loglevel=logging.INFO)
  # Open the channel.
  skv.open()
  # Read one .
  kvdict = skv.read()
  print(kvdict)
  # Close the channel.
  skv.close()

if __name__ == '__main__':
  main()
