"""Analysis Module Testing setup"""
import os
import random
import threading
import time

from analysis import NetworkStats, load_dataframe

#Testing Settings uses a separate CSV so the real data is not tampered with
CSV = "test_metrics.csv"
SIZES = {"text": 25 * 1024**2, "audio": 512 * 1024**2, "video": 2 * 1024**3}
FAKE_SPEED = 50 * 1024**2


# Fake test clients doing every operation
def fake_client(stats, name):
    stats.client_connected()
    for kind, size in SIZES.items():
        for op in ("upload", "download"):
            with stats.track(name, op, f"{kind}_file", size):
                time.sleep(size / FAKE_SPEED * random.uniform(0.01, 0.02)) #speed up fake transfer speeds for testing purposes
    for op in ("dir", "subfolder", "delete"):
        with stats.track(name, op):
            time.sleep(random.uniform(0.01, 0.05))
    stats.client_disconnected()


def main():
    #Overwrites Test csv
    if os.path.exists(CSV):
        os.remove(CSV)
    stats = NetworkStats(CSV)

    #Runs 3 threads at once to test the safety of threads
    threads = [threading.Thread(target=fake_client, args=(stats, f"client{i}")) for i in range(1, 4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    #Simulated fake download to test fail conditions
    try:
        with stats.track("client1", "download", "missing_file"):
            raise FileNotFoundError
    except FileNotFoundError:
        pass

    df = load_dataframe(CSV)
    print(df.to_string())
    print("\nSummary:", stats.summary())

    #3(clients) * 9(operations) + 1 fail = 28 expected rows
    assert len(df) == 3 * 9 + 1, "wrong row count"
    assert not df.iloc[-1]["success"], "failure not recorded"
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()