# Searches shodan for hosts defined by IP blocks in CIDR notation
# Input is a file with an IP block in each line
# Example: > cat file.txt
#   192.168.10.0/24
#   192.163.12.0/24

import shodan
import time
import json
import sys
import ipaddress

SHODAN_API_KEY = "YOUR_API_KEY"

if len(sys.argv) != 2:
    print("Usage:",sys.argv[0],"file")
    print("- file: File containing a list of IP blocks in CIDR notation")
    exit()

fileName = sys.argv[1]

cidrs = []

try:
    with open(fileName, "r") as f:
        for line in f.readlines():
            cidrs.append(line.strip())
except:
    print("ERRO! Nao foi possivel ler o arquivo:",sys.exc_info()[0])
    exit(1)

hosts = {}
for cidr in cidrs:
    net = ipaddress.IPv4Network(cidr, False)
    for host in net.hosts():
        hosts.setdefault(cidr, []).append(host.exploded)

# DEBUG
#hosts = { "177.152.120.0/22": [ "177.152.120.9" ] }

api = shodan.Shodan(SHODAN_API_KEY)

print("cidr;ip;last_update;isp;os;ports;vulns")

for cidr in hosts.keys():
    for ip in hosts[cidr]:
        try:
            host = api.host(ip)

            org = host.get('org', 'None')
            lastUpdate = host.get('last_update', 'None')
            isp = host.get('isp', 'None')
            os = host.get('os', 'None')
            ports = ';'.join(str(e) for e in host.get('ports', ['None']))
            vulns = ';'.join(str(e) for e in host.get('vulns', ['None']))

        except shodan.APIError as e:
            org = lastUpdate = isp = os = ports = vulns = 'Not found'
            
        print("\"{}\";\"{}\";\"{}\";\"{}\";\"{}\";\"{}\";\"{}\";".format(cidr, ip, lastUpdate, isp, os, ports, vulns))
