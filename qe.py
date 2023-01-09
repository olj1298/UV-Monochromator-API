import time
import pyvisa as visa
import datetime
import os
import os.path
import sys
import codecs
import pandas as pd
import serial
import serial.tools.list_ports
import numpy as np
import shutterapi as shutter
import pixisapi as pixis
import fwapi as fw
import nuvu as nuvu
import command
import PhotodiodeLinux as mclinux
import port_utils as pt
import monochromatorapi as mcapi
import subprocess
from subprocess import Popen, PIPE, STDOUT
import sys
from datetime import datetime,timedelta
import logging
# import clr # Import the .NET class library

"""Quantum Efficiency Measurement using picoammeter, filter wheel, NUVU camera."""

def get_qe_data():
    wl_min = 150
    wl_max=420
    exp_time=40
    step=10
    nburst=1
    flist=[1,2,3]
    lamp='D2'
    Ch1ON=1 #Channel 1 ON
    Ch2ON=1 #Channel 2 ON 
    nsamples=10 #previously 100 
    interval=0.1 #no change. 
    #intiallize picoammeter with the settings. 
    picoa=mclinux.picoammeter_initialize(Ch1ON,Ch2ON,interval,nsamples,picoasrl,debug=False)
    data_dir = nuvu.getpath()
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
        log.info("Starting QE data collection")
        log.info(f"Start wavelenght={wl_min} nm")
        log.info(f"Stop wavelenght={wl_max} nm")
        log.info(f"Exposure time={exp_time} sec")
        log.info(f"Scant step={step}")
        log.info(f"filters used ={flist}")
        log.info(f"lamp ={lamp}")
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
    flag_data_log=0
    for idxf,filtnum in enumerate(flist): 
        log.info(f"Scanning for filer number {filtnum}")
        filtnum=fw.set_fw_to_position(filtnum,FWPort)
        current_wl=mcapi.whereishome
        for idx,next_wl in enumerate(wl_list):
            if idx==0: 
                mcapi.go_to_fromhome(MCPort,next_wl)
            else: 
                mcapi.go_to_from(MCPort,current_wl,next_wl)
            log.info(f"Monochromator at {next_wl} nm")
            t1 = datetime.datetime.now()
            log.info(f'Taking Bias for {next_wl} nm images')
            imno = nuvu.getimno()
            time.sleep(0.2)
            imtype='Bias'
            if flag_data_log==0: 
                log_df=pd.DataFrame(nuvu.get_log_data(imtype,exp_time,imno,next_wl,lamp,filtnum))
                flag_data_log=1
            else: 
                temp_df=pd.DataFrame(nuvu.get_log_data(imtype,exp_time,imno,next_wl,lamp,filtnum))
                log_df=pd.concat([log_df,temp_df],ignore_index=True)
            nuvu.bias()
            time.sleep(0.2)

            log.info(f'Taking Dark along with photodiode for {next_wl} nm with exposure time ={exp_time} seconds')
            imno = nuvu.getimno()
            time.sleep(0.2)
            imtype='Dark'
            temp_df=pd.DataFrame(nuvu.get_log_data(imtype,exp_time,imno,next_wl,lamp,filtnum))
            log_df=pd.concat([log_df,temp_df],ignore_index=True)
            #dark(exp_time)
            picoa_filename=data_dir + f'picoa_{imtype}_f{filtnum}_{next_wl}nm_{imno}.csv'
            nuvu.dark_wt_pdiode(exp_time,nburst,picoa,picoa_filename)
            time.sleep(0.2)

            log.info(f'Taking Exposure along with photodiode for {next_wl} nm with exposure time ={exp_time} seconds')
            imno = nuvu.getimno()
            time.sleep(0.2)
            imtype='Exposure'
            temp_df=pd.DataFrame(nuvu.get_log_data(imtype,exp_time,imno,next_wl,lamp,filtnum))
            log_df=pd.concat([log_df,temp_df],ignore_index=True)
            #exposure_burst(exp_time,nburst)
            picoa_filename=data_dir + f'picoa_{imtype}_f{filtnum}_{next_wl}nm_{imno}.csv'
            nuvu.exposure_wt_pdiode(exp_time,nburst,picoa,picoa_filename)
            current_wl=next_wl

            time.sleep(0.2)
            # imno = getimno()
            # log.info(f'Taking post-bias')
            # imno = getimno()
            # time.sleep(0.2)
            # imtype='Bias'
            # temp_df=pd.DataFrame(get_log_data(imtype,exp_time,imno,next_wl,lamp,filtnum))
            # log_df=pd.concat([log_df,temp_df],ignore_index=True)
            # bias()
            # time.sleep(0.2)
            t2 = datetime.datetime.now()
            #et = int(et/2)
            log.info(f"Exp {idx}, exptime {exp_time} ended at {t2}")
            log.info(f'This exposure took {t2-t1} seconds')

        t3 = datetime.datetime.now()
        log.info(f'This fitler {filtnum} took {t3-t0} seconds')
    t4 = datetime.datetime.now()
    log.info(f'This scan took {t4-t0} seconds')
    log.info(f'Saving data log in {fn}')
    log_df.to_csv(fn)
    log.info(f'Images saved in {data_dir}')
    log.info(f'Scan complete. See scan log in {logfilename}')