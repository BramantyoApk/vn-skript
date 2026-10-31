import sys
import socket
import struct

def rcon_command(host, port, password, command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15.0)
    try:
        sock.connect((host, port))
        
        # 1. Authenticate (Type 3)
        req_id = 1
        auth_payload = password.encode('utf-8')
        packet = struct.pack('<iii', len(auth_payload) + 10, req_id, 3) + auth_payload + b'\x00\x00'
        sock.sendall(packet)
        
        raw_len = sock.recv(4)
        if len(raw_len) < 4:
            return "Failed to read auth response length"
        resp_len = struct.unpack('<i', raw_len)[0]
        auth_resp = sock.recv(resp_len)
        auth_req_id = struct.unpack('<i', auth_resp[0:4])[0]
        if auth_req_id == -1:
            return "RCON Authentication failed"
            
        # 2. Send Command (Type 2)
        req_id = 2
        cmd_payload = command.encode('utf-8')
        packet = struct.pack('<iii', len(cmd_payload) + 10, req_id, 2) + cmd_payload + b'\x00\x00'
        sock.sendall(packet)
        
        raw_len = sock.recv(4)
        if len(raw_len) < 4:
            return ""
        resp_len = struct.unpack('<i', raw_len)[0]
        cmd_resp = sock.recv(resp_len)
        # Body starts after req_id (4) + type (4)
        body = cmd_resp[8:-2].decode('utf-8', errors='replace')
        return body
    except Exception as e:
        return f"RCON Error: {e}"
    finally:
        sock.close()

if __name__ == "__main__":
    cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "list"
    result = rcon_command("127.0.0.1", 25575, "storydev", cmd)
    if result:
        print(result)
