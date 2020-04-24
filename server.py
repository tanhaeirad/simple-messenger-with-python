import socket, threading
import random


def generate_session():
    session = ""
    for i in range(30):
        x = random.randint(0, 9)
        session += str(x)
    return session


class User:
    all_users = []

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.active_sessions = []
        User.all_users.append(self)

    def add_active_session(self, session):
        self.active_sessions.append(session)

    def del_session(self, session):
        self.active_sessions.remove(session)

    @staticmethod
    def get_user(username):
        for user in User.all_users:
            if username == user.username: return user
        return None

    @staticmethod
    def is_register(username):
        usernames = []
        for user in User.all_users:
            usernames.append(user.username)
        if username in usernames:
            return True
        return False

    @staticmethod
    def valid_for_login(username, password):
        if not User.is_register(username): return False
        user = User.get_user(username)
        if user.password == password: return True
        return False

    def active_sessions(self):
        return self.active_sessions


class Session:
    all_sessions = []

    def __init__(self, session, user):
        self.session_text = session
        self.pm = []
        self.user = user
        Session.all_sessions.append(self)

    @staticmethod
    def get_session(session_text):
        for s in Session.all_sessions:
            if s.session_text == session_text: return s
        return None

    @staticmethod
    def del_session(session_text):
        session = Session.get_session(session_text)
        Session.all_sessions.remove(session)

    @staticmethod
    def is_defined(session):
        for s in Session.all_sessions:
            if s.session_text == session: return True
        return False

    @staticmethod
    def get_user(session_text):
        for s in Session.all_sessions:
            if s.session_text == session_text: return s.user
        return None

    def add_pm(self, pm):
        self.pm.append(pm)

    def calc_not_seen_pm(self):
        all_pm = self.pm
        counter = 0
        for pm in all_pm:
            if not pm.seen: counter += 1
        return counter

    def get_not_seen_pm(self):
        all_pm = self.pm
        valid_pm = []
        for pm in all_pm:
            if not pm.seen:
                valid_pm.append(pm)
        return valid_pm


class Pm:
    def __init__(self, sender, msg):
        self.sender = sender
        self.msg = msg
        self.seen = False


def threaded(c, addr):
    while True:
        data = c.recv(1024)
        data = str(data, 'utf-8')
        command = data.split()[0]

        # for register
        if command == "register":
            username = data.split()[1]
            password = data.split()[2]

            if User.is_register(username):
                c.sendall(b"this username registered")
            else:
                User(username, password)
                c.sendall(b"you registered successfully")

        # for login
        elif command == "login":
            username = data.split()[1]
            password = data.split()[2]
            if User.valid_for_login(username, password):
                user = User.get_user(username)
                session_text = generate_session()
                user.add_active_session(session_text)
                session = Session(session_text, user)
                c.sendall(bytes(session_text, encoding='utf-8'))
            else:
                c.sendall(b"wrong username or password")

        # for logout
        elif command == "logout":
            session_text = data.split()[1]
            if Session.is_defined(session_text):
                user = Session.get_user(session_text)
                user.del_session(session_text)
                Session.del_session(session_text)
                c.sendall(b"your session logout successfully")
            else:
                c.sendall(b"invalid session")

        # for send
        elif command == "send":
            session_of_sender = data.split()[1]
            contact_username = data.split()[2]
            message = data.split()[3:]
            message = " ".join(message)
            x = ""
            flag = True
            if not Session.is_defined(session_of_sender):
                x += "invalid session"
                flag = False
            if not User.is_register(contact_username):
                x += "\nyour contact did not register"
                flag = False

            if flag:
                sender = Session.get_user(session_of_sender)
                receiver = User.get_user(contact_username)
                sessions_to_be_send = receiver.active_sessions
                for s in sessions_to_be_send:
                    session = Session.get_session(s)
                    pm = Pm(sender, message)
                    session.add_pm(pm)
                x = "your message send successfully"
                c.sendall(bytes(x, 'utf-8'))
            else:
                if x[0] == '\n': x = x[1:]
                c.sendall(bytes(x, 'utf-8'))
        #
        # # for receive
        elif command == "receive":
            session_text = data.split()[1]
            if not Session.is_defined(session_text):
                c.sendall(b"invalid session")
            else:
                session = Session.get_session(session_text)
                counter = session.calc_not_seen_pm()
                pms = session.get_not_seen_pm()
                out = ""
                out += str(counter)
                for pm in pms:
                    pm.seen = True
                    out += "$"
                    out += pm.sender.username
                    out += ": "
                    out += pm.msg
                if counter == 0:
                    c.sendall(b" ")
                else:
                    c.sendall(bytes(out, 'utf-8'))
        else:
            c.sendall(b"Invalid command")


host = ''
port = 1234
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))

s.listen(100)

for i in range(100):
    c, addr = s.accept()
    threading.Thread(target=threaded, args=(c, addr)).start()

s.close()
