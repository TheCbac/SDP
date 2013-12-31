#################################
## System Device Protocol - SDP
##
## Author: Craig Cheney
## Date: 12/30/13
#################################

## <Device ID>
## <Status>
##
## Function Delimiter
##     <Function>
## End Function Delimiter
##
## Address Delimiter
##     <Address> 
## End Address Delimiter
##
## Data Delimiter
##     <Data>
## End Data Delimiter    
##
## <CRC>

## ASCII 
## ----------------------- EXAMPLE ---------------------------
##
## 0x00 - 0xFF  # range for device ID
## 0x00 - 0x05  # range for device status
##
## 0x00 - 0xFF # range for Function
##
## 0x06  # Addr Delimiter
## 0x30 - 0x39, 0x41 - 0x46 # Range for (hex Ascii value) Address Hi nibble
## 0x30 - 0x39, 0x41 - 0x46 # Range for (hex Ascii value) Address Low nibble
## 0x07  # End Addr Delimiter
##
##
##
## 0x08  # Data Delimiter
## 0x30 - 0x39, 0x41 - 0x46 # Range for (hex Ascii value) Data Hi nibble
## 0x30 - 0x39, 0x41 - 0x46 # Range for (hex Ascii value) Data Low nibble
## 0x09  # End Data Delimiter
##
## CRC   # number of high bits


## ID1 = 0x01
## 
## device = sdp.sdpDevice( ID1, STATUS_MASTER)
## device.read(


STATUS_MASTER = 0x01 # Status for master devices
STATUS_SLAVE = 0X02  # Status for slave devices

DELIMIT_ADDR = 0x06
DELIMIT_ADDR_END = 0x07
DELIMIT_DATA = 0x08
DELIMIT_DATA_END = 0x09


FN_WRITE = 0x10  # Hash for write function
FN_READ = 0x11  # Hash for read

SIZE_BYTE = 8 # size of a byte
BYTE_RANGE = 2**SIZE_BYTE # number of options for a byte (256 is standard)



POS_REPLY_ID        =0
POS_REPLY_STATUS    =1
POS_REPLY_FUNCTION  =2
POS_REPLY_ADDR      =3
POS_REPLY_DATA      =4
POS_REPLY_CRC       =5


class sdpDevice:    
    def __init__(self, name, deviceID, status):
        self.verbose = False  ## for debugging
        self.ultraVerbose = False
        
        # Information needed upon device creation
        self.name = name        # name just used for verbose
        self.deviceID = deviceID    #Unique Identification code
        self.deviceStatus = status        # Status code (Slave,Master)


        
        self.queryFunction = 0
        self.queryAddr=[]
        self.queryData= []
        self.queryCrc = 0


        self.replyAddr =[]
        self.replyData =[]
        self.replyCRC= 0

        self.receiveBuffer = []  # buffer for storing incoming packet
        self.sendBuffer = [[],[],[],[],[],[]]     # Buffer for outgoing data


    ###################################################### 
    def getDeviceID(self):
        return self.deviceID


    ###################################################### 
    def getStatus(self):
        if self.deviceStatus == STATUS_MASTER:
            return "Master"
        elif self.deviceStatus == STATUS_SLAVE:
            return "Slave"

        

    ######################################################  
    ## Calculates and returns the CRC from a recieved packet
    def getCRC(self):

        crcBuff = CRC(self.receiveBuffer[:-1])
        
        if self.ultraVerbose:
            print "Calculated CRC:", crcBuff
            
        return  crcBuff
    
    #######################################################
    ## Compares the calculated CRC with the received CRC
    def checkCRC(self):

        check = self.receiveBuffer[-1] == self.getCRC()
        
        if self.ultraVerbose:
            print "Received CRC:",self.receiveBuffer[-1]
            print "CRC check:", check

        return check


    def setReplyAddr(self):
        buildAddr=[]


        if self.queryFunction == FN_WRITE:
            # if writing, return the address written to
            buildAddr.append(self.queryAddr)

    
        
        # include the delimiters
        buildAddr.append(DELIMIT_ADDR_END)
        buildAddr.insert(0,DELIMIT_ADDR)

        if self.ultraVerbose:
            print "replyAddr:", buildAddr
        
        self.replyAddr =buildAddr



    def setReplyData(self):
        buildData=[]


        
        if self.queryFunction == FN_WRITE:
            # if writing, return the address written to
            buildAddr.append(self.queryAddr)

            

        # include the delimiters
        buildData.append(DELIMIT_DATA_END)
        buildData.insert(0,DELIMIT_DATA)

        if self.ultraVerbose:
            print "replyData:", buildData
        
        self.replyData = buildData

    def setReplyCRC(self):
        replyCRC = CRC(self.sendBuffer[:-1])
        self.replyCRC = replyCRC
        
        if self.ultraVerbose:
            print "replyCRC:", replyCRC
            
        

    #######################################################
    ## builds the reply packet to be sent
    def buildReply(self):
        self.setReplyAddr()
        self.setReplyData()
        

        
        
    #######################################################
    ## builds the packet to be sent
    def buildReplyPacket(self):

        if self.ultraVerbose:
            print   "queryFunction:",self.queryFunction 
            print   "queryAddr:",   self.queryAddr
            print   "queryData:",   self.queryData
            print   "queryCRC:",    self.queryCrc
            print ""
        

        self.sendBuffer[POS_REPLY_ID ] = self.deviceID
        self.sendBuffer[POS_REPLY_STATUS ] = self.deviceStatus
        self.sendBuffer[POS_REPLY_FUNCTION ] = self.queryFunction

        if self.ultraVerbose:
                print "replyID:", self.deviceID
                print "replyStatus:", self.deviceStatus
                print "replyFunction:", self.queryFunction

        self.buildReply()    
        self.sendBuffer[POS_REPLY_ADDR] = self.replyAddr
        self.sendBuffer[POS_REPLY_DATA] = self.replyData

        self.setReplyCRC()
        self.sendBuffer[POS_REPLY_CRC] =  self.replyCRC

        
        if self.verbose:
            print "Reply Packet:", self.sendBuffer

    
    #######################################################
    ## Debugging functions
    def setVerbose(self):
        self.verbose = True
        self.ultraVerbose = False
        print self.name, "Verbose"

    def setUltraVerbose(self):
        self.verbose = True
        self.ultraVerbose = True
        print self.name, "UltraVerbose"
        
    def clearVerbose(self):
        self.verbose = False
        self.ultraVerbose = False
        print self.name, "Non-Verbose"        




#######################################################
## bitsIn(value)
## returns the number of bits that are high in value.
## only works on positive numbers
## returns -1 on error
#######################################################

def bitsIn(value):

    bits=0

    if (value >=0) and (value < BYTE_RANGE):  # Check to make sure it is an acceptable value
        for index in xrange(SIZE_BYTE):     # iterate through the number of bits
            bits += value>>index & 1

        return bits
    
    return -1       # On error, return -1


##########################################################
## Calculate the Cyclic Redundancy Check (CRC) on an array
## returns the number of high bits in the array
#########################################################
def CRC(array):
    crc = 0

    # try on a list
    try:
        for element in array:
            if isinstance(element,int):
                crc+= bitsIn(element)
            elif isinstance(element,list):
                crc+= CRC(element)
            else:
                raise  sdpError("Invalid CRC")

    # if not a list raise an error
    except TypeError:
        raise sdpError("CRC: Not a list")
        
                
    return crc





#######################
test = [1,12,4,5]
test1 = [1,[12,4],4]
RPi = sdpDevice('RPi',0x01, STATUS_MASTER)
RPi.setUltraVerbose()
RPi.receiveBuffer=test1
RPi.queryAddr =10
RPi.queryFunction = FN_WRITE




##########################################
### Exception class for System Device Protocol

class sdpError(Exception):
    def __init__(self,value):
        self.value=value
    def __str__(self):
        return repr(self.value)
