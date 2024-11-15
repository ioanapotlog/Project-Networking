# inspirat de howCode - YouTube si codul din curs
import socket
import time
from scapy.layers.dns import DNS, DNSRR, UDP
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading
    
stopEvent = threading.Event()

typeDict =  {
1: "A",
2: "NS",
5: "CNAME",
12: "PTR",
15: "MX",
28: "AAAA",
16: "TXT",
33: "SRV",
6: "SOA"
}

records = {
"A": {},
"PTR": {},
"MX": {},
"NS": {},
"CNAME": {}
}
    
def loadRecords():
    with open("records.txt", "r") as f:
        for line in f:
            if line[0] == "#":
                continue

            record = line.strip().split()

            if not record:
                continue

            recordType = record[0]
      
            if recordType == "A":
                name, address = record[1], record[2]
                records["A"][name] = address
            
            elif recordType == "CNAME":
                name, alias = record[1], record[2]
                records["CNAME"][name] = alias
            
            elif recordType == "MX":
                name, mailServer, priority = record[1], record[2], int(record[3])
                records["MX"][name] = (mailServer, priority)
            
            elif recordType == "PTR":
                ptrName, domain_name = record[1], record[2]
                records["PTR"][ptrName] = domain_name
            
            elif recordType == "NS":
                name, nsServer = record[1], record[2]
                if name not in records["NS"]:
                    records["NS"][name] = []
                records["NS"][name].append(nsServer)
 
def buildResponse(packet, dnsAnswer):
    if dnsAnswer:
        return DNS(
            id = packet[DNS].id, 
            qr = 1,              # 1 pentru raspuns, 0 pentru query
            aa = 0,              # "Authoritative Answer"
            rcode = 0,           # 0, nicio eroare
            qd = packet.qd,      # request-ul original
            ad = 1,              # "Authentic Data"
            an = dnsAnswer)      # obiectul de reply
    else:
        return DNS(
            id = packet[DNS].id,
            qr = 1,
            aa = 0,
            rcode = 0,
            ad = 1,
            qd = packet.qd)

def answerQ(qType, query):
    answer = resolve(qType, query)
    if answer:
        return DNSRR(
            rrname = query,
            ttl = 330,
            type = qType,            
            rclass = "IN",
            rdata = answer)
    else:
        return None

def resolve(qType, query):
    try:
        return records[qType][query]
    except:
        return None

def resolveAndRespond(simpleUdp, data, sourceAddress):
    # converitm payload-ul in pachet scapy
    dnsPacket = DNS(data)
    dns = dnsPacket.getlayer(DNS)

    udpPacket = UDP(data)
    udp = udpPacket.getlayer(UDP)

    qType = typeDict[dns.qd.qtype]
    query = dns.qd.qname.decode("utf-8")
    if dns and dns.opcode == 0: # dns QUERY
        dnsAnswer = answerQ(qType, query)
        dnsResponse = buildResponse(dnsPacket, dnsAnswer).compress() 
        simpleUdp.sendto(bytes(dnsResponse), sourceAddress) # trimitem raspunsul
        
        log(datetime.now())
        log(f"From {sourceAddress} got: ")
        log(dnsPacket.summary() + "type: " + qType)
        
        # afisam raspunsul
        log("Response:")
        log(dnsResponse.summary())
        log("-------------------")

def serverRun():
    loadRecords()

    simpleUdp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
    address = "192.168.0.113"
    port = 53
    serverAddress = (address, port)
    simpleUdp.bind(serverAddress) # server pe ip specific, port 53

    print("DNS server started on port 53.")

    with ThreadPoolExecutor(max_workers=15) as executor:
        while not stopEvent.is_set():
            try:
                data, sourceAddress = simpleUdp.recvfrom(512)
                executor.submit(resolveAndRespond, simpleUdp, data, sourceAddress)
                simpleUdp.settimeout(1)
            except socket.timeout:
                continue

    simpleUdp.close()

def log(msg):
    with open("dnsLog.txt", "a") as f:
        f.write(str(msg) + "\n")

def addRecord():
    recordType = input("Enter record type (A, CNAME, MX, PTR, NS): ").strip().upper()
    if recordType not in records.keys():
        print("Invalid record type.")
        return
    with open ("records.txt", "a") as recordsFile:
        name = input("Enter name: ").strip()
        if recordType == "A":
            address = input("Enter address: ").strip()
            recordsFile.write("A\t" + name + "\t" + address + "\n")
            print("Record added.")
        elif recordType == "CNAME":
            alias = input("Enter alias: ").strip()
            recordsFile.write("CNAME\t" + name + "\t" + alias + "\n")
            print("Record added.")
        elif recordType == "MX":
            mailServer = input("Enter mail server: ").strip()
            priority = input("Enter priority: ").strip()
            recordsFile.write("MX\t" + name + "\t" + mailServer + "\t" + priority + "\n")
            print("Record added.")
        elif recordType == "PTR":
            domainName = input("Enter domain name: ").strip()
            recordsFile.write("PTR\t" + name + "\t" + domainName + "\n")
            print("Record added.")
        elif recordType == "NS":
            nsServer = input("Enter NS server: ").strip()
            recordsFile.write("NS\t" + name + "\t" + nsServer + "\n")
            print("Record added.")

def userInput():
    time.sleep(1)
    while not stopEvent.is_set():
        cmd = input("Enter command: (1)Add Record   (0)Stop Server:")
        if cmd == "0":
            print("Shutting down the server...")
            stopEvent.set()
        elif cmd == "1":
            addRecord() # recordurile sunt valabile de urmatoarea data cand pornim serverul
            
def main():
    serverThread = threading.Thread(target=serverRun)
    serverThread.start()

    userThread = threading.Thread(target=userInput)
    userThread.start()

    serverThread.join()
    userThread.join()



if __name__ == "__main__":
    main()