import socket
import threading
import json
import time
import datetime
import sys

# ==================== CONFIGURATIE ====================
DATA_FILE = "C:\\Users\\pjvth\\High-tech Engineering\\Thesis\\Grasshopper control\\Grasshopper python scripts\\Grasshopper script components\\print_data.json"
LAPTOP_IP = "0.0.0.0"         
WAYPOINT_PORT = 3000

DUET_IP = "172.19.126.242"
DUET_PORT = 23
PROXY_PORT = 2323
# ======================================================

# NIEUW: Een signaal-vlaggetje om het hoofdscript te pauzeren
proxy_done = threading.Event()

def log_message(direction, data):
    """Logt netwerkverkeer met milliseconden voor analyse in de terminal."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    text = data.decode('utf-8', errors='ignore').strip()
    if text:
        print(f"[{timestamp}] {direction}: {text}")

def forward_stream(source_sock, dest_sock, direction):
    """Proxy thread: stuurt data direct door tussen UR5 en Duet."""
    while True:
        try:
            data = source_sock.recv(4096)
            if not data:
                print(f"[-] Verbinding verbroken door {direction.split('->')[0].strip()}")
                break
            
            log_message(direction, data)
            dest_sock.sendall(data)
            
        except Exception as e:
            print(f"[!] Fout in datastroom ({direction}): {e}")
            break
            
    try: source_sock.close() 
    except: pass
    try: dest_sock.close() 
    except: pass
    
    # NIEUW: Als de robot de verbinding sluit, geef het signaal dat we klaar zijn
    if "UR5 -> DUET" in direction:
        proxy_done.set()

def start_proxy_server():
    """Start de TCP proxy voor de G-code."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((LAPTOP_IP, PROXY_PORT))
        server.listen(1)
        print(f"[PROXY] Wachten op UR5 G-code connectie (Poort {PROXY_PORT})...")
        
        ur5_sock, addr = server.accept()
        ur5_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        print(f"[PROXY] UR5 verbonden vanaf {addr[0]}")
        
        duet_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        duet_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        duet_sock.connect((DUET_IP, DUET_PORT))
        print("[PROXY] Verbonden met Duet! G-code proxy is live.\n")
        
        t1 = threading.Thread(target=forward_stream, args=(ur5_sock, duet_sock, "UR5 -> DUET"))
        t2 = threading.Thread(target=forward_stream, args=(duet_sock, ur5_sock, "DUET -> UR5"))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()
        
    except Exception as e:
        print(f"[PROXY ERROR] {e}")

def run_waypoint_server():
    """Leest de JSON en stuurt de coördinaten naar de UR5."""
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            waypoints = data["P"]
            layer_heights = data["H"]
            distances = data["D"]
        print(f"[*] Data succesvol geladen: {len(waypoints)} waypoints.")
    except FileNotFoundError:
        print(f"[!] Fout: Kan '{DATA_FILE}' niet vinden. Heb je geëxporteerd vanuit Grasshopper?")
        sys.exit(1)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LAPTOP_IP, WAYPOINT_PORT))
    server.listen(1)

    print(f"[*] Waypoint Server klaar op poort {WAYPOINT_PORT}.")
    print("====================================================")
    print("✓ ALLES IS GEREED — JE KUNT DE ROBOT NU STARTEN")
    print("====================================================\n")
    
    conn, addr = server.accept()
    print(f"[+] Robot (hoofdprogramma) verbonden vanaf {addr[0]}")

    try:
        for w, h, d in zip(waypoints, layer_heights, distances):
            request = conn.recv(1024).decode()
            
            if "NEXT" in request:
                message = f"({w}, {h}, {d})\n"
                conn.sendall(message.encode())
            else:
                print(f"[!] Onverwachte data ontvangen: {request}")
                break

        print("[*] Alle waypoints verzonden. STOP signaal verstuurd...")
        conn.sendall("STOP\n".encode())
        
        # NIEUW: Wacht tot de proxy meldt dat de robot is afgesloten
        print("[*] Wachten op de laatste commando's (M104, M140, M107)...")
        
        # Wacht maximaal 15 seconden als failsafe, mocht de robot vastlopen
        if proxy_done.wait(timeout=15.0):
            print("[✓] Robot heeft de proxy netjes afgesloten.")
        else:
            print("[!] Timeout: Robot sloot de proxy niet binnen 15 seconden.")

    except KeyboardInterrupt:
        print("\n[!] Handmatig afgebroken.")
    except Exception as e:
        print(f"\n[!] Fout tijdens printen: {e}")
    finally:
        conn.close()
        server.close()
        print("[*] Printcyclus en communicatie volledig afgerond.")

if __name__ == "__main__":
    # Reset de event vlag
    proxy_done.clear()

    # Start de proxy op de achtergrond
    proxy_thread = threading.Thread(target=start_proxy_server)
    proxy_thread.daemon = True
    proxy_thread.start()
    
    time.sleep(0.5)
    
    # Start de waypoint verzender op de voorgrond
    run_waypoint_server()