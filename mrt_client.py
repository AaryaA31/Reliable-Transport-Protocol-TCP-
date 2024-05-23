#
# Columbia University - CSEE 4119 Computer Networks
# Assignment 2 - Mini Reliable Transport Protocol
#
# mrt_client.py - defining client APIs of the mini reliable transport protocol
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

#Header struct and checksum are based on the information found at this link:
#https://www.synopsys.com/dw/dwtb/ethernet_mac/ethernet_mac.html#:~:text=Checksum%20is%20a%20simple%20error,is%20corrupted%20along%20the%20network.

WINDOW_SIZE = 4
Header_size = 6
Headerbytes = 28



acknumber = 0


class Client:
    def init(self, src_port, dst_addr, dst_port, segment_size):
        """
        initialize the client and create the client UDP channel

        arguments:
        src_port -- the port the client is using to send segments
        dst_addr -- the address of the server/network simulator
        dst_port -- the port of the server/network simulator
        segment_size -- the maximum size of a segment (including the header)
        """
        self.src_port = src_port
        self.dst_addr = dst_addr
        self.dst_port = dst_port
        self.segment_size = segment_size
        self.sendsize = 28
        self.state = 'closed'
        self.seqnumber = 0
        log_file_path = f"log_{src_port}.txt"
        print("Binded")
        self.log_file = open(log_file_path, "w")
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.bind(("", src_port))
        self.send_sock.settimeout(1)

    def connect(self):
        """
        connect to the server
        blocking until the connection is established

        it should support protection against segment loss/corruption/reordering
        """
        if self.state != 'closed':
            print("connection already established")
        else:
            print("Trying to establish connection")
            validdata = 0
            synpacket = Segment(self.src_port, self.dst_port, 1, 0, 0, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)
            self.state = 'syn_sent'
            self.handle(synpacket, "connect")

    def handle(self, packet, operation):        
        whileflag = 1
        closecounter = 0
        packetflag = 0
        nextstate = self.state
        sendport, rcvport, syn, ack, fin, seqnum, acknum, segsize, validdata, windsize, check, data = 0 , 0,0 , 0,0 , 0,0 , 0,0 , 0,0 , 0
        while whileflag == 1:
            try:   
                if self.state == 'syn_sent' or self.state == 'closed' or self.state == 'syn_received':
                    self.seqnumber += 1
                    packet.seq_num = self.seqnumber
                    packet.update()
                    self.send_sock.sendto(packet.header, (self.dst_addr, self.dst_port))
                    self.log_file.write(f"\nsent: {datetime.datetime.now()} {self.src_port} {packet.dest_port} {packet.seq_num} {packet.ack_num} {packet.syn} {packet.ack} {packet.final} {packet.validdata}")
                    
                else:
                    self.seqnumber += 1
                    packet.seq_num = self.seqnumber
                    packet.update()
                    self.send_sock.sendto(packet.packet, (self.dst_addr, self.dst_port))
                    self.log_file.write(f"\nsent: {datetime.datetime.now()} {self.src_port} {packet.dest_port} {packet.seq_num} {packet.ack_num} {packet.syn} {packet.ack} {packet.final} {packet.validdata}")
                print("sent a packet")
                time.sleep(0.2)
                if self.state != 'time_wait':
                    recvpacket, addr = self.send_sock.recvfrom(28)
                    sendport, rcvport, syn, ack, fin, seqnum, acknum, segsize, validdata, windsize, check, data = unpack(recvpacket)
                    self.log_file.write(f"\nreceived: {datetime.datetime.now()} {self.src_port} {sendport} {seqnum} {acknum} {syn} {ack} {fin} {validdata}")
                
                if acknum == self.seqnumber:
                     packetflag = 1
                else:
                    self.seqnumber = self.seqnumber - 1 
            except IOError:
                 self.seqnumber = self.seqnumber - 1

            
            if packetflag == 1:           
                if self.state == 'closed':
                        if operation == "close":
                            whileflag = 0
                            self.send_sock.close()
                            print("Client closed Successfully")
                        else:
                            nextstate = 'syn_sent'
                        
                elif self.state == 'syn_sent':
                        if syn == 1 and ack != 1:
                            nextstate = 'syn_received'
                            packet = Segment(self.src_port, self.dst_port, 1, 1, 0, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)
                        if syn == 1 and ack == 1:
                            nextstate = 'established'
                            packet = Segment(self.src_port, self.dst_port, 0, 1, 0, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)             
                elif self.state == 'syn_received':
                        if syn == 1 and ack == 1:
                            nextstate = 'established'
                elif self.state == 'established':
                        if fin == 1:
                                packet = Segment(self.src_port, self.dst_port, 0, 1, 1, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)
                                nextstate = 'close_wait'
                        if operation == "connect": 
                            whileflag = 0
                        if operation == "send":
                            whileflag = 0
                elif self.state == 'finwait-1':
                        if ack == 1 and fin == 1:
                            nextstate = 'finwait-2'
                            packet = Segment(self.src_port, self.dst_port, 0, 1, 1, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)
                        if fin == 1 and ack != 1:
                            nextstate = 'closing'
                            packet = Segment(self.src_port, self.dst_port, 0, 1, 1, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)
                elif self.state == 'finwait-2':    
                        if fin == 1:
                            packet = Segment(self.src_port, self.dst_port, 0, 1, 0, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)  
                            nextstate = 'time_wait'
                elif self.state == 'close_wait':
                        packet = Segment(self.src_port, self.dst_port, 0, 1, 0, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)
                        nextstate = 'last_ack'
                elif self.state == 'last_ack':
                        if fin == 1 and ack == 1:
                            nextstate = 'closed'
                            operation = "close"
                elif self.state == 'closing':
                        if ack == 1 and fin == 1:
                            nextstate = 'time_wait'
                elif self.state == 'time_wait':
                        if closecounter < 3:
                            packet = Segment(self.src_port, self.dst_port, 0, 0, 1, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)
                            closecounter +=1
                        else:
                            #time.sleep(3)
                            nextstate = 'closed'
                            whileflag = 0
                            self.send_sock.close()
                            print("Client closed Successfully")


                self.state = nextstate
    
    def send(self, data):
        """
        send a chunk of data of arbitrary size to the server
        blocking until all data is sent

        it should support protection against segment loss/corruption/reordering and flow control

        arguments:
        data -- the bytes to be sent to the server
        """
        self.state = 'established'
        segments = [data[i:i+(self.segment_size-28)] for i in range(0, len(data), self.segment_size-28)]
        
        for segment in segments:
            # Create a Segment object
            segment = Segment(self.src_port, self.dst_port, 0, 0, 0, 0, 0, self.segment_size, 0, WINDOW_SIZE, segment)

            # Send the segment
            self.handle(segment, "send")
        
        return len(data)

    def close(self):
        """
        request to close the connection with the server
        blocking until the connection is closed
        
        """
        #self.log_file.write("TRANSMISSION INCOMPLETE\n")
        #self.log_file.close()
        try:
            validdata = 0
            packet = Segment(self.src_port, self.dst_port, 0, 0, 1, 0, 0, self.segment_size, validdata, WINDOW_SIZE, 0)
            self.state = 'finwait-1'
            self.handle(packet, "close") 
        except:
            pass



