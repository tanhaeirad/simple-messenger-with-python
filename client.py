import socket

host = '127.0.0.1'
port = 12345
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((host, port))

while True:
    message = input()
    s.sendall(message.encode('ascii'))
    data = s.recv(1024)
    data = str(data, 'utf-8')
    if data == " ": data = ""
    print(data)
