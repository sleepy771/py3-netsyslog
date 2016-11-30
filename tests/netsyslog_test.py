#!/usr/bin/env python3
import os
import socket
import syslog
import time
import mock
import pytest
import sys

import netsyslog

DEFAULT_TIMESTAMP = "Jun  7 09:00:00"
DEFAULT_HOSTNAME = "myhost"
DEFAULT_HEADER = "%s %s" % (DEFAULT_TIMESTAMP, DEFAULT_HOSTNAME)


@pytest.fixture(scope='function')
def sendto():
    orig = socket.socket.sendto
    mock_socket = mock.Mock()
    socket.socket.sendto = mock_socket
    yield mock_socket
    socket.socket.sendto = orig


@pytest.fixture(scope='function')
def localtime():
    orig = time.localtime
    time.localtime = mock_local_time
    yield mock_local_time
    time.localtime = orig


@pytest.fixture(scope='function')
def gethostname():
    orig = socket.gethostname
    socket.gethostname = mock_hostname
    yield mock_hostname
    socket.gethostname = orig


def mock_local_time():
    return 2005, 6, 7, 9, 0, 0, 1, 158, 1


def mock_hostname():
    return DEFAULT_HOSTNAME


def test_priority_format():
    """Check PRI is correctly formatted"""
    pri = netsyslog.PriPart(syslog.LOG_LOCAL4, syslog.LOG_NOTICE)
    assert str(pri) == "<165>"


def test_automatic_timestamp(localtime, gethostname):
    """Check HEADER is automatically calculated if not set"""
    header = netsyslog.HeaderPart()
    assert str(header) == " ".join((DEFAULT_TIMESTAMP, DEFAULT_HOSTNAME))


def test_incorrect_characters_disallowed(localtime, gethostname):
    """Check only valid characters are used in the HEADER"""
    # Only allowed characters are ABNF VCHAR values and space.
    # Basically, if ord() returns between 32 and 126 inclusive
    # it's okay.
    bad_char = "\x1f"  # printable, ord() returns 31
    header = netsyslog.HeaderPart()
    header.timestamp = header.timestamp[:-1] + bad_char
    assert str(header) == " ".join((DEFAULT_TIMESTAMP, DEFAULT_HOSTNAME))


def test_set_timestamp_manually(localtime, gethostname):
    """Check it is possible to set the timestamp in HEADER manually"""
    timestamp = "Jan 31 18:12:34"
    header = netsyslog.HeaderPart(timestamp=timestamp)
    assert str(header) == "%s %s" % (timestamp, DEFAULT_HOSTNAME)


def test_set_hostname_manually(localtime, gethostname):
    """Check it is possible to set the hostname in HEADER manually"""
    hostname = "otherhost"
    header = netsyslog.HeaderPart(hostname=hostname)
    assert str(header) == "%s %s" % (DEFAULT_TIMESTAMP, hostname)


# check format of time and hostname, set automatically if incorrect
#   - time is "Mmm dd hh:mm:ss" where dd has leading space, hh leading 0
#   - single space between time and hostname
#   - no space in hostname
#   - if using hostname, not IP, no dots allowed
# print message to stderr if badly formatted message encountered


DEFAULT_TAG = "program"
MOCK_PID = 1234


@pytest.fixture(scope='function')
def sys_args():
    orig = sys.argv
    sys.argv = [DEFAULT_TAG]
    yield sys.argv
    sys.argv = orig


@pytest.fixture(scope='function')
def get_pid():

    def mock_pid():
        return MOCK_PID

    orig = os.getpid
    os.getpid = mock_pid
    yield mock_pid
    os.getpid = orig


def test_tag_defaults_to_progname(sys_args):
    """Check TAG defaults to program name"""
    msg = netsyslog.MsgPart()
    assert msg.tag == DEFAULT_TAG


def test_override_tag():
    """Check TAG can be set manually"""
    msg = netsyslog.MsgPart(tag="mytag")
    assert msg.tag == "mytag"


def test_tag_trimmed_if_too_long():
    """Check long TAGs are trimmed to 32 characters"""
    tag = "abcd" * 10
    msg = netsyslog.MsgPart(tag=tag)
    assert msg.tag == tag[:32]


def test_space_prefixed_to_content():
    """Check single space inserted infront of CONTENT if necessary"""
    msg = netsyslog.MsgPart("program", content="hello")
    assert str(msg) == "program: hello"


def test_space_only_added_if_necessary():
    """Check space only added to CONTENT if necessary"""
    msg = netsyslog.MsgPart("program", content=" hello")
    assert str(msg) == "program hello"


def test_include_pid():
    """Check the program's pid can be included in CONTENT"""
    msg = netsyslog.MsgPart("program", "hello", pid=MOCK_PID)
    assert str(msg) == "program[%d]: hello" % MOCK_PID


DEFAULT_PRI = netsyslog.PriPart(syslog.LOG_LOCAL4, syslog.LOG_NOTICE)
DEFAULT_HEADER = netsyslog.HeaderPart(DEFAULT_TIMESTAMP, DEFAULT_HOSTNAME)
DEFAULT_MSG = netsyslog.MsgPart(DEFAULT_TAG, "hello")


def test_message_format():
    """Check syslog message is correctly constructed"""
    packet = netsyslog.Packet(DEFAULT_PRI, DEFAULT_HEADER, DEFAULT_MSG)
    header = " ".join((DEFAULT_TIMESTAMP, DEFAULT_HOSTNAME))
    start_of_packet = "<165>%s %s" % (header, DEFAULT_TAG)
    assert str(packet).startswith(start_of_packet)


def test_max_length():
    """Check that no syslog packet is longer than 1024 bytes"""
    message = "a" * 2048
    packet = netsyslog.Packet(DEFAULT_PRI, DEFAULT_HEADER, message)
    assert len(str(packet)) == netsyslog.Packet.MAX_LEN


def test_send_message(sendto, gethostname, localtime, sys_args):
    """Check we can send a message via UDP"""
    logger = netsyslog.Logger()

    packet = netsyslog.Packet(DEFAULT_PRI, DEFAULT_HEADER, DEFAULT_MSG)

    hostname = "localhost"
    address_1 = (hostname, netsyslog.Logger.PORT)
    logger.add_host(hostname)

    logger.log(syslog.LOG_LOCAL4, syslog.LOG_NOTICE, "hello")
    sendto.assert_called_once_with(
        bytes(str(packet), encoding='ascii'), address_1)


def test_send_message_to_multiple(sendto, gethostname, localtime, sys_args):
    logger = netsyslog.Logger()

    packet = netsyslog.Packet(DEFAULT_PRI, DEFAULT_HEADER, DEFAULT_MSG)

    hostname = "localhost"
    address_1 = (hostname, netsyslog.Logger.PORT)
    logger.add_host(hostname)

    hostname = "remotehost"
    address_2 = (hostname, netsyslog.Logger.PORT)
    logger.add_host(hostname)

    logger.log(syslog.LOG_LOCAL4, syslog.LOG_NOTICE, "hello")

    assert sendto.call_count == 2
    sendto.assert_has_calls(
        (
            mock.call(bytes(str(packet), encoding='ascii'), address_1),
            mock.call(bytes(str(packet), encoding='ascii'), address_2)
        ),
        any_order=True
    )


def test_remove_host(sendto, gethostname, localtime, sys_args):
    """Check host can be removed from list of those receiving messages"""
    hostname = "localhost"
    logger = netsyslog.Logger()
    logger.add_host(hostname)
    logger.remove_host(hostname)
    logger.log(syslog.LOG_LOCAL4, syslog.LOG_NOTICE, "hello")
    assert sendto.call_count == 0


def test_pid_not_included_by_default(sendto, gethostname, localtime, sys_args):
    """Check the program's pid is not included by default"""
    packet = "<165>%s myhost program: hello" % DEFAULT_TIMESTAMP
    hostname = "localhost"
    address = (hostname, netsyslog.Logger.PORT)

    logger = netsyslog.Logger()
    logger.add_host(hostname)
    logger.log(syslog.LOG_LOCAL4, syslog.LOG_NOTICE, "hello")
    sendto.assert_called_once_with(bytes(packet, encoding='ascii'), address)


def test_include_pid_logger_test(sendto, gethostname, localtime, sys_args, get_pid):
    """Check the program's pid can be included in a log message"""
    packet = "<165>%s myhost program[1234]: hello" % DEFAULT_TIMESTAMP
    hostname = "localhost"
    address = (hostname, netsyslog.Logger.PORT)

    logger = netsyslog.Logger()
    logger.add_host(hostname)
    logger.log(syslog.LOG_LOCAL4, syslog.LOG_NOTICE, "hello", pid=True)

    sendto.assert_called_once_with(bytes(packet, encoding='ascii'), address)


def test_send_packets_by_hand(sendto):
    """Check we can send a hand crafted log packet"""
    hostname = "localhost"
    address = (hostname, netsyslog.Logger.PORT)
    packet_text = "<165>Jan  1 10:00:00 myhost myprog: hello"

    pri = netsyslog.PriPart(syslog.LOG_LOCAL4, syslog.LOG_NOTICE)
    header = netsyslog.HeaderPart("Jan  1 10:00:00", "myhost")
    msg = netsyslog.MsgPart("myprog", "hello")
    packet = netsyslog.Packet(pri, header, msg)
    logger = netsyslog.Logger()
    logger.add_host(hostname)
    logger.send_packet(packet)
    sendto.assert_called_once_with(
        bytes(packet_text, encoding='ascii'),
        address)
