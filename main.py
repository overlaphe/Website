# Coding:utf-8

import sys

sys.path.append('/home/Server/.local/lib/python3.8/site-packages')

import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import pickle
import time
import threading
import asyncio

if sys.platform == 'win32':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class BaseHandler(tornado.web.RequestHandler):
	def get_current_user(self):
		return self.get_secure_cookie("user")
	def get(self):
		if not current_user:
			self.redirect("/login")
	def get_User_id(self):
		global Data
		try:
			user = str(self.get_secure_cookie("user"),"utf-8")
			if user in Data["Name_id"]:
				return Data["Name_id"][user]
		except:
			return -1
	def get_permission_level(self):
		global Data
		id = self.get_User_id()
		if id == -1:
			return -1
		return Data["id_Data"][id]["PmLv"]

class MainHandler(BaseHandler):
	def get(self):
		self.redirect("/login")

class AdminPageHandler(BaseHandler):
	def get(self):
		if self.get_permission_level() != 0:
			self.redirect("/login")
		try:
			self.get_secure_cookie("temp")
			self.clear_cookie("temp")
		except:
			pass
		self.render("html/Admin.html")
	def post(self):
		self.set_secure_cookie("auto_login","0")
		self.redirect("/login")

class TestCheckinHandler(BaseHandler):
	def get(self):
		if self.get_permission_level() != 0:
			self.redirect("/login")
		User_Name = str(self.current_user,"utf-8")
		Students = ["asdasda a", "asdasfasfasfa b","asdasdasdasdas c","asdasdasdasdasd D"]
		Students.sort()
		Club_Name = "CS Club"
		self.render("html/Students-Check-in.html",list=Students,Title=Club_Name)
	def post(self):
		print("...I dnot really know if it do success")
		print("Just assume it is.")
		self.redirect("/Admin")

class SubmitHandler(BaseHandler):
	def get(self):
		if not self.current_user:
			self.redirect("/login")
			return -1
		self.render("html/Submit.html")

class IndexHandler(BaseHandler):
	def get(self):
		if not self.current_user:
			self.redirect("/login")
			return -1
		User_Name = str(self.current_user,"utf-8")
		self.write("test"+str(Data["id_Data"][Data["Name_id"][User_Name]]))

class LoginHandler(BaseHandler):
	def get(self):
		if self.current_user:
			try:
				if self.get_secure_cookie("auto_login") == b'1': 
					User_Name = str(self.current_user,"utf-8")
					Level = Data["id_Data"][Data["Name_id"][User_Name]]["PmLv"]
					if Level == 0:
						self.redirect("/Admin")
					else:
						self.redirect("/index")
			except:
				pass
		self.render("html/Login.html")
	def post(self):
		global Data
		User_id = self.get_argument("user")
		Pswd	= self.get_argument("pswd")
		if User_id in Data["Name_id"] and Pswd == Data["id_Data"][Data["Name_id"][User_id]]["Pswd"]:
			try:
				self.get_argument("Rmbr")
				self.set_secure_cookie("auto_login", "1")
			except:
				self.set_secure_cookie("auto_login", "0")
			self.set_secure_cookie("user", User_id)
			if Data["id_Data"][Data["Name_id"][User_id]]["PmLv"] == 0:
				self.redirect("/Admin")
				return
			self.redirect("/index")
		self.redirect("/WrongPassword")

class WrongPswdHandler(BaseHandler):
	def get(self):
		if self.get_secure_cookie("wherefrom") == "old_P":
			self.render("html/WrongPa.html")
		if self.get_secure_cookie("wherefrom") == "new_p":
			self.render("html/RepeatPa.html")
		else:
			self.render("html/WrongPassword - 副本.html", title = "Wrong Password", des = "or wrong user name", url="../login", text="Go back")
	def post(self):
		if self.get_secure_cookie("wherefrom") == "old_P":
			self.redirect("/PasswordChange")
		if self.get_secure_cookie("wherefrom") == "new_p":
			self.redirect("/PasswordChange")
		else:
			self.redirect("/login")

class ECACreationHandler(BaseHandler):
	def get(self):
		if get_permission_level()==0:
			self.render("html/ECACreate.html")
		else:
			self.redirect("/login")
	def post(self):
		self.redirect("/Admin")

class PasswordChangeHandler(BaseHandler):
	def get(self):
		self.render("html/PasswordChange.html")
	def post(self):
		if self.get_argument("original_p") == Data["id_Data"][self.get_User_id()]["Pswd"]:
			if self.get_argument("new_p") == self.get_argument("repeat_p"):
				Data["id_Data"][self.get_User_id()]["Pswd"] = self.get_argument("new_p")
				if self.get_permission_level() == 0:
					self.redirect("/Admin")
				elif self.get_permission_level() == 1:
					self.redirect("/index")
			else:
				self.set_secure_cookie("wherefrom","new_p")
				self.redirect("/WrongPassword")
		else:
			self.set_secure_cookie("wherefrom","old_P")
			self.redirect("/WrongPassword")

class TestHandler(BaseHandler):
	def get(self):
		self.render("html/test.html")
	def post(self):
		print(self.get_argument("i"))
		self.redirect("/login")

class ECACreationHandler(BaseHandler):
	def get(self):
		if self.get_permission_level()==0:
			self.render("html/ECACreate.html")
		else:
			self.redirect("/login")
	def post(self):
		Days = {}
		if self.get_argument("ECA_name") == "":
			print(".?")
			self.redirect("/Admin")
			return
		for i in [1,2,3,4]:
			try:
				self.get_argument(str(i))
				Days[i] = True
			except:
				pass
		Days["Name"] = self.get_argument("ECA_name")
		self.set_secure_cookie("temp",str(Days))
		try:
			self.get_argument("search_student")
			self.redirect("/Search/0/ ")
			return
		except:
			try:
				self.get_argument("search_teacher")
				self.redirect("/Search/1/ ")
				return
			except:
				pass
		self.redirect("/Admin")

class SearchHandler(BaseHandler):
	def get(self, b, a):
		print(str(a))
		global Data
		b = int(b)
		m = Search(b,str(a))
		self.render("html/test.html",list=m,type=b)
	def post(self, *args):
		f = self.get_argument("i")
		print(f)
		g = self.get_argument("j")
		print(g)
		self.redirect("/login")

def New_Student(Name):
	global Data
	target_id = Data["Avlb"][0]
	if Data["Avlb"].__len__() == 1:
		Data["Avlb"][0] += 1
	else:
		Data["Avlb"] = Data["Avlb"][1:]
	Data["Name_id"][Name] = target_id
	Data["id_Name"][target_id] = Name
	Data["id_Data"][target_id] = {"Pswd":"123456","Name":Name, "PmLv": 1, "Lead":[]}

def Remove_Student(Name):
	global Data
	if Name not in Data["Name_id"]:
		return
	id = Data["Name_id"][Name]
	del Data["id_Name"][id]
	del Data["id_Data"][id]
	del Data["Name_id"][Name]
	Data["Avlb"].append(id)
	Data["Avlb"].sort()

def Avail_student(day):
	global Data
	ret = []
	for i in Data['id_Data']:
		if day in Data['id_Data'][i]['avai']:
			ret.append(i)
	return ret

def Remove_Avail(id, day):
	global Data
	Data['id_Data'][id]['avai'].remove(day)

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
	Data["id_Data"][id][Key] = Content

def Auto_Save():
	global Data
	while True:
		pickle.dump(Data, open("Data","wb"))
		time.sleep(60)

def Search(ty, string):
	print("1%s1"%string)
	if ty == 0 or string == " " or string == "":
		return [[-1," "]]
	global Data
	ret = []
	for i in Data["id_Data"]:
		if Data["id_Data"][i]["PmLv"] == ty:
			for n in string.split(" "):
				if n == "":
					continue
				if n.lower() not in Data["id_Data"][i]["Name"].lower():
					break
			else:
				ret.append([i,Data["id_Name"][i]])
	print(ret)
	if ret == [[]]:
		return [[-1," "]]
	return ret

<<<<<<< Updated upstream
Data = {"Name_id":{},"id_Name":{},"id_Data":{},"Avlb":[0]}
=======
def new_Club(Name,advisor,leader,days):
	global Data
	target_id = None
	if len(Data["Clubs"]) == 0:
		target_id = 0
	else:
		target_id = max(Data["Clubs"]) + 1
	Data["Clubs"][target_id] = {}
	Data["Clubs"][target_id]["Name"] = Name
	Data["Clubs"][target_id]["advisor"] = advisor
	Data["Clubs"][target_id]["leader"] = leader
	Data["Clubs"][target_id]["students"] = {}
	Data["id_Data"][0]["Lead"].append(target_id)
	Data["id_Data"][advisor]["Lead"].append(target_id)
	Data["id_Data"][leader]["Lead"].append(target_id)
	for day in days:
		Data["Clubs"][target_id]["students"][day] = []
		add_student_to_club(target_id,leader,day)
		Remove_Avail(leader,day)

def add_student_to_club(Club_id,student_id,day):
	global Data
	Data["Clubs"][Club_id]["students"][day].append(student_id)

def get_day():
	return 2

Data = {"Name_id":{},"id_Name":{},"id_Data":{},"Avlb":[0], "Clubs":{}}
Temp = {}
>>>>>>> Stashed changes

New_Student("Admin")
New_Student("TonyZhaChuanming")
Data_Modify("Admin","PmLv",0)
Data_Modify("TonyZhaChuanming","Avai",[1,3])

Search(1," ")

"""
To Do list:
	make a template for notion
	make a more aligned shit
"""

if True:
	threading.Thread(target=Auto_Save).start()
	app = tornado.web.Application(handlers=[(r"/",MainHandler),
		(r"/login",LoginHandler),
		(r"/WrongPassword",WrongPswdHandler),
		(r"/Admin",AdminPageHandler),
		(r"/Admin/ClubCreating",AdminPageHandler),
		(r"/index",IndexHandler),
		(r"/TestCheckin",TestCheckinHandler),
		(r"/Asset/(.*)",tornado.web.StaticFileHandler, {"path":"./Asset"}),
		(r"/ECACreation",ECACreationHandler),
		(r"/PasswordChange", PasswordChangeHandler),
		(r"/Search/(.*)/(.*)",SearchHandler)],
	cookie_secret="1234567")
	server = tornado.httpserver.HTTPServer(app)
	server.listen(8800)
	tornado.ioloop.IOLoop.instance().start()
