# Change Log

### v5.2.0:
##### 新特征
    1. 新增 `--php` 参数，默认根据 --url 设置的 URL 判断是否 .php 后缀使用 PHP 连接方式，特殊情况下可手工使用 --php 指定为 PHP 的连接方式

### v5.1.0:
##### 新特征
    1. 新增 `--request-template` 参数，用于设置请求模板，规避流量检测
##### 修复
    1. 更新 `-r` 参数的文档说明

### v5.0.2:
##### 增强
    1. 支持 php < 5.4 版本的 (特别感谢 @me1ons 的issue #82)
##### 修复
    1. 修复 php 在部分环境下，不支持 `php://input` 导致无法正常使用的情况

### v5.0.1:
##### 增强
    1. java 通过反射的方式，提高兼容性, 如tomcat10无法使用 (特别感谢 @BeichenDream 的PR)
    2. 使用 class 的静态变量替代 `application` 全局变量，提高兼容性 (特别感谢 @c0ny1 的建议)
##### 修复
    1. 修复异常连接时，未能正常退出
    2. 修复 `blv_decode` 的异常处理逻辑 (issue #73)

### v5.0.0:
##### 新特征
    1. java/chsarp/php 都改用 `BLV (Byte-LengthOffset-Value)` 数据结构进行传输，正式移除三年前发布第一版沿用至今的随机 Header 技术
    2. 在 `BLV` 数据结构下，实现请求重试机制，可克服恶劣环境 (如服务器不稳定、负载均衡下只在部分机器上部署了服务端等特殊情况)
    3. 新增了 golang 的服务端，支持另起进程提供服务，为解决更加恶劣的特殊环境 :)  (特别感谢 @M09Ic 解决io阻塞等问题)
    4. 新增 `-R/--force-redirect` 参数选项，为 java 解决 `islocal()` 检测，导致无法转发到本机的服务，添加了强制转发功能
    5. 新增 `--max-retry` 参数选项，可控制 Neoreg 的重试次数
##### 增强
    1. 简化使用，`tunnel.jsp(x)` 已实现最佳兼容性，此版本开始移除 `tunnel_compatibility.jsp(x)`
    2. java 改用 Gzip 压缩，对 jsp(x) 进行压缩，文件体积缩小了 30%
    3. php 修改了 `set_time_limit(0)` 的位置，使得 CONNECT 以外的请求时间更加稳定可靠
    4. java 设置了 connect timeout 为 3 秒，保证稳定性的同时，在极端网络下提升并发速度 (特别感谢 @c0ny1 的解决方案)
    5. csharp 设置了 connect timeout 为 2 秒，保证稳定性的同时，在极端网络下提升并发速度
    6. 客户端日志输出重新设计与优化
##### 修复
    1. banner 改用 base64，使得 `-f FILE` 可用性更高
    2. 修复 php 下行流量过大时，无法正常运作的问题
    3. 修复 php 因 `exit` 导致无法正常输出后续的其它内容
    4. 修复 `-k KEY` 特殊 Key 无法正常使用的情况

### v4.0.0:
    感谢 @BeichenDream 对项目的贡献，提供了 `KTLV (Key-Type-Length-Value)` 隐去随机 Header 设计，并在实现阶段中 (参考 PR#60)。
    后来设计出更适合 Neoreg 的新传输方案 `BLV`，并先于 v4 版本完成实现发布

### v3.8.1:
    Server: java 端，修复在 listener 下 neoreg 没有回显问题
    Server: java 端，内网转发支持 https 了 (忽略证书安全 @BeichenDream 的 PR)

### v3.8.0:
    Server: 优化 php, 删除 `?>` 结尾，避免其它编辑器保存时末尾添加`\n`
    Client: 增加 http 请求时的 debug 信息, 方便调试分析
    Client: 增加 `--extract expr` 参数，应对服务端动态前后追加内容的环境，手动设置提取 BODY 内容, 如服务端返回 <p>base64data  </p>, 则可用 `--extract '<p>REGBODY</p>'` 应对

### v3.7.0:
    Client: 新增 `--cut-left/--cut-right` 参数，可根据特殊环境进行调整body的偏移 (如Confluence)

### v3.6.0:
    Server: aspx/ashx 新增支持内网转发功能 (参考 -r)

### v3.5.0:
    Server: jsp(x) 改用 classloader 的方式，解决 jdk 语法不向下兼容导致无法正常运行的问题 (兼容 jdk >= 1.5) (特别感谢 @c0ny1 的 PR)
    Server: jsp(x) 修复 websphere 环境，FORWARD 的 java.lang.NegativeArraySizeException 错误

### v3.4.0:
    Clinet: 增加 `--php-connect-timeout` 参数，解决 Windows 上 PHP 响应较慢导致的端口连接状态无法判断问题

### v3.3.0:
    Client: 增强了数据传输时的打印信息，便于调试
    Client: 修复 `FORWARD` 请求，数据类型错误，导致无法获取 body 的特殊情况
    Server: jsp(x) 修复在 Nginx 使用 HTTP/1.0 时转发兼容性问题

### v3.2.1:
    Server: jsp(x) 修复在 Jboss 环境下，无法正常编译的错误

### v3.2.0:
    修复解决高宽带时出现的 BUG 提高稳定性，并提升10倍以上高宽带的传输速度
    Client: 添加 `--max-read-size` 参数控制 `READ` 请求的响应包最大长度
    Client: 修复 python 的 `socket.send()` 不能完全写入的问题
    Client: 修复 INFO 打印模式下，`FORWARD` 请求的调试信息打印信息的准确性
    Client: 释放 `--read-buff` 参数限制，并设置默认值为 7kb
    Server: aspx/ashx/jsp(x) 解决下载流量过大时，无法即时更新 socket IO 问题 (特别感谢 Godzilla 作者 @BeichenDream 的解决方案)
    Server: jsp(x) 修复下载流量过大时，base64 内容被截断问题
    Server: jsp(x) 修复释放 POST Body 的限制，大幅提升 `FORWARD` 请求速度

### v3.1.0:
    Server: jsp(x) 在保持兼容性的前提下，修复性能问题，大幅提高 `READ` 请求速度 (特别感谢 @XinRoom 的 PR 解决方案)

### v3.0.0
    Client: 仅对 php 的 Cookie 进行验证
    Server: aspx/ashx/jsp/jspx 使用全局变量替代了 Session, 已不再依赖 Cookie (特别感谢 @c0ny1 的解决方案)

### v2.6.0
    Client: 增加 `--write-interval` 参数，可调整 FORWARD 请求间隔
    Client: 重新调整 `--read-interval` 默认值为 300
    Clinet: 增加 `--target` 参数，实现端口转发功能

### v2.5.1
    Client: 当 Session 过期时，自动追加 Cookie 继续运行
    Server: 修复 jsp(x) 在部分 jdk 低版本中找不到 java.nio.ByteBuffer.clear() 方法问题

### v2.5.0
    Client: 检测 socks 连接已关闭，则自动结束会话，减少大量请求流量
    Client: 优化了异常信息输出，已能捕获高并发产生的异常
    Client: 文档新增 Mac OSX 环境的运行建议
    Client: 调整默认设置，流量减少约 46%
    Client: 修复 `--file` 读取复杂文件编码转义问题

### v2.4.1
    添加 Session 过期提示
    调整 `askGeorg` 检测请求，timeout 为 10 秒

### v2.4.0
    修复非 apache 的环境 BUG [php]

### v2.3.2
    修复 `--local-dns` 参数注释

### v2.3.1
    修复 python3 中 response 错误信息提醒 BUG
    优化了错误信息提醒

### v2.3.0
    jsp(x) 恢复兼容低版本 jdk 的 `trimDirectiveWhitespaces` 设置版本 `tunnel_compatibility.jsp(x)`
    jsp(x) 的 `response.getOutputStream()` 替换成 `out.write()` 解决 websphere 上错误信息导致的性能与稳定性问题
    关闭 Windows 上的彩色终端打印

### v2.2.0
    修复 `--file` 文件的错误编码问题
    优化传输速率
    内网转发，本地即不进行转发

### v2.1.0
    支持内网转发，应对负载均衡环境
    优化输出打印信息
    修复 `-H` 设置 BUG

### v2.0.0
    实现单 Session 多 TCP 会话，解决部分环境仅支持单 Session HTTP 通讯导致的无法使用
    支持同服务器多 URL 的请求路径，避免单路径访问频率过高
    支持自定义服务端的 HTTP 响应码
    修改了部分指令为 GET , 更接近正常请求
    去除空行与去除部分特征
    支持服务端的 DNS 解析，并默认使用 (使用本地 DNS 解析用 `--local-dns`)
    优化了错误信息输出
    修改了目录名称 scripts/ => templates/ 和 neoreg_server/ => neoreg_servers/
    移除 socks4 的支持
    移除 javascript tunnel 支持

### v1.5.0
    修复 php >= 7.1 版本，无法正常使用的问题
    修复 php 环境高占用 CPU 的问题  (特别感谢 @junmoxiao 提供的支持)
    tunnel.nosocket.php 替换 tunnel.php

### v1.4.0
    jsp(x) 不依赖内置 `base64` 方法，兼容 jdk9 及以上版本
    jsp(x) 移除 `trimDirectiveWhitespaces="true"` 兼容小于 jdk8 版本
    tunnel.tomcat.5.jsp(x) 已移除

### v1.3.0
    修复 `--cookie  JSESSIONID` 冲突，负载均衡环境，服务端找不到 session 无法使用问题

### v1.2.0
    新增 `-k debug_all (or debug_base64|debug_headers_key|debug_headers_values)` 时，关闭随机混淆，方便调试

### v1.1.0
    新增 jspx 的支持
