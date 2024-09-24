"""
    3331 assignment 21-T3
    Python 3
    Usage: python3 TCPClient3.py localhost 12000
    coding: utf-8
    
    Author: Zhaocheng Li
"""
import os
from socket import *
import sys
from threading import Thread
import _thread
import time

'''

    Data Structure

'''
#Server would be running on the same host as Client
if len(sys.argv) != 3:
    print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT ======\n")
    exit(0)
serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
serverAddress = (serverHost, serverPort)
# define a socket for the client side, it would be used to communicate with the server
clientSocket = socket(AF_INET, SOCK_STREAM)

# build connection with the server and send message to it
clientSocket.connect(serverAddress)

# create multi-thread class for client to send the message from server after logged in
class ClientP2PSenderThread(Thread):
    def __init__(self, clientSocket):
        Thread.__init__(self)
        self.clientSocket = clientSocket

    def run(self):
        while True:
            message = input("=====You already started p2p channel, Please type any messsage you want to send to your friend: =====\n")
            clientSocket.sendall(message.encode())
            if message == 'logout':
                break
            else:
                #print('[send]' + message)
                continue
        os._exit(0)
    
# create multi-thread class for client to send the message from server after logged in
class ClientSenderThread(Thread):
    def __init__(self, clientSocket):
        Thread.__init__(self)
        self.clientSocket = clientSocket

    def run(self):
        while True:
            message = input("=====You already logged in, Please type any messsage you want to send to server: =====\n")
            clientSocket.sendall(message.encode())
            if message == 'logout':
                break
            else:
                #print('[send]' + message)
                continue
        os._exit(0)

# create multi-thread class for client to receive the message from server after logged in
class ClientReceiveThread(Thread):
    def __init__(self, clientSocket):
        Thread.__init__(self)
        self.clientSocket = clientSocket
    def run(self):
        while True:
            # use recv() to receive message from the client
            data = self.clientSocket.recv(1024)
            message = data.decode()
            portNumber = 0
            server = ''
            if ' logs into the server' in message:
                print(message)
            elif ' logs out the server' in message:
                print(message)
            elif message == 'logout request':
                break
            elif 'port number:' in message:
                portNumber = int(message.split(":")[1])
                print(portNumber)
            elif 'client tcp connection is established' in message:
                print(message)
                '''
                time.sleep(1)
                serverHost = "0.0.0.0"
                serverPort = portNumber
                serverAddress = (serverHost, serverPort)
                clientSocket = socket(AF_INET, SOCK_STREAM)
                clientSocket.connect(serverAddress)
                clientSenderThread = ClientP2PSenderThread(clientSocket)
                clientReceiveThread = ClientReceiveThread(clientSocket)
                clientReceiveThread.start()
                clientSenderThread.start()
                '''
            elif 'p2p connection starts' in message:
                print(message)
                '''
                serverHost = "0.0.0.0"
                serverPort = portNumber
                serverAddress = (serverHost, serverPort)
                serverSocket = socket(AF_INET, SOCK_STREAM)
                serverSocket.bind(serverAddress)
                while True:
                    serverSocket.listen()
                    clientSocket, clientAddress = serverSocket.accept()
                    clientSenderThread = ClientP2PSenderThread(clientSocket)
                    clientReceiveThread = ClientReceiveThread(clientSocket)
                    clientReceiveThread.start()
                    clientSenderThread.start()
                '''
            else:
                print(message)
        os._exit(0)

while True:
    message = input("===== Please type any messsage you want to send to server: =====\n")
    clientSocket.sendall(message.encode())

    # receive response from the server
    # 1024 is a suggested packet size, you can specify it as 2048 or others
    data = clientSocket.recv(1024)
    receivedMessage = data.decode()

    # parse the message received from server and take corresponding actions
    if receivedMessage == "":
        print("[recv] Message from server is empty!")
    elif receivedMessage == "user credentials request":
        print("[recv] You need to provide username and password to login")
    elif receivedMessage == "download filename":
        print("[recv] You need to provide the file name you want to download")
    # user log in or create account
    elif receivedMessage == "please enter your username":
        username = input('please enter your username: ')
        clientSocket.send(username.encode())
        data = clientSocket.recv(1024)
        receivedMessage = data.decode()
        # if the account is already login
        if receivedMessage == 'You can not log an account that already login ':
            print(receivedMessage)
            break
        # if the account is already created
        if receivedMessage == "please enter your password":
            password = input('please enter your password: ')
            clientSocket.send(password.encode())
            # if the second input password is not same as the first one, re-send the password
            while receivedMessage != 'log in successful':
                data = clientSocket.recv(1024)
                receivedMessage = data.decode()
                if receivedMessage == 'log in successful':
                    clientSenderThread = ClientSenderThread(clientSocket)
                    clientReceiveThread = ClientReceiveThread(clientSocket)
                    clientReceiveThread.start()
                    clientSenderThread.start()
            
                    while True:
                        if clientReceiveThread.isAlive and clientSenderThread.isAlive:
                            continue
                        else:
                            break
                    break
                elif 'Please try to log in again after ' in receivedMessage:
                    os._exit(0)
                else:
                    set_password = input('please re-enter your password: ')
                    clientSocket.send(set_password.encode())
        # if the account have not created
        elif receivedMessage == 'Please enter your password to create an account':
            set_password = input('please enter your password: ')
            clientSocket.send(set_password.encode())
            data = clientSocket.recv(1024)
            receivedMessage = data.decode()
            if receivedMessage == 'Please check your password to create an account':
                set_password = input('please re-enter your password: ')
                clientSocket.send(set_password.encode())
                # if the second input password is not same as the first one, re-send the password
                while True:
                    data = clientSocket.recv(1024)
                    receivedMessage = data.decode()
                    if receivedMessage == 'Welcome!':
                        print("account created!")
                        break
                    else:
                        set_password = input('please re-enter your password: ')
                        clientSocket.send(set_password.encode())
    else:
        print("[recv] " + receivedMessage)
      
    ans = input('\nDo you want to continue(y/n) :')
    if ans == 'y':
        continue
    else:
        break



# close the socket
clientSocket.close()

