# TCP Client
import socket
import logging
import time
import sys

logging.basicConfig(format=u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level=logging.NOTSET)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)

# adresa si portul Server-ului
port = 10000
adresa = 'localhost'
server_address = (adresa, port)
mesaj = "Buna, Maricica! Ce mai faci?"

try:
    # Clientul se conecteaza la Server
    logging.info('Handshake cu %s', str(server_address))
    sock.connect(server_address)

    while True:
        # Clientul trimite un mesaj Server-ului la fiecare 3 secunde
        time.sleep(3)
        sock.send(mesaj.encode('utf-8'))
        # Asteapta sa primeasca date de la server
        data = sock.recv(1024)
        if len(data) > 0:
            logging.info('Content primit: "%s"', data)

finally:
    logging.info('closing socket')
    sock.close()