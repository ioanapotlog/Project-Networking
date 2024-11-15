# Resurse harta:
# https://plotly.com/python/map-configuration/
# https://plotly.com/python/scatter-plots-on-maps/

import socket
import traceback
import random
import time
import json
import sys

import requests as requests

import plotly.graph_objs as go
import plotly.offline as pyo

# socket de UDP
udp_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)

# socket RAW de citire a răspunsurilor ICMP
icmp_recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
# setam timout in cazul in care socketul ICMP la apelul recvfrom nu primeste nimic in buffer
icmp_recv_socket.settimeout(3)

# Bind cu toate interfetele
icmp_recv_socket.bind(("192.168.1.155", 0))

def ip_location(ip):
    token = "5d76217707427a"
    fake_HTTP_header = {
        'referer': 'https://ipinfo.io/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
    }

    try:
        raspuns = requests.get(f"http://ipinfo.io/{ip}?token={token}", headers=fake_HTTP_header)
        if "bogon" not in raspuns.json():
            if raspuns.status_code == 200 and raspuns.content:
                data = raspuns.json()
                oras = raspuns.json()["city"]
                regiune = raspuns.json()["region"]
                tara = raspuns.json()["country"]
                loc = data.get("loc", "").split(',')
                latitude, longitude = loc if len(loc) == 2 else (None, None)
                location_info = f"City: {oras}  Region: {regiune}  Country: {tara}"
                with open('location_data_example.txt', 'a') as f:
                    f.write(location_info + '\n')
                print(f"City: {oras}  Region: {regiune}  Country: {tara}")
                return oras, regiune, tara, latitude, longitude
            else:
                print(f"Failed to get location info for {ip}: {raspuns.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching location info for {ip}: {e}")
    return None, None, None, None, None


def traceroute(ip, port):
    print(f"traceroute to {ip}, 64 hops max")
    if not('0' <= ip[len(ip) - 1] <= '9'):
        ip = socket.gethostbyname(ip)

    # setam TTL in headerul de IP pentru socketul de UDP
    TTL = 1
    destination_reached = False

    locatii = []

    while not destination_reached and TTL <= 64:
        counter = 3
        while counter > 0:
            udp_send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, TTL)

            # trimite un mesaj UDP catre un tuplu (IP, port)
            start_time = time.time()
            udp_send_sock.sendto(b'maricica', (ip, port))
            try:
                data, addr = icmp_recv_socket.recvfrom(63535)
                end_time = time.time()
                # Calculeaza RTT in milisecunde
                rtt = (end_time - start_time) * 1000

                # Primii 20 de bytes fac parte din IPv4 Header
                icmp_header = data[20:28]
                icmp_type = icmp_header[0]
                if icmp_type == 11 and counter == 3:
                    print(f"{TTL}  {addr[0]}  {rtt:.2f} ms", end="  ")
                elif icmp_type == 11 and counter != 3:
                    print(f"{rtt:.2f} ms", end="  ")
                elif icmp_type == 3 and addr[0] == ip and counter == 3:
                    print(f"{TTL}  {addr[0]}  {rtt:.2f} ms", end="  ")
                    destination_reached = True
                else:
                    print(f"{rtt:.2f} ms", end="  ")
                    destination_reached = True

                if counter == 1:
                    print()
                    oras, regiune, tara, latitude, longitude = ip_location(addr[0])
                    locatii.append((addr[0], oras, regiune, tara, latitude, longitude))
            except socket.timeout:
                if counter == 3:
                    print(f"{TTL}  *", end="  ")
                elif counter == 2:
                        print("*", end="  ")
                else:
                    print("*", end="\n")
            except Exception as e:
                print("Socket timeout ", str(e))
                print(traceback.format_exc())
                break
            counter = counter - 1

        TTL = TTL + 1
    with open('location_data_example.txt', 'a') as f:
        f.write('\n')

    udp_send_sock.close()
    icmp_recv_socket.close()
    print(addr)
    return locatii



random_port = random.randint(33434, 33534)
#traceroute('8.8.8.8', random_port)
#traceroute('google.com', random_port)
#traceroute('dns.google.com', random_port)

# Asia (China)
#traceroute('m.airchina.com.cn', random_port)
#traceroute('138.113.148.29', random_port)

# Australia
#traceroute('ugg.com.au', random_port)
#traceroute('23.227.38.70', random_port)

# Africa
#traceroute('axxess.co.za', random_port)
#traceroute('172.66.40.132', random_port)

ip = sys.argv[1]
locatii = traceroute(ip, random_port)
# print(locatii)

latitudini = []
longitudini = []
texts = []

for locatie in locatii:
    if locatie[3] is not None:
        latitudini.append(float(locatie[4]))
        longitudini.append(float(locatie[5]))
        texts.append(f"{locatie[1]}, {locatie[2]}, {locatie[3]}")

trace = go.Scattergeo(
    lon=longitudini,
    lat=latitudini,
    mode='lines+markers',
    marker={'size':8, 'color':'red'},
    line={'width':2, 'color':'green'},
    text=texts
)

layout = go.Layout(
    title='Traceroute Map',
    geo={'showland':True,}
)

fig = go.Figure(data=[trace], layout=layout)

pyo.plot(fig, filename='traceroute_map.html')