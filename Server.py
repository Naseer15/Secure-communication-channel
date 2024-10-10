import socket
import threading
import json

# Dictionary to store registered users
registered_users = {
    "Alice": "password1",
    "Bob": "password2"
}

# Dictionary to store currently logged-in users
current_users = {}

# Function to handle client connections
def handle_client(client_socket, username):
    while True:
        try:
            # Receive message from client
            message = client_socket.recv(1024).decode("utf-8")
            if message:
                # Broadcast message to the other client
                if username == "Alice":
                    other_user = "Bob"
                else:
                    other_user = "Alice"
                if other_user in current_users:
                    data = {
                        "username": username,
                        "message": message
                    }
                    current_users[other_user].send(f"MESSAGEBROADCAST {json.dumps(data)}".encode("utf-8"))
        except ConnectionResetError:
            # Handle connection reset by peer (client disconnect)
            break
        except:
            # Handle other errors
            break
    # Remove client from dictionary if still exists
    if username in current_users:
        del current_users[username]
    client_socket.close()


# Function to accept client connections
def accept_clients(server_socket):
    while True:
        client_socket, client_address = server_socket.accept()
        auth_data = json.loads(client_socket.recv(1024).decode("utf-8"))
        username = auth_data.get("username")
        password = auth_data.get("password")
        if username in registered_users and registered_users[username] == password:
            if username not in current_users:
                current_users[username] = client_socket
                print(f"{username} connected from {client_address}")
                client_socket.send("SERVERMESSAGE {\"message\":\"You are now connected to the chat server.\"}".encode("utf-8"))
                threading.Thread(target=handle_client, args=(client_socket, username)).start()
            else:
                print(f"Rejected connection from {client_address} (username: {username})")
                client_socket.send("SERVERMESSAGE {\"message\":\"You are already logged in.\"}".encode("utf-8"))
                client_socket.close()
        else:
            print(f"Rejected connection from {client_address} (username: {username})")
            client_socket.send("SERVERMESSAGE {\"message\":\"Invalid username or password.\"}".encode("utf-8"))
            client_socket.close()

# Main function to start the server
def main():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to a host and port
    server_socket.bind(("localhost", 9049))

    # Listen for incoming connections
    server_socket.listen(5)
    print("Server is listening for connections...")

    # Accept clients in a separate thread
    threading.Thread(target=accept_clients, args=(server_socket,)).start()

if __name__ == "__main__":
    main()