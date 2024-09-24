"""
    3331 assignment 21-T3
    Python 3
    Usage: python3 TCPserver3.py localhost 12000
    coding: utf-8
    
    Author: Zhaocheng Li
"""
from os import times
from socket import *
from threading import Thread
import sys, select
import threading
import time

'''

    Data Structure

'''

ONLINE_USERS = []
USERNMAES = []
BLACKLIST = []
BLOCK_LOGIN_LIST = []
HISTORY_USERS = []


# acquire server host and port from command line parameter
if len(sys.argv) != 4:
    print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT BLOCK_TIME TIMEOUT_DURATION======\n")
    exit(0)
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)
timeBlock = int(sys.argv[2])
timeoutDuration = int(sys.argv[3])
# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

"""

    Define multi-thread class to handle the blocked_user who can not logged in during the blocked time

"""
class HandleBlockedLogIn(Thread):
    def __init__(self, blocked_user):
        Thread.__init__(self)
        self.blocked_user = blocked_user
    
    def run(self):
        time.sleep(timeBlock)
        BLOCK_LOGIN_LIST.remove(self.blocked_user)

"""

    Define multi-thread class for offline message deliver

"""
class OfflineDelivery(Thread):
    def __init__(self, message, offline_user, sender_index):
        Thread.__init__(self)
        self.message = message
        self.offline_user = offline_user
        self.process_alive = True
        self.sender_index = sender_index
        print("===== waitting for clients to log in: ")
    
    def run(self):
        while self.process_alive:
            receiver_index = 0
            for client in USERNMAES:
                if self.offline_user == client:
                    sender = USERNMAES[self.sender_index]
                    block_info = client + "+" + sender
                    sender_blocked = False
                    for blocked_info in BLACKLIST:
                        if block_info == blocked_info:
                            sender_blocked = True
                            break
                    if not sender_blocked:
                        #print('[send] ' + self.message + ' to ' + self.offline_user)
                        send_message = USERNMAES[self.sender_index] + ': ' + self.message
                        ONLINE_USERS[receiver_index].send(send_message.encode())
                    self.process_alive = False
                else:
                    receiver_index += 1

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
        
        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True
        
    def run(self):
        message = ''
        
        while self.clientAlive:
            # use recv() to receive message from the client
            data = self.clientSocket.recv(1024)
            message = data.decode()
            
            # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
            if message == '':
                self.clientAlive = False
                print("===== the user disconnected - ", clientAddress)
                break
            # handle message from the client
            if message == 'login':
                #print("[recv] New login request")
                self.process_login()
                timer = threading.Timer(timeoutDuration, self.process_logout)
                timer.start()
            elif message == 'logout':
                #print("[recv] New logout request")
                self.process_logout()
                timer.cancel()
            elif message == 'download':
                #print("[recv] Download request")
                message = 'download filename'
                #print("[send] " + message)
                self.clientSocket.send(message.encode())
                timer.cancel()
            elif 'broadcast' in message:
                #print("[rece] broadcast request")
                self.process_broadcast(message)
                timer.cancel()
            elif "message" in message:
                #print("[rece] message request")
                self.process_message(message)
                timer.cancel()
            elif "whoelse" == message:
                #print("[rece] whoelse request")
                self.process_whoelse()
                timer.cancel()
            elif "whoelsesince" in message:
                #print("[rece] whoelse request")
                self.process_whoelsesince(message)
                timer.cancel()
            elif 'unblock' in message:
                #print("[rece] unblock request")
                unblock_user = message
                self.clientSocket.send('Are you sure to unblock the user?(yes/no)'.encode())
                data = self.clientSocket.recv(1024)
                confirm_infor = data.decode()
                if confirm_infor == 'yes':
                    self.process_unblock(unblock_user)
                else:
                    self.clientSocket.send('you cancel the blocking process'.encode())
                timer.cancel()
            elif "block" in message:
                #print("[rece] block request")
                block_user = message
                self.clientSocket.send('Are you sure to block the user?(yes/no)'.encode())
                data = self.clientSocket.recv(1024)
                confirm_infor = data.decode()
                if confirm_infor == 'yes':
                    self.process_block(block_user)
                else:
                    self.clientSocket.send('you cancel the blocking process'.encode())
                timer.cancel()
            elif "startprivate" in message:
                #print("[rece] startprivate request")
                self.process_p2p(message)
            elif 'yes' in message:
                confirm_message = "please re-type 'yes' again to confirm your aggrement to establish p2p connection"
                self.clientSocket.send(confirm_message.encode())
            elif 'no' in message:
                confirm_message = "please re-type 'no' again to reject the requirement of p2p connection"
                self.clientSocket.send(confirm_message.encode())
            else:
                #print("[recv] " + message)
                #print("[send] Cannot understand this message")
                message = 'Cannot understand this message'
                self.clientSocket.send(message.encode())
                timer.cancel()
            if not timer.isAlive:
                timer.start()
    
    """
        You can create more customized APIs here, e.g., logic for processing user authentication
        Each api can be used to handle one specific function, for example:
        def process_login(self):
            message = 'user credentials request'
            self.clientSocket.send(message.encode())
    """
    def process_p2p(self, message):
        p2p_user = message[13:-1]
        client_online = False

        f = open("credentials.txt", "r")
        outputdata = f.readlines()
        contain = False
        for line in outputdata:
            username = line.split()[0]
            if p2p_user == username:
                contain = True
        if contain:
            index_receiver = 0
            for client in USERNMAES:
                if client == p2p_user:
                    client_online = True
                    break
                else:
                    index_receiver += 1
            index_sender = 0
            for client in ONLINE_USERS:
                if client == self.clientSocket:
                    break
                else:
                    index_sender += 1
            not_blocked = True
            if client_online:
                for blocked_infor in BLACKLIST:
                    if blocked_infor == USERNMAES[index_receiver] + '+' +USERNMAES[index_sender]:
                        not_blocked = False
                        break
                if not_blocked:
                    if self.clientSocket != ONLINE_USERS[index_receiver]:
                        message = 'Do you want to create p2p channel with ' + USERNMAES[index_sender] + ' (yes/no)'
                        ONLINE_USERS[index_receiver].send(message.encode())
                        data = ONLINE_USERS[index_receiver].recv(1024)
                        message = data.decode()
                        if message == 'yes':
                            #p2p_information_sender = str(self.clientSocket)
                            #p2p_information_receiver = str(ONLINE_USERS[index_receiver])
                            portNumber = 'port number:4920'
                            aggrement_message_sender = 'p2p connection starts'
                            aggrement_message_receiver = 'client tcp connection is established'
                            ONLINE_USERS[index_receiver].send(portNumber.encode())
                            self.clientSocket.send(portNumber.encode())
                            self.clientSocket.send(aggrement_message_sender.encode())
                            ONLINE_USERS[index_receiver].send(aggrement_message_receiver.encode())
                        else:
                            error_message = USERNMAES[index_receiver] + ' reject your p2p requirement'
                            self.clientSocket.send(error_message.encode())
                    else:
                        error_message = 'You can not establish p2p connection to yourself'
                        self.clientSocket.send(error_message.encode())
                else:
                    error_message = 'You can not establish p2p connection to ' + p2p_user
                    ONLINE_USERS[index_sender].send(error_message.encode())
            else:
                error_message = p2p_user + ' is not online'
                self.clientSocket.send(error_message.encode())
        else:
            error_message = p2p_user + ' is not exist'
            self.clientSocket.send(error_message.encode())
    def process_unblock(self, message):
        unblock_name = message[8:-1]

        f = open("credentials.txt", "r")
        outputdata = f.readlines()
        contain = False
        for line in outputdata:
            username = line.split()[0]
            if unblock_name == username:
                contain = True

        if contain:
            index = 0
            for client in ONLINE_USERS:
                if client == self.clientSocket:
                    break
                index += 1
            current_client = USERNMAES[index]
            if current_client == unblock_name:
                self.clientSocket.send('you can not unblock yourself'.encode())
            else:
                block_infor = current_client + '+'  + unblock_name
                found = False
                for infor in BLACKLIST:
                    if block_infor == infor:
                        found = True
                if found:        
                    BLACKLIST.remove(block_infor)
                    message = 'unblocked ' + unblock_name + ' successfully'
                    self.clientSocket.send(message.encode())
                else:
                    error_message = unblock_name + ' is not exist'
                    self.clientSocket.send(error_message.encode())
        else:
            error_message = 'user name is invalid'
            self.clientSocket.send(error_message.encode())
    
    def process_block(self, message):
        block_name = message[6:-1]

        f = open("credentials.txt", "r")
        outputdata = f.readlines()
        contain = False
        for line in outputdata:
            username = line.split()[0]
            if block_name == username:
                contain = True

        if contain:
            index = 0
            for client in ONLINE_USERS:
                if client == self.clientSocket:
                    break
                index += 1
            current_client = USERNMAES[index]
            if current_client == block_name:
                self.clientSocket.send('you can not block yourself'.encode())
            else:
                block_infor = current_client + '+'  + block_name
                BLACKLIST.append(block_infor)
                message = 'blocked ' + block_name + ' successfully'
                self.clientSocket.send(message.encode())
        else:
            error_message = 'user name is invalid'
            self.clientSocket.send(error_message.encode())

    def process_whoelsesince(self,message):
        TIME = int(message[13:-1])
        index = 0
        send_message = 'history_record:'
        for client in ONLINE_USERS:
            if client == self.clientSocket:
                break
            index += 1
        current_client = USERNMAES[index]

        blockerlist = []
        for block_infor in BLACKLIST:
            blocker = block_infor.split('+')[0]
            blocked_user = block_infor.split('+')[1]
            if blocked_user == current_client:
                blockerlist.append(blocker)

        if len(blockerlist) == 0:
            for history in HISTORY_USERS:
                user_logout = history.split('+')[0]
                logout_time = int(history.split('+')[1])
                if TIME >= int(time.time()) - logout_time:
                    send_message = send_message + ' ' + user_logout
        else:            
            for history in HISTORY_USERS:
                user_logout = history.split('+')[0]
                logout_time = int(history.split('+')[1])
                for blocker in blockerlist:
                    if current_client != user_logout and user_logout != blocker and TIME >= int(time.time()) - logout_time:
                        send_message = send_message + ' ' + user_logout
        #print('[send] ' + send_message)
        self.clientSocket.send(send_message.encode())

    def process_whoelse(self):
        index = 0
        send_message = 'Online users:'
        for client in ONLINE_USERS:
            if client == self.clientSocket:
                break
            index += 1
        current_client = USERNMAES[index]

        blockerlist = []
        for block_infor in BLACKLIST:
            blocker = block_infor.split('+')[0]
            blocked_user = block_infor.split('+')[1]
            if blocked_user == current_client:
                blockerlist.append(blocker)

        if len(blockerlist) == 0:
            for client_name in USERNMAES:
                if current_client != client_name:
                    send_message = send_message + ' ' + client_name
        else:            
            for client_name in USERNMAES:
                for blocker in blockerlist:
                    if current_client != client_name and client_name != blocker:
                        send_message = send_message + ' ' + client_name
        #print('[send] ' + send_message)
        self.clientSocket.send(send_message.encode())

    def process_message(self, message):
        message_list = message.split('<')
        send_message = message_list[2][:-1]
        receiver = message_list[1][:-1]
    
        sender_index = 0
        found = False
        for client in ONLINE_USERS:
            if client == self.clientSocket:
                found = True
                break
            sender_index += 1
        if not found:
            message = 'you need to log in to the server'
            #print(message)
            self.clientSocket.send(message.encode())
        else:
            f = open("credentials.txt", "r")
            outputdata = f.readlines()
            contain = False
            for line in outputdata:
                username = line.split()[0]
                if receiver == username:
                    contain = True
            # if the receiver is invalid
            if contain:
                receiver_index = 0
                receiver_found = False
                for online_client in USERNMAES:
                    if receiver == online_client:
                        receiver_found = True
                        break
                    else:
                        receiver_index += 1
                if receiver_found:
                    # check the black list of reciver
                    send_blocked = False
                    blocker = ''
                    blocked_user = ''
                    for block_infor in BLACKLIST:
                        blocker = block_infor.split('+')[0]
                        blocked_user =  block_infor.split('+')[1]
                        if blocked_user == USERNMAES[sender_index]:
                            send_blocked = True
                            break
                        else:
                            continue
                    if send_blocked and blocker == USERNMAES[receiver_index]:
                        message = 'sending successful'
                        self.clientSocket.send(message.encode())
                    else:
                        #print('[send] ' + send_message + ' to ' + receiver)
                        send_message = USERNMAES[sender_index] + ': ' + send_message
                        ONLINE_USERS[receiver_index].send(send_message.encode())
                        message = 'sending successful'
                        self.clientSocket.send(message.encode())
                # The receiver is offline
                else:
                    # check the black list of reciver
                    #print('store the message for offline delivery')
                    offlineDelivery = OfflineDelivery(send_message, receiver, sender_index)
                    offlineDelivery.start()
            else:
                send_message = 'receiver is not exist!'
                #print('[send] ' + send_message)
                self.clientSocket.send(send_message.encode())

    def process_broadcast(self, message):
        send_message = message[10:-1]
        index = 0
        found = False
        for client in ONLINE_USERS:
            if client == self.clientSocket:
                found = True
                break
            index += 1
        if not found:
            message = 'you need to log in to the server'
            #print(message)
            self.clientSocket.send(message.encode())
        else:
            #print('[send] ' + message)
            index_receiver = 0
            for client in ONLINE_USERS:
                receiver_blocked = False
                for blocked_infor in BLACKLIST:
                    if blocked_infor == USERNMAES[index_receiver] + '+' +USERNMAES[index]:
                        index_receiver += 1
                        receiver_blocked = True
                if client != self.clientSocket and not receiver_blocked:
                    client.sendall(send_message.encode())

    def process_logout(self):
        message = 'logout request'
        
        index_client = 0
        found = False
        for client in ONLINE_USERS:
            if client == self.clientSocket:
                found = True
                break
            index_client += 1
        if not found:
            message = 'you need to log in to the server'
            #print(message)
            self.clientSocket.send(message.encode())
        else:
            #print('[send] ' + message)
            self.clientSocket.send(message.encode())
            # send the notification to the clint who is logged out the server
            notification = USERNMAES[index_client]+ ' logs out the server'
            inputname = USERNMAES[index_client]

            index = 0
            blockedlist = []

            for block_infor in BLACKLIST:
                blocker = block_infor.split('+')[0]
                blocked_user = block_infor.split('+')[1]
                if blocker == inputname:
                    blockedlist.append(blocked_user)

            if len(blockedlist) == 0:
                for client in ONLINE_USERS:
                    if client != self.clientSocket:
                        client.sendall(notification.encode())
            else:
                for client in ONLINE_USERS:
                        for blocked_user in blockedlist:
                            if client != self.clientSocket and USERNMAES[index] != blocked_user:
                                client.sendall(notification.encode())
                            elif client != self.clientSocket and USERNMAES[index] == blocked_user:
                                continue
                        index += 1
            #print('[Remove] ' + inputname + ' from server')
            ONLINE_USERS.remove(self.clientSocket)
            USERNMAES.pop(index_client)
            logout_time = int(time.time())
            history = inputname + '+' + str(logout_time)
            contain_in_history =  False
            for history_user in HISTORY_USERS:
                user_logout = history_user.split('+')[0]
                if user_logout == inputname:
                    HISTORY_USERS.remove(history_user)
                    HISTORY_USERS.append(history)
                    contain_in_history =  True
            if not contain_in_history:
                HISTORY_USERS.append(history)

    def process_login(self):
        message = 'please enter your username'
        #print('[send] ' + message)
        self.clientSocket.send(message.encode())
        """
        The Server receives the username from client
        """
        data = self.clientSocket.recv(1024)
        inputname = data.decode()
        """
        The Server checks the username is contained in credentials.txt
        """
        f = open("credentials.txt", "r")
        outputdata = f.readlines()
        contain = False
        for line in outputdata:
            """
            if the user name is contained
            """
            username = line.split()[0]
            password = line.split()[1]
            for blocked_user in BLOCK_LOGIN_LIST:
                if blocked_user == inputname:
                    message = 'Please try to log in again after ' + str(timeBlock) + ' seconds'
                    #print('[send] ' + message)
                    self.clientSocket.send(message.encode())
                    return
            for user in USERNMAES:
                if user == inputname:
                    message = 'You can not log an account that already login '
                    self.clientSocket.send(message.encode())
                    return
            if inputname == username:
                contain = True

                message = 'please enter your password'
                #print('[send] ' + message)
                self.clientSocket.send(message.encode())

                data = self.clientSocket.recv(1024)
                inputpassword = data.decode()
                """
                first time
                """
                if inputpassword == password:
                    message = 'log in successful'
                    #print('[send] ' + message)
                    self.clientSocket.send(message.encode())
                    # if the user re-login, remove logout history
                    for history_user in HISTORY_USERS:
                        user_logout = history_user.split('+')[0]
                        if user_logout == inputname:
                            HISTORY_USERS.remove(history_user)
                    # add the user into list, if the use logs into the server
                    ONLINE_USERS.append(self.clientSocket)
                    USERNMAES.append(inputname)
                    # send the notification to the clint who is logged into the server
                    notification = inputname + ' logs into the server'
                    index = 0
                    blockedlist = []

                    for block_infor in BLACKLIST:
                        blocker = block_infor.split('+')[0]
                        blocked_user = block_infor.split('+')[1]
                        if blocker == inputname:
                            blockedlist.append(blocked_user)

                    if len(blockedlist) == 0:
                        for client in ONLINE_USERS:
                            if client != self.clientSocket:
                                client.sendall(notification.encode())
                    else:
                        for client in ONLINE_USERS:
                            for blocked_user in blockedlist:
                                if client != self.clientSocket and USERNMAES[index] != blocked_user:
                                    client.sendall(notification.encode())
                                elif client != self.clientSocket and USERNMAES[index] == blocked_user:
                                    continue
                            index += 1
                                        
                else:
                    #print('password is not match')
                    count = 0
                    while True:
                        message = 'please re-enter your password'
                        #print('[send] ' + message)
                        self.clientSocket.send(message.encode())

                        data = self.clientSocket.recv(1024)
                        inputpassword = data.decode()
                        if inputpassword == password:
                            message = 'log in successful'
                            #print('[send] ' + message)
                            self.clientSocket.send(message.encode())
                            # if the user re-login, remove logout history
                            for history_user in HISTORY_USERS:
                                user_logout = history_user.split('+')[0]
                                if user_logout == inputname:
                                    HISTORY_USERS.remove(history_user)
                            # add the use into list, if the use logs in to the server
                            ONLINE_USERS.append(self.clientSocket)
                            USERNMAES.append(inputname)
                            # send the notification to the clint who is logged into the server
                            notification = inputname + ' logs into the server'
                            for client in ONLINE_USERS:
                                if client != self.clientSocket:
                                    client.send(notification.encode())
                            break
                        elif count == 1:
                            BLOCK_LOGIN_LIST.append(inputname)
                            message = 'Please try to log in again after ' + str(timeBlock) + ' seconds'
                            handleBlockedLogIn = HandleBlockedLogIn(inputname)
                            handleBlockedLogIn.start()
                            #print('[send] ' + message)
                            self.clientSocket.send(message.encode())
                            break
                        else:
                            #print('password is not match')
                            count += 1
                            continue
                break
        f.close()
        """
            if the user name is not contained
        """
        if not contain:
            message = 'Please enter your password to create an account'
            #print('[send] ' + message)
            self.clientSocket.send(message.encode())
            data = self.clientSocket.recv(1024)
            inputpassword = data.decode()

            message = 'Please check your password to create an account'
            #print('[send] ' + message)
            self.clientSocket.send(message.encode())
            data = self.clientSocket.recv(1024)
            inputpassword2 = data.decode()

            # if the second input password is same as the first one, created account and inform client welcome message!
            if inputpassword == inputpassword2:
                UserName_PassWord = inputname + ' ' + inputpassword + '\n'
                message = 'Welcome!'
                #print('[send] ' + message)
                self.clientSocket.send(message.encode())
                f = open("credentials.txt", "a+")
                f.write(UserName_PassWord)
                f.close()
                
            # if the second input password is not same as the first one, re-send the check message
            else:
                while True:
                    message = 'password is not same as second password, please try again'
                    #print('[send] ' + message)
                    self.clientSocket.send(message.encode())
                    data = self.clientSocket.recv(1024)
                    inputpassword2 = data.decode()
                    if inputpassword == inputpassword2:
                        UserName_PassWord = inputname + ' ' + inputpassword + '\n'
                        message = 'Welcome!'
                        #print('[send] ' + message)
                        self.clientSocket.send(message.encode())
                        f = open("credentials.txt", "a+")
                        f.write(UserName_PassWord)
                        f.close()
                        break
            





print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")


while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()
