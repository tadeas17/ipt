#!/usr/bin/env python3.8

import socket
import sys
import os


def err_exit(msg):
    sys.exit(msg)


def find_server(domain, UDP_IP, UDP_PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        msg = 'WHEREIS {}\r\n'.format(domain).encode("ascii")

        udp_sock.sendto(msg, (UDP_IP, UDP_PORT))
        udp_sock.settimeout(30)
        try:
            data, address = udp_sock.recvfrom(4096)
        except socket.timeout:
            err_exit("ERR No answer from {}:{}.\r\n".format(UDP_IP, UDP_PORT))
        res = data.decode('ascii').split()
        if res[0] == "OK":
            ret = res[1].split(":")
            return (ret[0], int(ret[1]))
        else:
            err = ' '.join(res)
            err_exit(err)


def check_arguments(argv):
    if len(argv) != 5 and ((argv[1] != "-n" and argv[3] != "-f") or (argv[1] != "-f" and argv[3] != "-n")):
        err_exit(
            "ERR program parameter\r\n\r\nfileget -n NAMESERVER -f SURL\r\nNAMESERVER - IP adresa a číslo portu jmenného serveru.\r\nSURL - SURL souboru pro stažení. Protokol v URL je vždy fsp .\r\nOba parametry jsou povinné. Jejich pořadí je volitelné.\r\n")

#stahne a ulozi soubor
def download_file(server, domain, server_file):
    msg = "GET {} FSP/1.0\r\nHostname: {}\r\nAgent: xkotta00\r\n\r\n".format(server_file, domain).encode('ascii')
    tst = b'FSP/1.0 Success\r\nLength:51\r\n\r\n'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
        tcp_sock.settimeout(2)
        try:
            tcp_sock.connect(server)
        except ConnectionRefusedError as e:
            print(e)
        except socket.timeout:
            err_exit("ERR No answer from {} - {}:{}.\r\n".format(domain, server[0], server[1]))
        tcp_sock.sendall(msg)
        data = b''
        while not data:
            break
        data = tcp_sock.recv(1024)

        if data[0:15] != b'FSP/1.0 Success':  # osetreni chyb
            res = data.decode('ascii')
            return res

        size = bytearray(b'')
        position = 24
        while True:
            if data[position] == ord('\r'):
                break
            size.append(data[position])
            position += 1
        size = int(size.decode("ascii"))
        data_for_write = data[position + 4:]
        while data:
            data = tcp_sock.recv(1024)
            if not data:
                if len(data_for_write) == size:
                    if "/" in server_file:
                        directory = server_file.rsplit('/', 1)[0]
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                    file = open(server_file, 'wb')
                    file.write(data_for_write)
                    file.close()
                else:
                    for i in range(15):
                        data = tcp_sock.recv(1024)
                        if data:
                            break
                    else:
                        err_exit("Connection list.")
                        pass
            data_for_write += data
        return ''

if __name__ == '__main__':
    check_arguments(sys.argv)
    arg_position = 1
    while arg_position <= 4:
        if sys.argv[arg_position] == "-n":
            arg_position += 1
            nameserver = sys.argv[arg_position].split(":")
            if len(nameserver) != 2:
                err_exit("Error nameserver\r\nNAMESERVER - IP adresa a číslo portu jmenného serveru.\r\n")
            nameserver_addr = nameserver[0]
            nameserver_port = int(nameserver[1])
        elif sys.argv[arg_position] == "-f":
            arg_position += 1
            if sys.argv[arg_position][:6] != "fsp://":
                err_exit("Error surl\r\nSURL - SURL souboru pro stažení. Protokol v URL je vždy fsp .\r\n")
            surl = sys.argv[arg_position][6:].split('/', 1)
            domain, file = surl
        arg_position += 1

    comunication_addr = find_server(domain, nameserver_addr, nameserver_port)
    if file == "*":
        download_file(comunication_addr, domain, "index")
        index = open("index", "r")
        files = index.read().replace('\r', '').split('\n')
        if not files[-1]:
            files.pop()
        index.close()
    else:
        files = [file]
    for file in files:
        res = download_file(comunication_addr, domain, file)
        if res:
            print("Error file {}\r\n{}".format(file, res), file=sys.stderr)



