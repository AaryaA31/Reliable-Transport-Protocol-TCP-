#
# Columbia University - CSEE 4119 Computer Networks
# Assignment 2 - Mini Reliable Transport Protocol
#
# mrt_server.py - defining server APIs of the mini reliable transport protocol
#

from queue import Queue
import xml.etree.ElementTree as ET
import time
import datetime 
import socket
import sys
import os
import threading
import struct
from common_functions import *


#
# Server
#

WINDOW_SIZE = 4
Header_size = 7
Headerbytes = 28

class Server:
    def init(self, src_port, receive_buffer_size):
        """
        initialize the server, create the UDP connection, and configure the receive buffer

        arguments:
        src_port -- the port the server is using to receive segments
        receive_buffer_size -- the maximum size of the receive buffer
        """
        self.src_port = src_port
        self.receive_buffer_size = receive_buffer_size
        self.sendsize = 28
        self.seqnum = 0
        self.acknum = 0
        self.data = b""
        self.acked = []
        if 49152 <= src_port <= 65535:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind(('', src_port))
            self.server_socket.settimeout(3.0)
            filename = f"log_{src_port}.txt"
            self.file = open(filename, 'w')
        else:
            print("Error: src_port must be between 49152 and 65535")
            sys.exit(1)

    def accept(self):
        """
        accept a client request
        blocking until a client is accepted

        it should support protection against segment loss/corruption/reordering

        return:
        the connection to the client
        """
        self.state = 'listen'
        print(f"Server listening on port {self.src_port}")
        self.handle(Segment(0,0,0,0,0,0,0,0,0,0,0),"accept")
        conn = self.sendport
        return conn


    def handle(self, packet, operation):        
        whileflag = 1
        closecounter = 0
        nextstate = self.state
        sendport, rcvport, syn, ack, fin, seqnum, acknum, segsize, validdata, windsize, check, data = 0 , 0,0 , 0,0 , 0,0 , 0,0 , 0,0 , 0
        while whileflag == 1 and self.state != 'closed':
            print(self.state)
            try:
                time.sleep(0.2)
                if self.state != 'time_wait' or self.state != 'closed':
                    recvpacket, addr = self.server_socket.recvfrom(4096)
                    sendport, rcvport, syn, ack, fin, seqnum, acknum, segsize, validdata, windsize, check, data = unpack(recvpacket)
                    self.segment_size = segsize
                    self.acknum = seqnum
                    packet.ack_num = seqnum
                    packet.seq_num = seqnum
                    packet.update()
                    self.sendport = sendport
                    self.file.write(f"\nreceived: {datetime.datetime.now()} {self.src_port} {self.sendport} {seqnum} {packet.ack_num} {syn} {ack} {fin} {validdata}")
                              
                self.sendport = sendport
            except IOError:
                 pass
            if self.state == 'closed':
                    whileflag = 0
                    sendflag = 0
                    self.server_socket.close()
                    break
                    print("Server closed successfully")
            elif self.state == 'listen':
                if operation == "receive":
                     whileflag = 0
                sendflag = 0
                if syn == 1:
                    print("Accepted connection from client")
                    nextstate = 'syn_received'
                    sendflag = 1
                    packet = Segment(self.src_port, sendport, 1, 1, 0, self.acknum, self.acknum, self.segment_size, 0, WINDOW_SIZE, 0)            
            elif self.state == 'syn_received':
                    if ack == 1 and syn != 1:
                        nextstate = 'established'
                        whileflag = 0
                        
            elif self.state == 'established':               
                    sendflag = 0
                    if fin == 1:
                             sendflag = 1
                             packet = Segment(self.src_port, sendport, 0, 1, 0, self.acknum, self.acknum, self.segment_size, 0, WINDOW_SIZE, 0)
                             nextstate = 'close_wait'

                    if operation == "receive":
                        sendflag = 1
                        if self.acknum not in self.acked:
                            self.acked.append(self.acknum)
                            if data != 0:
                                if validdata > 0:
                                    if check == checksum(data):
                                        self.data = self.data + data
                                        print("Recevied a data packet")
                                    else:
                                         sendflag = 0
                        packet = Segment(self.src_port, sendport, 0, 1, 0, self.acknum, self.acknum, self.segment_size, 0, WINDOW_SIZE, 0)

            elif self.state == 'finwait-1':
                    sendflag = 1
                    if ack == 1 and fin == 1:
                         nextstate = 'fin-wait2'
                    if fin == 1 and ack != 1:
                        nextstate = 'closing'
                        packet = Segment(self.src_port, sendport, 0, 1, 1, 0, self.acknum, self.segment_size, 0, WINDOW_SIZE, 0)
            elif self.state == 'finwait-2':
                    if fin == 1:
                         packet = Segment(self.src_port, sendport, 0, 1, 1, 0, self.acknum, self.segment_size, 0, WINDOW_SIZE, 0)
                         nextstate = 'time_wait'
            elif self.state == 'close_wait':
                    packet = Segment(self.src_port, sendport, 0, 1, 1, 0, self.acknum, self.segment_size, 0, WINDOW_SIZE, 0)
                    nextstate = 'last_ack'
            elif self.state == 'last_ack':
                    if fin == 1 and ack == 1:
                         nextstate = 'closed'
                        
            elif self.state == 'closing':
                    if ack == 1 and fin == 1:
                         nextstate = 'time_wait'
            elif self.state == 'time_wait':
                    #time.sleep(3)
                    if closecounter < 3:
                        packet = Segment(self.src_port, sendport, 0, 0, 1, 0, self.acknum, self.segment_size, 0, WINDOW_SIZE, 0)
                        closecounter +=1
                    else:
                        nextstate = 'closed'

            if sendflag == 1:
                self.file.write(f"\nsent: {datetime.datetime.now()} {self.src_port} {packet.dest_port} {packet.seq_num} {packet.ack_num} {packet.syn} {packet.ack} {packet.final} {packet.validdata}")
                self.server_socket.sendto(packet.header, ('', self.sendport))

            self.state = nextstate

    def receive(self, conn, length):
        """
        receive data from the given client
        blocking until the requested amount of data is received

        it should support protection against segment loss/corruption/reordering
        the client should never overwhelm the server given the receive buffer size

        arguments:
        conn -- the connection to the client
        length -- the number of bytes to receive

        return:
        data -- the bytes received from the client, guaranteed to be in its original order


        """
        print("receiving data")
        self.seqnum = 0
        self.state = 'established'
        while sys.getsizeof(self.data) < length:
            self.handle(Segment(0,0,0,0,0,0,0,0,0,0,0), "receive")

        return self.data[0:length]

    def close(self):
        """
        close the server and the client if it is still connected
        blocking until the connection is closed
        """
        packet = Segment(self.src_port, self.sendport, 0, 0, 1, 0, self.acknum, self.segment_size, 0, WINDOW_SIZE, 0)
        if self.state != 'closed':
            self.state = 'finwait-1'
            self.handle(packet, "close") 

        
        pass


