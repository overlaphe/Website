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
		global Data
		if self.get_permission_level() != 0:
			self.redirect("/login")
		try:
			self.get_secure_cookie("temp")
			self.clear_cookie("temp")
		except:
			pass
		li = Data["id_Data"][self.get_User_id()]["Lead"]
		di = {}
		for i in li:
			di[i] = Data["Clubs"][i]["Name"]
		self.render("html/Admin.html",di=di)
	def post(self):
		self.set_secure_cookie("auto_login","0")
		self.redirect("/login")

class CheckinHandler(BaseHandler):
	def get(self,a):
		global Data
		try:
			a = int(a)
		except:
			return
		if self.get_permission_level() != 0:
			self.redirect("/login")
		if a not in Data["id_Data"][self.get_User_id()]["Lead"]:
			self.redirect("/notice/No Permission/Just leave this page/Admin/Go back")
			return
		Students = Data["Clubs"][a]["students"][get_day()]
		Students.sort()
		di = {}
		for s in Students:
			di[s] = Data["id_Name"][s]
		Club_Name = Data["Clubs"][a]["Name"]
		self.render("html/Students-Check-in.html",di=di,Title=Club_Name)
	def post(self,a):
		global Temp
		try:
			a = int(a)
		except:
			return
		Temp[a] = []
		for i in Data["Clubs"][a]["students"][get_day()]:
			try:
				self.get_argument(str(i))
			except:
				Temp[a].append(i)
		print(Temp)
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
		self.redirect("/notice/Wrnong Password/or wrong user name/login/Go back")

class PasswordChangeHandler(BaseHandler):
	def get(self):
		self.render("html/PasswordChange.html")
	def post(self):
		if self.get_argument("original_p") != Data["id_Data"][self.get_User_id()]["Pswd"]:
			self.redirect("notice/The password is wrong/or wrong user name/PasswordChange/Go back")
			return
		if self.get_argument("new_p") != self.get_argument("repeat_p"):
			self.redirect("/notice/The old password is not same as new/or wrong user name/PasswordChange/Go back")
			return
		if self.get_argument("new_p").__len__() < 8:
			self.redirect("/notice/The passowrd is too short/at least 8 digits/PasswordChange/Go back")
			return
		Data["id_Data"][self.get_User_id()]["Pswd"] = self.get_argument("new_p")
		if self.get_permission_level() == 0:
			self.redirect("/Admin")	
			return
		self.redirect("/index")

class ECACreationHandler(BaseHandler):
	def get(self):
		global Data
		if self.get_permission_level()!=0:
			self.redirect("/login")
			return
		data = {}
		try:
			data = eval(self.get_secure_cookie("temp"))
			print(data,"?")
		except:
			pass
		for i in [1,2,3,4]:
			if i not in data:
				data[i] = False
		if "Name" not in data:
			data["Name"] = ""
		for i in ["2","1"]:
			if i not in data:
				data[i] = "Not selected yet"
			else:
				data[i] = Data["id_Name"][data[i]]
		print(data)
		self.render("html/ECACreate.html",list=data)			
	def post(self):
		Days = {}
		m = []
		try:
			Days = eval(self.get_secure_cookie("temp"))
			print(Days)
		except:
			pass
		for i in [1,2,3,4]:
			try:
				self.get_argument(str(i))
				Days[i] = True
				m.append(i)
			except:
				Days[i] = False
		Days["Name"] = self.get_argument("ECA_name")
		self.set_secure_cookie("temp",str(Days))
		try:
			self.get_argument("search_student")
			self.redirect("/Search/2/ ")
			return
		except:
			try:
				self.get_argument("search_teacher")
				self.redirect("/Search/1/ ")
				return
			except:
				pass
		try:
			new_Club(Days["Name"],Days['2'],Days['1'],m)
			self.redirect("/notice/Succeed!/Club create finisded/Admin/Go back")
		except:
			self.redirect("/notice/Missing Infomation/re fill-in the form please/ECACreation/Go back")

class SearchHandler(BaseHandler):
	def get(self, b, a):
		print(str(a))
		global Data
		b = int(b)
		m = Search(b,str(a))
		self.render("html/search.html",list=m,type=b,a=a)
	def post(self, b, a):
		try:
			text = self.get_argument("T")
			self.redirect("/Search/%s/%s"%(b,text))
			return
		except:
			pass
		n = self.get_argument("i")
		print(n)
		g = self.get_argument("j")
		print(g,"j")
		try:
			f = self.get_secure_cookie("temp")
			f = eval(f)
		except:
			f = {}
		f[g] = int(n)
		self.set_secure_cookie("temp",str(f))
		if int(g) in [0,1,2]:
			self.redirect("/ECACreation")
		else:
			self.redirect("/Admin")

class AttendenceHandler(BaseHandler):
	def get(self):
		global Temp,Data
		dicti = {}
		for s in Data["Clubs"]:
			dicti[s]=[]
			dicti[s].append(Data["Clubs"][s]["Name"])
			li = []
			if s in Temp:
				dicti[s].append("checked")
				for i in Temp[s]:
					li.append(Data["id_Name"][i])
			else:
				dicti[s].append("unchecked")
				li = []
			dicti[s].append(li)
		self.render("html/Attendence.html",dicti=dicti)

class ClubManageHandler(BaseHandler):
	def get(self,a):
		global Data
		try:
			a = int(a)
		except:
			return
		if a not in Data["id_Data"][self.get_User_id()]["Lead"]:
			self.redirect("/notice/No Permission/Just leave this page/Admin/Go back")
			return
		s = Data["Clubs"][a]["students"]
		self.render("html/ClubMemberManager.html",s=s)


class NoticeHandler(BaseHandler):
	def get(self,a,b,c,d):
		self.render("html/notice.html", title = a, des = b, url="/"+c, text=d)

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
	if ret == [[]]:
		return [[-1," "]]
	return ret

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

def add_student_to_club(Club_id,student_id,day):
	global Data
	Data["Clubs"][Club_id]["students"][day].append(student_id)

def get_day():
	return 2

Data = {"Name_id":{},"id_Name":{},"id_Data":{},"Avlb":[0], "Clubs":{}}
Temp = {}

New_Student("Admin")
New_Student("TonyZhaChuanming")
New_Student("EthanChangWuji")
New_Student("JoshAntonio")
Data_Modify("JoshAntonio","PmLv",2)
Data_Modify("Admin","PmLv",0)

new_Club("CS Club",3,1,[2,4])

print(Data)

"""
To Do list:
	make a template for notion
	make a more aligned shit
"""

if True:
	threading.Thread(target=Auto_Save).start()
	app = tornado.web.Application(handlers=[(r"/",MainHandler),
		(r"/login",LoginHandler),
		(r"/Admin",AdminPageHandler),
		(r"/Admin/ClubCreating",AdminPageHandler),
		(r"/index",IndexHandler),
		(r"/Checkin/(.*)",CheckinHandler),
		(r"/Asset/(.*)",tornado.web.StaticFileHandler, {"path":"./Asset"}),
		(r"/ECACreation",ECACreationHandler),
		(r"/PasswordChange", PasswordChangeHandler),
		(r"/ClubManage/(.*)", ClubManageHandler),
		(r"/Attendence",AttendenceHandler),
		(r"/Search/(.*)/(.*)",SearchHandler),
		(r"/notice/(.*)/(.*)/(.*)/(.*)",NoticeHandler)],
	cookie_secret="1234567")
	server = tornado.httpserver.HTTPServer(app)
	server.listen(8800)
	tornado.ioloop.IOLoop.instance().start()