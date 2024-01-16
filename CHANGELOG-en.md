# Change Log

### v5.2.0:
##### New Features
    1. Added `--php` parameter. By default, it is judged based on the URL set by --url whether the .php suffix uses the PHP connection method. In special cases, you can manually use --php to specify the PHP connection method.

### v5.1.0:
##### New Features
    1. Add `--request-template` parameter to set request template to avoid traffic detection
##### Fix
    1. Updated documentation for `-r` parameter

### v5.0.2:
##### Enhancement
    1. Support for php < 5.4 (special thanks to @me1ons for issue #82)
#####  Fix
    1. Fix the situation where php does not support `php://input` in some environments and cannot be used normally

### v5.0.1:
##### Enhancement
    1. Java improves compatibility through reflection, such as tomcat10 cannot be used (special thanks to @BeichenDream for PR)
    2. Use class static variables instead of `application` global variables to improve compatibility (special thanks to @c0ny1 for his suggestion)
##### Fix
    1. When repairing the abnormal connection, it failed to exit normally
    2. Fix exception handling logic of `blv_decode` (issue #73)

### v5.0.0:
##### New Features
    1. Both java/chsarp/php use the `BLV (Byte-Length-Value)` data structure for transmission, officially removing the random header technology that has been used since the first version was released three years ago
    2. Under the `BLV` data structure, implement a request retry mechanism, which can overcome harsh environments (such as server instability, load balancing, and only some servers are deployed on some machines, etc.)
    3. A new golang server is added, which supports starting a new process to provide services, in order to solve the more severe special environment :) (Special thanks to @M09Ic for solving io blocking and other problems)
    4. Add `-R/--force-redirect` parameter option to solve the `islocal()` detection for java, resulting in the service that cannot be forwarded to the local machine, and added the force forwarding function
    5. Add `--max-retry` parameter option, which can control the number of retries of Neoreg
##### Enhancement
    1. Simplify the use, `tunnel.jsp(x)` has achieved the best compatibility, and this version starts to remove `tunnel_compatibility.jsp(x)` 2. Java uses Gzip compression instead, and jsp(x) is compressed, and the file 30% smaller in size
    3. PHP modified the position of `set_time_limit(0)` to make the request time other than CONNECT more stable and reliable
    4. Java has set the connect timeout to 3 seconds to ensure stability and improve concurrent speed under extreme network conditions (special thanks to @c0ny1 for his solution)
    5. csharp set the connect timeout to 2 seconds to ensure stability and improve concurrent speed under extreme network conditions
    6. Client log output redesign and optimization
##### fix
    1. The banner is changed to base64, which makes `-f FILE` more usable
    2. Fix the problem that php cannot work normally when the downstream traffic is too large
    3. Fix the failure of php to output other subsequent content normally due to `exit`
    4. Fix `-k KEY` special key can not be used normally

### v4.0.0:
    Thanks to @BeichenDream for his contribution to the project, `KTLV (Key-Type-Length-Value)` is provided to hide the random Header design, and in the implementation stage (refer to PR#60)
    Later, a new transmission scheme `BLV` more suitable for Neoreg was designed, and it was released before the v4 version

### v3.8.1:
    Server: java side, fix the problem that neoreg has no echo under listener
    Server: java side, intranet forwarding supports https (ignoring certificate security @BeichenDream PR)

### v3.8.0:
    Server: Optimize php, remove the `?>` end, avoid adding `\n` at the end when other editors save
    Client: Add debug information for http requests to facilitate debugging and analysis
    Client: Add the `--extract expr` parameter to deal with the environment where the server dynamically appends content before and after, manually set the extraction BODY content, if the server returns <p>base64data </p>, you can use `--extract '<p>REGBODY< /p>'` to deal with

### v3.7.0:
    Client: Added `--cut-left/--cut-right` parameters to adjust the offset of the body according to the special environment (such as Confluence)

### v3.6.0:
    Server: aspx/ashx added support for intranet forwarding function (reference -r)

### v3.5.0:
    Server: jsp(x) uses classloader instead to solve the problem that jdk syntax is not backward compatible and cannot run normally (compatible with jdk >= 1.5) (special thanks to @c0ny1 for the PR solution)
    Server: jsp(x) repair websphere environment, java.lang.NegativeArraySizeException error of FORWARD

### v3.4.0:
    Clinet: Add the `--php-connect-timeout` parameter to solve the problem that the port connection status cannot be judged due to the slow response of PHP on Windows

### v3.3.0:
    Client: Enhance the printing information during data transmission, which is convenient for debugging
    Client: Fix the special case of `FORWARD` request, the data type is wrong, resulting in the inability to obtain the body
    Server: jsp(x) fixed forwarding compatibility issues when using HTTP/1.0 in Nginx

### v3.2.1:
    Server: jsp(x) fixes the error that cannot be compiled normally in the Jboss environment

### v3.2.0:
    Fix bugs that occurred when solving high-bandwidth, improve stability, and increase the transmission speed of high-bandwidth by more than 10 times
    Client: Add the `--max-read-size` parameter to control the maximum length of the response packet of the `READ` request
    Client: Fix the problem that python `socket.send()` cannot be written completely
    Client: Fix the accuracy of debugging information requested by `FORWARD` in INFO print mode
    Client: Release the `--read-buff` parameter limit and set the default value to 7kb
    Server: aspx/ashx/jsp(x) Solve the problem that the socket IO cannot be updated immediately when the download traffic is too large (Special thanks to Godzilla author @BeichenDream for the solution)
    Server: jsp(x) Fix the problem that base64 content is truncated when the download traffic is too large
    Server: jsp(x) fixes the limitation of releasing POST body, greatly improving the request speed of `FORWARD`

### v3.1.0:
    Server: jsp(x) fixes performance issues while maintaining compatibility, greatly improves the speed of `READ` requests (special thanks to @XinRoom for the PR solution)

### v3.0.0
    Client: Client: Only verify php cookies
    Server: aspx/ashx/jsp/jspx Use global variables to replace `Session`, and no longer rely on Cookie (Special thanks to @c0ny1 for the solution)

### v2.6.0
    Client: Add the `--write-interval` parameter to adjust the FORWARD request interval
    Client: Readjust `--read-interval` default value is 300
    Clinet: Add `--target` parameter to realize port forwarding function

### v2.5.1
    Client: When the Session expires, automatically append cookies to continue running
    Server: Fix jsp(x) find java.nio.ByteBuffer.clear() method problem in some low jdk versions

### v2.5.0
    Client: When detecting that the socks connection is closed, the session is automatically ended, reducing a lot of request traffic
    Client: Optimized the output of exception information, and has been able to capture exceptions caused by high concurrency
    Client: The document adds operating suggestions for the Mac OSX environment
    Client: Adjust the default settings, the network traffic is reduced by about 46%
    Client: Fix `--file` read complex file encoding escape problem 

### v2.4.1
    Added session expiration reminder
    Adjust `askGeorg` detection request, timeout is 10 seconds

### v2.4.0
    Fix non-apache environment BUG [php]

### v2.3.2
    Fix `--local-dns` commit

### v2.3.1
    Fix the BUG in response to error messages in python3
    Optimized the error message reminder

### v2.3.0
    jsp(x) Restore the `trimDirectiveWhitespaces` set version `tunnel_compatibility.jsp(x)` that is compatible with the lower version of jdk
    jsp(x) `response.getOutputStream()` replaced with ʻout.write()` to solve the performance and stability problems caused by error messages on websphere
    Turn off color terminal printing on Windows

### v2.2.0
    Fix the wrong encoding problem of `--file` file
    Optimize the transmission rate
    Intranet forwarding, no forwarding locally

### v2.1.0
    Support HTTP forwarding, coping with load balancing environment
    Optimize the output printing information
    Fix `-H` setting bug

### v2.0.0
    Realize single-session multiple TCP sessions, and solve the unavailability caused by only supporting single-session HTTP communication in some environments
    Support multiple URL request paths of the same server to avoid excessive single-path access frequency
    Support custom server HTTP response code
    Modified some commands to GET, which is closer to normal requests
    Remove blank lines and remove some features
    Support DNS resolution on the server, and use (local DNS resolution with `--local-dns`) to optimize the output of error messages. Modify the directory name scripts / => templates / and neoreg_server / => neoreg_servers /
    Support for removing socks 4
    Removable javascript tunnel support

### v1.5.0
    Fix the problem that php>= 7.1 version cannot be used normally
    Fix the problem of high CPU usage in php environment (special thanks to @junmoxiao for the support)
    tunnel.nosocket.php 替换 tunnel.php

### v1.4.0
    jsp(x) does not rely on the built-in `base64` method, compatible with jdk9 and above
    jsp(x) remove `trimDirectiveWhitespaces="true"` to be compatible with versions less than jdk8
    tunnel.tomcat.5.jsp(x) has been removed

### v1.3.0
    Fixed `--cookie JSESSIONID` conflict, unavailable in load balancing environment

### v1.2.0
    Added `-k debug_all (or debug_base64|debug_headers_key|debug_headers_values)`, Easy to debug

### v1.1.0
    Added jspx support
