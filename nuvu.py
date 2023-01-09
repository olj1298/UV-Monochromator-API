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
# import clr # Import the .NET class library

def start_camserver(ros):
    """Open NUVU camera server.
    Inputs:
        :ros(string):
    Return:
        ::server shell"""
    try:
        cam_server_path='/home/nuvu_setup/nuvu/nuvuserver/server_CIT/bin/camserver_cit'
        command0 = cam_server_path+f' {ros}'
        server=subprocess.Popen(command0,shell=True,stdout=subprocess.PIPE)
        return server
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def dark(exptime):
    """Take dark frame with exposure time.
    Inputs:
        exptime():exposure time
    Returns:
        ::"""
    try:
        command0 = cam_comm+' burst 1'
        subprocess.call(command0,shell=True)
        command1 = cam_comm+' exptime '+str(exptime)
        subprocess.call(command1,shell=True)
        command2 = cam_comm+' dark'
        subprocess.call(command2,shell=True)
    except Exception as ex:
        msg = f"Could not take dark frame with nuvu camera. Error {ex}"
        print(msg)
        return

def bias():
    """Take bias frame with exposure time.
    Inputs:
    Returns:
        ::"""
    try:
        command0 = cam_comm+' burst 1'
        subprocess.call(command0,shell=True)
        command1 = cam_comm+' exptime 0.0'
        subprocess.call(command1,shell=True)
        command2 = cam_comm+' bias'
        subprocess.call(command2,shell=True)
    except Exception as ex:
        msg = f"Could not take bias frame with nuvu camera. Error {ex}"
        print(msg)
        return

def getpath():
    """Set path for camera commands.
    Returns:
        ::"""
    try:
        command0 = str(cam_comm) +' path'
        path = subprocess.check_output(command0,shell=True)
        res = str(path.decode()).strip('\n')
        return(res)
    except Exception as ex:
        msg = f"Could not open path for nuvu camera. Error {ex}"
        print(msg)
        return

def getimno():
    """Set path for image number used in later identification in image analysis.
    Returns:
        ::"""
    try:
        command0 = str(cam_comm) +' imno'
        imno = subprocess.check_output(command0,shell=True)
        res = str(imno.decode()).strip('\n')
        return(int(res))
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def run_dark_exp(exptime=None):
    """Dark exposure.
    Returns:
        ::"""
    try:
        data_dir = getpath()
        print(f'The current working directory is {data_dir}')
        val = input("Is this the correct data directory?")
        if val == 'Y': ##Need to enter the response with 'Y'
            pass
        else:
            print(f'Please set the correct directory path.')
            exit()
        t0 = time.time()
        print(f'Script is starting...')
        if exptime ==None: 
            print("No exposure time provided. Taking default dark for 1 second.")
            exptime = [1]
        print(f'Entering loop for taking bias and dark exposures')
        fn = data_dir + 'darks_log.csv'
        dir   = os.path.dirname(fn)
        if not os.path.exists(dir):
            os.makedirs(dir)
        if not os.path.exists(fn): # write a header?
            writeheader = True
        else:
            writeheader = False
        fp = open(fn, 'a+')
        if writeheader:
            fp.write('Time, Exptime [s], Bias1 img #, Dark img #, Bias img #\n')# header
        fp.close()
        i = 0    
        for et in exptime:
            fp = open(fn, 'a+')
            t1 = time.time()
            imb1 = getimno()
            bias()
            print(f'Exposure time is {et} seconds')
            imd = getimno()
            dark(et)
            t2 = time.time()
            print('Finished dark exposure.')
            imb2 = getimno()
            bias()
            t3 = time.time()
            print(f'Exposure time is {t3-t2} seconds')
            i=i+1
            fp.write('{0}, {1}, {2}, {3}, {4}\n'.format(datetime.now().strftime("%D %T"),str(et),str(imb1),str(imd),str(imb2)))
            fp.close()
        t4 = time.time()
        print(f'Total script time is {t4-t0} seconds')
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def exposure_burst(exptime,nburst):
    """Burst of images.
    Inputs:
        :exptime():
        :nburst():
    Returns:
        ::"""
    try:
        command0 = str(cam_comm) +' burst='+str(nburst)
        subprocess.call(command0,shell=True)
        command1 = str(cam_comm) +' exptime='+str(exptime)
        subprocess.call(command1,shell=True)
        command2 = str(cam_comm) +' expose'
        subprocess.call(command2,shell=True)
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def exposure_wt_pdiode(exptime,nburst,picoa,picoa_filename):
    """Explanation.
    Inputs:
        :exptime():
        :nburst():
        :picoa():
        :picoa_filename():
    Returns:
        ::"""
    try:
        command0 = str(cam_comm) +' burst='+str(nburst)
        subprocess.call(command0,shell=True)
        command1 = str(cam_comm) +' exptime='+str(exptime)
        subprocess.call(command1,shell=True)
        command2 = str(cam_comm) +' expose'
        p=subprocess.Popen(command2,shell=True)
        picoaflag=0
        while True:
            if picoaflag==0: 
                picodata= mclinux.picoa_get_measurement_nosave(picoa,0.1,10)
                picoaflag=1
                if p.poll()==0: 
                    picodata.to_csv(picoa_filename)
                    break
            else: 
                picodata=pd.concat([picodata,mclinux.picoa_get_measurement_nosave(picoa,interval=0.1,nsamples=5)],ignore_index=True)
                if p.poll()==0: 
                    picodata.to_csv(picoa_filename)
                break
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def dark_wt_pdiode(exptime,nburst,picoa,picoa_filename):
    """Explanation
    Inputs:
        :exptime():
        :nburst():
        :picoa():
        :picoa_filename():
    Returns:
        ::"""
    try:
        command0 = str(cam_comm) +' burst='+str(nburst)
        subprocess.call(command0,shell=True)
        command1 = str(cam_comm) +' exptime='+str(exptime)
        subprocess.call(command1,shell=True)
        command2 = str(cam_comm) +' dark'
        p=subprocess.Popen(command2,shell=True)
        picoaflag=0
        while True:
            if picoaflag==0: 
                picodata= mclinux.picoa_get_measurement_nosave(picoa,0.1,10)
                picoaflag==1
                if p.poll()==0: 
                    picodata.to_csv(picoa_filename)
                    break
            else: 
                picodata=pd.concat([picodata,mclinux.picoa_get_measurement_nosave(picoa,interval=0.1,nsamples=5)],ignore_index=True)
                if p.poll()==0: 
                    picodata.to_csv(picoa_filename)
                break
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def scan_with_nuvu():
    """Explanation
    Inputs:
    Returns:
        ::"""
    try: 
        wl_min = 150
        wl_max=200
        exp_time=25
        step=10
        nburst=1
        flist=[1]
        lamp='D2'
        data_dir = getpath()
        print(f'The current working directory is {data_dir}')
        val = input("Is this the correct data directory? Y or N")
        if val == 'Y': ##Need to enter the response with 'Y'
            pass
        else:
            print('Please set the correct directory path.')
            exit()

        log = logging.getLogger("application")
        if not getattr(log, 'handler_set', None):
            sh = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "", "%")
            sh.setFormatter(formatter)
            log.addHandler(sh)
            logfilename=data_dir+'scan_log.txt'
            log.addHandler(logging.FileHandler(logfilename))
            log.setLevel(logging.INFO)
            log.info("Starting PTC data collection ")
            log.info(f"Saving data and log in {data_dir}")

        t0 = datetime.datetime.now()

        log.info(f'Start time={t0}')

        fn = data_dir + 'scan_log.csv'
        dir   = os.path.dirname(logfilename)

        if not os.path.exists(dir):
            log.info("Log directory does not exist. Making one!")
            os.makedirs(dir)

        if not os.path.exists(fn): # write a header?
            log.info("Log file does not exist.")
            writeheader = True
        else:
            writeheader = False
            log.info("Log file exits in this folder.")

        wl_list=np.arange(wl_min,wl_max+step,step)

        for filtnum in flist: 
            log.info(f"Scanning for filer number {filtnum}")
            fw.set_fw_to_position(filtnum,FWPort)
            # mcapi.home()
            current_wl=mcapi.whereishome
            for idx,next_wl in enumerate(wl_list):
                if idx==0: 
                    mcapi.go_to_fromhome(MCPort,next_wl)
                else: 
                    mcapi.go_to_from(MCPort,current_wl,next_wl)

                log.info(f"Monochromator at {next_wl} nm")
                t1 = datetime.datetime.now()

                log.info(f'Taking pre-bias')
                imno = getimno()
                time.sleep(0.2)
                imtype='Bias'
                if idx==0: 
                    log_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp))
                else: 
                    temp_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp))
                    log_df=pd.concat([log_df,temp_df],ignore_index=True)
                bias()
                time.sleep(0.2)
                log.info(f'Taking Dark with exposure time ={exp_time} seconds')
                imno = getimno()
                time.sleep(0.2)
                imtype='Dark'
                temp_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp))
                log_df=pd.concat([log_df,temp_df],ignore_index=True)
                dark(exp_time)
                time.sleep(0.2)

                log.info(f'Taking Exposure for {next_wl} nm with exposure time ={exp_time} seconds')
                imno = getimno()
                time.sleep(0.2)
                imtype='Exposure'
                temp_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp))
                log_df=pd.concat([log_df,temp_df],ignore_index=True)
                #exposure_burst(exp_time,nburst)
                
                current_wl=next_wl

                time.sleep(0.2)
                imno = getimno()
                log.info(f'Taking post-bias')
                imno = getimno()
                time.sleep(0.2)
                imtype='Bias'
                temp_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp))
                log_df=pd.concat([log_df,temp_df],ignore_index=True)
                bias()
                time.sleep(0.2)
                t2 = datetime.datetime.now()
                #et = int(et/2)
                log.info(f"Exp {idx}, exptime {exp_time} ended at {t2}")
                log.info(f'This exposure took {t2-t1} seconds')

            t3 = datetime.datetime.now()
            log.info(f'This fitler took {t3-t0} seconds')
        t4 = datetime.datetime.now()
        log.info(f'This fitler took {t4-t0} seconds')
        log.info(f'Saving data log in {fn}')
        log_df.to_csv(fn)
        log.info(f'Images saved in {data_dir}')
        log.info(f'Scan complete. See scan log in {logfilename}')
    except Exception as ex:
        msg = f"Could not open Nuvu camera server. Error {ex}"
        print(msg)
        return

def get_log_data(imtype,et,imno,wl,lamp='D2',filtnum=1):
    """Explanation.
    Inputs:
        :imtype():
        :et():
        :imno():
        :wl():
        :lamp():
        :filternum():
    Returns:
        ::"""
    try:
        data = {
            'time': [],
            'imtype':[],
            'Exp_time': [],
            'Lamp': [],
            'wl': [],
            'imno':[],
            'filtnum':[]
            }
        data['time'].append(datetime.datetime.now())
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