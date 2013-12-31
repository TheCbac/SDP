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



POS_SENDER    =0
POS_RECIPIENT =1
POS_STATUS    =2
POS_FUNCTION  =3
POS_ADDR      =4
POS_DATA      =5
POS_CRC       =6


class sdpDevice:    
    def __init__(self, name, deviceID, status):
        self.verbose = False  ## for debugging
        self.ultraVerbose = False
        
        # Information needed upon device creation
        self.name = name        # name just used for verbose
        self.deviceID = deviceID    #Unique Identification code
        self.deviceStatus = status        # Status code (Slave,Master)
        self.registers={}


        self.querySender= 0
        self.queryRecipient=0
        self.queryStatus=0
        self.queryFunction = 0
        self.queryAddr=[]
        self.queryData= []
        self.queryCrc = 0

        self.replySender= 0
        self.replyRecipient=0
        self.replyStatus=0
        self.replyFunction = 0
        self.replyAddr=[]
        self.replyData= []
        self.replyCrc = 0

        self.queryBuffer = [[],[],[],[],[],[],[]]      # buffer for storing incoming packet
        self.replyBuffer = [[],[],[],[],[],[],[]]      # Buffer for outgoing data




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
    def validateQueryCRC(self):

        #calculate CRC
        crcBuff = CRC(self.queryBuffer[:-1])
        
        if self.ultraVerbose:
            print "Calculated query CRC:", crcBuff, "Received query CRC:", self.queryCrc
            
        return  self.queryCrc == crcBuff

    ######################################################  
    ## Calculates and returns the CRC from a recieved packet
    def validateReplyCRC(self):

        #calculate CRC
        crcBuff = CRC(self.replyBuffer[:-1])
        
        if self.ultraVerbose:
            print "Calculated reply CRC:", crcBuff, "Received reply CRC:", self.replyCrc
            
        return  self.replyCrc == crcBuff

    ## Creates the reply CRC
    def setReplyCRC(self):
        replyCRC = CRC(self.replyBuffer[:-1])
        self.replyCRC = replyCRC
        
        if self.ultraVerbose:
            print "replyCRC:", replyCRC


    ## the Writing function
    def processWrite(self, address, data):

        if address.pop(0) == DELIMIT_ADDR and address.pop() == DELIMIT_ADDR_END and\
            data.pop(0) == DELIMIT_DATA and data.pop() == DELIMIT_DATA_END:


            
            address1 = address.pop() # get rid of nested list
            data1 = data.pop()

            if len(data1) == len(address1):
                for element in xrange(len(address1)):
                    
                    if self.ultraVerbose:
                        print "Writing" , data1[element], "to" ,address1[element]
                
                    self.registers[address1[element]] = data1[element]
            else:
                raise sdpError("Address and Data arrays of different lengths")

            return [address1], [data1]

                

        else:
            if self.ultraVerbose:
                print "Delimiter mismatch"
            

            

 ## the reading function
    def processRead(self, address):
        dataRead=[]
        if self.ultraVerbose:
            print "reading" ,address


        if address.pop(0) == DELIMIT_ADDR and address.pop() == DELIMIT_ADDR_END:
            addressRead = address.pop() # get rid of nested list

            for elements in xrange(len(addressRead)):

                if self.ultraVerbose:
                    print "reading from Address:", addressRead[elements] 

                dataRead.append(self.registers[addressRead[elements]])

            
            
        return [addressRead] , [dataRead] 
         

    
##############################

    def buildReplyInfo(self):
        buildAddr=[]
        buildData=[]

        #################
        if self.queryFunction == FN_WRITE:
            try:
                (buildAddr, buildData) = self.processWrite(self.queryAddr, self.queryData)
            except KeyError:
                print "No such register"
                

            
        ##################
        if self.queryFunction == FN_READ:
            try:
                (buildAddr, buildData) = self.processRead(self.queryAddr) 
            except KeyError:
                print "No such register" 
            

            
        
        
        # include the delimiters
        buildAddr.append(DELIMIT_ADDR_END)
        buildAddr.insert(0,DELIMIT_ADDR)

        if self.ultraVerbose:
            print "replyAddr:", buildAddr

        
        # include the delimiters
        buildData.append(DELIMIT_DATA_END)
        buildData.insert(0,DELIMIT_DATA)

        if self.ultraVerbose:
            print "replyData:", buildData
            
        
        self.replyAddr =buildAddr
        self.replyData = buildData

        

            
                
    #######################################################
    ## builds the packet to be sent
    def buildReplyPacket(self):

        if self.validateQueryCRC():


            self.replyBuffer[POS_SENDER ] = self.deviceID
            self.replyBuffer[POS_RECIPIENT] = self.querySender
            self.replyBuffer[POS_STATUS ] = self.deviceStatus
            self.replyBuffer[POS_FUNCTION ] = self.queryFunction

            if self.ultraVerbose:
                    print "replyID:", self.deviceID
                    print "replyStatus:", self.deviceStatus
                    print "replyFunction:", self.queryFunction

            self.buildReplyInfo()    
            self.replyBuffer[POS_ADDR] = self.replyAddr
            self.replyBuffer[POS_DATA] = self.replyData

            self.setReplyCRC()
            self.replyBuffer[POS_CRC] =  self.replyCRC

            
            if self.verbose:
                print self.name, "Produced Reply Packet:", self.replyBuffer

        else:
            print "Query CRC Validation Failed"


    #add address delimiters
    def delimitAddr(self, addr):
        dAddr=[addr]
        dAddr.append(DELIMIT_ADDR_END)
        dAddr.insert(0,DELIMIT_ADDR)

        return dAddr

    # add the data delimiters
    def delimitData(self, data):
        dData=[data]
        dData.append(DELIMIT_DATA_END)
        dData.insert(0,DELIMIT_DATA)

        return dData

    def readQuery(self):
        self.querySender = self.queryBuffer[POS_SENDER ]
        self.queryRecipient = self.queryBuffer[POS_RECIPIENT ] 
        self.queryStatus = self.queryBuffer[POS_STATUS ] 
        self.queryFunction  = self.queryBuffer[POS_FUNCTION ] 
        self.queryAddr = self.queryBuffer[POS_ADDR] 
        self.queryData =  self.queryBuffer[POS_DATA]  
        self.queryCrc  = self.queryBuffer[POS_CRC]

    def readReply(self):
        self.replySender =      self.replyBuffer[POS_SENDER ]
        self.replyRecipient =   self.replyBuffer[POS_RECIPIENT ] 
        self.replyStatus =      self.replyBuffer[POS_STATUS ] 
        self.replyFunction  =   self.replyBuffer[POS_FUNCTION ] 
        self.replyAddr =        self.replyBuffer[POS_ADDR] 
        self.replyData =        self.replyBuffer[POS_DATA]  
        self.replyCrc  =        self.replyBuffer[POS_CRC]

        if self.validateReplyCRC():
            if self.ultraVerbose:
                print "validatedreplyCRC"
            
        else:
            raise sdpError("Reply CRC failed")
            

    def replyMatchQuery(self):

        if self.replySender == self.queryRecipient and \
           self.replyFunction == self.queryFunction: 
           
           return True

        print self.name, self.replySender , self.queryRecipient

        return False
        

###################################
            
    def buildQueryPacket(self):

        self.querySender = self.deviceID
        if self.ultraVerbose:
                print   "querySender", self.querySender
                print   "queryRecipient", self.queryRecipient
                print   "queryFunction:",self.queryFunction 
                print   "queryAddr:",   self.queryAddr
                print   "queryData:",   self.queryData
                print   "queryCRC:",    self.queryCrc
                print ""
            

            
        self.queryBuffer[POS_SENDER ] = self.querySender
        self.queryBuffer[POS_RECIPIENT ] = self.queryRecipient
        self.queryBuffer[POS_STATUS ] = self.deviceStatus
        self.queryBuffer[POS_FUNCTION ] = self.queryFunction   


        #Add on the delimiter
        self.queryBuffer[POS_ADDR] = self.delimitAddr(self.queryAddr)
        self.queryBuffer[POS_DATA] = self.delimitData(self.queryData)

        #Build the CRC 
        self.queryBuffer[POS_CRC] =  CRC(self.queryBuffer[:-1])

        if self.verbose:
            print self.name , "produced Query Packet:", self.queryBuffer

        return self.queryBuffer
        

    def receiveQueryPacket(self, packet):

        #if directed at me 
        if packet[POS_RECIPIENT] == self.deviceID:
            
            self.queryBuffer = packet
            if self.ultraVerbose:
                print self.name,  "received Query packet:", packet

            self.readQuery()
            self.buildReplyPacket()

            return self.replyBuffer
            
        else:
            if self.ultraVerbose:
                print self.name ,"Packet passed. Expected ID:", self.deviceID, "received  ID:", packet[POS_RECIPIENT]




    def receiveReplyPacket(self, packet):

        #if directed at me 
        if packet[POS_RECIPIENT] == self.deviceID:
            self.replyBuffer= packet

            if self.ultraVerbose:
                print self.name,  "received Reply packet:", packet

            self.readReply()

            if self.replyMatchQuery():

                if self.queryFunction == FN_WRITE:
                    return len(self.replyAddr[1])

                elif self.queryFunction == FN_READ:
                    return (self.replyAddr[1], self.replyData[1])
            

            

    def writeReg(self, device, addr, data):
        self.queryRecipient = device
        self.queryFunction = FN_WRITE
        self.queryAddr = addr
        self.queryData = data

        self.buildQueryPacket()

        return self.queryBuffer

    def readReg(self, device, addr):
        self.queryRecipient = device
        self.queryFunction = FN_READ
        self.queryAddr = addr
        self.queryData = []

        self.buildQueryPacket()

        return self.queryBuffer

    
        


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

    def setQuery(self):
        self.queryBuffer[POS_SENDER ] = self.deviceID
        self.queryBuffer[POS_RECIPIENT ] = self.queryRecipient
        self.queryBuffer[POS_STATUS ] = self.deviceStatus
        self.queryBuffer[POS_FUNCTION ] = self.queryFunction   
        self.queryBuffer[POS_ADDR] = self.queryAddr
        self.queryBuffer[POS_DATA] = self.queryData
        self.queryBuffer[POS_CRC] =  self.queryCrc




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
#RPi.setVerbose()


Ard = sdpDevice('Ard',0x02, STATUS_SLAVE)
#Ard.setVerbose()


RPi.receiveReplyPacket(Ard.receiveQueryPacket(RPi.writeReg(2, [50,40],[21,20])))
RPi.receiveReplyPacket(Ard.receiveQueryPacket(RPi.readReg(2, [50,40])))


##########################################
### Exception class for System Device Protocol

class sdpError(Exception):
    def __init__(self,value):
        self.value=value
    def __str__(self):
        return repr(self.value)
