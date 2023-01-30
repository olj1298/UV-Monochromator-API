import codecs
import time
import serial
import pandas as pd
import numpy as np
import pyvisa as visa
import datetime
import os
import sys
from yaml import scan
import port_utils as pt

"""Commands for McPherson 789-A Scan Controller movement and status"""

def whereishome(): 
    """Returns the home wavelength for the monochrmator for use in movement.
    Inputs: 
        ::None
    Return: 
        ::Home wavelnegth(float)"""
    return float(np.round(631.26,2))

def checkstatus(MCPort,waittime=1):
    """Gives value of limit switch to determine if the scan controller is at a wavelength greater than or less than home wavelength. Used in home function.(our home is 631.26nm)
    Return values are taken from McPherson 789A-4 scan controller manual.
    Inputs:
        :MCport(string): Serial Port Connection
        :waittime(float): Pause for full readout from serial
    Returns:
        :: 0 Scan controller above home
        :: 2 Scan controller above home and moving
        :: 32 Scan controller below home
        :: 34 Scan controller below home and moving
        :: Error message due to improper connection"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        time.sleep(waittime) #gives time to readout full message from serial reciever
        ser.open() #open ser conection for write command
        ser.write(b'] \r'); #ascii keyboard input for checking limit status
        s = ser.read_until(size=None)
        ser.close()
        statnow = codecs.decode(s) #decodes info from serial to confirm movement
        statnow = int(str(statnow[4:])) #should slice output to only be the interger, not ]    0 as previous testing
        if statnow == 0:
            msg = f"Limits status is reading scan controller above home"
        if statnow == 2:
            msg = f"Limits status is reading scan controller above home and moving"
        if statnow == 32:
            msg = f"Limits status is reading scan controller below home"
        if statnow == 34:
            msg = f"Limits status is reading scan controller below home and moving"
        return statnow,msg #prints limit status and message for user to understand where scan controller is in relation to home wavelength
    except Exception as ex:
        msg =f"Limit Status Could Not Be Read. Error Code: {ex}"
        return msg

def stop(MCPort):
    """Immediate stop of scan controller. Command which is a part of homing procedure.
        Inputs:
            :MCPort(string): Serial Port connection
        Returns:
            ::Error message if exception occurs."""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'@ \r'); #ASCII key for soft stop sent as byte
        ser.read_until(size=None)
        ser.close()
        msg =f"scan controller stopped"
        print(msg)
        return
    except Exception as ex:
        msg =f"Error, could not stop scan. Error: {ex}"
        print(msg)
        return 

def home(MCPort):
    """Moves the scan controller from any wavelength to home. Important for conducting other movement functions that assume you begin at home.
        Home function power cycling needed rarely due to error in function.
    Inputs:
        :MCport(string): Serial Port connection
    Returns:
        ::Initial location of the controller
        ::Movement status messages
        ::Error message and code when exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open()
        ser.write(b'+72000 \r'); #increase wavelength for 2 motor revolutions to prevent power switch issue seen during testing
        #Issue: when already at home and home command run, would scan continously until stop command given
        ser.read_until(size=None)
        ser.close()
        ser.open() #open ser conection for write command
        ser.write(b'A8 \r'); #ASCII key enables home circuit to configure to home wavelength sent as byte
        ser.close() #close to prevent error
        print("home circuit enabled, prepared to home")
        statnow,msg = checkstatus(MCPort,waittime=1) #read limit switch on controller and print direction from home
        if statnow < 32: #above home statnow=0, above home and moving statnow=2
            print("scanner is above home so moving down to home")
            ser.open()
            ser.write(b'm-23000 \r'); #move at constant vel. of 23KHz decreasing wavelength
            ser.read_until(size=None)
            ser.close()
            print("decreasing wavelength at 23KHz rate") #number of mircosteps/sec
            while statnow < 32: #once scan passes home statnow should switch to 34
                statnow,msg = checkstatus(MCPort,waittime=1)
                print(msg)
                if statnow==999: #error value to indicate to user that there is an error
                    print(f"home switch stat ={msg},Error code ={statnow}")
                    return 
                if statnow > 32: #below home statnow=32, below home and moving statnow=34
                    stop(MCPort)

                    #remove backlash
                    time.sleep(0.8)
                    ser.open()
                    ser.write(b'-108000 \r'); #turns motor for 3 rev., subtracts 12nm
                    ser.read_until(size=None)
                    ser.close()
                    print("decreasing wavelength for 3 revolutions")
                    time.sleep(4) #time for backlash movement before next command
                    ser.open()
                    ser.write(b'+72000 \r'); #turns motor for 2 rev., adds 8nm
                    ser.read_until(size=None)
                    ser.close()
                    print("increasing wavelength for 2 revolutions")
                    time.sleep(3) #time for backlash movement before next command
                    ser.open()
                    ser.write(b'A24 \r'); #enable high accuracy circuit for fine movement
                    ser.read_until(size=None)
                    ser.close()
                    print("high accuracy circuit enabled")
                    ser.open()
                    ser.write(b'F4500,0 \r'); #find edge of home flag at 1000 steps/sec
                    ser.read_until(size=None)
                    ser.close()
                    print("finding edge of home flag at 4500KHz this will take about 15 seconds")
                    time.sleep(15) #rough time it takes to complete F4500,0 movement
                    stop(MCPort)
                    ser.open()
                    ser.write(b'A0 \r'); #disable home circuit
                    ser.read_until(size=None)
                    ser.close()
                    print(f"disabled home circuit")
                    print("homing successful")
                    return
        if statnow > 0: #below home wavelength statnow=32, below home and moving statnow=34
            print("scanner is below home so moving up to home")
            ser.open()
            ser.write(b'm+23000 \r') #move at constant vel. of 23KHz increasing wavelength
            ser.read_until(size=None)
            ser.close()
            print("increasing wavelength at a rate of 23KHz")
            while statnow > 2: #once scan passes home statnow should switch to 2
                statnow,msg = checkstatus(MCPort,waittime=1)
                print(msg)
                if statnow==999: #error value to indicate to user that there is an error
                    print(f"home switch stat ={msg},Error code ={statnow}") 
                    return
                if statnow < 32: #above home wavelength statnow=0, above home and moving statnow=2
                    stop(MCPort)

                    #removes backlash
                    time.sleep(0.8)    
                    ser.open()
                    ser.write(b'-108000 \r'); #decreasing wavelength for 3 motor revolutions or 12nm
                    ser.read_until(size=None)
                    ser.close()
                    print(f"decrease wavelength for 3 revolutions")
                    time.sleep(3) #time to complete backlash movement before next command
                    ser.open()
                    ser.write(b'+72000 \r'); #increase wavelength for 2 motor revolutions or 8nm
                    ser.read_until(size=None)
                    ser.close()
                    print(f"increase wavelength for 2 revolutions")
                    time.sleep(2) #time to complete backlash movement before next command
                    ser.open()
                    ser.write(b'A24 \r'); #enable high accuracy circuit
                    ser.read_until(size=None)
                    ser.close()
                    print(f"high accuracy circuit enabled")
                    ser.open()
                    ser.write(b'F4500,0 \r'); #find edge of home flag at 4500 microsteps/sec
                    ser.read_until(size=None)
                    ser.close()
                    print(f"finding edge of home flag at 4500KHz, this will take about 12 seconds")
                    time.sleep(12) #time for home flag finding movement to complete before next command
                    stop(MCPort)
                    print("homing movement successful")
                    ser.open()
                    ser.write(b'A0 \r'); #disable home circuit
                    ser.read_until(size=None)
                    ser.close()
                    print(f"disabled home circuit")
                    print("homing successful")
                    return
    except Exception as ex:
        msg =f"Limit Status Could Not Be Read. Error: {ex}"
        print(msg)
        return

def movestat(MCPort,waittime=1):
    """Checks if scan controller is moving or not. Used in movement functions so once a movement is stopped the code moves to the next line in the function.
    Return values are taken from McPherson 789A-4 scan controller manual.
        Inputs:
            :MCPort(string): Serial Port connection
            :waittime(float): Pause for full readout from serial
        Returns:
            ::0 No motion
            ::1 Moving
            ::2 High constant velocity
            ::16 slewing ramping complete
            ::33 Moving
            ::Error message if exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        time.sleep(waittime) #user input of time to read moving status
        ser.open() #open ser conection for write command
        ser.write(b'^ \r'); #read moving status input
        s=ser.read_until(size=None)
        ser.close()
        read = codecs.decode(s)
        movenow = int(str(read[4:])) #should slice output to only be the interger, not ^    0 as previous testing
        if movenow == 0:
            msg=f"moving status: scan controller not moving"
        if movenow == 1:
            msg=f"moving status: scan controller is moving"
        if movenow == 2:
            msg=f"moving status: scan controller is moving at high constant velocity"
        if movenow == 16:
            msg=f"moving status: scan controller slewing ramping complete"
        if movenow == 33:
            msg=f"moving status: scan controller is moving"
        return movenow,msg
    except Exception as ex:
        movenow=int(999) #error value too large to be from movement status
        msg =f"Move Status Could Not Be Read. Error Code: {ex}"
        print(msg)
        return movenow,msg

def go_to_fromhome(MCPort,wl):
    """Moves scan controller to one wavelength starting from home wavelength. Movements converts wavelength to mechanical steps and revolutions, then to bytes sent to scan controller.
        Inputs:
            :MCPort(string): Serial Port connection
            :wl(float): Desired wavelength to end movement at
        Returns
            ::Movement status. Completion of movement
            ::Error message if exception occurs"""
    try:
        home(MCPort)        
        uplim = 900.0 #nm #actual upper limit of device is 999.9nm
        lowlim = 100.0 #nm #actual lower limit of device is 0.1nm
        home_wl = 631.26 #nm #home wavelength for limit switch of scan controller
        rev = 9000 #microsteps #1nm = 9000 microsteps 
        difference = wl - home_wl #nm distance between home wavelength and desired wavelength. Used for movement command
        steps = difference * rev #number of motor steps from home to desired wavelength. Used from movement command
        serialsteps = round(steps,0) #take off fraction of a step for mechanical movement
        intsteps=int(serialsteps)
        if intsteps > 0: #adds plus to python calculation for distance scan controller needs to move grating. converts to byte for device to read
            tempstr = str('+' f'{intsteps}' + ' \r')
            gotostr = bytes(tempstr, 'ascii')
        if intsteps <= 0: #negative already in python calculation for distance scan controller needs to move grating. converts to byte for device to read
            tempstr = str(f'{intsteps}' + ' \r')
            gotostr = bytes(tempstr, 'ascii')
        if lowlim < wl < uplim:
            #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
            ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                                baudrate = 9600, #per 789A-4 manual. bits/sec
                                timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                                xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                                parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                                stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                                bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                                )      
            ser.close() #close open ser connection
            ser.open() #open ser conection for write command
            ser.write(gotostr); #command to move scan controller sent as bytes
            ser.close()
            print(f"scan controller is moving for {round(difference,2)}nm") #spectral resolution only to 2 decimal, but movement caluclation could have many decimals
            mvread,msg = movestat(MCPort,waittime=1) #previous command to check the movement statusso user sees that controller is moving
            if mvread == 999: #error value for user to read movement status could not be completed
                print(msg)
                return msg
            while mvread > 0: #controller value for some type of motion
                mvread,msg = movestat(MCPort,waittime=1)
                print(msg)
                if mvread == 999: #error value for user to read movement status could not be completed
                    print(msg)
                    return msg               
                if mvread == 0: #controller value for no motion
                    stop(MCPort) #stop command for controller as a safeguard to stop movement
                    msg = f"Movement completed"
                    return msg
            print(f"Now at {wl} nm")
    except Exception as ex: 
        msg = f"Could not complete move command, Error: {ex}"
        print(msg)
        return

def go_to_from(MCPort,wlstart,wlend):
    """Moves scan controller from wlstart to wlend wavelength. Movements converts wavelength to mechanical steps and revolutions, then to bytes sent to scan controller.
        Inputs:
            :MCPort(string): Serial Port connection
            :wlstart(float): Start wavelength
            :wlend(float): End wavelength
            :exposuretime(float): Exposure time in seconds which is converted to ms
        Returns
            ::Movement status. Completion of movement
            ::Error message if exception occurs"""
    try:       
        uplim = 900.0 #nm #actual upper limit of device is 999.9nm
        lowlim = 100.0 #nm #actual lower limit of device is 0.1nm
        current_wl = wlstart #nm why
        print(f"Monochromator is at {current_wl} nm")
        rev = 9000 #microsteps #1nm = 9000 microsteps 
        #equation to find difference between home position and new wavelength desired
        difference = wlend - current_wl
        #eq for number of motor steps from home to desired wavelength, 9000 steps = 1 nm
        steps = difference * rev
        #take off fraction of a step for mechanical movement
        serialsteps = round(steps,0)
        intsteps=int(serialsteps)
        if intsteps > 0:
            tempstr = str('+' f'{intsteps}' + ' \r')
            gotostr = bytes(tempstr, 'ascii')
        if intsteps <= 0:
            tempstr = str(f'{intsteps}' + ' \r')
            gotostr = bytes(tempstr, 'ascii')
        if lowlim < wlend < uplim:
            #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
            ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                                baudrate = 9600, #per 789A-4 manual. bits/sec
                                timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                                xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                                parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                                stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                                bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                                )      
            ser.close() #close open ser connection
            ser.open() #open ser conection for write command
            ser.write(gotostr); 
            ser.close()
            print(f"scan controller is moving for {round(difference,2)} nm")
            mvread,msg = movestat(MCPort,waittime=1) #check the movement status
            if mvread ==999:
                print(msg)
                return msg #sets msg at current read value
            while mvread > 0: #some type of motion
                mvread,msg = movestat(MCPort,waittime=1)
                print(msg)
                if mvread ==999:
                    print(msg)
                    return msg #sets msg at current read value             
                if mvread == 0: #no motion
                    stop(MCPort)
                    msg = f"Movement completed"
                    return msg #sets msg at current read value
            print(f"Now at {wlend} nm")
    except Exception as ex: 
        msg = f"Could not complete move command, Error: {ex}"
        print(msg)
        return

"""Original commands to communicate through putty to 789A-4 controller. refer to manual for details on commands"""

def initialize(MCPort): 
    """Original command for putty from device manual. Used for diagnostics in communication.
    Tests if scan controller serial parameters are correct and if port to scan controller is closed or open. 
    Inputs:
        :MCport(string): Serial port connection
    Returns:
        ::Confirmation that connection is working
        ::Error message if exception occured"""
    try: 
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b' \r'); #ASCII key for pressing enter on keyboard sent as byte
        ser.read_until(size=None) #reads out feedback from scan controller until no data is left
        ser.close()
        msg = f"Program communication initialized, Run the exit command before closing out of window!"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not establish communication, check serial connection Error: {ex}"
        print(msg)
        return

def makescanarray(wlstart,wlend,wlstep,exposuretimes):
    """Creates scan array input for advance scan pixis function for given start wavelenghts, stop wavelenths and wavelength step size, and exposure times. 
    Inputs: 
        :wlstart: Start wavelength for advanced scan
        :wlstop: Stop wavelength for advanced scan
        :wlstep: Wavelenght step for the scan
        :exposuretimes: A float exposure time or a 1d numpy array listing the exposure times in increaseing order of wavelength.  
    Returns:
        ::Array for values
        ::ValueError message if exception occurs"""
    wavelist=np.arange(wlstart,wlend+wlstep,wlstep,format=float) #create array of wavelengths to scan from inputs to function
    if type(exposuretimes)==float: #check if exposure times are floats, if they are, continue code
        explist=float(exposuretimes*np.ones(len(wavelist)))#creates an  array of ones as long as wavelist
        return np.column_stack((wavelist,explist)) #stacks two 1D arrays into one 2D array
    elif type(exposuretimes)==np.ndarray: #if exposure times are in an array, check length of wavelist
        if len(exposuretimes)!=len(wavelist): #if the lengths of exposure times list and wavelengths don't match, throw error as code can't continue
            raise ValueError("Length of exposure time list and wavelength range list does not match.")
        return np.column_stack((wavelist,explist)) #stack two 1D arrays into one 2D array
    else: 
        raise ValueError("Incorrect data type. Expecting float or Numpy Array") 

def moveit(MCPort,move):
    """Continous scanning movement at given speed. Must run stop command to stop.
        Inputs:
            :MCPort(string): Serial Port connection
            :move(float): Movement speed, units are steps
        Returns:
            ::Message if controller passed home wavelength
            ::Error message if exception occurs"""
    try:
        strmove = str(f'M{move}' + '\r')
        move2bytes = bytes(strmove, 'ascii')
        print(f"MUST RUN mcapi.stop(port) TO STOP CONTINUOUS MOTION!")
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(move2bytes); #continuous move
        ser.read_until(size=None)
        ser.close()
        statnow,msg = checkstatus(MCPort,waittime=1)#check if controller is above or below home
        if statnow < 32: #if above home
            while statnow < 32: #while above home 
                statnow,msg = checkstatus(MCPort,waittime=1) #check where controller is
                if statnow > 32: #once it passed home 2 becomes 32
                    print(f"scanner has passed home of 631.26nm")
        if statnow > 0: #if below home
            while statnow > 2: #while above home
                statnow,msg = checkstatus(MCPort,waittime=1) #check wehre controller is
                if statnow < 32: #once it passed home 32 becomes 2
                    print(f"scanner has passed home of 631.26nm")
    except Exception as ex:
        msg = f"Error, could interpret move command. Error:{ex}"
        print(msg)
        return

def param(MCPort):
    """Parameters for scan controller. Lists values of ramp speed, starting velocity, scanning velocity respectively.
        Inputs:
            :MCPort(string): Serial Port connection
        Returns:
            ::Values for scanning parameters
            ::Error message if exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'X \r'); #X=K(ramp speed),I(starting velocity),V(scanning velocity)
        s = ser.read_until(size=None) #reads the data coming from the serial until there is no data left
        param = codecs.decode(s)   
        ser.close()
        msg = f"ramp speed, start vel. , scan vel. (steps per second) : {param}"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not return parameters, Error:{ex}"
        print(msg)
        return

def rspeed(MCPort,Rspeed):
    """Scanning ramp speed.
        Inputs:
            :MCPort(string): Serial Port connection
            :Rspeed(int): Ramping speed for scan controller
        Returns:
            ::Ramp speed Value
            ::Error message if exception occurs"""
    try:
        stringRspeed = (f'K{Rspeed}' + '\r')
        speed2bytes = bytes(stringRspeed, 'ascii')
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(speed2bytes); #ramp speed
        s = ser.read_until(size=None) #reads the data coming from the serial until there is no data left
        rs = codecs.decode(s)   
        ser.close()
        msg = f"ramp speed: {rs}"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not return parameters, Error:{ex}"
        print(msg)
        return

def startvel(MCPort,Startvel):
    """Starting velocity of scan controller.
        Inputs:
            :MCPort(string): Serial Port connection
            :Startvel(int): Starting velocity for scan controller in steps per second
        Returns:
            ::starting velocity value
            ::Error message if exception occurs"""
    try:
        stringStartvel = (f'I{Startvel}' + '\r')
        Startvel2bytes = bytes(stringStartvel, 'ascii')
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(Startvel2bytes); #starting velocity
        s = ser.read_until(size=None) #reads the data coming from the serial until there is no data left
        startv = codecs.decode(s)   
        ser.close()
        msg = f"ramp speed: {startv}"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not return parameters, Error:{ex}"
        print(msg)
        return

def scanvel(MCPort,Scanvel):
    """Scanning velocity.
        Inputs:
            :MCPort(string): Serial Port connection
            :Scanvel(int): 
        Returns:
            ::scanning velocity value
            ::Error message if exception occurs"""
    try:
        stringScanvel = (f'G{Scanvel}' + '\r')
        Scanvel2bytes = bytes(stringScanvel, 'ascii')
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(Scanvel2bytes); #scanning velocity
        s = ser.read_until(size=None) #reads the data coming from the serial until there is no data left
        svelocity = codecs.decode(s)   
        ser.close()
        msg = f"ramp speed: {svelocity}"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not return parameters, Error:{ex}"
        print(msg)
        return

def edge(MCPort):
    """Finds edge of limit switch when scan controller is close to home. Slow scanning speed of 4500 steps/rev. Must run hcircuit and acircuit functions before running this command.
        Inputs:
            :MCPort(string): Serial Port connection
        Returns:
            ::Movement has begun
            ::Exception if error occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'F4500,0 \r'); #find edge. home swtich must be blocked. motor moves upward 4500steps/sec
        ser.read_until(size=None)
        ser.close()
        msg = f"finding edge of home flag"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not execute home flag finding function. Error: {ex}"
        print(msg)
        return

def hcircuit(MCPort):
    """Switches home circuit to on. Used for fine, slow movements.
        Inputs:
            :MCPort(string): Serial Port connection
        Returns:
            ::Circuit enabled
            ::Error message if exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'A8 \r'); #enable home circuit
        ser.close()
        msg = f"home circuit enabled"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not enable home circuit. Error:{ex}"
        print(msg)
        return

def dcircuit(MCPort):
    """Switches home circuit to off. Used for fine, slow movements.
        Inputs:
            :MCPort(string): Serial Port connection
        Returns:
            ::Circuit disabled
            ::Error message if exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'A0 \r'); #Disable Home Circuit
        ser.close()
        msg = f"disabled home circuit"
        print(msg)
        return msg
    except Exception as ex:
        msg =f"Error, could not disable home circuit. Error:{ex}"
        print(msg)
        return

def acircuit(MCPort):
    """Switches home accuracy circuit to on. Used for fine, slow movements.
        Inputs:
            :MCPort(string): Serial Port connection
        Returns:
            ::Accuracy circuit enabled
            ::Error message if exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'A24 \r'); #home accuracy circuit enabled
        ser.close()
        msg = f"high accuracy circuit enabled"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not enable high accuracy circuit. Error: {ex}"
        print(msg)
        return

def exep(MCPort,progname):
    """Runs user's premade scan controller movement program from files.
        Inputs:
            :MCPort(string): Serial Port connection
            :progname(string): File path to user made program file
        Returns:
            ::Execution of program
            ::Error message if exception occurs"""
    try:
        strprog = (f'G{progname}' + '\r')
        prog2bytes = bytes(strprog, 'ascii')
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(prog2bytes); #exectues program 
        ser.read_until(size=None)
        ser.close()
        msg = f"executing {progname}"
        print(msg)
        return
    except Exception as ex:
        msg = f"could not execute program. Error:{ex}"
        print(msg)
        return

def store(MCPort):
    """Saves current scan controller parameters to non-volitile memory.
        Inputs:
            :MCPort(string): Serial Port connection
        Returns:
            ::Storing completion
            ::Error message if exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'S \r'); #store parameters 
        ser.read_until(size=None)
        ser.close()
        msg = f"storing parameters to memory"
        print(msg)
        return
    except Exception as ex:
        msg = f"could not store new parameters to memory. Error:{ex}"
        print(msg)
        return

def clear(MCPort):
    """Erases current scan controller parameters.
        Inputs:
            :MCport(string): Serial Port connection
        Returns:
            ::Cleared message
            ::Error message if exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'C1 \r'); #clear
        ser.read_until(size=None)
        ser.close()
        msg = f"cleared pre-programmed parameters"
        print(msg)
        return
    except Exception as ex:
        msg =f"could not clear parameters. Error: {ex}"
        print(msg)
        return

def reset(MCPort):
    """Stops movement of scan controller. Assumes idle state.
        Inputs:
            :MCPort(string):
        Returns:
            ::Reset message
            ::Error message if exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'^C \r'); #Reset
        ser.read_until(size=None)
        ser.close()
        msg = f"reset,stopping motion,becoming idle"
        print(msg)
        return
    except Exception as ex:
        msg = f"could not reset. Could not stop motion.Error:{ex}"
        print(msg)  
        return

def exit(MCPort):
    """Exit program mode. Run before closing code window.
        Inputs:
            :MCPort(string): Serial Port connection
        Returns:
            ::Exit message
            ::Error message if exception occurs"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=MCPort, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per 789A-4 manual. bits/sec
                            timeout = None, #per 789A-4 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per 789A-4 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per 789A-4 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per 789A-4 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per 789A-4 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser conection for write command
        ser.write(b'P \r'); #enter or exit
        ser.read_until(size=None)
        ser.close()
        msg = f"exited program"
        print(msg)
        return
    except Exception as ex:
        msg = f"could not exit program. Please exit manually. Error:{ex}"
        print(msg)
        return