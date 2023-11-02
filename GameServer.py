import socket
import threading
import sys
import constants as consts

# Global Vars
USERS = {}

def authenticate_user(username, password):
    return username in USERS and USERS[username] == password

# Function to handle client connections
def handle_client(client_socket):
    authenticated = False

    while not authenticated:
        # Receive the login message from the client
        login_message = client_socket.recv(1024).decode()
        username, password = login_message.split()[1:]

        # Authenticate the client
        if authenticate_user(username, password):
            # Authentication successful
            client_socket.send(consts.AUTHENTICATION_SUCCESSFUL.encode())
            authenticated = True
        else:
            # Authentication failed
            client_socket.send(consts.AUTHENTICATION_FAILED.encode())

    client_socket.close()

# Function to start the server
def start_server(port, user_info_file):
    # Read user information from the file and store it in memory
    with open(user_info_file, 'r') as file:
        for line in file:
            username, password = line.strip().split(':')
            USERS[username] = password
    print("Users successfully read from " + user_info_file)

    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', port))
    server_socket.listen(5)
    print("Server started and listening on port", port)

    # Accept client connections and start a new thread for each client
    while True:
        client_socket, address = server_socket.accept()
        print("New connection from", address)
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

# Start the server
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Please specify the port and path to UserInfo.txt file")
        sys.exit()
    port = int(sys.argv[1])
    user_info_path = sys.argv[2]
    start_server(port, user_info_path)