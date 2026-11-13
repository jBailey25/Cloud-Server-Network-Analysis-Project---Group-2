"""Network Analysis Module: Goal to time transfers & commands and log them into a CSV File"""
import csv
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime

#The Columns of the CSV
FIELDS = [
    "timestamp", "client", "operation", "filename", "size_bytes",
    "duration_s", "rate_mbps", "concurrent_clients", "protocol", "success",
]

class NetworkStats:
    #One shared instance of a CSV per server
    def __init__(self, csv_path="Network_Stats.csv", protocol="TCP"):
        self.csv_path = csv_path
        self.protocol = protocol
        self.records = []
        self.active_clients = 0
        self._lock = threading.Lock() #Prevents threads from writing at the same time
        if not os.path.exists(csv_path): #Will only write the header for a new file
            with open(csv_path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writeheader()
    
    #Called on when the client connects
    def client_connected(self):
        with self._lock:
            self.active_clients += 1

    #Called on when the client disconnects
    def client_disconnected(self):
        with self._lock:
            self.active_clients = max(0, self.active_clients - 1)
    
    # Builds one row and saves it to memory + CSV
    def record(self, client, operation, duration_s, filename="", size_bytes=0, success=True):
        rate = (size_bytes / (1024 * 1024)) / duration_s if size_bytes and duration_s > 0 else 0.0
        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "client": client,
            "operation": operation,
            "filename": filename,
            "size_bytes": size_bytes,
            "duration_s": round(duration_s, 4),
            "rate_mbps": round(rate, 2),
            "concurrent_clients": self.active_clients,
            "protocol": self.protocol,
            "success": success,
        }
        with self._lock:
            self.records.append(row)
            with open(self.csv_path, "a", newline="") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
        return row

    # Stopwatch: times whatever runs inside "with stats.track(...)"
    @contextmanager
    def track(self, client, operation, filename="", size_bytes=0):
        start = time.perf_counter()
        result = {"success": True}
        try:
            yield result
        except Exception:
            result["success"] = False
            raise
        finally:
            self.record(client, operation, time.perf_counter() - start,
                        filename, size_bytes, result["success"])

    # Quick averages per client operation
    def summary(self):
        with self._lock:
            rows = list(self.records)
        out = {}
        for r in rows:
            s = out.setdefault(r["operation"], {"count": 0, "total_s": 0.0, "rates": []})
            s["count"] += 1
            s["total_s"] += r["duration_s"]
            if r["rate_mbps"]:
                s["rates"].append(r["rate_mbps"])
        for s in out.values():
            s["avg_s"] = round(s["total_s"] / s["count"], 4)
            s["avg_rate_mbps"] = round(sum(s["rates"]) / len(s["rates"]), 2) if s["rates"] else 0.0
            del s["rates"], s["total_s"]
        return out

# Loads the CSV into pandas, for Graphs & analysis
def load_dataframe(csv_path="Network_Stats.csv"):
    import pandas as pd
    return pd.read_csv(csv_path)