import socket
import threading
import sys
import constants as consts
import random

# Shared Vars (must lock if write+read in a thread)
users = {}
game_halls = [[] for _ in range(consts.NUM_GAME_HALLS)]
hall_answers = [str(random.choice([True, False])).lower() for _ in range(consts.NUM_GAME_HALLS)] # Randomly generated boolean values for each 
guess_record = [[False, False] for _ in range(consts.NUM_GAME_HALLS)]
num_guesses = [0] * consts.NUM_GAME_HALLS
client_states = {}

lock = threading.Lock()

# ---------User Authentication---------
def authenticate_user(login_message):
    username, password = login_message.split()[1:]
    return username in users and users[username] == password

# Function to handle client connections
def handle_client(client_socket):

    while True:
        # Receive the login message from the client
        try:
            login_message = client_socket.recv(1024).decode()
            if authenticate_user(login_message):
                client_socket.send(consts.AUTHENTICATION_SUCCESSFUL_MESSAGE.encode())
                break
            else:
                # Authentication failed
                client_socket.send(consts.AUTHENTICATION_FAILED_MESSAGE.encode()) 
        except ValueError:
            # If the above code throws in exception (bad login message), return failed message
            client_socket.send(consts.AUTHENTICATION_FAILED_MESSAGE.encode())

    # Set state to be in game hall after authentication
    client_states[client_socket] = consts.IN_GAME_HALL_STATE
    room_num = -1 # Room number this client is currently in
    player_num = -1 # player number (either 0 or 1)

    while True:
        # Get next message from client
        try:
            client_message = client_socket.recv(1024).decode().split()
            with lock:
                #---------In Game Hall---------
                if client_states[client_socket] == consts.IN_GAME_HALL_STATE:
                    if client_message[0] == consts.LIST_COMMAND:
                        # /list
                        room_occupancy = [len(i) for i in game_halls]
                        response = "3001 {} {}".format(consts.NUM_GAME_HALLS,' '.join(map(str, room_occupancy)))
                        client_socket.send(response.encode())
                    elif client_message[0] == consts.ENTER_ROOM_COMMAND and len(client_message) == 2:
                        # /enter <room_num>
                        room_num = int(client_message[1]) - 1
                        if 0 <= room_num < consts.NUM_GAME_HALLS:
                            occupancy = len(game_halls[room_num])
                            response = ""
                            if occupancy == 0:
                                # Room is empty, must wait for another player
                                response = consts.WAIT_FOR_ANOTHER_PLAYER_MESSAGE
                                game_halls[room_num].append(client_socket)

                                # Update state to playing game
                                client_states[client_socket] = consts.IN_PLAYING_GAME_STATE

                                # Set player num to 0 (first player)
                                player_num = 0
                                
                            elif occupancy == 1:
                                # Start game message
                                response = consts.GAME_START_MESSAGE
                                game_halls[room_num].append(client_socket)

                                # Send the other player status code 3012 to start the game
                                game_halls[room_num][0].send(consts.GAME_START_MESSAGE.encode())

                                # Update state to playing game
                                client_states[client_socket] = consts.IN_PLAYING_GAME_STATE

                                # Set player num to 1 (second player)
                                player_num = 1

                            elif occupancy == 2:
                                # Room already full
                                response = consts.ROOM_FULL_MESSAGE
                                
                            client_socket.send(response.encode())
                        else:
                            # Print DNE if the room number is out of bounds
                            client_socket.send("Room does not exist. Please try again.".encode())
                    elif client_message[0] == consts.EXIT_COMMAND:
                        #---------Exit from System---------
                        client_socket.send(consts.EXIT_MESSAGE.encode())
                        break
                    else:
                        client_socket.send(consts.UNRECOGNIZED_COMMAND_MESSAGE.encode())

                #---------Playing a Game---------
                elif client_states[client_socket] == consts.IN_PLAYING_GAME_STATE:
                    # Make the guess
                    if client_message[0] == consts.GUESS_COMMAND and len(client_message) == 2:
                        num_guesses[room_num] += 1
                        guess_record[room_num][player_num] = client_message[1].lower() # record the guess 
                    elif client_message[0] == consts.GUESS_COMMAND and len(game_halls[room_num]) == 1:
                        # If this is a buffered guess command and the other player exited already,
                        # then do nothing so the commands can re-sync
                        continue
                    else:
                        client_socket.send(consts.UNRECOGNIZED_COMMAND_MESSAGE.encode())
                        continue
                    
                    # if num_guesses[room_num] is 2, that means both players finished guessing
                    if num_guesses[room_num] == 2:

                        if guess_record[room_num][0] == guess_record[room_num][1]:
                            # If it's a tie
                            for i in range(2):
                                game_halls[room_num][i].send(consts.TIE_GAME_MESSAGE.encode())
                        else:
                            winner, loser = 0, 1
                            if guess_record[room_num][1] == hall_answers[room_num]:
                                winner, loser = 1, 0
                            game_halls[room_num][winner].send(consts.WIN_GAME_MESSAGE.encode())
                            game_halls[room_num][loser].send(consts.LOSE_GAME_MESSAGE.encode())
                        
                        # Reset variables and return player state to game hall
                        client_states[game_halls[room_num][0]] = consts.IN_GAME_HALL_STATE
                        client_states[game_halls[room_num][1]] = consts.IN_GAME_HALL_STATE
                        game_halls[room_num] = []
                        guess_record[room_num] = [False, False]
                        num_guesses[room_num] = 0
        except IndexError: # On ctrl+c from client
            if client_states[client_socket] == consts.IN_PLAYING_GAME_STATE and len(game_halls[room_num]) == 2:
                winner = not player_num
                game_halls[room_num][winner].send(consts.WIN_GAME_MESSAGE.encode())
                client_states[game_halls[room_num][winner]] = consts.IN_GAME_HALL_STATE
                game_halls[room_num] = []
                guess_record[room_num] = [False, False]
                num_guesses[room_num] = 0
            elif client_states[client_socket] == consts.IN_PLAYING_GAME_STATE and len(game_halls[room_num]) == 1:
                game_halls[room_num] = []
                guess_record[room_num] = [False, False]
                num_guesses[room_num] = 0

            del client_states[client_socket]
            break
        except:
            break

    client_socket.close()
    
    # ~~ exit thread at EOF ~~

# Function to start the server
def start_server(port, user_info_file):
    # Read user information from the file and store it in memory
    with open(user_info_file, 'r') as file:
        for line in file:
            username, password = line.strip().split(':')
            users[username] = password
    print("Users successfully read from " + user_info_file)

    print(hall_answers)

    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', port))
    server_socket.listen(5)
    print("Server started and listening on port", port)

    # Accept client connections and start a new thread for each client
    try:
        while True:
            client_socket, address = server_socket.accept()
            print("New connection from", address)

            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()
    except:
        return

# Start the server
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Please specify the port and path to UserInfo.txt file")
        sys.exit()
    port = int(sys.argv[1])
    user_info_path = sys.argv[2]
    start_server(port, user_info_path)