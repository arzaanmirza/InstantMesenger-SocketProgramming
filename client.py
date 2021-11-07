import socket
import select
import errno
import sys


HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234
my_username = input("Username: ")

# Create a socket
# socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to a given ip and port
client_socket.connect((IP, PORT))

# Prepare username and header and send them
# We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(username_header + username)

# Recieves the message whether its a new account or not
return_message_header = client_socket.recv(HEADER_LENGTH)
# Convert header to int value
return_message_length = int(return_message_header.decode('utf-8').strip())
# Receive and decode return message
return_message = client_socket.recv(return_message_length).decode('utf-8')

if return_message == "Old Account":
    my_password = input("Password: ")
    password = my_password.encode('utf-8')
    password_header = f"{len(password):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(password_header + password)

elif return_message == "New Account":
    new_password = input("This is a new user. Enter a password: ")
    password = new_password.encode('utf-8')
    password_header = f"{len(password):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(password_header + password)



# Returns whether its succesfully logged in or the password is wrong. 

return_message_header = client_socket.recv(HEADER_LENGTH)
return_message_length = int(return_message_header.decode('utf-8').strip())
return_message = client_socket.recv(return_message_length).decode('utf-8')
if return_message != "Invalid Password, Please try again!":
    print(return_message)

#-------------------------------------------------------------------------------------

# Special Case where the password is wrong and it has to try 3 times.
wrong_counter = 0

while return_message == "Invalid Password, Please try again!":
    
    if wrong_counter == 2:
        print("Invalid Password. Your account has been blocked. Please try again later.")
        sys.exit()
    else:
        print(return_message)
    my_password = input("Password: ")
    password = my_password.encode('utf-8')
    password_header = f"{len(password):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(password_header + password)
    return_message_header = client_socket.recv(HEADER_LENGTH)
    return_message_length = int(return_message_header.decode('utf-8').strip())
    return_message = client_socket.recv(return_message_length).decode('utf-8')
    wrong_counter = wrong_counter + 1


#--------------------------------------------------------------------------------------


# This statement ensures that the message keeps appearing. Related to recv()
client_socket.setblocking(False)

while True:

    # Wait for user to input a message
    message = input(f'{my_username} > ')

    # If message is not empty - send it
    if message:

        # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(message_header + message)

    try:
        # Now we want to loop over received messages (there might be more than one) and print them
        while True:

            # Receive our "header" containing username length, it's size is defined and constant
            username_header = client_socket.recv(HEADER_LENGTH)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(username_header):
                print('Connection closed by the server')
                sys.exit()

            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())

            # Receive and decode username
            username = client_socket.recv(username_length).decode('utf-8')

            # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
            message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')

            # Print message
            print(f'{username} > {message}')

    except IOError as e:
        # This is normal on non blocking connections - when there are no incoming data error is going to be raised
        # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
        # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
        # If we got different error code - something happened
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

        # We just did not receive anything
        continue

    except Exception as e:
        # Any other exception - something happened, exit
        print('Reading error: '.format(str(e)))
        sys.exit()