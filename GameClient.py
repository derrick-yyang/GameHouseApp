import socket
import sys
import constants as consts


# Function to authenticate the client
def authenticate_client(client_socket):
    # Authenticate until success message from server is returned
    try:
        while True:
            username = input("Please input your username: ")
            password = input("Please input your password: ")
            login_message = "/login {} {}".format(username, password)
            client_socket.send(login_message.encode())

            # Receive and process the server response
            response = client_socket.recv(1024).decode()
            print(response)

            if response == consts.AUTHENTICATION_SUCCESSFUL_MESSAGE:
                return
    except:
        return

def process_commands(client_socket):

    # Send/receive messages to/from server until the exit message from the server is received
    response = ""
    while response != consts.EXIT_MESSAGE:
        try:
            cmd = input()
            client_socket.send(cmd.encode())
            
            # Receive and process the server response
            response = client_socket.recv(1024).decode()

            print(response)
        except:
            break

        # wait for the signal of another player to join the room
        try:
            if response == consts.WAIT_FOR_ANOTHER_PLAYER_MESSAGE:
                start_signal = client_socket.recv(1024).decode()
                while start_signal != consts.GAME_START_MESSAGE:
                    start_signal = client_socket.recv(1024).decode()
                print(start_signal)
        except:
            continue
    print("Client ends")

# Function to start the client
def start_client(server_host, server_port):
    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))

    # ---------User Authentication---------
    authenticate_client(client_socket)

    # Once authenticated, client may start to enter commands
    process_commands(client_socket)

    # Close the connection
    client_socket.close()

# Start the client
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Please specify the server IP address and port")
        sys.exit()
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    start_client(server_host, server_port)