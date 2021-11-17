from socket import *
from threading import Thread
import sys, select
import time
from datetime import datetime

# acquire server host and port from command line parameter
# if len(sys.argv) != 2:
#     print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT ======\n");
#     exit(0);
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# timeout_inputted = int(sys.argv[2]) 

# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

# Online Users
OnlineUsers = []
# Accounts & its corresponding Client Socket. Key -> username, Value -> ClientSocket
Sockets = {}
Address = {}
# Usernames & Passwords for the clients
Accounts = {}
# Offline Messages:
Offline_Messages = {}
# Can't send message to: Key -> username, Value -> List of users can't send message to.
Blocked_Users = {}
# Account username and the seconds since login. Key -> username , Value -> Time at login.
TimeAtLogin = {}

def create_accounts():
    
    with open('credentials.txt') as f:
        lines = f.readlines()

    for each_line in lines:
        username = each_line.split()[0]
        password = each_line.split()[1]
        Accounts[username] = password

# Create the Accounts:
create_accounts()

"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be runing in a separate therad, which is the multi-threading
"""
class ClientThread(Thread):

    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False
        self.firstLogin = True
        self.username = ""
        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True
        self.secondsSinceLogin = 0
        self.p2p_user = ""
        
    def run(self):
        message = ''

        # self.clientSocket.settimeout(timeout_inputted)
        
        while self.clientAlive:

            # use recv() to receive message from the client
            try:
                data = self.clientSocket.recv(1024)
            except:
                self.clientAlive = False
                print("===== the user disconnected - ", clientAddress)
                OnlineUsers.remove(self.username)
                self.clientSocket.send("You are now offline due to inactivity.".encode())

                logout_notification = f"Notification: {self.username} has been logged out due to inactivity."

                for user in OnlineUsers:
                    if self.username != user and self.username not in Blocked_Users[user]:
                        clientSocketSend = Sockets[user]
                        clientSocketSend.send(logout_notification.encode())
                break

            message = data.decode()

            if self.firstLogin == True:
                self.process_login(message)

            elif message == "whoelse":
                self.whoelse(message)

            elif message.startswith("whoelsesince"):
                self.whoelsesince(message)

            elif message.startswith("message"):
                self.message_user(message)
            
            elif message.startswith("block"):
                self.block(message)

            elif message.startswith("unblock"):
                self.unblock(message)

            elif message.startswith("broadcast"):
                self.broadcast(message)
            
            elif message.startswith("startprivate"):
                self.startprivate(message)

            elif message.startswith("P2P Connect"):
                print(f"P2P CONNECT: {message}")
                self.p2p_connect(message)

            elif message == "logout":
                # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
                self.clientAlive = False
                print("===== the user disconnected - ", clientAddress)
                OnlineUsers.remove(self.username)
                self.clientSocket.send("You are now offline.".encode())

                logout_notification = f"Notification: {self.username} has logged out."

                for user in OnlineUsers:
                    if self.username != user and self.username not in Blocked_Users[user]:
                        clientSocketSend = Sockets[user]
                        clientSocketSend.send(logout_notification.encode())

            else:
                print("[recv] " + message)
                print("[send] Cannot understand this message")
                message = "This is not a recognisable command. Please try again!"
                self.clientSocket.send(message.encode())
    
    """
        You can create more customized APIs here, e.g., logic for processing user authentication
        Each api can be used to handle one specific function, for example:
        def process_login(self):
            message = 'user credentials request'
            self.clientSocket.send(message.encode())
    """
    def process_login(self,message):

        # If this is true, then this would be the first login.
        if self.firstLogin is True:

            self.firstLogin = False
            self.username = message
            
            if self.username in Accounts:
                self.clientSocket.sendall("Old Account".encode())
                data = self.clientSocket.recv(1024)
                password = data.decode()

                if password == Accounts[self.username]:
                    self.clientSocket.sendall("Succesfully Logged In".encode())
                    OnlineUsers.append(self.username)
                else:

                    while True:

                        self.clientSocket.sendall("Invalid Password, Please try again!".encode())
                        data = self.clientSocket.recv(1024)
                        password = data.decode()

                        if password == Accounts[self.username]:
                            self.clientSocket.sendall("Successfully Logged In".encode())
                            OnlineUsers.append(self.username)
                            break


            else:
                self.clientSocket.sendall("New Account".encode())
                data = self.clientSocket.recv(1024)
                password = data.decode()
                Accounts[self.username] = password
                self.clientSocket.sendall("Succesfully Logged In".encode())
                OnlineUsers.append(self.username)
                Offline_Messages[self.username] = []

        TimeAtLogin[self.username] = datetime.now()
        Sockets[self.username] = self.clientSocket
        Address[self.username] = self.clientAddress
        Blocked_Users[self.username] = []

        presence_notification = f"Notification: {self.username} has logged in."

        for user in OnlineUsers:
            if self.username != user and self.username not in Blocked_Users[user]:
                clientSocketSend = Sockets[user]
                clientSocketSend.send(presence_notification.encode())

        # Sending the offline messages once logged back in.
        clientSocketSend = Sockets[self.username]
        for each_message in Offline_Messages[self.username]:
            each_message = "\n" + each_message
            clientSocketSend.send(each_message.encode())


    def whoelse(self,message):
        string_s = ""

        for each_user in OnlineUsers:
            if each_user != self.username and each_user not in Blocked_Users[self.username]:
                string_s = string_s + " " + each_user

        if len(string_s) == 0: # Checks if there is no one else online
            self.clientSocket.send("There is no one else online except you!".encode())
        else:
            self.clientSocket.send(string_s.strip().encode())

    def whoelsesince(self,message):

        try:
            seconds = int(message.split()[1])
        except: # Checks for the case where the person doesn't enter the seconds as an Integer
            self.clientSocket.send("Please enter the seconds as an Integer for the command: whoelsesince <seconds> ".encode())
            return

        currentTime = datetime.now()
        Users = []
        for username,loginTime in TimeAtLogin.items():

            secondsDifference = currentTime - loginTime
            secondsDifference = secondsDifference.total_seconds()

            if secondsDifference <= seconds and self.username != username and username not in Blocked_Users[self.username]:
                Users.append(username)
        
        Users_string = ""

        for user in Users:
            Users_string = Users_string + " " + user
        
        if len(Users_string.strip()) == 0:
            self.clientSocket.send(f"No one else has logged in within the last {seconds} seconds.".encode())
        else:
            self.clientSocket.send(Users_string.strip().encode())

    
    def message_user(self,message):

        user = message.split()[1]
        message_recv = message.split()[2:]
        message_recv = ' '.join(message_recv)
        message = f"{self.username} > {message_recv}"

        if user not in OnlineUsers:
            Offline_Messages[user].append(message)
            return 

        if user in Blocked_Users[self.username]:

            self.clientSocket.send("Sorry, this message is unable to be sent.".encode())

        else:

            clientSocketSend = Sockets[user]
            clientSocketSend.send(message.encode())

    def block(self,message):

        user_blocked = message.split()[1] # User to be blocked.
        Blocked_Users[user_blocked].append(self.username)
        message = f"{user_blocked} has been succesfully blocked!"
        self.clientSocket.send(message.encode())

    def unblock(self,message):

        user_blocked = message.split()[1] # User to be unblocked.
        try:
            Blocked_Users[user_blocked].remove(self.username)
        except:
            return
        message = f"{user_blocked} has been succesfully unblocked!"
        self.clientSocket.send(message.encode())

    def broadcast(self,message):
        someone_blocked = False
        message_recv = message.split()[1:]
        message_recv = ' '.join(message_recv)
        message = f"{self.username} > {message_recv}"

        for user in OnlineUsers:

            if user in Blocked_Users[self.username]:
                someone_blocked = True

            if self.username != user and user not in Blocked_Users[self.username]:
                clientSocketSend = Sockets[user]
                clientSocketSend.send(message.encode())


        if someone_blocked:
            self.clientSocket.send("This message could not be sent to some recipients.".encode())

    def startprivate(self,message):
        
        user = message.split()[1]
        self.p2p_user = user.strip()
        clientSocketSend = Sockets[user]
        send_message = f"Are you willing to engage in a private chat with {self.username}? Reply with 'Yes' or 'No'"
        clientSocketSend.send(send_message.encode())
    
    def p2p_connect(self,message):

        user = message.split()[3].strip() # Name of user
        reply = message.split()[4].strip() # Yes or No
        clientSocketSend = Sockets[user] # Address of the user

        # You are sending it to yourself at this point as user is yourself. You need to find Arzaan and send it to him. 
        if user in Blocked_Users[self.username]:
            clientSocketSend.send("You can't start a private chat with yourself!".encode())
            return

        elif user in Blocked_Users[self.username]:
            clientSocketSend.send("Unfortunately, this private chat cannot be commenced".encode())
            return 
        
        elif user not in OnlineUsers:
            clientSocketSend.send("This user is not Online!".encode())
            return

        if reply == "Yes" or "yes":
            socket_address = Sockets[self.username]
            send_mesage = f"P2P_SocketAddress: {socket_address}"
            self.clientSocket.send(send_mesage.encode())
            return

        elif reply == "No" or "no":
            send_message = f"{user} has declined to have a private chat with you."
            clientSocketSend.send(send_mesage.encode())
            return
        else:
            return


        




print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")


while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()