import socket
import threading
import json
import time

def citeste_configul(filename):
    f = open(filename, 'r')
    data_json = json.load(f)
    f.close()
    return data_json

def handle_client(conn, configData):
    print("[SERVER] Thread nou pornit pentru clientul curent.")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print("[SERVER] Clientul s-a deconectat (conexiune inchisa).")
                break
                
            mesaj_primit = json.loads(data.decode('utf-8'))
            print("[SERVER] Am primit comanda:", mesaj_primit)
            
            if mesaj_primit.get("comanda") == "listare":
                lista_servicii = []
                for s in configData['servicii']:
                    lista_servicii.append(s['numeService'])
                    
                raspuns = {"servicii": lista_servicii}
                conn.sendall(json.dumps(raspuns).encode('utf-8'))
        except Exception as e:
            print("[SERVER] Eroare pe threadul clientului:", e)
            break
            
    conn.close()

def start_Server(port, configData):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('0.0.0.0', port))
    serverSocket.listen(5)
    print("[SERVER] Astept conexiuni pe portul " + str(port))
    while True:
        conn, adresa = serverSocket.accept()
        print("[SERVER] S-a conectat un nod de la adresa: ", adresa)
        
        thread_client = threading.Thread(target=handle_client, args=(conn, configData))
        thread_client.start()

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
                
                while True:
                    comanda_user = input("Scrie o comanda (ex: list): ")
                    if comanda_user == "list":
                        mesaj_json = {"comanda": "listare"}
                        sock_client.sendall(json.dumps(mesaj_json).encode('utf-8'))
                        
                        raspuns_server = sock_client.recv(1024)
                        if not raspuns_server:
                            print("[CLIENT] Nodul a cazut / Serverul a inchis conexiunea.")
                            sock_client.close()
                            break
                        
                        print("[CLIENT] Am primit raspuns:", raspuns_server.decode('utf-8'))
                    else:
                        print("Comanda necunoscuta. Incearca 'list'.")
                        
            except Exception as e:
                print("[CLIENT] Eroare / Conexiunea a picat:", e)
                sock_client.close()
        
        print("[CLIENT] Nu am gasit noduri active. Astept 3 secunde...")
        time.sleep(3)

if __name__ == '__main__':
    configData = citeste_configul('config.json')
    my_port = configData['portLocal']
    noduriProx = configData['noduriProximitate']
    print("=== Pornire Nod ===")
    
    t_server = threading.Thread(target=start_Server, args=(my_port, configData))
    t_server.start()
    
    time.sleep(1)
    
    t_client = threading.Thread(target=startClient_logic, args=(noduriProx,))
    t_client.start()
