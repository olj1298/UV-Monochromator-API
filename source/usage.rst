Usage
=====

Connecting to Devices listed in README
--------------------------------------

To get serial to usb port list of devices connected,
you can use the ``pt.get_port_database()`` function:

.. py:function:: pt.get_port_databse(path="port_database.csv")

   Prints current ports for each serial connection. 

   :param kind: filename for csv of portlist in same folder as command and port_utils files.
   :type kind: list[str] 
   :return: port_database
   :raise pt.InvalidPathError: If the path is invalid.
   :rtype: list[str]

you can use the ``pt.get_port_database()`` function:

.. autofunction:: pt.get_port_database