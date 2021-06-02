# Change Log

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
