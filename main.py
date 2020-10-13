# Coding:utf-8

import sys

sys.path.append('/home/WebLinux/.local/lib/python3.8/site-packages')

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
		li = {}
		for i in Data["id_Data"][self.get_User_id()]["Lead"]:
			li[i] = Data["Clubs"][i]["Name"]
		di = {}
		for i in li:
			if get_day() in Data["Clubs"][i]["students"]:
				di[i] = Data["Clubs"][i]["Name"]
		self.render("html/Admin.html",di=di,li=li)
	def post(self):
		self.set_secure_cookie("auto_login","0")
		self.redirect("/login")

class StandardHandler(BaseHandler):
	def get(self):
		global Data
		if self.get_permission_level() == 0:
			self.redirect("/Admin")
		di = {}
		li = Data["id_Data"][self.get_User_id()]["Lead"]
		for i in li:
			if Data["id_Name"][Data["Clubs"][i]["leader"]]:
				if get_day() in Data["Clubs"][i]["students"]:
					di[i] = Data["Clubs"][i]["Name"]
		self.render("html/StandardUser.html", user = self.get_current_user(), dic=di)
	def post(self):
		self.set_secure_cookie("auto_login","0")
		self.redirect("/login")

class ManageHandler(BaseHandler):
	def get(self,a):
		global Data
		try:
			a = int(a)
		except:
			return
		if a not in Data["id_Data"][self.get_User_id()]["Lead"]:
			self.redirect("/notice/No Permission/Just leave this page/Admin/Go back")
			return
		try:
			f = self.get_secure_cookie("temp")
			f = eval(f)
			add_student_to_club(a,f["member"],int(f["day"]))
			print("fin")
			self.clear_cookie("temp")
		except:
			pass
		Students = Data["Clubs"][a]["students"]
		for i in Students:
			Students[i].sort()
		dic = {}
		lead = {}
		for i in Students:
			dic[i] = {}
			lead[i] = {}
			for j in Students[i]:
				dic[i][j] = Data["id_Name"][j]
				lead[i][j] = a in Data["id_Data"][j]["Lead"]
		print(dic,lead)
		Club_Name = Data["Clubs"][a]["Name"]
		self.render("html/Students-Management-new.html",dic=dic,Title=Club_Name,lead=lead,l=self.get_permission_level() == 0)
	def post(self,a):
		global Data
		if int(a) not in Data["id_Data"][self.get_User_id()]["Lead"]:
			self.redirect("/notice/No Permission/Just leave this page/Admin/Go back")
			return
		try:
			self.get_argument("submit")
			self.redirect("/MainPage")
			return
		except:
			pass
		f = int(self.get_argument("day"))
		try:
			self.get_argument("search_student")
			self.redirect("/MemberAdd/%s/%s/ "%(int(a),f))
			return	
		except:
			pass
		for i in Data["Clubs"][int(a)]["students"][f]:
			try:
				self.get_argument(str(i))
				Remove_Member(i, int(a),f)
				break
			except:
				pass
		for i in Data["Clubs"][int(a)]["students"][f]:
			try:
				print("?adada",i)
				self.get_argument("l"+str(i))
				print("?adadab",i)
				print(Data["id_Data"][i]["Lead"])
				if int(a) in Data["id_Data"][i]["Lead"]:
					del Data["id_Data"][i]["Lead"][Data["id_Data"][i]["Lead"].index(int(a))]
				else:
					Data["id_Data"][i]["Lead"].append(int(a))
				print(Data["id_Data"][i]["Lead"])
				break
			except:
				pass
		self.redirect("")
		print("?")

class CheckinHandler(BaseHandler):
	def get(self,a):
		global Data
		try:
			a = int(a)
		except:
			return
		if a not in Data["id_Data"][self.get_User_id()]["Lead"]:
			self.redirect("/notice/No Permission/Just leave this page/Admin/Go back")
			return
		print(Data["Clubs"][a]["students"])
		Students = Data["Clubs"][a]["students"][get_day()]
		Students.sort()
		di = {}
		for s in Students:
			di[s] = Data["id_Name"][s]
		Club_Name = Data["Clubs"][a]["Name"]
		print(di,"?")
		self.render("html/Attendance.html",di=di,Title=Club_Name,Club_id=a)
	def post(self,a):
		global Temp
		try:
			a = int(a)
		except:
			return
		Temp[a] = {}
		for i in Data["Clubs"][a]["students"][get_day()]:
			m = self.get_argument(str(i))
			if m == "A":
				Temp[a][i] = "A"
			elif m == "T":
				Temp[a][i] = "T"
		print(Temp)
		self.redirect("/MainPage")

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
					self.redirect("/MainPage")
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
			self.redirect("/MainPage")
			return
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
		self.redirect("/MainPage")

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
		if b in ["1","2"]:
			print(str(a))
			global Data
			b = int(b)
			m = Search(b,str(a))
			self.render("html/search.html",list=m,type=b,a=a)
		else:
			m = Search(1,str(a))
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
			self.redirect("/Manage/" + str(int(g)-3))

class MemberSearchHandler(BaseHandler):
	def get(self, club_id, day, s):
		m = Search(1,s)
		print(m)
		self.render("html/memberSearch.html",list=m,a=1)
	def post(self, club_id, day, s):
		print("?",club_id, day, s)
		try:
			text = self.get_argument("T")
			self.redirect("/MemberAdd/%s/%s/%s"%(club_id,day,text))
			return
		except:
			pass
		temp = {"day":day,"member":int(self.get_argument("i"))}
		print(temp)
		self.set_secure_cookie("temp",str(temp))
		self.redirect("/Manage/%s"%club_id)
		print("?")

class MainPageHandler(BaseHandler):
	def get(self):
		if self.get_permission_level() == 0:
			self.redirect("/Admin")
		elif self.get_permission_level() == 1:
			self.redirect("/Standard")
		else:
			self.redirect("/login")

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
			print(Data["id_Data"][self.get_User_id()],a)
			self.redirect("/notice/No Permission/Just leave this page/Admin/Go back")
			return
		s = Data["Clubs"][a]["students"]
		self.render("html/ClubMemberManager.html",s=s)

class NoticeHandler(BaseHandler):
	def get(self,a,b,c,d):
		self.render("html/notice.html", title = a, des = b, url="/"+c, text=d)

class FeedBackHandler(BaseHandler):
	def get(self):
		self.write("<form method=\"post\"><input type=\"text\" name=\"str\" placeholder=\" Feedback...\"><input type=\"submit\" value=\"submit\"></form>")
	def post(self):
		print(self.get_argument("str"))
		self.redirect("")


def Remove_Member(member_id,club_id,day):
	#
	global Data
	Data["Clubs"][club_id]["students"][day].remove(member_id)
	Data["id_Data"][id]["Lead"].remove(club_id)

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
	global Data, Temp
	while True:
		pickle.dump(Data, open("Data","wb"))
		time.sleep(60)
		f = time.localtime()
		n = f.tm_hour*3600+f.tm_min*60+f.tm_sec
		if n > 58500 and n < 58570:
			pickle.dump(Temp,open("%s-%sdata"%(f.tm_mon,f.tm_mday),"wb"))
			Temp = {}

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

def new_leader_of_club(Club_id,student_id):
	if Club_id in Data["id_Data"][student_id]["Lead"]:
		return
	Data["id_Data"][student_id]["Lead"].append(Club_id)

def get_day():
	return time.localtime().tm_wday+1

Data = {"Name_id":{},"id_Name":{},"id_Data":{},"Avlb":[0], "Clubs":{}}
if True:
	Data = pickle.load(open("Data","rb"))
Temp = {}
New_Student("Teacher")
Data_Modify("Teacher","PmLv",2)

"""
To Do list:
	Three types of attendence
		Click once, turn green (present)
		Click twice, turn yellow (tardy)
		Click thrice, turn back to red (absent)
	User for teachers
		One teacher, one account
	More formal Feedback page
		Just, make some decoration
	About page?(need discussion)
	Empty home page
"""

if True:
	threading.Thread(target=Auto_Save).start()
	app = tornado.web.Application(handlers=[(r"/",MainHandler),
		(r"/login",LoginHandler),
		(r"/Admin",AdminPageHandler),
		(r"/Admin/ClubCreating",AdminPageHandler),
		(r"/index",IndexHandler),
		(r"/Standard", StandardHandler),
		(r"/Checkin/(.*)",CheckinHandler),
		(r"/Manage/(.*)", ManageHandler),
		(r"/Asset/(.*)",tornado.web.StaticFileHandler, {"path":"./Asset"}),
		(r"/ECACreation",ECACreationHandler),
		(r"/PasswordChange", PasswordChangeHandler),
		(r"/ClubManage/(.*)", ClubManageHandler),
		(r"/Attendence",AttendenceHandler),
		(r"/MainPage",MainPageHandler),
		(r"/Search/(.*)/(.*)",SearchHandler),
		(r"/Feedback",FeedBackHandler),
		(r"/notice/(.*)/(.*)/(.*)/(.*)",NoticeHandler),
		(r"/MemberAdd/(.*)/(.*)/(.*)",MemberSearchHandler)],
	cookie_secret="1234567")
	server = tornado.httpserver.HTTPServer(app)
	server.listen(8800)
	tornado.ioloop.IOLoop.instance().start()