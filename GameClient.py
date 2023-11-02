import socket
import sys
import constants as consts


# Function to authenticate the client
def authenticate_client(client_socket):
    while True:
        username = input("Please input your username: ")
        password = input("Please input your password: ")
        login_message = "/login {} {}".format(username, password)
        client_socket.send(login_message.encode())

        # Receive and process the server response
        response = client_socket.recv(1024).decode()
        print(response)

        if response == consts.AUTHENTICATION_SUCCESSFUL:
            break

# Function to start the client
def start_client(server_host, server_port):
    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))
    print("Connected to the server")

    # ---------User Authentication---------
    authenticate_client(client_socket)

    #---------In Game Hall---------

    #---------Playing a Game---------

    #---------Exit from System---------

    # Close the connection
    client_socket.close()
    print("Connection closed.")

# Start the client
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Please specify the server IP address and port")
        sys.exit()
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    start_client(server_host, server_port)