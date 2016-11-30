README
======

This is unofficial port of netsyslog library written for python2 to python3.
Library api should be fully compatible with original netsyslog library.

For more information visit pages of original project Netsyslog_

.. _Netsyslog: http://hacksaw.sourceforge.net/netsyslog/


Readme from original netsyslog project
--------------------------------------

netsyslog enables you to construct syslog messages and send them (via
UDP) to a remote syslog server directly from Python. Unlike other
syslog modules it allows you to set the metadata (e.g. time, host
name, program name, etc.) yourself, giving you full control over the
contents of the UDP packets that it creates.

netsyslog was initially developed for the Hack Saw project, where it
was used to read log messages from a file and inject them into a
network of syslog servers, whilst maintaining the times and hostnames
recorded in the original messages.

The module also allows you to send log messages that contain the
current time, local hostname and calling program name (i.e. the
typical requirement of a logging package) to one or more syslog
servers.

The format of the UDP packets sent by netsyslog adheres closely to
that defined in RFC 3164.

For more information see http://hacksaw.sourceforge.net/netsyslog/