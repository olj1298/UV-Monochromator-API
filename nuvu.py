import time
import pyvisa as visa
import datetime
from datetime import datetime,timedelta
import os.path
import os
import sys
import codecs
import pandas as pd
import logging
import subprocess
from subprocess import Popen, PIPE, STDOUT
import serial
import serial.tools.list_ports
import numpy as np
import matplotlib.pyplot as plt
import command
import shutterapi as shutter
import fwapi as fw
import monochromatorapi as mcapi
import PhotodiodeLinux as mclinux
import port_utils as pt
import ptc as ptc
#import clr # Import the .NET class library

"""NUVU controller commands for connecting to server, using shutter, and camera controls. Uses variables in command.py and port_utils.py."""

def start_camserver(ros):
    """Open NUVU controller camera server.
    Inputs:
        :ros(string):
    Return:
        ::server shell
        ::error message if controller server cannot connect"""
    try:
        cam_server_path='/home/nuvu_setup/nuvu/nuvuserver/server_CIT/bin/camserver_cit' #directory for NUVU server
        command0 = cam_server_path+f' {ros}' #where is ros defined
        server=subprocess.Popen(command0,shell=True,stdout=subprocess.PIPE) #runs command in shell
        return server
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def dark(exptime, cam_comm):
    """Take dark frame with exposure time.
    Inputs:
        exptime(integer):exposure time
        cam_comm(string): directory address for camera defined in command.py file
    Returns:
        ::error message if controller server cannot connect"""
    try:
        command0 = cam_comm+' burst 1' #burst 
        subprocess.call(command0,shell=True) #run in shell
        command1 = cam_comm+' exptime '+str(exptime) #enter exposure time in command
        subprocess.call(command1,shell=True) #run in shell
        command2 = cam_comm+' dark' #add dark flag to command
        subprocess.call(command2,shell=True) #run in shell
        return command2
    except Exception as ex:
        msg = f"Could not take dark frame with nuvu camera. Error {ex}"
        print(msg)
        return

def bias(cam_comm):
    """Take bias frame with exposure time.
    Inputs:
    Returns:
        ::error message if controller server cannot connect"""
    try:
        command0 = cam_comm+' burst 1' #burst
        subprocess.call(command0,shell=True) #run in shell
        command1 = cam_comm+' exptime 0.0' #no exposure, shutter closed
        subprocess.call(command1,shell=True) #run in shell
        command2 = cam_comm+' bias' #add bias flag to command
        subprocess.call(command2,shell=True) #run in shell
        return command2
    except Exception as ex:
        msg = f"Could not take bias frame with nuvu camera. Error {ex}"
        print(msg)
        return

def getpath(cam_comm):
    """Set path for camera commands.
    Returns:
        ::error message if controller server cannot connect"""
    try:
        command0 = str(cam_comm) +' path' #add path flag
        path = subprocess.check_output(command0,shell=True) #run in shell
        res = str(path.decode()).strip('\n') #remove space at end
        return res
    except Exception as ex:
        msg = f"Could not open path for nuvu camera. Error {ex}"
        print(msg)
        return

def getimno(cam_comm):
    """Set path for image number used in later identification in image analysis.
    Returns:
        ::error message if controller server cannot connect"""
    try:
        command0 = str(cam_comm) +' imno' #add image number flag
        imno = subprocess.check_output(command0,shell=True) #run in shell
        res = str(imno.decode()).strip('\n') #remove space at end
        return(int(res)) #why run as integer?
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def run_dark_exp(exptime=None):
    """Dark exposure.
    Returns:
        ::directory path verification prompt to user
        ::exposure time default if no exptime value specified
        ::loop messages for darks and biases taken
        ::error message if controller server cannot connect"""
    try:
        data_dir = getpath() #run getpath to return cam_comm variable with path flag
        print(f'The current working directory is {data_dir}') 
        val = input("Is this the correct data directory? (Y/N)") #prompt user to verify file location
        if val == 'Y': #If Yes, continue in code
            pass
        else: #if not Y, make user run run_dark_exp again when cam_comm is corrected
            print(f'Please set the correct directory path. Adress defined in cam_comm variable')
            exit()
        t0 = time.time() #set current computer time as start time
        print(f'Script is starting...')
        if exptime == None: #default value
            print("No exposure time provided. Taking default dark for 1 second.")
            exptime = [1]
        print(f'Entering loop for taking bias and dark exposures')
        fn = data_dir + 'darks_log.csv' #add string to directory path for darks to be saved separately
        dir = os.path.dirname(fn) 
        if not os.path.exists(dir): #create directory for darks if it doesnt exist
            os.makedirs(dir)
        if not os.path.exists(fn): #write a header?
            writeheader = True
        else:
            writeheader = False
        fp = open(fn, 'a+') #open directory with a+
        if writeheader: #already set as True, should run write command
            fp.write('Time, Exptime [s], Bias1 img #, Dark img #, Bias img #\n')#header
        fp.close()
        i = 0 #set array counter to 0    
        for et in exptime: #for item in exposure time array
            fp = open(fn, 'a+') #open directory with a+
            t1 = time.time() #add current computer time
            imb1 = getimno() #add image number for pre-bias
            bias() #run bias function as specified above

            print(f'Exposure time is {et} seconds') #current exposure time for dark
            imd = getimno() #add image number for dark
            dark(et) #run dark function as specified above with exposure time
            t2 = time.time() #add current computer time
            print('Finished dark exposure.')

            imb2 = getimno() #add image number for post-bias
            bias() #run bias function as specified above
            t3 = time.time() #add current computer time
            print(f'Exposure time is {t3-t2} seconds') 
            i=i+1 #add one to counter to move to next exposure time
            fp.write('{0}, {1}, {2}, {3}, {4}\n'.format(datetime.now().strftime("%D %T"),str(et),str(imb1),str(imd),str(imb2)))
            #add items to file in directory
            fp.close()
        t4 = time.time() #current computer time
        print(f'Total script time is {t4-t0} seconds')
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def exposure_burst(exptime,nburst,cam_comm):
    """Burst of images for exposure.
    Inputs:
        :exptime(interger): exposure time in seconds
        :nburst(integer): burst time
        :cam_comm(string): address of camera server controller
    Returns:
        ::error message if NUVU controller server not connecting"""
    try:
        command0 = str(cam_comm) +' burst='+str(nburst) #add burst flag
        subprocess.call(command0,shell=True) #run in shell
        command1 = str(cam_comm) +' exptime='+str(exptime) #add exposure time string to directory
        subprocess.call(command1,shell=True) #run in shell
        command2 = str(cam_comm) +' expose' #add exposure flag
        subprocess.call(command2,shell=True) #run in shell
        return command2
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        return msg

def exposure_wt_pdiode(exptime,nburst,picoa,picoa_filename,cam_comm):
    """Exposure to photodiode specification.
    Inputs:
        :exptime(integer): exposure time in seconds
        :nburst(integer): number of bursts
        :picoa(string): picoammeter 
        :picoa_filename(string): directory for picoammeter data to be saved
        :cam_comm(string): directory address for camera controller server
    Returns:
        ::error message if NUVU controller server not connecting"""
    try:
        exposure_burst(exptime,nburst,cam_comm) #run function specified above
        p=subprocess.Popen(command2,shell=True) #run command in shell
        picoaflag=0 #counter to zero
        while True:
            if picoaflag == 0: 
                picodata = mclinux.picoa_get_measurement_nosave(picoa,0.1,10) #run preliminary check
                picoaflag = 1 #change value after taking measurement with no save
                if p.poll() == 0: #save data
                    picodata.to_csv(picoa_filename) #save data to csv
                    break
            else: 
                picodata=pd.concat([picodata,mclinux.picoa_get_measurement_nosave(picoa,interval=0.1,nsamples=5)],ignore_index=True) #?
                if p.poll() == 0: #save data
                    picodata.to_csv(picoa_filename) #save data to csv
                break
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def dark_wt_pdiode(exptime,nburst,picoa,picoa_filename,cam_comm):
    """Explanation
    Inputs:
        :exptime(integer):
        :nburst(integer):
        :picoa(string):
        :picoa_filename(string):
        :cam_comm(string):
    Returns:
        ::error message if NUVU controller not connecting"""
    try:
        dark(exptime, cam_comm) #run dark function as specified above
        p=subprocess.Popen(command2,shell=True) #run in shell
        picoaflag=0 #set value to zero
        while True:
            if picoaflag==0: 
                picodata= mclinux.picoa_get_measurement_nosave(picoa,0.1,10) #run preliminary check
                picoaflag==1 #change value after taking measurement with no save
                if p.poll()==0: #save data
                    picodata.to_csv(picoa_filename) #save data to csv
                    break
            else: 
                picodata=pd.concat([picodata,mclinux.picoa_get_measurement_nosave(picoa,interval=0.1,nsamples=5)],ignore_index=True)#?
                if p.poll()==0: #save data
                    picodata.to_csv(picoa_filename) #save data to csv
                break
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def scan_with_nuvu(wl_min,wl_max,exp_time,step,lamp,nburst=1,flist=[1]):
    """Experiment example running NUVU controller with scanning implemented
    Inputs:
        :wl_min(integer): wavelength in nm
        :wl_max(integer): wavelength in nm
        :exp_time(integer): exposure time in seconds
        :step(integer): interval between wavelengths in nm
        :lamp(string): Xe=Xenon, D2=Deuterium lamp selected
        :nburst(integer): number of burst
        :flist(integer): item in array for filter list slots
    Returns:
        ::directory path verification prompt to user
        ::exposure time default if no exptime value specified
        ::loop messages for darks,biases,exposures taken
        ::error message if NUVU controller not connecting"""
    try: 
        data_dir = getpath() #function specified above
        print(f'The current working directory is {data_dir}')
        val = input("Is this the correct data directory? (Y/N)") #prompt user to verify file location
        if val == 'Y': #If Yes, continue in code
            pass
        else: #if not Y, make user run run_dark_exp again when cam_comm is corrected
            print(f'Please set the correct directory path. Adress defined in cam_comm variable')
            exit()
        log = logging.getLogger("application") #?
        if not getattr(log, 'handler_set', None): #make a header if not already exsist?
            sh = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "", "%") #format of output data
            sh.setFormatter(formatter)
            log.addHandler(sh)
            logfilename=data_dir+'scan_log.txt'
            log.addHandler(logging.FileHandler(logfilename))
            log.setLevel(logging.INFO)
            log.info("Starting PTC data collection ")
            log.info(f"Saving data and log in {data_dir}")
        t0 = datetime.datetime.now() #computer time
        log.info(f'Start time={t0}')
        fn = data_dir + 'scan_log.csv' #add flag to directory
        dir = os.path.dirname(logfilename) 
        if not os.path.exists(dir): #create folder for data to be saved
            log.info("Log directory does not exist. Making one!")
            os.makedirs(dir)
        if not os.path.exists(fn): #Checks for header file for data
            log.info("Log file does not exist.")
            writeheader = True 
        else:
            writeheader = False
            log.info("Log file exits in this folder.")
        wl_list=np.arange(wl_min,wl_max+step,step) #create array of wavelengths from input variables
        for filtnum in flist: #for current filter
            log.info(f"Scanning for filer number {filtnum}") #add movement to file
            fw.set_fw_to_position(filtnum,FWPort) #move to position
            current_wl=mcapi.whereishome #return home wavelength
            for idx,next_wl in enumerate(wl_list): #run loop for each wavlength in scan
                if idx==0: 
                    mcapi.go_to_fromhome(MCPort,next_wl) #move from home to first wavlength in array
                else: 
                    mcapi.go_to_from(MCPort,current_wl,next_wl) #move from current wavlength to next wavelength in array
                log.info(f"Monochromator at {next_wl} nm") #add movement to file
                t1 = datetime.datetime.now() #current computer time
                log.info(f'Taking pre-bias') #add message in data file
                imno = getimno() #run image number function specified above
                time.sleep(0.2) #sleep for .2 seconds
                imtype='Bias' #add bias flag
                if idx==0: 
                    log_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp)) #?
                else: 
                    temp_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp)) #?
                    log_df=pd.concat([log_df,temp_df],ignore_index=True)
                bias() #run bias function specified above
                time.sleep(0.2)

                log.info(f'Taking Dark with exposure time ={exp_time} seconds') #add message in data file
                imno = getimno() #run image number function specified above
                time.sleep(0.2)
                imtype='Dark' #add bias flag
                temp_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp)) #?
                log_df=pd.concat([log_df,temp_df],ignore_index=True) #?
                dark(exp_time) #run dark function with exposure time specified above
                time.sleep(0.2)

                log.info(f'Taking Exposure for {next_wl} nm with exposure time ={exp_time} seconds') #add message in data file
                imno = getimno() #run image number function specified above
                time.sleep(0.2)
                imtype='Exposure' #add exposure flag
                temp_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp)) #?
                log_df=pd.concat([log_df,temp_df],ignore_index=True) #?
                #exposure_burst(exp_time,nburst)
                current_wl=next_wl #change value to set up for next scan controller movement
                time.sleep(0.2)

                imno = getimno() #?
                log.info(f'Taking post-bias') #add message in data file
                imno = getimno() #run image number function specified above
                time.sleep(0.2)
                imtype='Bias' #add (post?)bias flag
                temp_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp)) #?
                log_df=pd.concat([log_df,temp_df],ignore_index=True) #?
                bias() #run bias function specified above
                time.sleep(0.2)
                t2 = datetime.datetime.now() #current computer time
                #et = int(et/2)
                log.info(f"Exp {idx}, exptime {exp_time} ended at {t2}")
                log.info(f'This exposure took {t2-t1} seconds')
            t3 = datetime.datetime.now() #current computer time
            log.info(f'This fitler took {t3-t0} seconds')
        t4 = datetime.datetime.now() #current computer time
        log.info(f'This fitler took {t4-t0} seconds')
        log.info(f'Saving data log in {fn}')
        log_df.to_csv(fn) #show data in .csv as output
        log.info(f'Images saved in {data_dir}')
        log.info(f'Scan complete. See scan log in {logfilename}')
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def get_log_data(imtype,et,imno,wl,lamp='D2',filtnum=1):
    """Set data header for log file used during data analysis.
    Inputs:
        :imtype(string): 'Bias'.'Dark','Exposure'
        :et(integer): exposure time in seconds
        :imno(integer): image number
        :wl(integer): wavelength in nm
        :lamp(string): Xe=Xenon, D2=Deuterium lamp selected
        :filternum(integer): filter  in filter list
    Returns:
        ::error message if NUVU controller not connecting"""
    try:
        data = {'time': [],
                'imtype':[],
                'Exp_time': [],
                'Lamp': [],
                'wl': [],
                'imno':[],
                'filtnum':[]}
        data['time'].append(datetime.datetime.now()) #current computer time
        data['imtype'].append(imtype)
        data['Exp_time'].append(et)
        data['Lamp'].append(lamp)
        data['wl'].append(wl)
        data['imno'].append(imno)
        data['filtnum'].append(filtnum)
        return data
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return