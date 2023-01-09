import serial
import port_utils as pt

def shutopen(shutterport):
    """
    Tests if VCM D1 shutter controller serial parameters are correct and if port is closed or open. Opens shutter and leaves open until close command sent. 
    Inputs:
        :port(string): Serial port connection
    Returns:
        ::Shutter open message
        ::error message due to improper connection"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=shutterport, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per VCMD1 manual. bits/sec
                            timeout = None, #per VCMD1 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per VCMD1 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per VCMD1 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per VCMD1 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per VCMD1 manual. Number of data bits in transmission
                            )
        ser.close() #close open ser connection
        ser.open() #open ser connection for write command
        ser.write(b'@'); #ASCII command to open shutter sent as byte
        msg = f"Shutter opened"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not establish communication, check serial connection Error: {ex}"
        print(msg)
        
def shutclose(shutterport):
    """
    Tests if VCM D1 shutter controller serial parameters are correct and if port is closed or open. Closes shutter and leaves closed until open command sent.
    Inputs:
        :port(string): Serial port connection
    Returns:
        ::Shutter close message
        ::error message due to improper connection"""
    try:
        #serial communication settings. port variable may be changed depending on computer connected, but other settings must stay the same
        ser = serial.Serial(port=shutterport, #string variable in command.py for shutter serial connection
                            baudrate = 9600, #per VCMD1 manual. bits/sec
                            timeout = None, #per VCMD1 manual. Add time when sending or recieveing transmissions
                            xonxoff = True, #per VCMD1 manual. Software flow control between computer and device
                            parity = serial.PARITY_NONE, #per VCMD1 manual. Checks if byte is even or odd
                            stopbits = serial.STOPBITS_ONE, #per VCMD1 manual. Adds stop byte after transmission ends
                            bytesize = serial.EIGHTBITS, #per VCMD1 manual. Number of data bits in transmission
                            )      
        ser.close() #close open ser connection
        ser.open() #open ser connection for write command
        ser.write(b'A'); #ASCII command to close shutter sent as a byte
        msg = f"Shutter closed"
        print(msg)
        return
    except Exception as ex:
        msg = f"Error, could not establish communication, check serial connection Error: {ex}"
        print(msg)