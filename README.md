$UV Monochromator API
========

UV Monochromator API will send commands to the devices connected for movements, taking images, and measurements.

Use command.py to enter and run commands, all function libraries should be imported at the beginnng of the file.
To test that RS232 connection is working for communication between your computer and the Scan Controller, run pt.get_port_database(path="port_database.csv"). You will need to check the serial ports on your computer for the correct port number each device is connected to.
The first movement before running any experiment should be the mcapi.home(MCPort) function.

Features
--------
This software can home, check the limit status, movement status, set scanning parameters, stop and move the controller at user given range and interval with pauses for exposure times. It can also communicate with the NUVU controller server to take dark, bias and science images at various exposure times. Written for integration with the McPherson 798-A Scan Controller, NUVU contoller, VCM-D1 Shutter Driver, McPherson 648 Filter Wheel and McPherson 747 Device Controller, Keithly 6482 Picoammeter and PIXIS 1024B camera.

Installation
------------
Download 798-A Scan Controller Application and drivers as well as drivers for Filter Wheel from McPherson.com
libraries to install in your Python instance: pyserial,pyvisa,pandas,numpy
Lightfield software for PIXIS

Contribute
----------

- Issue Tracker: https://github.com/olj1298/UV-Monochromator-API/issues
- Source Code: https://github.com/olj1298/UV-Monochromator-API

Support
-------

If you are having issues, please let us know.
olj1298@gmail.com

License
-------

The project is licensed under the BSD license.
