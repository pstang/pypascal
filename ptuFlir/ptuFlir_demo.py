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

def ptuConfigure(ptu):
  # Reset to factory defaults.
  ptu.command(cmd='DF')
  # Set baudrate.
  ptu.command(cmd='@(115200,0,T)')
  # Set back to terse feedback.
  ptu.command(cmd='FT')
  # Reset axes.
  ptu.command(cmd='RE')
  # Set speed.
  ptu.command(cmd='PS', args=[2000])
  ptu.command(cmd='TS', args=[2000])
  # Save config as default.
  ptu.command(cmd='DS')

def ptuQueryOperations(ptu):
  print(ptu.query('O'))
  print(ptu.getLimitsNative())
  print(ptu.getPositionNative())

def ptuBasicOperations(ptu):
  ptu.query(cmd='PP')
  ptu.query(cmd='TP')
  ptu.command(cmd='I')
  ptu.command(cmd='PP', args=[1000])
  ptu.command(cmd='A')
  ptu.command(cmd='PP', args=[-1000])
  ptu.command(cmd='A')
  ptu.command(cmd='PP', args=[0])
  ptu.command(cmd='A')

  ptu.command(cmd='TP', args=[1000])
  ptu.command(cmd='A')
  ptu.command(cmd='TP', args=[-1000])
  ptu.command(cmd='A')
  ptu.command(cmd='TP', args=[0])
  ptu.command(cmd='A')

def ptuPositionOperations(ptu):
  ptu.setPositionDegrees(90,10)
  print(ptu.getPositionNative())
  ptu.setPositionDegrees(-90,-89)
  print(ptu.getPositionNative())
  ptu.setPositionDegrees(0,0)
  print(ptu.getPositionNative())

def ptuBoxScan(ptu, pan_width, tilt_width):
  ptu.setPositionDegrees(pan_width,tilt_width)
  print(ptu.getPositionNative())
  ptu.setPositionDegrees(-pan_width,tilt_width)
  print(ptu.getPositionNative())
  ptu.setPositionDegrees(-pan_width,-tilt_width)
  print(ptu.getPositionNative())
  ptu.setPositionDegrees(pan_width,-tilt_width)
  print(ptu.getPositionNative())
  ptu.setPositionDegrees(pan_width,tilt_width)
  print(ptu.getPositionNative())

  ptu.setPositionDegrees(0,0)
  print(ptu.getPositionNative())
  pass

def main():
  # Create instance.
  # Set a high logging level so we can see our operations.
  # Timeout of 10seconds so we can wait for motion completion.
  ptu = ptuFlir.ptu(serialport=PORT,
                    baudrate=115200,
                    timeout=10,
                    loglevel=logging.INFO)
  # Open the channel to the PTU.
  ptu.open()

  # Configure (run only when needed).
  #ptuConfigure(ptu)

  # Do some operations.
  ptuQueryOperations(ptu)
  ptuBasicOperations(ptu)
  ptuPositionOperations(ptu)
  ptuBoxScan(ptu, 10, 10)

  # Close the channel.
  ptu.close()

if __name__ == '__main__':
  main()
