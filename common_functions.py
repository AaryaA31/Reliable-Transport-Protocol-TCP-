#
# Columbia University - CSEE 4119 Computer Networks
# Assignment 2 - Mini Reliable Transport Protocol
#
# common_functions.py - functions shared by both the client and server are contained in this file for organizational purposes
#

from queue import Queue
import xml.etree.ElementTree as ET
import time
import socket
import sys
import os
import threading
import struct

class Segment:
    def __init__(self, source_port, dest_port, syn, ack, final, seq_num, ack_num, segment_size, validdata, window_size,  app_data):
        self.source_port = source_port
        self.dest_port = dest_port
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.ack = ack
        self.final = final
        self.syn = syn
        self.validdata = validdata
        self.window_size = window_size
        self.segment_size = segment_size
        self.app_data = app_data

        Header_struct = "HHBBBIIIIHH"
        Header_size = 7

        if app_data == 0:
            self.app_data = b"0x00" * (segment_size-28)
            self.validdata = 0
        elif sys.getsizeof(app_data) < (segment_size-28):
            self.validdata = len(app_data)
            self.app_data = app_data + b"0x00" * (segment_size - 28 - len(app_data))
            
        else:
            self.app_data = app_data
            self.validdata = (segment_size-28)

        self.check = checksum(self.app_data)
        self.header = struct.pack(Header_struct, self.source_port, self.dest_port,self.syn, self.ack, self.final, self.seq_num, self.ack_num, self.segment_size, self.validdata, self.window_size, self.check)
        
        self.packet = self.header + self.app_data

    def update(self):
        Header_struct = "HHBBBIIIIHH"
        Header_size = 7
        check = checksum(self.app_data)
        self.header = struct.pack(Header_struct, self.source_port, self.dest_port,self.syn, self.ack, self.final, self.seq_num, self.ack_num, self.segment_size, self.validdata, self.window_size, check)
        self.packet = self.header + self.app_data

def unpack(segment):
    Header_struct = "HHBBBIIIIHH"
    header = segment[:28]
    sendport, rcvport, syn, ack, fin, seqnum, acknum, segsize, validdata, windsize, check = struct.unpack(Header_struct, header)
    contents = b""
    if validdata>0:
        contents = segment[28:28+validdata]

    return sendport, rcvport, syn, ack, fin, seqnum, acknum, segsize, validdata, windsize, check, contents

def checksum(data):
    return sum(data) % 256 

def integer_to_bytes(i):
    return i.to_bytes(4, byteorder='big')