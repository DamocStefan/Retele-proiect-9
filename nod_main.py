import socket
import threading
import json
import time
import subprocess
import os

stare_servicii = {}

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

            elif mesaj_primit.get("comanda") == "status":
                nume = mesaj_primit.get("numeService")
                if nume in stare_servicii:
                    raspuns = {"rezultat": stare_servicii[nume]}
                else:
                    raspuns = {"eroare": "Serviciul '" + str(nume) + "' nu exista."}
                conn.sendall(json.dumps(raspuns).encode('utf-8'))

            elif mesaj_primit.get("comanda") == "start":
                nume = mesaj_primit.get("numeService")
                serviciu_gasit = None
                for s in configData['servicii']:
                    if s['numeService'] == nume:
                        serviciu_gasit = s
                        break
                if serviciu_gasit is None:
                    raspuns = {"eroare": "Serviciul '" + str(nume) + "' nu exista in configuratie."}
                    conn.sendall(json.dumps(raspuns).encode('utf-8'))
                else:
                    try:
                        cmd = serviciu_gasit['startCmd']
                        rezultat_cmd = subprocess.run(cmd, shell=True)
                        stare_servicii[nume] = "Pornit"
                        raspuns = {"rezultat": "Serviciul '" + nume + "' a fost pornit cu succes.", "exitCode": rezultat_cmd.returncode}
                    except Exception as err_sub:
                        print("[SERVER] Eroare la executia comenzii start:", err_sub)
                        raspuns = {"eroare": "Eroare la pornire: " + str(err_sub)}
                    conn.sendall(json.dumps(raspuns).encode('utf-8'))

            elif mesaj_primit.get("comanda") == "stop":
                nume = mesaj_primit.get("numeService")
                serviciu_gasit = None
                for s in configData['servicii']:
                    if s['numeService'] == nume:
                        serviciu_gasit = s
                        break
                if serviciu_gasit is None:
                    raspuns = {"eroare": "Serviciul '" + str(nume) + "' nu exista in configuratie."}
                    conn.sendall(json.dumps(raspuns).encode('utf-8'))
                else:
                    try:
                        cmd = serviciu_gasit['stopCmd']
                        rezultat_cmd = subprocess.run(cmd, shell=True)
                        stare_servicii[nume] = "Oprit"
                        raspuns = {"rezultat": "Serviciul '" + nume + "' a fost oprit cu succes.", "exitCode": rezultat_cmd.returncode}
                    except Exception as err_sub:
                        print("[SERVER] Eroare la executia comenzii stop:", err_sub)
                        raspuns = {"eroare": "Eroare la oprire: " + str(err_sub)}
                    conn.sendall(json.dumps(raspuns).encode('utf-8'))

            else:
                raspuns = {"eroare": "Comanda necunoscuta."}
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
                    try:
                        comanda_user = input("Scrie o comanda (list / status <Nume> / start <Nume> / stop <Nume>): ")
                    except EOFError:
                        time.sleep(0.5)
                        continue
                    parti = comanda_user.strip().split(' ', 1)
                    actiune = parti[0]

                    if actiune == "list":
                        mesaj_json = {"comanda": "listare"}
                        sock_client.sendall(json.dumps(mesaj_json).encode('utf-8'))
                        raspuns_server = sock_client.recv(1024)
                        if not raspuns_server:
                            print("[CLIENT] Nodul a cazut / Serverul a inchis conexiunea.")
                            sock_client.close()
                            break
                        print("[CLIENT] Servicii disponibile:", raspuns_server.decode('utf-8'))

                    elif actiune == "status":
                        if len(parti) < 2:
                            print("[CLIENT] Folosire corecta: status <NumeServiceiu>")
                            continue
                        nume_serviciu = parti[1]
                        mesaj_json = {"comanda": "status", "numeService": nume_serviciu}
                        sock_client.sendall(json.dumps(mesaj_json).encode('utf-8'))
                        raspuns_server = sock_client.recv(1024)
                        if not raspuns_server:
                            print("[CLIENT] Nodul a cazut / Serverul a inchis conexiunea.")
                            sock_client.close()
                            break
                        raspuns_dict = json.loads(raspuns_server.decode('utf-8'))
                        if "rezultat" in raspuns_dict:
                            print("[CLIENT] Starea serviciului '" + nume_serviciu + "': " + raspuns_dict["rezultat"])
                        else:
                            print("[CLIENT] Eroare primita:", raspuns_dict.get("eroare", "Raspuns necunoscut"))

                    elif actiune == "start":
                        if len(parti) < 2:
                            print("[CLIENT] Folosire corecta: start <NumeServiceiu>")
                            continue
                        nume_serviciu = parti[1]
                        mesaj_json = {"comanda": "start", "numeService": nume_serviciu}
                        sock_client.sendall(json.dumps(mesaj_json).encode('utf-8'))
                        raspuns_server = sock_client.recv(1024)
                        if not raspuns_server:
                            print("[CLIENT] Nodul a cazut / Serverul a inchis conexiunea.")
                            sock_client.close()
                            break
                        raspuns_dict = json.loads(raspuns_server.decode('utf-8'))
                        if "rezultat" in raspuns_dict:
                            print("[CLIENT] " + raspuns_dict["rezultat"] + " (exit code: " + str(raspuns_dict.get("exitCode", "N/A")) + ")")
                        else:
                            print("[CLIENT] Eroare primita:", raspuns_dict.get("eroare", "Raspuns necunoscut"))

                    elif actiune == "stop":
                        if len(parti) < 2:
                            print("[CLIENT] Folosire corecta: stop <NumeServiceiu>")
                            continue
                        nume_serviciu = parti[1]
                        mesaj_json = {"comanda": "stop", "numeService": nume_serviciu}
                        sock_client.sendall(json.dumps(mesaj_json).encode('utf-8'))
                        raspuns_server = sock_client.recv(1024)
                        if not raspuns_server:
                            print("[CLIENT] Nodul a cazut / Serverul a inchis conexiunea.")
                            sock_client.close()
                            break
                        raspuns_dict = json.loads(raspuns_server.decode('utf-8'))
                        if "rezultat" in raspuns_dict:
                            print("[CLIENT] " + raspuns_dict["rezultat"] + " (exit code: " + str(raspuns_dict.get("exitCode", "N/A")) + ")")
                        else:
                            print("[CLIENT] Eroare primita:", raspuns_dict.get("eroare", "Raspuns necunoscut"))

                    else:
                        print("[CLIENT] Comanda necunoscuta. Incearca: list / status <Nume> / start <Nume> / stop <Nume>")

            except Exception as e:
                print("[CLIENT] Eroare / Conexiunea a picat:", e)
                sock_client.close()

        print("[CLIENT] Nu am gasit noduri active. Astept 3 secunde...")
        time.sleep(3)

if __name__ == '__main__':
    config_file = os.environ.get('CONFIG_FILE', 'config.json')
    configData = citeste_configul(config_file)
    my_port = configData['portLocal']
    noduriProx = configData['noduriProximitate']

    for serviciu in configData['servicii']:
        stare_servicii[serviciu['numeService']] = "Oprit"

    print("=== Pornire Nod ===")
    print("[INFO] Config folosit:", config_file)

    t_server = threading.Thread(target=start_Server, args=(my_port, configData))
    t_server.start()

    time.sleep(1)

    t_client = threading.Thread(target=startClient_logic, args=(noduriProx,))
    t_client.start()
