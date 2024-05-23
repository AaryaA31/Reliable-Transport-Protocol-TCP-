# CSEE 4119 Spring 2024, Assignment 2
## Aarya Agarwal
## GitHub username: AaryaA31



*Please replace this text with information on how to run your code, description of each file in the directory, and any assumptions you have made for your code*
Run the code as following:
python3 network.py 51000 127.0.0.1 60001 127.0.0.1 55001 Loss.txt
Python3 app_server.py 55001 0
Python3 app_client.py 60001 127.0.0.1 51000 26

You will see that I have added a common_functions.py file, this contains the segment class and some shared methods for client and server

My code only runs with a window size of 1. Unfortunately I was not able to pipeline it, impacting how quickly it can send packets
I also did not use the receive buffer since there is only 1 packet in flight at any given time.
One thing to keep in mind and I made a point of this in the testing file, is that my code can handle both packet loss and bit errors however your mileage may vary depending on how high those are turned up.

One assumption I am using that the app_server file will always ask for less bytes than the lenght of the data.txt being read

The format for which I am writing to the log files is as specified where server and client will open log files called "log_{src_port}:

self.file.write(f"{datetime.datetime.now()} {src_port} {sendport} {seqnum} {ack_num} {syn} {ack} {fin} {validdata}")
datatime.datetime.now = The current time
src_port = the port the data is sending from
sendport = the port the data is sending to
seqnum = The sequence number of the packet, in my implementation even syn and fin packets get seq numbers
ack_num = which seq number is being acknowledged
syn = 1 or 0 for if its a syn or not
ack = 1 or 0 for if its a ack or not
fin = 1 or 0 for if its a fin or not
validdata = The lenght of valid data included with the packet, 0 for syn ack and fin bits.


The state machines for my server and client are implemented as follows as described in the state machine diagram below from this link: https://www.ietf.org/rfc/rfc0793.txt
The server omits syn sent and the client omits listen since these states never happen
                                           Transmission Control Protocol
                                                Functional Specification



                                    
                              +---------+ ---------\      active OPEN  
                              |  CLOSED |            \    -----------  
                              +---------+<---------\   \   create TCB  
                                |     ^              \   \  snd SYN    
                   passive OPEN |     |   CLOSE        \   \           
                   ------------ |     | ----------       \   \         
                    create TCB  |     | delete TCB         \   \       
                                V     |                      \   \     
                              +---------+            CLOSE    |    \   
                              |  LISTEN |          ---------- |     |  
                              +---------+          delete TCB |     |  
                   rcv SYN      |     |     SEND              |     |  
                  -----------   |     |    -------            |     V  
 +---------+      snd SYN,ACK  /       \   snd SYN          +---------+
 |         |<-----------------           ------------------>|         |
 |   SYN   |                    rcv SYN                     |   SYN   |
 |   RCVD  |<-----------------------------------------------|   SENT  |
 |         |                    snd ACK                     |         |
 |         |------------------           -------------------|         |
 +---------+   rcv ACK of SYN  \       /  rcv SYN,ACK       +---------+
   |           --------------   |     |   -----------                  
   |                  x         |     |     snd ACK                    
   |                            V     V                                
   |  CLOSE                   +---------+                              
   | -------                  |  ESTAB  |                              
   | snd FIN                  +---------+                              
   |                   CLOSE    |     |    rcv FIN                     
   V                  -------   |     |    -------                     
 +---------+          snd FIN  /       \   snd ACK          +---------+
 |  FIN    |<-----------------           ------------------>|  CLOSE  |
 | WAIT-1  |------------------                              |   WAIT  |
 +---------+          rcv FIN  \                            +---------+
   | rcv ACK of FIN   -------   |                            CLOSE  |  
   | --------------   snd ACK   |                           ------- |  
   V        x                   V                           snd FIN V  
 +---------+                  +---------+                   +---------+
 |FINWAIT-2|                  | CLOSING |                   | LAST-ACK|
 +---------+                  +---------+                   +---------+
   |                rcv ACK of FIN |                 rcv ACK of FIN |  
   |  rcv FIN       -------------- |    Timeout=2MSL -------------- |  
   |  -------              x       V    ------------        x       V  
    \ snd ACK                 +---------+delete TCB         +---------+
     ------------------------>|TIME WAIT|------------------>| CLOSED  |
                              +---------+                   +---------+

                      TCP Connection State Diagram
                               Figure 6.


I used the info from this link to help create my segment class:
https://www.digitalocean.com/community/tutorials/python-struct-pack-unpack

Used the info from this link for packet structure and for checksum function infor:
https://www.synopsys.com/dw/dwtb/ethernet_mac/ethernet_mac.html#:~:text=Checksum%20is%20a%20simple%20error,is%20corrupted%20along%20the%20network.

My finalized header structure is as follows:
HHBBBIIIBHH (in struct format)

[source port][dest port]
[syn][ack][final]
[seqnumber]
[acknumber]
[seqment size]
[valid data]
[windsize][checksum]

This gives a total of 26 bytes per header

My implementation uses the handle functions for server and client as master state machine functions called at different states with different operations in order to mimic the necessary behavior
This did add some complications as I had to create overhead for each state in order to mimic the looping behavior but I think it was still better than writing within individual method because I basically copied the handle from client to server.


