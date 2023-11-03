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

        if response == consts.AUTHENTICATION_SUCCESSFUL_MESSAGE:
            return

def process_commands(client_socket):

    # TODO: instead of checking whether cmd is exit as exit cond for while loop, check that it receives the bye bye instead
    # TODO: Update code such that the exit is completely handled by the server
    cmd = input()
    while cmd != consts.EXIT_COMMAND:
        client_socket.send(cmd.encode())
        # Receive and process the server response
        response = client_socket.recv(1024).decode()
        print(response)

        # wait for the signal of another player to join the room
        if response == consts.WAIT_FOR_ANOTHER_PLAYER_MESSAGE:
            start_signal = client_socket.recv(1024).decode()
            while start_signal != consts.GAME_START_MESSAGE:
                start_signal = client_socket.recv(1024).decode()
            print(start_signal)
        cmd = input()
    
    # Send final /exit command
    client_socket.send(cmd.encode())
    exit_response = client_socket.recv(1024).decode()
    print(exit_response)

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