# TCP Server
import socket
import logging
import time

logging.basicConfig(format=u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level=logging.NOTSET)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)

# numarul port-ului la care sa asculte
port = 10000
# server-ul va asculta pe toate interfetele disponibile la retea
adresa = '0.0.0.0'
# combina adresa si port-ul => adresa server-ului
server_address = (adresa, port)
sock.bind(server_address)
logging.info("Serverul a pornit pe %s si portul %d", adresa, port)
# Asteapta conexiuni (5 conexiuni maxim)
sock.listen(5)

try:
    # "while" care asteapta conexiuni
    while True:
        logging.info('Asteptam conexiui...')
        # accepta conexiunea
        conexiune, address = sock.accept()
        logging.info("Handshake cu %s", address)
        time.sleep(2)

        # primeste date de la client
        while True:
            data = conexiune.recv(1024)
            if len(data) > 0:
                logging.info('Content primit: "%s"', data)
                # se trimite un mesaj de confimare inapoi la client
                conexiune.send(b"Server a primit mesajul: " + data)

finally:
    conexiune.close()
    logging.info('closing socket')
    sock.close()


# Comunicare TCP
# 1. Handshake = realizarea conexiunii dintre Client si Server
# 2. Transmiterea datelor = trimiterea si primirea datelor intre Client si Server
# 3. Terminare = inchiderea conexiunii