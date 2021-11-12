from socket import *
import sys
import select
import threading

#Server would be running on the same host as Client
# if len(sys.argv) != 3:
#     print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT ======\n");
#     exit(0);
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# define a socket for the client side, it would be used to communicate with the server
clientSocket = socket(AF_INET, SOCK_STREAM)
# build connection with the server and send message to it
clientSocket.connect(serverAddress)
clientSocket.settimeout(60)
FirstLogin = True

# First time logging in
if FirstLogin == True:
    message = input("Username: ")
    Username = message
    clientSocket.sendall(message.encode())
    data = clientSocket.recv(1024)
    account_type = data.decode() # Whether new account or old account

    if account_type == "Old Account":
        my_password = input("Password: ")
        clientSocket.sendall(my_password.encode())
    elif account_type == "New Account":
        new_password = input("This is a new user. Enter a password: ")
        clientSocket.sendall(new_password.encode())

    data = clientSocket.recv(1024)
    return_message = data.decode()
    
    if return_message != "Invalid Password, Please try again!":
        print(return_message)
    # Special Case where the password is wrong and it has to try 3 times.
    wrong_counter = 0

    while return_message == "Invalid Password, Please try again!":
        
        if wrong_counter == 2:
            print("Invalid Password. Your account has been blocked. Please try again later.")
            sys.exit()
        else:
            print(return_message)
            my_password = input("Password: ")
            clientSocket.sendall(my_password.encode())
            data = clientSocket.recv(1024)
            return_message = data.decode()
            wrong_counter = wrong_counter + 1   

    FirstLogin = False # Makes it false so the login prompt never runs again for this account.

def receive():

    while True:
    
        try:

            data = clientSocket.recv(1024)
            receivedMessage = data.decode()

            if receivedMessage:
                print(receivedMessage)
                

        except:
            clientSocket.close()
            break

def write():
    
    while True:

        message = input()
        clientSocket.sendall(message.encode())



receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()