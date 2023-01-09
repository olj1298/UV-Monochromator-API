import codecs
import time
import serial
import pandas as pd
import numpy as np
import pyvisa as visa
import datetime
import os
import sys
import monochromatorapi as mcapi # Import monochromator api
import port_utils as pt 
import clr # Import the .NET class library
import sys # Import python sys module
import os # Import os module
from System.IO import * # Import System.IO for saving and opening files
# Import C compatible List and String
from System import String
from System.Collections.Generic import List
# Add needed dll references
sys.path.append(os.environ['LIGHTFIELD_ROOT'])
sys.path.append(os.environ['LIGHTFIELD_ROOT']+"\\AddInViews")
clr.AddReference('PrincetonInstruments.LightFieldViewV5')
clr.AddReference('PrincetonInstruments.LightField.AutomationV5')
clr.AddReference('PrincetonInstruments.LightFieldAddInSupportServices')
# PI imports
from PrincetonInstruments.LightField.Automation import Automation
from PrincetonInstruments.LightField.AddIns import ExperimentSettings
from PrincetonInstruments.LightField.AddIns import CameraSettings
from PrincetonInstruments.LightField.AddIns import DeviceType
from PrincetonInstruments.LightField.AddIns import SensorTemperatureStatus
from PrincetonInstruments.LightField.AddIns import TriggerResponse
import PrincetonInstruments.LightField.AddIns as AddIns
 
def pixis_load_experiment(filename='DemoExp'):
    """Import premade settings file in LightField to send commands through api instead.
        Inputs:
            :filename(string): Experiment setting file premade in Lightfield
        Returns:
            ::Warning if Dummy Camera settings are loaded
            ::Connection message
            ::Error if not connected"""
    if pix_filename=='DemoExp': #premade settings for demo camera
        print("Warning: Loading Dummy Camera. Please select input filename to connect to the real PIXIS")
    auto = Automation(True, List[String]())
    experiment = auto.LightFieldApplication.Experiment
    connected=experiment.Load(filename) #loads premade settings for experiment
    if connected == False: 
        print("Warning: Could not connect to the camera. Check Light Field Window or Experiment file name.")
    elif connected == True: 
        print("Connection successful")
    return connected, auto, experiment

def pixis_set_value(setting, value):    
    """Check for existing experiment before setting new gain, adc rate, or adc quality.
        Inputs:
            :setting(string):
            :value():"""    
    if experiment.Exists(setting):
        experiment.SetValue(setting, value)

def pixis_get_value(setting):    
    """Check for settings for gain, adc rate, adc quality, return values
        Inputs:
            :setting(string):""" 
    if experiment.Exists(setting):
        return experiment.GetValue(setting)

def pixis_device_found():
    """Find connected device an inform user if device not detected
        Returns:
            ::Error message"""
    for device in experiment.ExperimentDevices:
        if (device.Type == DeviceType.Camera):
            return True
    print("Camera not found. Please add a camera and try again.")
    return False  

def pixis_take_bias_frames(n_bias):
    """Loop to capture bias images with PIXIS.
        Inputs:
            :n_bias(float): number of bias frames
        Returns:
            ::message that loop is beginning"""
    print(f"Taking {n_bias}  frames")
    bias_exposure_time=0 #exposure time set to 0 for bias frames 
            #may need to set the shutter function of PIXIS to not send trigger to ensure shutter does not open. 
            #Right now the assumption is that the shutter does not open when a 0 second exopsure is given. 
            #Set exposure time
    count =1 #starts count for number of bias frames taken
    while count<=n_bias: 
        count+=1
        pixis_set_value(CameraSettings.ShutterTimingExposureTime, bias_exposure_time)
        pixis_set_value(CameraSettings.ShutterTimingMode,3)
        if (pixis_device_found()==True): 
            # Acquire image
            waitUntil_ready()
            experiment.Acquire()
            waitUntil_ready()
            pixis_set_value(CameraSettings.ShutterTimingExposureTime, bias_exposure_time)
    pixis_set_value(CameraSettings.ShutterTimingMode,2)

def pixis_take_exposure(exposuretime):
    """Opens shutter, triggers LightField Aquire command, closes shutter.
        Inputs:
            :exposuretime(float): exposure time (seconds)
        Returns:
            ::Exposure time value, and completion"""  
    if (pixis_device_found()==True): 
            pixis_set_value(CameraSettings.ShutterTimingMode,2) # setting 2 means shutter open
            pixis_set_value(CameraSettings.ShutterTimingExposureTime, exposuretime) #hold shutter open for exposuretime
            print(f"exposure time set to {exposuretime}")
            waitUntil_ready()
            experiment.Acquire()
            waitUntil_ready()
            print("Exposure complete")

def pixis_take_dark_frames(n_dark,exposure_time):
    """Aquire images with shutter closed.
        Inputs:
            :n_dark(float): number of dark frames
            :exposure_time(float): time shutter is open
        Returns:
            ::Message that process is starting"""
    print(f"Taking {n_dark} dark frames")
    count =1 #begin count for dark images
    while count<=n_dark: 
        count+=1
        if (pixis_device_found()==True): 
            waitUntil_ready()
            pixis_set_value(CameraSettings.ShutterTimingMode,3) #setting of 3 means shutter closed
            pixis_set_value(CameraSettings.ShutterTimingExposureTime, exposure_time)
            # Acquire image
            waitUntil_ready()
            experiment.Acquire()
            waitUntil_ready()
    pixis_set_value(CameraSettings.ShutterTimingMode,2)

def waitUntil_ready(delay=5): #default value is 5 seconds
    """Delay for each command.
        Inputs:
            :delay(float): Time in seconds"""  
    ":delay: delay in seconds"
    condition=experiment.IsReadyToRun
    wU = True
    while wU == True:
        if condition: #checks the condition
            wU = False
        time.sleep(delay) #waits 60s for preformance

def pixis_set_folder(pix_exp_folder,pix_diretory):
    """Create new folder to store the experiment files and subfiles.
        Inputs:
            :exp_folder(string): folder name
            :parent_directory(string): location of folder
        Returns:
            ::folder and directory creation messages
            ::error message, if error code is 17, updates folder path and directory"""
    folder_location=pix_diretory+'\\'+pix_exp_folder
    import os # importing os module
    path = folder_location # path 
    # Create the directory in '/home / User / Documents' 
    try: 
        os.mkdir(path)
        customdirectory=path
        print(f"Created empty folder {customdirectory} for storing experiment files")
        pixis_set_value(ExperimentSettings.FileNameGenerationDirectory,customdirectory)
        pixis_set_value(ExperimentSettings.OnlineExportOutputOptionsCustomDirectory,customdirectory)
        print(f"Custom directory set to {customdirectory} ")
    except OSError as error: 
        out=error
        if out.errno==17: 
            customdirectory=path
            print(error)
            print(f"Path updated to existing {customdirectory}. Check that the folder is empty before proceeding")
            pixis_set_value(ExperimentSettings.FileNameGenerationDirectory,customdirectory)
            pixis_set_value(ExperimentSettings.OnlineExportOutputOptionsCustomDirectory,customdirectory)
            print(f"Custom directory set to {customdirectory} ")
            return(customdirectory)

def pixis_save_file(pix_filename):    
    """Set base file name, set increment, date, time.
        Inputs:
            :exp_folder(string): folder name
            :parent_directory(string): location of folder
        Returns:
            ::folder and directory creation messages
            ::error message, if error code is 17, updates folder path and directory"""
    experiment.SetValue(
        ExperimentSettings.FileNameGenerationBaseFileName,
        Path.GetFileName(pix_filename))
    # Option to Increment, set to false will not increment
    experiment.SetValue(ExperimentSettings.FileNameGenerationAttachIncrement,True)
    # Option to add date
    experiment.SetValue(ExperimentSettings.FileNameGenerationAttachDate,True)
    # Option to add time
    experiment.SetValue(ExperimentSettings.FileNameGenerationAttachTime,True)

def pixis_get_current_temperature():
    """Present temperature value of PIXIS for user to read.
        Returns:
            ::temperature in Celsius"""
    current_temp=experiment.GetValue(CameraSettings.SensorTemperatureReading)
    print(f"Current Temperature:{current_temp}")
    return current_temp
    
def pixis_set_temperature(temperature):
    """Set temperature if Ready condition is met and not aquiring data.
        Inputs:
            :temperature(float): value in Celsius
        Returns:
            ::Temperature change message and set message"""   
    if (experiment.IsReadyToRun & experiment.IsRunning==False): #checks if experiment is loaded and ready to set temperature low for the detector
        experiment.SetValue(CameraSettings.SensorTemperatureSetPoint,temperature)    
        time.sleep(5)
        while pixis_get_temperature_status()!=2: 
            time.sleep(4)
            ct=pixis_get_current_temperature() 
            print(f"Detector temperature is being changed to {temperature}. Current temperature is {ct}")
        print(pixis_get_temperature_status())
        print(f"Detctor temperature now set to {pixis_get_current_temperature()}")

def pixis_get_current_setpoint():
    """Present temperature setpoint for user to read.
        Returns:
            ::Set point in Celsius"""
    print(String.Format(
        "{0} {1}", "Current Temperature Set Point:",
        experiment.GetValue(CameraSettings.SensorTemperatureSetPoint)))        

def pixis_get_temperature_status():
    """Read Status of Lock and Unlock feature based on temperature.
        Returns:
            ::Status and if Locked or not"""     
    current = experiment.GetValue(CameraSettings.SensorTemperatureStatus)
    print(String.Format(
        "{0} {1}", "Current Status:",
        "UnLocked" if current == SensorTemperatureStatus.Unlocked 
        else "Locked"))
    return current

def slitposition(MC_lamp,Traget_spectral_bandpass):
    """Calculate slit width based on spectral bandpass and dispersion scale.
        Inputs:
            :MC_lamp(string): 'D2' or 'Xe' for our two lamp setup
            :Traget_spectral_bandpass(float): nm
        Returns:
            Values for entrance and exit slit for user to set for experiment run."""
    MC_dispersion_scale=1.24 #nm/mm for 1200 g/mm grating from Model 207V Manual
    MC_resolution = 0.04 #nm for 1200 g/mm from Model 207V Manual
    MC_exit_slit_posiiton=Traget_spectral_bandpass/MC_dispersion_scale #mm 
    print(f"Enterance slit is at {np.round(MC_exit_slit_posiiton,2)} mm")
    MC_entrnace_slit_posiiton=MC_exit_slit_posiiton #mm 
    print(f"exit slit is at {np.round(MC_exit_slit_posiiton,2)} mm. Set to same as enterance slit.")
    return

def experimentstatus(Experiment_PIXIS_default):
    """Opens Lightfield. Loads experiment settings preset by user. 
        Inputs:
            :Experiment_PIXIS_default(string): Name user gave to saved experiment settings
        Returns:
            ::Sucessful experiment loaded message"""
    Experiment_PIXIS_default='PIXIS_MC_Default' #make variable user can change
    # Experiment_PIXIS_default='DemoExp'
    status, auto, experiment=pixis_load_experiment(Experiment_PIXIS_default)
    if status==True: 
        print("PIXIS is ready")
    return 

def experimentfilesettings(pix_filenames_basename,pix_folder_name):
    """Creates file from loaded user settings of experiment. Names file based on user experiment settings. Useful for future experiment reference.
        Inputs:
            :exp_filenames_basename(string): Includes lamp used and exposure time
            :exp_folder_name(string): Adds wavelength range and PIXIS temperature setting from user experiment
        Returns:
            ::Sucessful folder creation, directory creation, and current PIXIS temperature message
            ::Updates path folder and directory if experiemnt with same name was already created"""
    pix_filnames_basename_bias=pix_filenames_basename+'_bias'
    pix_filnames_basename_dark=pix_filenames_basename+'_dark_'

    exp_filenames_attachdate=False #to attach date to filename
    exp_filenames_attachtime=False #to attach time to filename
    exp_filenames_attachincrement=True #to attach automatic increment to filename

    pixis_set_value(ExperimentSettings.OnlineExportEnabled,True) #eanbles export of acquired data other than the native *.spe format
    pixis_set_value(ExperimentSettings.OnlineExportFormat,1) #  1 for FITS format
    pixis_set_value(ExperimentSettings.OnlineExportOutputOptionsExportedFilesOnly,True)
    pixis_set_value(ExperimentSettings.OnlineExportFormatOptionsIncludeExperimentInformation,True)
    pixis_set_value(CameraSettings.ShutterTimingMode,2) # 2 open the shutter when exposure is taken, 3 for shutter remains closed when exposure is taken.  When Trigger ouput set to "Shutter"
    pix_directory=pixis_set_folder(pix_folder_name,pix_directory)

    pixis_set_value(ExperimentSettings.FileNameGenerationAttachDate,exp_filenames_attachdate) #add date
    pixis_set_value(ExperimentSettings.FileNameGenerationAttachTime,exp_filenames_attachtime) #add time
    pixis_set_value(ExperimentSettings.FileNameGenerationAttachIncrement,exp_filenames_attachincrement) #add increment
    pixis_set_value(ExperimentSettings.FileNameGenerationBaseFileName,pix_filenames_basename) #file base name

    pixis_set_value(CameraSettings.AdcSpeed,2) #set to 2 MHz, other option is 0.1 MHz
    pixis_set_value(CameraSettings.AdcGain,1) #set Adc Gain to 1, other values are 2, 3 

    return print(f" Detector Temperature = {pixis_get_current_temperature()}")

def experimentrun(pix_start,pix_end,pix_step,pix_time,n_bias):
    """Homes scan controller. Takes bias frames then scans from user start to end wavelengths at desired step. takes 1 dark and 1 exposure frame at each stop wavelength.
        Inputs:
            :start_wl(float): nm
            :end_wl(float): nm
            :wl_step(float): nm
            :exp_time(float): ms
        Returns:
            ::bias frames taken, taking exposure, exposure time, exposure complete, taking dark frame, movement status, set temperature messages"""
    pix_start=180.0 #nm #make variable user can change
    pix_end=700.0 #nm #make variable user can change
    pix_step=10.0 #nm #make variable user can change
    pix_time=1000.0 #milleseconds #make variable user can change
    ndark=int(1) #int
    mcapi.go_to_fromhome(MCPort,pix_start) 
    n_bias=10 #make variable user can change
    exp_filnames_basename_bias_pre=pix_filenames_basename+'_bias_pre'
    pixis_set_value(ExperimentSettings.FileNameGenerationBaseFileName,exp_filnames_basename_bias_pre)
    pixis_take_bias_frames(n_bias)
    pixis_set_value(ExperimentSettings.FileNameGenerationBaseFileName,pix_filenames_basename)
    current_wl=pix_start
    while current_wl<=pix_end:
        print(f"Taking exposure at {np.round(current_wl,2)} nm")
        exp_filename=pix_filenames_basename+"_wl"+str(np.round(current_wl,2)).replace(".", "_")
        pixis_set_value(ExperimentSettings.FileNameGenerationBaseFileName,exp_filename)
        pixis_take_exposure(pix_time)
        dark_filename=exp_filnames_basename_dark+"_wl"+str(np.round(current_wl,2)).replace(".", "_")
        pixis_set_value(ExperimentSettings.FileNameGenerationBaseFileName,dark_filename)
        pixis_take_dark_frames(ndark,pix_time)
        pixis_set_value(ExperimentSettings.FileNameGenerationBaseFileName,pix_filenames_basename)
        print(f"Going to {current_wl+pix_step} nm")
        mcapi.go_to_from(MCPort,current_wl,float(current_wl+pix_step))
        current_wl+=pix_step
    mcapi.home(MCPort)
    exp_filnames_basename_bias_post=pix_filenames_basename+'_bias_post'
    pixis_set_value(ExperimentSettings.FileNameGenerationBaseFileName,exp_filnames_basename_bias_post)
    pixis_take_bias_frames(n_bias)
    pixis_set_value(ExperimentSettings.FileNameGenerationBaseFileName,pix_filenames_basename)
    print("Scan complete")
    pixis_set_temperature(23)
    return pixis_get_current_temperature()

def experimentclose():
    """Sets PIXIS to ambient temperature. Closes Lightfield experiment window.
        Returns:
            ::set temperature message"""
    pixis_set_temperature(23)
    auto.Dispose()