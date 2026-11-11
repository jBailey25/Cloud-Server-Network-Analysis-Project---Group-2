import socket
import os
import time

def start_client():
    # Basic setup using standard socket configuration
    SERVER_IP = input("Enter server IP (default 127.0.0.1): ") or '127.0.0.1'
    PORT = int(input("Enter server port (default 5000): ") or 5000)
    
    print(f"Connecting to server at {SERVER_IP}:{PORT}...")
    
    # Create TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_IP, PORT))
        print("Connected successfully!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    while True:
        print("\n--- MENU ---")
        print("1. upload [filename]")
        print("2. download [filename]")
        print("3. dir")
        print("4. subfolder [create/delete] [path]")
        print("5. delete [filename]")
        print("6. exit")
        
        choice = input("Enter command: ").strip()
        
        if choice.startswith("upload"):
            parts = choice.split()
            if len(parts) < 2:
                filename = input("Enter local filename to upload: ").strip()
            else:
                filename = parts[1]
                
            if not os.path.exists(filename):
                print(f"Error: File '{filename}' not found locally.")
                continue
                
            filesize = os.path.getsize(filename)
            
            # Send command header to server
            header = f"UPLOAD:{filename}:{filesize}"
            client_socket.sendall(header.encode('utf-8'))
            
            # Check server response for overwrite prompt
            response = client_socket.recv(1024).decode('utf-8')
            if "EXISTS" in response:
                overwrite = input("File already exists on server. Overwrite? (y/n): ")
                client_socket.sendall(overwrite.encode('utf-8'))
                if overwrite.lower() != 'y':
                    print("Upload cancelled.")
                    continue
            
            # Send file data in chunks
            print(f"Uploading {filename}...")
            start_time = time.time()
            
            with open(filename, "rb") as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    client_socket.sendall(data)
                    
            end_time = time.time()
            total_time = end_time - start_time
            rate = (filesize / (1024 * 1024)) / total_time if total_time > 0 else 0
            print(f"Upload finished in {total_time:.2f} seconds ({rate:.2f} MB/s).")
            
            # Get final server ack
            ack = client_socket.recv(1024).decode('utf-8')
            print("Server response:", ack)

        elif choice.startswith("download"):
            parts = choice.split()
            if len(parts) < 2:
                filename = input("Enter filename to download: ").strip()
            else:
                filename = parts[1]
                
            header = f"DOWNLOAD:{filename}"
            client_socket.sendall(header.encode('utf-8'))
            
            response = client_socket.recv(1024).decode('utf-8')
            if "ERROR" in response:
                print("Server error:", response)
                continue
                
            # Expecting size from server like "SIZE:1024"
            try:
                filesize = int(response.split(":")[1])
                client_socket.sendall("ACK".encode('utf-8'))
            except:
                print("Protocol error receiving file size.")
                continue
                
            print(f"Downloading {filename} ({filesize} bytes)...")
            start_time = time.time()
            
            os.makedirs("downloads", exist_ok=True)
            save_path = os.path.join("downloads", filename)
            
            received_bytes = 0
            with open(save_path, "wb") as f:
                while received_bytes < filesize:
                    chunk = client_socket.recv(min(4096, filesize - received_bytes))
                    if not chunk:
                        break
                    f.write(chunk)
                    received_bytes += len(chunk)
                    
            end_time = time.time()
            total_time = end_time - start_time
            rate = (filesize / (1024 * 1024)) / total_time if total_time > 0 else 0
            print(f"Download complete! Saved to {save_path} in {total_time:.2f}s ({rate:.2f} MB/s)")

        elif choice == "dir":
            client_socket.sendall("DIR".encode('utf-8'))
            listing = client_socket.recv(4096).decode('utf-8')
            print("\n--- Server Files ---")
            print(listing)
            print("--------------------")

        elif choice.startswith("subfolder"):
            parts = choice.split()
            if len(parts) < 3:
                action = input("Action (create/delete): ").strip()
                path = input("Enter directory path: ").strip()
            else:
                action = parts[1]
                path = parts[2]
                
            command = f"SUBFOLDER:{action}:{path}"
            client_socket.sendall(command.encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            print("Server response:", response)

        elif choice.startswith("delete"):
            parts = choice.split()
            if len(parts) < 2:
                filename = input("Enter filename to delete: ").strip()
            else:
                filename = parts[1]
                
            command = f"DELETE:{filename}"
            client_socket.sendall(command.encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            print("Server response:", response)

        elif choice == "exit":
            client_socket.close()
            print("Disconnected. Exiting.")
            break
        else:
            print("Invalid command. Try again.")

if __name__ == "__main__":
    start_client()
