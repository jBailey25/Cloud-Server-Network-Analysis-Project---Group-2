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