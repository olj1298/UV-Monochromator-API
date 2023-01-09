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
import shutterapi as shutter
import fwapi as fw
import monochromatorapi as mcapi
import port_utils as pt
import command
import clr # Import the .NET class library

def picoammeter_initialize(Ch1ON=1,Ch2ON=1,interval=0.1,nsamples=50,asrl="asrl5::instr",debug=False):
        """Sets channel number, range limits, instrument address, and serial port settings for picoameter.
        Inputs:
                :Ch1ON(integer): 0 = off, 1 = on
                :Ch2ON(integer): 0 = off, 1 = on
                :interval(float): separation between samples
                :nsamples(integer): number of samples taken
                :asrl(string): address of picoammeter
                :debug(boolean): True/False
        Return:
                ::Error if no channels are set to on
                ::Send and Requests sent to the device
                ::Error if device is not connected or if problem occurs during sample collection"""
        def KISend(cmd): #send information to picoammeter
                picoa.write(cmd)
                if debug:
                        print( 'Sent '+cmd)
        def KIRequest(cmd): #query request to get information back from picoammeter
                response = picoa.query( cmd )
                if debug:
                        print( 'Sent '+cmd)
                        print( 'Received '+response.strip())
                return(response)
        Ch1ON = Ch1ON  # 0 = channel off, 1 = channel on
        Ch2ON = Ch2ON  # 0 = channel off, 1 = channel on
        asrl=asrl  # asrl = "asrl5::instr" #instrument address for picoammeter
        runtime = interval * nsamples #calcuate time for measurements so user can see how long it will take
        print(f"samples will be taken in a {runtime} second exposure")
        """Channel 1"""
        Ch1ON = Ch1ON
        Ch1ULimit = .01  # current upper auto range limit 
        Ch1LLimit = 1e-7  # current lower auto range limit
        Ch1NPLC = 1 # Measurement Speed in NPLC
        Ch1SrcV = 0  # Source Voltage
        """ Note on Ch NPLC 
        Options: 0.01 for fast readout mode,FAST: Sets speed to 0.01 PLC and sets display resolution to 3½ digits.
        • MED: Sets speed to 0.10 PLC and sets display resolution to 4½ digits.
        • NORMAL: Sets speed to 1.00 PLC and sets display resolution to 5½ digits.
        • HI ACCURACY: Sets speed to 10.00 PLC and sets display resolution to 6½ digits.
        • OTHER: Use to set speed to any PLC value from 0.01 to 10. Display resolution is not
        changed when speed is set with this option."""
        """Channel 2"""
        Ch2ON = Ch2ON
        Ch2ULimit = .01  # current upper auto range limit 
        Ch2LLimit = 1e-7  # current lower auto range limit 
        Ch2NPLC = 1 # Measurement Speed in NPLC
        Ch2SrcV = 0  # Source Voltage
        if Ch1ON + Ch2ON < 1:
                print( "This program requires at least one measurement channel: "+str(Ch1ON+Ch2ON)+" selected" )
                return
        try:
                rm = visa.ResourceManager() #create PyVISA instrument session with 6482
                picoa = rm.open_resource(asrl) #asrl# could change depending on the serial port used COM3 goes to asrl3::instr
                picoa.write_termination='\r' #ASCII command for enter key
                picoa.read_termination='\r' #ASCII command for enter key
                picoa.baud_rate = 9600 #communication between device and computer
                picoa.data_bits = 8 #communication between device and computer
                picoa.parity = visa.constants.Parity.none #communication between device and computer
                picoa.flow_control = visa.constants.VI_ASRL_FLOW_NONE #communication between device and computer
                # csvpath = os.getcwd( )+'\\' #we should change this to a user defined path. #in command.py 
                '''Set up 6482 communications from the 6482 front panel: RS-232, 9600 Baud, 8 data bits, No parity, No Flow Control, CR terminator
                USE < and > Edit keys and Enter key to select values. Menu -> Communication -> 
                                        -> RS-232 (if not already RS-232, you'll hear the instrument click, then repeat above)
                                        -> BAUD -> 9600
                                        -> BITS -> 8
                                        -> PARITY -> NONE
                                        -> TERMINATOR -> <CR>
                                        -> FLOW-CTRL -> NONE'''
                # other globals
                outputqueue=[]
                debug=1
                outputqueue.append(KIRequest('*IDN?')+'\n')
                print( outputqueue[0]+'added to output queue')
                KISend('*RST') #reset instrument
                val = 0 #wait for instrument to complete reset
                while val != 1:
                        val = int( KIRequest('*OPC?'))
                # set channel parameters, data format, etc.
                if Ch1ON:
                        KISend(':SENS1:CURR:RANG:AUTO ON')
                        KISend(':SENS1:CURR:RANG:AUTO:ULIM '+str(Ch1ULimit))
                        KISend(':SENS1:CURR:RANG:AUTO:LLIM '+str(Ch1LLimit))
                        KISend(':SENS1:CURR:NPLC '+str(Ch1NPLC))
                        KISend(':SOUR1:VOLT:RANGE:AUTO 1 ')
                        KISend(':SOUR1:VOLT '+str(Ch1SrcV))
                        KISend('OUTP1 ON')
                if Ch2ON:
                        KISend(':SENS2:CURR:RANG:AUTO ON')
                        KISend(':SENS2:CURR:RANG:AUTO:ULIM '+str(Ch2ULimit))
                        KISend(':SENS2:CURR:RANG:AUTO:LLIM '+str(Ch2LLimit))
                        KISend(':SENS2:CURR:NPLC '+str(Ch2NPLC))
                        KISend(':SOUR2:VOLT:RANGE:AUTO 1 ')
                        KISend(':SOUR2:VOLT '+str(Ch2SrcV))
                        KISend('OUTP2 ON')
        except Exception as ex:
                msg =f"Could not read using picoammeter. Error: {ex}"
                print(msg)
                return
        return(picoa)

def picoammeter_end(picoa):
        """Closes serial port after samples are collected.
        Inputs:
                :picoa(string): rm.open_resource(asrl)
        Return:
                ::Measurements complete message
                ::Error if device is already closed or serial port could not be found""" 
        try: 
                picoa.close()
                print("Measurements complete")
        except: 
                print("Error! Device already closed or incorrect device specified")

def PICOA_Send(picoa,cmd,debug=False):
        """Write command string to picoammeter.
        Inputs:
                :picoa(string): rm.open_resource(asrl)
                :cmd(string): command line to picoammeter
                :debug(boolean): True/False
        Return:
                ::Sent confirmation for command"""
        try:
                picoa.write(cmd)
                if debug:
                        print('Sent' + cmd)
        except Exception as ex:
                msg =f"Error, could not write command to picoammeter. Error: {ex}"
                print(msg)
                return 

def PICOA_Request(picoa,cmd,debug=False):
        """Response from picoammeter query.
        Inputs:
                :picoa(string): rm.open_resource(asrl)
                :cmd(string): command line to picoammeter
                :debug(boolean): True/False
        Return:
                ::Sent confirmation for command
                ::Recieved confirmation with intrument response"""
        response = picoa.query(cmd)
        try:
                if debug:
                        print('Sent' + cmd)
                        print('Received' + response.strip())
                return(response)
        except Exception as ex:
                msg =f"Error, could not query picoammeter. Error: {ex}"
                print(msg)
                return 

def picoa_get_measurement(picoa,filename,interval=0.1,nsamples=50):
        """Saves data samples to csv file.
        Inputs:
                :picoa(string): rm.open_resource(asrl)
                :filename(string): destination address for csv file
                :interval(float): separation between samples
                :nsamples(integer): number of samples taken"""
        interval = interval #time (s) between consecutive writes of selected channel readings to datalog
        nsamples = nsamples  # number of readings total written to datalog
        count=1 #counter for number of samples taken
        filename=filename
        StartTime = time.time() #current computer time
        try:
                while count<=nsamples:
                        if count==1: #begin data to be saved in csv
                                rawout=PICOA_Request(picoa,':READ?').strip()+','+f'{time.time()-StartTime}' #returns reading and time for csv
                                outlist=[[float(s) for s in rawout.split(',')]] #splits data at every comma
                        else: 
                                rawout=PICOA_Request(picoa,':READ?').strip()+','+f'{time.time()-StartTime}' #data to add to csv
                                outlist.append([float(s) for s in rawout.split(',')])#splits data at every coma
                                count+=1 #increment number of samples taken by 1
                outdf=pd.DataFrame(outlist) #create dataframe from measurements
                outdf.columns=['Ch1','Ch2','Elapsed_time']
                outdf.to_csv(filename) #save dataframe
                return outdf
        except Exception as ex:
                msg =f"Error, could not take measurement with picoammeter. Error: {ex}"
                print(msg)
                return 

def picoa_get_measurement_nosave(picoa,interval=0.1,nsamples=50): 
        """Saves data samples to csv file.
        Inputs:
                :picoa(string): rm.open_resource(asrl)
                :filename(string): destination address for csv file
                :interval(float): separation between samples
                :nsamples(integer): number of samples taken"""
        interval = interval #time (s) between consecutive writes of selected channel readings to datalog
        nsamples = nsamples  # number of readings total written to datalog
        count=1 #counter for number of samples taken
        StartTime = time.time() #current computer time
        try:
                while count<=nsamples:
                        if count==1: #begin data counter
                                rawout=PICOA_Request(picoa,':READ?').strip()+','+f'{time.time()-StartTime}' #returns reading and time
                                outlist=[[float(s) for s in rawout.split(',')]] #splits data at every comma
                        else: 
                                rawout=PICOA_Request(picoa,':READ?').strip()+','+f'{time.time()-StartTime}'
                        outlist.append([float(s) for s in rawout.split(',')])
                count+=1
                outdf=pd.DataFrame(outlist)
                outdf.columns=['Ch1','Ch2','Elapsed_time']
                return outdf
        except Exception as ex:
                msg =f"Error, could not take measurement with picoammeter. Error: {ex}"
                print(msg)
                return

def picoa_set_folder(exp_folder,parent_diretory):
    """Create new folder to store the experiment files and subfiles.
        Inputs:
            :exp_folder(string): folder name
            :parent_directory(string): location of folder
        Returns:
            ::folder and directory creation messages
            ::error message, if error code is 17, updates folder path and directory"""
    folder_location=os.path.join(parent_diretory, exp_folder) #adds location for folder in directory for saving
    import os # importing os module   
    path = folder_location # path
    # Create the directory in '/home/User/Documents' 
    try: 
        os.mkdir(path) #create directory for save data
        customdirectory=path
        print(f"Created empty folder {customdirectory} for storing experiment files")
        return customdirectory
    except OSError as error: 
        out=error
        if out.errno==17: #error code if folder already exists
            customdirectory=path
            print(error)
            print(f"Path updated to existing {customdirectory}. Check that the folder is empty before proceeding.")
            return customdirectory

def savefile(Lamp,slitsize,start_wl,end_wl):
    """Sets filename to inculde experiment settings for easier management and identification
    Inputs:
        :Lamp(string): Lamp selection D2 or Xe
        :slitsize(string): slit diammeter in microns
        :start_wl(float): wavelength in nm
        :end_wl(float): wavelength in nm
    Returns:
        ::filename for directory experiment data will be saved to"""
    try:
        date_today = datetime.datetime.now() #adding the date of experiment to the filename
        datestr = date_today.strftime('%m%d%Y') #format date 
        exp_filenames_basename = f'Exp{datestr}_{Lamp}_slit_{slitsize}micron' #Directory where the data is stored
        exp_folder_name = exp_filenames_basename+f'_{int(start_wl)}nmto{int(end_wl)}nm' #sets folder for save file
        exp_filenames_basename_dark = exp_filenames_basename+'_dark' #adds dark flag if data taken is a dark image
        exp_directory = picoa_set_folder(exp_folder_name,parent_directory) #sets directory for save file
        return exp_directory
    except Exception as ex:
        msg =f"Error, could not set filename or directory for experiment. Error: {ex}"
        print(msg)
        return 

def MC_run_exp():
    """Runs experiment.
    Inputs:
        :Ch1ON(string): 1 = on, 0 = off
        :Ch2ON(string): 1 = on, 0 = off
        :interval(float): time between measurements in s
        :nsamples(float): number of measurements taken by picoammeter
        :picoasrl(string): PLC address for picoammeter
        :MCPort(string): serial address for scan controller
        :FWPort(string): serial address for filter wheel
        :shutterport(string): serial address for shutter
        :start_wl(float): wavelength in nm
        :end_wl(float): wavelength in nm
        :wl_step(float): interval between first and end wavelength in nm
    Returns:
        ::picoammeter settings initialized
        ::current filter confirmation of filter selection
        ::pre dark frames taken
        ::filenames experiment data will be stored in
        ::picoammeter measurements taken
        ::dark frames taken
        ::movement messages
        ::filter change confimation following the filter table
        ::post dark froms taken
        ::exit picoammeter
        ::files saved in their directories
        ::monochromator homing after experiment is complete
        ::error message if scan run is interrupted or issue occurs"""
    try:
        picoa = picoammeter_initialize(Ch1ON,Ch2ON,interval,nsamples,picoasrl,debug=False) #intiallize picoammeter with the settings. 
        mcapi.go_to_fromhome(MCPort,start_wl) #scan to start wavelength
        current_wl = start_wl #begins current wavelength check at first wavelength
        select_filter = fw.which_filter(current_wl) #print which filter is for start wavelength
        filternum = fw.get_fw_position(FWPort) #which filter is currently used
        time.sleep(3) #pause for three seconds to give system time before filter change. used in testing
        if filternum != select_filter: 
            filternum = fw.set_fw_to_position(select_filter,FWPort) #move filter if not used for start wavelength
        shutter.shutclose(shutterport) #close shutter
        print("Taking pre dark")
        filename = exp_filenames_basename_dark+'_pre.csv' #save file for pre darks
        dark_filename = os.path.join(exp_directory, filename) #sets dark data file save name for pre dark
        data = picoa_get_measurement(picoa,dark_filename,interval,nsamples) #take picoammeter reading for pre dark
        counter = int(1)
        while current_wl <= end_wl: #until the end of list of wavelengths
            counter = counter+int(1) #counter to take dark for every 10 lamp exposures 
            filename = exp_filenames_basename+f'_Filter_{filternum}'+f'_wl_{current_wl}nm'+'.csv' #add filter used and wavelength for picoammeter data taken
            filename = os.path.join(exp_directory, filename) #save file in directory for late use
            print(f"Taking data for {current_wl}")
            shutter.shutopen(shutterport) #open shutter
            data = picoa_get_measurement(picoa,filename,interval,nsamples) #take science image and save data
            shutter.shutclose(shutterport)#close shutter
            if counter == int(10): #taking dark for every 10 lamp exposures 
                counter = int(1) #begin counter for number of exposures
                filename = exp_filenames_basename_dark+f'_Filter_{filternum}'+f'_wl_{current_wl}nm'+'.csv' #save file for darks
                dark_filename = os.path.join(exp_directory, filename) #sets dark data file save name
                data = picoa_get_measurement(picoa,dark_filename,interval,nsamples)#take picoammeter reading for dark
                print("Taking wl dark")
            print(f"Going to {current_wl+wl_step} nm") 
            mcapi.go_to_from(MCPort,current_wl,float(current_wl+wl_step)) #movement to next wavelength
            current_wl = current_wl+wl_step #increments current wavelength to next wavelength in list
            select_filter = fw.which_filter(current_wl) #checks if filter is correct for wavelength based on filter wheel map file
            if filternum != select_filter: #check if filter wheel needs to change position for wavelength
                filternum = fw.set_fw_to_position(select_filter,FWPort) #change position
            print("Taking post dark")
            filename = exp_filenames_basename_dark+f'_Filter_{filternum}'+'_post.csv' #save file for post dark
            dark_filename = os.path.join(exp_directory, filename) #sets post dark data file name
            data = picoa_get_measurement(picoa,dark_filename,interval,nsamples) #takes picoameter reading for post dark
            picoammeter_end(picoa) #close picoameter serial connection
            print(f"All data taken and stored in {exp_directory}")
            print("Monochromator is going home!")
            mcapi.home(MCPort) #home at end of experiment
    except Exception as ex:
        msg = f"Error, could not establish communication, check serial connection Error: {ex}"
        print(msg)
        return