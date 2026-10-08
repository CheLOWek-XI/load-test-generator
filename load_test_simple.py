import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEVELOPER_NAME = "CheLOWek"

def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("URL не може бути порожнім.")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url

def fetch_once(url: str):
    start = time.perf_counter()
    try:
        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urlopen(req, timeout=15) as response:
            response.read()
            status = response.getcode()
            elapsed = time.perf_counter() - start
            return {"status": status, "latency": elapsed, "ok": 200 <= status < 400, "error": None}
    except HTTPError as e:
        elapsed = time.perf_counter() - start
        return {"status": e.code, "latency": elapsed, "ok": False, "error": f"HTTPError: {e.code}"}
    except URLError as e:
        elapsed = time.perf_counter() - start
        return {"status": 0, "latency": elapsed, "ok": False, "error": f"URLError: {e.reason}"}
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"status": 0, "latency": elapsed, "ok": False, "error": str(e)}

def run_load_test(url: str, total_requests: int, workers: int, log_widget):
    status_codes = {}
    latencies = []
    success_count = 0
    error_count = 0
    counter_lock = threading.Lock()
    counter = {"value": total_requests}

    def worker():
        nonlocal success_count, error_count
        while True:
            with counter_lock:
                if counter["value"] <= 0:
                    return
                counter["value"] -= 1

            item = fetch_once(url)

            if item["ok"]:
                success_count += 1
            else:
                error_count += 1

            code = item["status"]
            status_codes[code] = status_codes.get(code, 0) + 1
            latencies.append(item["latency"])

    start_total = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker) for _ in range(workers)]
        for f in futures:
            f.result()

    total_elapsed = time.perf_counter() - start_total
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    rps = total_requests / total_elapsed if total_elapsed > 0 else 0.0

    summary = (
        "\n" + "=" * 50 + "\n"
        "РЕЗУЛЬТАТ НАВАНТАЖЕННЯ\n"
        "=" * 50 + "\n"
        f"URL: {url}\n"
        f"Запитів: {total_requests}\n"
        f"Потоків: {workers}\n"
        f"Успішно: {success_count}\n"
        f"Помилок: {error_count}\n"
        f"Середній latency: {avg_latency:.4f} сек\n"
        f"RPS: {rps:.2f} запитів/сек\n"
        f"Час виконання: {total_elapsed:.3f} сек\n"
        f"HTTP статуси: {status_codes}\n"
        f"Розробник: {DEVELOPER_NAME}\n"
        "=" * 50 + "\n"
    )

    log_widget.after(0, lambda: log_widget.insert(tk.END, summary))
    log_widget.after(0, lambda: log_widget.see(tk.END))

def start_test():
    try:
        url = normalize_url(url_entry.get())
        total_requests = int(requests_entry.get())
        workers = int(workers_entry.get())
    except ValueError as e:
        messagebox.showerror("Помилка", f"Помилка введення: {e}")
        return

    if total_requests <= 0 or workers <= 0:
        messagebox.showerror("Помилка", "Кількість запитів і потоків має бути більше 0.")
        return

    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, f"Запуск навантаження для: {url}\n")
    output_box.insert(tk.END, f"Запитів: {total_requests}\n")
    output_box.insert(tk.END, f"Потоків: {workers}\n")
    output_box.insert(tk.END, "Прочекайте...\n\n")

    def worker_thread():
        run_load_test(url, total_requests, workers, output_box)

    threading.Thread(target=worker_thread, daemon=True).start()

# GUI
root = tk.Tk()
root.title("Load Test Tool")
root.geometry("800x600")

main = ttk.Frame(root, padding=15)
main.pack(fill="both", expand=True)

title = ttk.Label(main, text="Load Test Tool", font=("Arial", 16, "bold"))
title.pack(pady=(0, 15))

ttk.Label(main, text="URL сайту:", font=("Arial", 10)).pack(anchor="w")
url_entry = ttk.Entry(main, width=70, font=("Arial", 10))
url_entry.insert(0, "https://example.com")
url_entry.pack(fill="x", pady=(0, 10))

ttk.Label(main, text="Кількість запитів:", font=("Arial", 10)).pack(anchor="w")
requests_entry = ttk.Entry(main, width=20, font=("Arial", 10))
requests_entry.insert(0, "1000")
requests_entry.pack(anchor="w", pady=(0, 10))

ttk.Label(main, text="Кількість потоків:", font=("Arial", 10)).pack(anchor="w")
workers_entry = ttk.Entry(main, width=20, font=("Arial", 10))
workers_entry.insert(0, "50")
workers_entry.pack(anchor="w", pady=(0, 15))

start_button = ttk.Button(main, text="Запустити тест", command=start_test)
start_button.pack(pady=(0, 15))

output_box = scrolledtext.ScrolledText(main, wrap=tk.WORD, width=95, height=20, font=("Courier", 9))
output_box.pack(fill="both", expand=True)

footer = ttk.Label(main, text=f"Розробник: {DEVELOPER_NAME}", font=("Arial", 8))
footer.pack(pady=(10, 0))

root.mainloop()
