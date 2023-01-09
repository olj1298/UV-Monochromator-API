import codecs
import time
import serial
import serial.tools.list_ports
import pandas as pd
import numpy as np
import datetime
import os
import sys
import pyvisa as visa
import monochromatorapi as mcapi
import shutterapi as shutter
import pixisapi as pixis
import fwapi as fw
import PhotodiodeLinux as mclinux
import port_utils as pt
import nuvu as nuvu
import clr # Import the .NET class library
import sys # Import python sys module
import os # Import os module
#"""libraries for PIXIS"""
#from System.IO import * # Import System.IO for saving and opening files
# Import C compatible List and String
#from System import String
#from System.Collections.Generic import List
# Add needed dll references
#sys.path.append(os.environ['LIGHTFIELD_ROOT'])
#sys.path.append(os.environ['LIGHTFIELD_ROOT']+"\\AddInViews")
#clr.AddReference('PrincetonInstruments.LightFieldViewV5')
#clr.AddReference('PrincetonInstruments.LightField.AutomationV5')
#clr.AddReference('PrincetonInstruments.LightFieldAddInSupportServices')
# PI imports
#from PrincetonInstruments.LightField.Automation import Automation
#from PrincetonInstruments.LightField.AddIns import ExperimentSettings
#from PrincetonInstruments.LightField.AddIns import CameraSettings
#from PrincetonInstruments.LightField.AddIns import DeviceType
#from PrincetonInstruments.LightField.AddIns import SensorTemperatureStatus
#from PrincetonInstruments.LightField.AddIns import TriggerResponse
#import PrincetonInstruments.LightField.AddIns as AddIns

"""Import any global variables from updated or new experiments. Run commands in this file imported from function libraries."""

"""Port Variables""" #used for connection to devices in experiment, including moving the grating
ports = pt.update_port_databse(path="port_database.csv")
port_database=pt.get_port_database()
MCPort = port_database[port_database['Port_Alias']=='MCPort']['Port_Name'].values[0]
shutterport= port_database[port_database['Port_Alias']=='ShutPort']['Port_Name'].values[0]
PicoPort=port_database[port_database['Port_Alias']=='PicoPort']['Port_Name'].values[0]
picoasrl='ASRL'+PicoPort+'::INSTR' #port for the picoammeter
FWPort=port_database[port_database['Port_Alias']=='FWPort']['Port_Name'].values[0]

"""PhotodiodeLinux experiment funciton settings"""
#mcapi.go_to_from(MCPort,600,610) #power recycling issue so 10 nm offset, assumes scan controller is already at home
start_wl=float(100.0) #nm #start wavelength for experiment movement functions
end_wl=float(700.0) #nm #end wavelength for experiment movement functions
wl_step=float(1.0) #nm #step between wavelengths for experiment movement functions
slitsize= 1500 #micron #exit and enter port slits of monochromator to add to filename as flag for later analysis
"""Remember to physically switch the lamp on the monochromator"""
Lamp='D2' #lamp switched to D2 on 2:00 PM 08/26/2022 #D2 = Deuterium, Xe = Xenon
exp_folder = '/home/nuvu_setup/Monochromator_software/UV-Monochromator-control/10282022' #save folder for picoameter data
parent_directory = r'/home/nuvu_setup/Monochromator_software/UV-Monochromator-control' #save directory for picoameter data. change this to a data directory in the future 
#mcapi.home(MCPort) #home monochromator to wavelength
Ch1ON=1 #1 = On, 2 = Off #channel status for picoameter
Ch2ON=1 #1 = On, 2 = Off #channel status for picoameter
nsamples=30 #previously 100 #number of samples for picoameter to take
interval=0.1 #rate of samples for picoameter to take
#csvpath = os.getcwd( )+'\\' #we should change this to a user defined path. 
#filename='' #csv file location for data taken by picoammter
#mclinux.savefile(Lamp,slitsize,start_wl,end_wl) #create savefile location in directory with experiment values for easier use after measurements
#mclinux.MC_run_exp() #takes predarks, picoameter readings, post darks and changes filter wheel and changes shutter when needed. saves data in directory for later analysis
#mcapi.go_to_from(MCPort,631.26,640)
pt.setports()
#pt.get_port_database(path="port_database.csv")
#mcapi.home(MCPort)

"""NUVU experiment function settings"""
# For adding the date of experiment to the filename
#date_today=datetime.datetime.now()
#datestr=date_today.strftime('%m%d%Y')
#Directory where the data is stored 
#parent_directory=r'/home/nuvu_setup/Monochromator_software/UV-Monochromator-control' #change this to a data directory in the future 
#exp_filenames_basename=f'Exp{datestr}_{Lamp}_slit_{slitsize}micron_Filter{filternum}'
#exp_filenames_basename=f'Exp{datestr}_{Lamp}_slit_{slitsize}micron'
#exp_folder_name=exp_filenames_basename+f'_{int(start_wl)}nmto{int(end_wl)}nm'
#exp_filenames_basename_dark=exp_filenames_basename+'_dark'
#exp_directory=mclinux.picoa_set_folder(exp_folder_name,parent_directory)
#nuvu.run_ptc(wl=wl,filtnum=1)
#wl_min = 150
#wl_max=420
#exp_time=40
#step=10
#nburst=1
#flist=[1,2,3]
#lamp='D2'
#Ch1ON=1 #Channel 1 ON
#Ch2ON=1 #Channel 2 ON 
#nsamples=10 #previously 100 
#interval=0.1 #no change.

"""ptc experiment function settings"""
#cam_comm = '/home/nuvu_setup/nuvu/nuvuserver/server_CIT/bin/cam_cit'
#lamp = D2 #D2 for Deuterium Lamp, Xe for Xenon Lamp
#wl = #wavelength (nm) 
#filtnum= 1 #filternumber for filter wheel refer to filter change map

"""qe experiment function settings"""
#wl_min = 150
#wl_max=420
#exp_time=40
#step=10
#nburst=1
#flist=[1,2,3]
#lamp='D2'
#Ch1ON=1 #Channel 1 ON
#Ch2ON=1 #Channel 2 ON 
#nsamples=10 #previously 100 
#interval=0.1 #no change. 

"""Remember to physically switch the lamp on the monochromator"""
#Lamp='D2' #lamp switched to Xe on at 12:15 PM 08/30/2022
#update the port database if required. Typically required when moving to a new machine or the USB cables 
#pt.update_port_databse()
#port_database=pt.get_port_database()
# For adding the date of experiment to the filename
#date_today=datetime.datetime.now()
#datestr=date_today.strftime('%m%d%Y')
#Directory where the data is stored 
#parent_directory=r'/home/nuvu_setup/Monochromator_software' #change this to a data directory in the future 
#exp_filenames_basename=f'Exp{datestr}_{Lamp}_slit_{slitsize}micron_{Grating_angle}_{Detector_angle}'
#exp_folder_name=f'jesstest/'
#exp_directory=mclinux.picoa_set_folder(exp_folder_name,parent_directory)
#filename=exp_directory+exp_filenames_basename+'.csv'
#Ch1ON=1 #Channel 1 ON
#Ch2ON=1 #Channel 2 ON 
#nsamples=30 #previously 100 
#interval=0.1 #no change.
#mcapi.go_to_from(MCPort,631.26,640) #power recycling issue give it a little kick of 10 nm 
#mcapi.home(MCPort)
#mclinux.Mc_run_exp()

"""PIXIS experiment function settings"""
#pix_filename = '' #directory for PIXIS experiment settings for live camera
#MC_lamp = 'Xe' #Xe for Xenon lamp, D2 for Deuterium lamp 
#Traget_spectral_bandpass = 0.62 #nm bandpass of the Monochromator
#Experiment_PIXIS_default='PIXIS_MC_Default' #use presaved default settings for camera
#pix_directory='C:\\Users\\User\\Documents\\LightField' #save data in directory
#pix_filenames_basename=f'exp_{MC_lamp}_500ms' #save data with exposure time 
#pix_folder_name=pix_filenames_basename+'_180to700nm_10C' #save data with wavelength and camera temperature
#pix_start=180.0 #nm start wavelength of scan
#pix_end=700.0 #nm end wavelength of scan
#pix_step=10.0 #nm distance to each wavelength in scan
#pix_time=1000.0 #ms #exposure time at each wavelength
#n_bias=10 #number of bias frames
# pixis.pixis_load_experiment(pix_filename)
# pixis.pixis_device_found()
# pixis.slitposition(MC_lamp,Traget_spectral_bandpass)
# pixis.pixis_take_bias_frames(n_bias)