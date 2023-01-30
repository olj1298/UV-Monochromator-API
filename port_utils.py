import time
import pyvisa as visa
import datetime
import os
import sys
import codecs
import codecs
import pandas as pd
import serial
import serial.tools.list_ports
import numpy as np
# import clr # Import the .NET class library

def update_port_databse(path="port_database.csv"):
    """Assigns port name to serial number of the usb device connected to the computer.
    Inputs:
        :path(string):filename for port list csv
    Returns:
        ::updated port list
        ::error message if device is not found"""
    port_dict_SN={'Port_Alias': ['MCPort','FWPort','ShutPort','PicoPort','Turbo'], 
    'Port_SN':['A6040X2D','A6040W3Z','A65892C1','A65893GG','A67166PW'],
    'Port_Name':['/dev/ttyUSB0', '/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3','/dev/ttyUSB4']
    }
    port_database=pd.DataFrame(port_dict_SN)
    for idx,portsn in enumerate(port_database['Port_SN']):
        found=0
        for comport in serial.tools.list_ports.comports():
            if comport.serial_number==portsn: 
                print(comport.device)
                port_database['Port_Name'][idx]=comport.device
                found=1
                break
        if found ==0: 
            print("Device not found. Leaving the local port to default value.")
    path=path
    port_database.to_csv(path)
    return port_database

def get_port_database(path="port_database.csv"):
    """Prints current ports for each serial connection.
    Inputs:
        :path(string): filename for port database"""
    port_database=pd.read_csv(path,index_col=[0])
    return port_database

def setports():
    """Retrieves port csv file and assigns port alias to each usb to serial connection for the varius devices.
    Returns:
        ::Table of port names, alias, and asl or serial address"""
    try:
        port_database=get_port_database()
        MCPort = port_database[port_database['Port_Alias']=='MCPort']['Port_Name'].values[0] #port for scan controller
        shutterport= port_database[port_database['Port_Alias']=='ShutPort']['Port_Name'].values[0] #port for shutter
        PicoPort=port_database[port_database['Port_Alias']=='PicoPort']['Port_Name'].values[0]#port for picoamerter
        picoasrl='ASRL'+PicoPort+'::INSTR' #asrl port for the picoammeter
        FWPort=port_database[port_database['Port_Alias']=='FWPort']['Port_Name'].values[0] #port for filter wheel
        return port_database
    except Exception as ex:
        msg =f"Error, could not set port database. Error: {ex}"
        print(msg)
        return