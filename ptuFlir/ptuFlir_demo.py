#!/usr/bin/env python3

"""
FLIR PTU E-series control library demonstration.
Copyright (c) 2020-2021 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.
"""

# system
import logging
import sys
import time
# package
import ptuFlir

PORT = '/dev/ttyUSB0'

def ptuBasicOperations(ptu):
  ptu.query(cmd='PP')
  ptu.query(cmd='TP')
  ptu.command(cmd='S')
  ptu.command(cmd='PP', args=[1000])
  ptu.command(cmd='TP', args=[200])
  ptu.command(cmd='A')
  ptu.command(cmd='PP', args=[-1000])
  ptu.command(cmd='TP', args=[-200])
  ptu.command(cmd='A')
  ptu.command(cmd='PP', args=[0])
  ptu.command(cmd='TP', args=[0])
  ptu.command(cmd='A')

def ptuPanTiltOperations(ptu):
  ptu.setPanTiltNative(1000,200)
  print(ptu.getPanTiltNative())
  ptu.setPanTiltNative(-1000,-200)
  print(ptu.getPanTiltNative())
  ptu.setPanTiltNative(0,0)
  print(ptu.getPanTiltNative())

def ptuBoxScan(ptu, pan_width, tilt_width):
  ptu.setPanTiltNative(pan_width,tilt_width)
  print(ptu.getPanTiltNative())
  ptu.setPanTiltNative(-pan_width,tilt_width)
  print(ptu.getPanTiltNative())
  ptu.setPanTiltNative(-pan_width,-tilt_width)
  print(ptu.getPanTiltNative())
  ptu.setPanTiltNative(pan_width,-tilt_width)
  print(ptu.getPanTiltNative())
  ptu.setPanTiltNative(pan_width,tilt_width)
  print(ptu.getPanTiltNative())

  ptu.setPanTiltNative(0,0)
  print(ptu.getPanTiltNative())
  pass

def main():
  # Create instance.
  # Set a high logging level so we can see our operations.
  ptu = ptuFlir.ptu(serialport=PORT,
                    baudrate=115200,
                    timeout=5,
                    loglevel=logging.DEBUG)
  # Open the channel to the PTU.
  ptu.open()

  # Reset axes.
  #ptu.command(cmd='RE')

  # Do some operations.
  ptuBasicOperations(ptu)
  ptuPanTiltOperations(ptu)
  ptuBoxScan(ptu, 1000, 200)

  # Close the channel.
  ptu.close()

if __name__ == '__main__':
  main()
