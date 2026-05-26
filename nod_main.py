import socket
import threading
import json
import time

def citeste_configul(filename):
    f = open(filename, 'r')
    data_json = json.load(f)
    f.close()
    return data_json

def start_Server(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('0.0.0.0', port))
    serverSocket.listen(5)
    print("[SERVER] Astept conexiuni pe portul " + str(port))
    while True:
        conn, adresa = serverSocket.accept()
        print("[SERVER] S-a conectat un nod de la adresa: ", adresa)
        conn.sendall(b"Salut, connection OK\n")
        conn.close()


def startClient_logic(lista_noduri):
    while True:
        for nod in lista_noduri:
            parts = nod.split(':')
            ip = parts[0]
            port_dest = int(parts[1])
            try:
                print(f"[CLIENT] Incerc sa ma conectez la {ip}:{port_dest}...")
                sock_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock_client.connect((ip, port_dest))
                print("[CLIENT] M-am conectat cu succes la " + nod)
                
                data = sock_client.recv(1024)
                print("[CLIENT] Primit de la server: " + data.decode('utf-8'))
                
                sock_client.close() 
            except Exception as e:
                pass
        
        
        print("[CLIENT] Nu am gasit noduri active. Astept 3 secunde...")
        time.sleep(3)


if __name__ == '__main__':
    configData = citeste_configul('config.json')
    my_port = configData['portLocal']
    noduriProx = configData['noduriProximitate']
    print("=== Pornire Nod ===")
    
    t_server = threading.Thread(target=start_Server, args=(my_port,))
    t_server.start()
    
    time.sleep(1)
    
    t_client = threading.Thread(target=startClient_logic, args=(noduriProx,))
    t_client.start()
