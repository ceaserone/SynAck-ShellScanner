import threading
import requests
import random
import time
import sys
import urllib3
from queue import Queue
from itertools import cycle

# synacknetwork.com
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64)",
    "Mozilla/5.0 (iPad; CPU OS 13_2_3 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 5)",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "curl/7.68.0",
]


def spinner():
    spin = cycle(['|', '/', '-', '\\'])
    while not done_event.is_set():
        sys.stdout.write(f"\rScanning... {next(spin)} {current_task} ETA: {eta:.1f}s")
        sys.stdout.flush()
        time.sleep(0.1)

def load_data(target_file, shell_file="shells.txt"):
    with open(target_file) as f:
        targets = [line.strip().rstrip('/') for line in f if line.strip()]
    with open(shell_file) as f:
        paths = [line.strip() for line in f if line.strip()]
    return targets, paths

def worker():
    global scanned_count
    while not q.empty():
        target = q.get()
        for path in shell_paths:
            schemes = ['http://', 'https://']
            if target.startswith("http://") or target.startswith("https://"):
                schemes = ['']  # Already has scheme

            for scheme in schemes:
                url = f"{scheme}{target}{path}"
                headers = {"User-Agent": random.choice(user_agents)}
                try:
                    r = requests.get(url, headers=headers, timeout=6, allow_redirects=False, verify=False)
                    code = r.status_code
                    if code == 200 and any(k in r.text.lower() for k in ['r57', 'wso', 'c99', 'b374k', 'cmd', 'execute']):
                        msg = f"[FOUND SHELL] {url} [Status: {code}]"
                        print("\n" + msg)
                        with open("found_shells.txt", "a") as out:
                            out.write(msg + "\n")
                        break
                    elif code == 200:
                        print(f"\n[+] 200 OK: {url}")
                        break
                    elif code in [301, 302]:
                        print(f"\n[→] Redirect: {url}")
                        break
                    elif code == 403:
                        print(f"\n[!] Forbidden: {url}")
                        break
                except Exception:
                    continue
        scanned_count += 1
        q.task_done()

def start_scan(target_file, threads=17):
    global q, shell_paths, current_task, scanned_count, eta
    targets, shell_paths = load_data(target_file)
    q = Queue()
    total = len(targets)
    scanned_count = 0

    for t in targets:
        q.put(t)

    thread_list = []
    for _ in range(min(threads, total)):
        t = threading.Thread(target=worker)
        t.start()
        thread_list.append(t)

    start_time = time.time()
    spin_thread = threading.Thread(target=spinner)
    spin_thread.start()

    while any(t.is_alive() for t in thread_list):
        current_task = f"{scanned_count}/{total}"
        elapsed = time.time() - start_time
        eta = (elapsed / scanned_count) * (total - scanned_count) if scanned_count else 0
        time.sleep(1)

    done_event.set()
    spin_thread.join()
    print("\n Scan complete.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python find_shells.py targets.txt")
        sys.exit(1)

    current_task = ""
    eta = 0
    done_event = threading.Event()
    start_scan(sys.argv[1])
  
