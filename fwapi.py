import time
import pyvisa as visa
import datetime
import os
import sys
import codecs
import pandas as pd
import serial
import serial.tools.list_ports
import numpy as np
import PhotodiodeLinux as mclinux
import shutterapi as shutter
import monochromatorapi as mcapi
import port_utils as pt
import command
import serial.tools.list_ports
import time
import codecs
import serial

"""McPherson 747 Filter Wheel Controller commands using variables stored in command.py"""

def update_filter_change_map(list=[240,350,500,605,700]):
    """"Given the list of wavelenghts where the filter need to be changed. This function generates a map and stores it in csv.
    Inputs:
        :list(array): wavelength which filters cutoff
    Returns:
        ::updated filter map
        ::error message if filter wheel not connecting to computer"""
    try:
        FW_change_map= {'filternum':[1,2,3,4,5],'Change_Wavelength':list} #add integer for filter slot corresponding to wavelength
        FW_change_map_df=pd.DataFrame(FW_change_map) #use pandas to acces file
        FW_change_map_df.to_csv("Filter_change_map.csv") #convert to .csv
        print("Updated filter map!")
    except Exception as ex:
        msg =f"Error, could not update filter change map. Error: {ex}"
        print(msg)
        return 

def get_filter_change_map(filename="Filter_change_map.csv"): 
    """Outputs the filter change table into terminal from csv file. File saved in code folder
    Inputs:
        :filename(string): address for file location csv
    Returns:
        ::Table of wavelength cutoffs for filters used"""
    FW_change_map=pd.read_csv("Filter_change_map.csv")#read filter change map file
    return FW_change_map

def which_filter(current_wl):
    """Returns the filter to select for a particular wavelength. Used in loops for conditions to change filter during experiment.
    Inputs:
        :current_wl(integer): wavelength in nm
    Returns:
        ::message if wavelength is outside of upper and lower limit range of scan controller
        ::filter number used for input wavelength based on the filter wheel change map
        ::error message if issue occurs"""
    FW_change_map=get_filter_change_map()
    llim=100 #nm lower limit for our experiment. Instrument lower limit is 0.1nm
    ulim=700 #nm upper limit for our experiment. Instrument upper limit is 999.9nm
    try:
        if (current_wl<llim)|(current_wl>ulim): #wavelength is below low limit or above upper limit
            print(f"{current_wl} nm is outside the wavelength limits. Setting filter number to 1") 
            return 1 #filter 1
        for idx,filternum in enumerate(FW_change_map['filternum']): 
            if current_wl<=FW_change_map['Change_Wavelength'][idx]: #checks if wavelength is above or below filter ranges
                return int(filternum) #filter for current wavelength
    except:
        return("Some error has occured. Please check the wavelength input")

def set_fw_to_position(filternum,FWPort):
    """Increments filter wheel position for any filter.
    Inputs:
        :filternum(float): number 1-5 corresponding to filter wheel slots
        :FWPort(string): serial address for filter wheel connection
    Returns:
        ::error message and 0 if filter num is not 1-5
        ::current filter position before movement
        ::movementnt to new position is completed and new current filter"""
    filternum=int(filternum)
    try:
        if (filternum<int(1))|(filternum>int(5)): #error if filter is outside of 1-5 range
            print(f"{filternum} is greater than the limits.")
            return int(0) #error code
        curpos=get_fw_position(FWPort) #reads the filter wheel position
        time.sleep(3) #time for device to read and respond
        while int(curpos)!=filternum: #checks if current wavelength matches range or needs to move
            increment_fw_position(FWPort) #moves filter wheel
            time.sleep(3) #time for device to read and respond
            curpos=get_fw_position(FWPort) #read filter wheel position
            print(f"Currently at {curpos}")
            time.sleep(3) #time for device to read and respond
        if int(curpos)==filternum: #check if current wavelength matches filter range
            print(f"Now at position {curpos}") 
            return int(curpos)
    except Exception as ex:
        msg =f"Error, could not set filter wheel position. Error: {ex}"
        print(msg)
        return

"""Code under this line was used for testing and communication to Filter Wheel through Hex ASCII commands"""    

def connect_FW(FWPort):
    """Tests if 747 filter wheel serial parameters are correct and if port is closed or open. 
    Inputs:
        :wheelport(string): Serial port connection
    Returns:
        ::Error message if exception occured"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=FWPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per FW manual. bits/sec
                            timeout = None, #per FW manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per FW manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per FW manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per FW manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per FW manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        return ser
    except Exception as ex:
        msg = f"Error, could not establish communication, check serial connection Error: {ex}"
        print(msg)
        return msg

def enquiry(ser):
    """Writes Enquiry message and recieves acknowledgement from device.
    Inputs:
        :ser(string): Serial port connection for filter wheel
    Returns:
        ::Acknowledgement byte
        ::Error message"""
    #ser.write(ENQUIRY_ID + chr(0x20).encode() + ControlCodes.ENQ)
    ser.write(b'N!\x05')
    # ser.write(b'4E2105/r')
    ack = ser.read(size=3)
    # print(ack)
    ack_check=b'N!\x06'
    assert ack == ack_check, "ACK not received. Instead got: "+repr(ack)
    return ack

def get_fw_position(FWPort):
    """Opens serial connection, sends enquire and recieves acknowledgement. 
        Creates several header entities and sends them to the controller. Reads response, gets acknowledgement, closes connection.
    Inputs:
        :FWPort(string): Serial port address for filter wheel
    Returns:
        ::Current filter wheel position"""
    ser=connect_FW(FWPort)
    ser.open()
    ack=enquiry(ser) #send enquiry, read acknowledgement
    ser.flush() #flush unwanted data
    #Read header to read Device 1. Create Header Entities
    soh= chr(0x01) #Start of Header
    addr= chr(0x30)+chr(0x31) #Controller Address 
    oprw= chr(0x30) #Operation Read or write (R=30, W=38)
    data_type=chr(0x31) #VMemory alays 31
    msb=chr(0x30)+chr(0x34) #04
    lsb=chr(0x41)+chr(0x31) #A1
    cdb=chr(0x30)+chr(0x30) #00
    pdb=chr(0x30)+chr(0x34) #04
    hstaddr=chr(0x30)+chr(0x31) #01
    etb=chr(0x17) #end of header
    #Checksum
    ck_calc=hex(int(format(ord(addr[0]),"x"),16)^int(format(ord(addr[1]),"x"),16)^int(format(ord(oprw[0]),"x"),16)^int(format(ord(data_type[0]),"x"),16)^int(format(ord(msb[0]),"x"),16)^int(format(ord(msb[1]),"x"),16)^int(format(ord(lsb[0]),"x"),16)^int(format(ord(lsb[1]),"x"),16)^int(format(ord(cdb[0]),"x"),16)^int(format(ord(cdb[1]),"x"),16)^int(format(ord(pdb[0]),"x"),16)^int(format(ord(pdb[1]),"x"),16)^int(format(ord(hstaddr[0]),"x"),16)^int(format(ord(hstaddr[1]),"x"),16))
    cksum=str(ck_calc).replace('0x','')
    #Join all header entities into a Header
    hdr_list=[soh,addr,oprw,data_type,msb,lsb,cdb,pdb,hstaddr,etb,cksum]
    hdr=''.join(hdr_list)
    ser.write(hdr.encode()) #Send the header to the controller
    time.sleep(1)
    res = ser.readlines()[0] #Read the response from the controller
    ack=enquiry(ser) #Send Acknoledgement to the controller
    ser.write(b'\x04') #Send end to Transmission to controller
    ser.close() #Close the connection
    position=int(res[4:4+2].decode())
    print(f"Filter Wheel is at position {position}")
    return position

def increment_fw_position(FWPort):
    """Opens serial connection, sends enquire and recieves acknowledgement. Creates several header entities and sends them to the controller. 
        Reads response, gets acknowledgement, closes connection.
    Inputs:
        :FWPort(string): Serial port address for filter wheel
    Returns:
        ::Filter wheel position movement complete"""
    ser=connect_FW(FWPort)
    ser.open()
    ack=enquiry(ser) #Send Enquiry and read Acknowledgement
    ser.flush() #Flush Unwanted data
    #Read header to read Device 1. Create Header Entities
    soh= chr(0x01) #Start of Header
    addr= chr(0x30)+chr(0x31) #Controller Address 
    oprw= chr(0x38) #Operation Read or write (R=30, W=38)
    data_type=chr(0x31)
    msb=chr(0x34)+chr(0x31)
    lsb=chr(0x38)+chr(0x31)
    cdb=chr(0x30)+chr(0x30)
    pdb=chr(0x30)+chr(0x34)
    hstaddr=chr(0x30)+chr(0x31)
    etb=chr(0x17)
    #Calculate the Checksum for header
    ck_calc=hex(int(format(ord(addr[0]),"x"),16)^int(format(ord(addr[1]),"x"),16)^int(format(ord(oprw[0]),"x"),16)^int(format(ord(data_type[0]),"x"),16)^int(format(ord(msb[0]),"x"),16)^int(format(ord(msb[1]),"x"),16)^int(format(ord(lsb[0]),"x"),16)^int(format(ord(lsb[1]),"x"),16)^int(format(ord(cdb[0]),"x"),16)^int(format(ord(cdb[1]),"x"),16)^int(format(ord(pdb[0]),"x"),16)^int(format(ord(pdb[1]),"x"),16)^int(format(ord(hstaddr[0]),"x"),16)^int(format(ord(hstaddr[1]),"x"),16))
    cksum=str(ck_calc).replace('0x','0')
    #Compile the header
    hdrwrite=soh+addr+oprw+data_type+msb+lsb+cdb+pdb+hstaddr+etb+cksum
    #Create Data Entities
    stx=chr(0x2)
    b3=chr(0x30)
    b4=chr(0x31)
    b1=chr(0x30)
    b2=chr(0x30)
    etx=chr(0x03)
    #Calcluate checksum for data
    ck_calc_data=hex(int(format(ord(b3),"x"),16)^int(format(ord(b4),"x"),16)^int(format(ord(b1),"x"),16)^int(format(ord(b2),"x"),16))
    cksum_data=str(ck_calc).replace('0x','0')
    #Compile the data
    datawrite=stx+b3+b4+b1+b2+etx+cksum_data
    ser.write(hdrwrite.encode()) #Send the header to the controller
    time.sleep(1)
    ack = ser.read(size=3) #Read Acknoledgement to the controller
    ack_check=b'N!\x06'
    ser.write(datawrite.encode()) #Send the data to the controller
    time.sleep(1)    
    ack = ser.read(size=3) #Read Acknoledgement to the controller
    ser.write(b'\x04') #Send end to Transmission to controller
    ser.close()
    time.sleep(3)
    print("Move command complete.")
    return ack