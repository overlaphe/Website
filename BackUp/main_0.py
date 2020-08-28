import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import pickle
import time
import threading

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.write("Hello, "+name)

class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="user">'
                   'Password: <input type="text" name="pswd">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')
    def post(self):
        global Data
        User_id = self.get_argument("user")
        Pswd    = self.get_argument("pswd")
        if User_id in Data["Name_id"] and Pswd == Data["id_Data"][Data["Name_id"][User_id]]["Pswd"]:
            self.set_secure_cookie("user", User_id)
            self.redirect("/")
        self.redirect("/WrongPassword")

class WrongPswdHandler(BaseHandler):
    def get(self):
        self.write("wrong username or password!\n"
                   '<html<body><form action="/WrongPassword" method="post">'
                   '<input type="submit" value="login">'
                   '<form></body></html>')
    def post(self):
        self.redirect("/login")

def New_Student(Name):
    global Data
    target_id = Data["A"][0]
    if Data["A"].__len__() == 1:
        Data["A"][0] += 1
    else:
        Data["A"] = Data["A"][1:]

    Data["Name_id"][Name] = target_id
    Data["id_Name"][target_id] = Name
    Data["id_Data"][target_id] = {"Pswd":"123456","Name":Name}

def Remove_Student(Name):
    global Data
    if Name not in Data["Name_id"]:
        return
    id = Data["Name_id"][Name]
    del Data["id_Name"][id]
    del Data["id_Data"][id]
    del Data["Name_id"][Name]
    Data["A"].append(id)
    Data["A"].sort()

def Data_read(id):
    global Data
    if type(id) == str:
        if id not in Data["Name_id"]:
            return -1
        id = Data["Name_id"][id]
    return Data["id_Data"][id]

def Data_Modify(id,Key,Content):
    global Data
    if type(id) == str:
        if id not in Data["Name_id"]:
            return -1
        id = Data["Name_id"][id]
    Data["id_Data"][id] = Content

def Auto_Save():
    global Data
    while True:
        pickle.dump(Data, open("Data","wb"))
        time.sleep(60)

Data = pickle.load(open("Data","rb"))

threading.Thread(target=Auto_Save).start()

app = tornado.web.Application(handlers=[(r"/",MainHandler),(r"/login",LoginHandler),(r"/WrongPassword",WrongPswdHandler)],cookie_secret="1234567")
server = tornado.httpserver.HTTPServer(app)
server.listen(80)
tornado.ioloop.IOLoop.instance().start()
