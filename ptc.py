import time
import pyvisa as visa
import datetime
import codecs
import pandas as pd
import serial
import serial.tools.list_ports
import monochromatorapi as mcapi
import shutterapi as shutter
import pixisapi as pixis
import fwapi as fw
import nuvu as nuvu
import command
import PhotodiodeLinux as mclinux
import port_utils as pt
import os.path
import os
import numpy as np
import subprocess
from subprocess import Popen, PIPE, STDOUT
import sys
from datetime import datetime,timedelta
import logging

def run_ptc(lamp='D2',wl=0,filtnum=1):
    """Set log data, exposuretimes, directory names, take bias and darks.
    Inputs:
        :lamp(string): Lamp selection. D2=Deuterium Lamp, Xe=Xenon Lamp. Must be manually switched to the lamp
        :wl(integer): wavelength entered into log of image for further data analysis
        :filtnum(integer): Filter 1-5 of filter wheel. Refer to filter change map for cutoff values
    Returns:
        ::Updates on images taken and output of log data
        ::Error message if code reaches an exception"""
    try:
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
            logfilename=data_dir+'ptc_log.txt'
            log.addHandler(logging.FileHandler(logfilename))
            log.setLevel(logging.INFO)
            log.info("Starting PTC data collection ")
            log.info(f"Saving data and log in {data_dir}")
            t0 = datetime.datetime.now()
            log.info(f'Start time={t0}')
            fn = data_dir + 'ptc_log.csv'
            dir = os.path.dirname(logfilename)
       if not os.path.exists(dir):
            log.info("Log directory does not exist. Making one!")
            os.makedirs(dir)
       if not os.path.exists(fn): # write a header?
            log.info("Log file does not exist.")
            writeheader = True
        else:
            writeheader = False
            log.info("Log file exits in this folder.")
            exptime=[0.010,0.20,0.025,0.050,0.075,0.1,0.2,0.25,0.5,0.75,1,2,3,5,7.5,10,20,30,40,50,60,70,80,90,100,120,140,160,180,200,250,300] #exp in seconds
            log.info(f'exptime list: {exptime}')
            filtnum=fw.set_fw_to_position(filtnum,FWPort)
            log.info(f'filter wheel set to {filtnum}')
            log.info('Entering loop for taking exposures')
        for idx,et in enumerate(exptime):
            t1 = datetime.datetime.now()
            log.info(f'Exposure time is set for {et} seconds')
            log.info(f'Taking pre-bias')
            imno = nuvu.getimno()
            time.sleep(0.2)
            imtype='Bias'
            if idx==0: 
                log_df=pd.DataFrame(nuvu.get_log_data(imtype,et,imno,wl,lamp,filtnum))
            else: 
                temp_df=pd.DataFrame(nuvu.get_log_data(imtype,et,imno,wl,lamp,filtnum))
                log_df=pd.concat([log_df,temp_df],ignore_index=True)
            nuvu.bias()
            time.sleep(0.2)

            log.info(f'Taking pre-dark')
            imno = nuvu.getimno()
            time.sleep(0.2)
            imtype='Dark'
            temp_df=pd.DataFrame(nuvu.get_log_data(imtype,et,imno,wl,lamp,filtnum))
            log_df=pd.concat([log_df,temp_df],ignore_index=True)
            nuvu.dark(et)
            time.sleep(0.2)

            log.info(f'Taking First Flat Exposures')
            imno = nuvu.getimno()    
            time.sleep(0.2)
            imtype='Flat'
            temp_df=pd.DataFrame(nuvu.get_log_data(imtype,et,imno,wl,lamp,filtnum))
            log_df=pd.concat([log_df,temp_df],ignore_index=True)
            nuvu.exposure_burst(et,1)
            time.sleep(0.2)

            log.info(f'Taking Second Flat Exposures')
            imno = nuvu.getimno()    
            time.sleep(0.2)
            imtype='Flat'
            temp_df=pd.DataFrame(nuvu.get_log_data(imtype,et,imno,wl,lamp,filtnum))
            log_df=pd.concat([log_df,temp_df],ignore_index=True)
            nuvu.exposure_burst(et,1)
            time.sleep(0.2)

            log.info(f'Taking post-dark')
            imno = nuvu.getimno()
            time.sleep(0.2)
            imtype='Dark'
            temp_df=pd.DataFrame(nuvu.get_log_data(imtype,et,imno,wl,lamp,filtnum))
            log_df=pd.concat([log_df,temp_df],ignore_index=True)
            nuvu.dark(et)
            time.sleep(0.2)

            log.info(f'Taking post-dark')
            imno = nuvu.getimno()
            imtype='Bias'
            temp_df=pd.DataFrame(nuvu.get_log_data(imtype,et,imno,wl,lamp,filtnum))
            log_df=pd.concat([log_df,temp_df],ignore_index=True)
            nuvu.bias()
            time.sleep(0.2)

            t2 = datetime.datetime.now()
            #et = int(et/2)
            log.info(f"Exp {idx}, exptime {et} ended at {t2}")
            log.info(f'This exposure took {t2-t1} seconds')
        t3 = datetime.datetime.now()
        log.info(f'This exposure took {t3-t0} seconds')
        log.info(f'Saving data log in {fn}')
        log_df.to_csv(fn)
        log.info(f'Images saved in {data_dir}')
        log.info(f'Scan complete. See scan log in {logfilename}')
        #led(0)
        # print(f'Total script time is {t3-t0} seconds')
    except Exception as ex:
        msg =f"Data Could Not Be Taken. Error Code: {ex}"
        return 
    def main(): 
        wl=460
        mcapi.go_to_fromhome(MCPort,wl)
        run_ptc(wl=wl,filtnum=1)

    if __name__=="__main__":
        main()
