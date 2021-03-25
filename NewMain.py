import threading
import tornado.ioloop
import tornado.web
import tornado.httpserver
import time
import pickle
import Manager

# Coding:utf-8

import sys

sys.path.append('/home/WebLinux/.local/lib/python3.8/site-packages')

if sys.platform == 'win32':
	import asyncio
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class BaseHandler(tornado.web.RequestHandler):
	@property
	def is_not_current_user(self):
		if not self.get_secure_cookie('user'):
			return True
		user = self.get_secure_cookie('user')
		if not self.get_secure_cookie("pswd"):
			return True
		pswd = str(self.get_secure_cookie('pswd'), 'utf-8')
		try:
			if Manager.getUserById(int(user)).password + "salt" != pswd:
				print(Manager.getUserById(int(user)).password + "salt", pswd)
				print("3")
				return True
		except:
			return True
		return False

	def current_user(self):
		if self.is_not_current_user:
			return
		user_id = int(self.get_secure_cookie('user'))
		return Manager.Data["users"][user_id]

	def option_checked(self, key):
		try:
			self.get_argument(key)
			return True
		except:
			return False


class MainHandler(BaseHandler):
	def get(self):
		if not self.is_not_current_user:
			try:
				self.get_secure_cookie("Rmbr")
				self.redirect("/HomePage")
				return
			except:
				pass
		self.redirect("/login")


class NoticeHandler(BaseHandler):
	def get(self, a, b, c, d):
		self.render("html/notice.html", title=a, des=b, url="/" + c, text=d)


class LoginHandler(BaseHandler):
	def get(self):
		self.render("html/Login.html")

	def post(self):
		global Data
		User = Manager.UserSearch(self.get_argument("name"))
		Pswd = self.get_argument("pswd")
		if User != -1 and User.password == Pswd:
			self.set_secure_cookie("user", str(User.id))
			self.set_secure_cookie("pswd", Pswd + "salt")
			self.redirect("/HomePage")
			return
		try:
			self.get_argument("Rmbr")
			self.set_secure_cookie("Rmbr", "?")
		except:
			pass
		self.redirect("/notice/Wrong Password/or wrong user name/login/Go back")


class HomePageHandler(BaseHandler):
	def get(self):
		if self.is_not_current_user:
			self.redirect("/notice/Please login/Why/login/Go back")
			return
		LeadingClubs = []
		for club in Manager.Data['clubs'].values():
			if self.current_user().isLeading(club):
				LeadingClubs.append(club)
		LeadingClubs.sort()
		AttendanceClubs = []
		if get_day() in [1, 2, 3, 4]:
			for club in LeadingClubs:
				if club.students[get_day()] != []:
					AttendanceClubs.append(club)
		self.render("html/HomePage.html", LeadingClubs=LeadingClubs, AttendanceClubs=AttendanceClubs,
					User=self.current_user())

	def post(self):
		self.clear_cookie("user")
		self.clear_cookie("Rmbr")
		self.redirect("/login")


class CheckinHandler(BaseHandler):
	def get(self, a):
		club = Manager.getClubById(int(a))
		if not self.current_user().isLeading(club):
			self.redirect("/notice/No Permission/Just leave this page/HomePage/Go back")
			return
		if get_day() not in [1, 2, 3, 4] or club.students[get_day()] == []:
			self.redirect("/notice/No student this day/No ECA this day/HomePage/Go back")
			return
		students = club.students[get_day()]
		students.sort()
		self.render("html/Students-Check-in.html", students=students, club=club)

	def post(self, a):
		club = Manager.getClubById(int(a))
		if not self.current_user().isLeading(club):
			self.redirect("/HomePage")
			return
		if get_day() not in [1, 2, 3, 4] or club.students[get_day()] == []:
			self.redirect("/HomePage")
			return
		for student in club.students[get_day()]:
			Att = self.get_argument(str(student.id))
			if Att == "A":
				Manager.setStudentAtt(student, club, 'A')
			elif Att == "T":
				Manager.setStudentAtt(student, club, 'T')
			else:
				Manager.setStudentAtt(student, club, 'P')
		Manager.ClubChecked(club)
		self.redirect("/HomePage")


class ECACreationHandler(BaseHandler):
	def get(self):
		if self.is_not_current_user:
			self.redirect("/notice/Haven't Login/Just leave this page/login/Go back")
			return
		print("test")
		if self.current_user().permissionLevel != 2:
			self.redirect("/notice/No Permission/Just leave this page/HomePage/Go back")
			return
		self.render("html/ECACreate.html", Info=self.current_user().Temp)

	def post(self):
		self.current_user().Temp['ECA_Name'] = self.get_argument('ECA_Name')
		try:
			self.get_argument('search_teacher')
			self.redirect('/Search?Target=ECACreation&type=Student&Search=&Ttype=ECA_Leader')
			return
		except:
			pass
		try:
			self.get_argument('search_student')
			self.redirect('/Search?Target=ECACreation&type=Teacher&Search=&Ttype=ECA_Advisor')
			return
		except:
			pass
		try:
			Name = self.current_user().Temp['ECA_Name']
			Leader = self.current_user().Temp['ECA_Leader']
			Advisor = self.current_user().Temp['ECA_Advisor']
			del self.current_user().Temp['ECA_Name']
			del self.current_user().Temp['ECA_Leader']
			del self.current_user().Temp['ECA_Advisor']
			club = Manager.Club(Name)
			Leader.LeadClub(club)
			Advisor.LeadClub(club)
			self.redirect("/HomePage")
		except:
			self.redirect("/notice/Missing Argument/Please full All the information/ECACreation/Go back")


class SearchHandler(BaseHandler):
	def get(self):
		try:
			target = self.get_argument('Target')
			Stype = self.get_argument('type')
			Keyword = self.get_argument('Search')
			Ttype = self.get_argument('Ttype')
		except:
			self.redirect("/notice/Error/Less argument than needed/HomePage/Go back to Home Page")
			return
		Ret = Manager.UserMatch(Keyword, eval("Manager." + Stype))
		Ret.sort()
		self.render("html/search.html", SearchList=Ret, Result=Keyword)

	def post(self):
		SaveKey = self.get_argument('Ttype')
		try:
			self.get_argument('i')
			self.current_user().Temp[SaveKey] = Manager.getUserById(int(self.get_argument('i')))
			self.redirect("/" + self.get_argument("Target"))
		except:
			target = self.get_argument('Target')
			Stype = self.get_argument('type')
			Keyword = self.get_argument('T')
			self.redirect("/Search?Target=%s&type=%s&Search=%s&Ttype=%s" % (target, Stype, Keyword, SaveKey))


class ManageHandler(BaseHandler):
	def get(self, a):
		club = Manager.getClubById(int(a))
		if not self.current_user().isLeading(club):
			self.redirect("/HomePage")
			return
		Temp = self.current_user().Temp
		if "Adding_Student" in Temp:
			if Temp["Adding_Student"] not in club.students[Temp["Adding_Day"]]:
				Temp["Adding_Student"].JoinClub(club, Temp["Adding_Day"])
			del Temp['Adding_Day']
			del Temp['Adding_Student']
		if "Adding_Ad" in Temp:
			if Temp['Adding_Ad'] not in club.leaders:
				Temp['Adding_Ad'].LeadClub(club)
				del Temp['Adding_Ad']
		for day in club.students:
			club.students[day].sort()
		User = self.current_user()
		self.render("html/Students-Management-new.html", club=club, user=User)

	def post(self, a):
		club = Manager.getClubById(int(a))
		try:
			self.get_argument("submit")
			self.redirect("/HomePage")
			return
		except:
			pass
		try:
			self.get_argument("search_Ad")
			self.redirect('/Search?Target=Manage/%s&type=Teacher&Search=&Ttype=Adding_Ad' % club.id)
			return
		except:
			pass
		try:
			self.get_argument("DismissClub")
			club.Dismiss()
			self.redirect(
				'/notice/Club is Dismissed/Say Sorry to club members if that was an accident/HomePage/Go back')
			return
		except:
			pass
		if not self.current_user().isLeading(club):
			self.redirect("/HomePage")
			return
		day = int(self.get_argument('day'))
		try:
			self.get_argument('search_student')
			self.redirect('/Search?Target=Manage/%s&type=Student&Search=&Ttype=Adding_Student' % club.id)
			self.current_user().Temp['Adding_Day'] = day
			return
		except:
			pass
		for student in club.students[day]:
			try:
				state = self.get_argument(str(student.id))
				if self.get_argument(str(student.id)) == 'Lead':
					if student.isLeading(club):
						student.UnleadClub(club)
					else:
						student.LeadClub(club)
				else:
					student.LeaveClub(day)
				break
			except:
				pass
		self.redirect(str(a))


class PasswordChangeHandler(BaseHandler):
	def get(self):
		self.render("html/PasswordChange.html")

	def post(self):
		if self.get_argument("original_p") != self.current_user().password:
			self.redirect("notice/The password is wrong/or wrong user name/PasswordChange/Go back")
		elif self.get_argument("new_p") != self.get_argument("repeat_p"):
			self.redirect("/notice/The old password is not same as new/or wrong user name/PasswordChange/Go back")
		elif self.get_argument("new_p").__len__() < 8:
			self.redirect("/notice/The passowrd is too short/at least 8 digits/PasswordChange/Go back")
		else:
			self.current_user().password = self.get_argument("new_p")
			self.redirect("/HomePage")


class NewUserHandler(BaseHandler):
	def get(self):
		if self.current_user().permissionLevel != 2:
			self.redirect("/notice/No Permission/Just leave this page/HomePage/Go back")
			return
		self.render("html/NewStudent.html")

	def post(self):
		name = self.get_argument("Name")
		if self.get_argument("UserType") == 'Teacher':
			Manager.Teacher(name)
		else:
			Manager.Student(name)
		self.redirect("/notice/Succeed!/User created/HomePage/Go back")


class AttendanceHandler(BaseHandler):
	def get(self):
		clubs = []
		if get_day() in [1, 2, 3, 4]:
			for club in Manager.Data['clubs'].values():
				if club.students[get_day()] == []:
					continue
				clubs.append(club)
		day = get_day()
		clubs.sort()
		self.render("html/Attendance.html", clubs=clubs, day=day)


def get_day():
	return time.localtime().tm_wday + 1


def auto_save():
	while True:
		pickle.dump(Manager.Data, open("Data", "wb"))
		time.sleep(10)
		current_time = time.localtime()
		n = current_time.tm_hour * 3600 + current_time.tm_min * 60 + current_time.tm_sec
		if 58500 < n and n < 58570:
			pickle.dump(Manager.Temp, open("Att/%s-%s" % (current_time.tm_mon, current_time.tm_mday), "wb"))
			pickle.dump(Manager.Data, open("Historical Data/%s-%s" % (current_time.tm_mon, current_time.tm_mday), "wb"))
			pickle.dump(Manager.Data, open("Data" % (current_time.tm_mon, current_time.tm_mday), "wb"))
			Manager.Temp = {"T": [], "A": [], "checkedClub": []}


Manager.Data = pickle.load(open("Data", "rb"))

# # print(list(Data['users'].values())[-1])
# Manager.Admin('Tester')
#
# f = open('test.txt', 'r', encoding='utf-8').readlines()
#
# clubs = {}
# for i in f[1:]:
#     i = i[:-1]
#     for j in i.split('\t')[3::2]:
#         if Manager.ClubSearch(j) == -1:
#             Manager.Club(j)
#
# for i in f[1:]:
#     i = i[:-1]
#     Joined = i.split('\t')[3::2]
#     name = ''.join(i.split('\t')[:3]).replace(' ', '')
#     i = Manager.Student(name)
#     for j in range(4):
#         i.JoinClub(Manager.ClubSearch(Joined[j]), j + 1)
#
# f = open("ECA login.txt", "r").readlines()
#
# for i in f:
#     Manager.Teacher(i[:-1])
#
# # Manager.Data = pickle.load(open("Data", 'rb'))
# Manager.Admin("Admin")
# # Manager.Teacher("JasonJohnson")
# Manager.Admin("Zeus")
#
# print(Manager.Data['clubs'])
#
# pickle.dump(Manager.Data, open("Data", "wb"))
#
# # for q in Manager.Data['clubs'].values():
# # 	q.students = {Days: [Manager.getUserById(student_id) for student_id in q.students[Days]] for Days in q.students}

# clubs = {0: {0: ['AliciaHan12A', 'AmenLin10A', 'CalisaZeng09C', 'ChrisChe12A', 'CindyGu11C', 'EileenZhang12E', 'ElaineShen12C', 'FrankPan12B', 'HelenLang09C', 'IvoryXu12D', 'JeffreyChen10A', 'LucasJi11B', 'MervinMa11A', 'YoyoWu12D'], 1: [], 2: [], 3: [], 'Name': 'Urban Design'}, 1: {0: ['CalisaZeng09C'], 1: ['AnnieLi10A', 'BettyXu10C', 'CeciliaChen10A', 'JackWu09C', 'JackYuan10D', 'JackZhangShenHao10C', 'JackZhangXiao10C', 'JanetLiu10B', 'JaydenTu10D', 'JeffCheng10D', 'JenniferDeng10A', 'JessieLiu09C', 'JohnLi10A', 'MiaShang10B', 'MichaelLi09C', 'PeterMao10B', 'SenQiao09C', 'SimonChen10B', 'TonyZha11B', 'WendyXing10C'], 2: ['AmberLiu10B', 'AmberWang10D', 'AmenLin10A', 'HelenLang09C', 'JessieLiu09C', 'KevinZheng10C', 'LyonZhang10C', 'MapleXu10C', 'OliviaLi10A', 'OwenXu10D', 'SabrinaXing10D', 'TicoWang10B', 'WilliamWang10A', 'WinstonMao10D'], 3: [], 'Name': 'Study Hall (A)'}, 2: {0: [], 1: [], 2: ['AnnieLi10A', 'AshleyMu10A', 'CalisaZeng09C', 'GraceLyu10B', 'HelenLang09C', 'HermioneXue10A', 'MiaShang10B', 'ZaraRobbertze10D'], 3: [], 'Name': 'Yoga'}, 3: {0: [], 1: [], 2: [], 3: ['AbbyLiu11B', 'AllanXu11B', 'AllenWang10C', 'BobbyYe11D', 'CeciliaChen10A', 'CeciliaLyu12D', 'HelenLang09C', 'JackYuan10D', 'JanetLiu10B', 'JasonZhao11B', 'JenniferDeng10A', 'LucasJi11B', 'NathanXu11A', 'SamGao11A'], 'Name': 'House of Tales'}, 4: {0: ['AgnesWu12D', 'AllenShi12C', 'AngelYou12E', 'ChristinaLu12B', 'DollyChen12A', 'EricPang12C', 'HarrisZhai12A', 'HarryXie10D', 'JackWu09C', 'JackYuan10D', 'JackyLi12B', 'JaxonZhang12E', 'JaydenTu10D', 'JimmyShi12E', 'JoyceXu12A', 'KenZhou12E', 'LeoQian12B', 'LouisJin11D', 'MichaelLi09C', 'RickySu12C', 'RonnieRan12C', 'RoyeeChen12A', 'SabrinaYan12D', 'SenQiao09C', 'SherryHe12A', 'VivianXie12D', 'ZoeZhou12E'], 1: [], 2: [], 3: [], 'Name': 'Business Lab'}, 5: {0: ['AlanTang11C', 'AustinZhang12B', 'DennisWu12D', 'EdwardXu12D', 'HenryHuang10A', 'JackZhangShenHao10C', 'JerryZhou11A', 'MartinXu12D', 'SteelTao12C'], 1: [], 2: ['AlanTang11C', 'DennisWu12D', 'EdwardXu12D', 'EthanChang11B', 'FredChen11A', 'JackWu09C', 'JackZhangShenHao10C', 'JeffCheng10D', 'JimmyCheng10D', 'MichaelLi09C', 'MichaelRen12C', 'NathanXu11A', 'SenQiao09C', 'SteelTao12C', 'TonyZha11B', 'ZackYe11A'], 3: ['CharlieYang11A'], 'Name': 'Computer Science'}, 6: {0: [], 1: [], 2: [], 3: ['MichaelLi09C', 'SenQiao09C'], 'Name': 'Chem Competition'}, 7: {0: [], 1: ['AngelMeng11D', 'AshleyMu10A', 'CatherineWangKe11B', 'DennisWu12D', 'DollyChen12A', 'EthanChang11B', 'GraceLyu10B', 'HansonLiu10B', 'HermioneXue10A', 'JamesWang11C', 'JarvisQian10B', 'JeffYan10D', 'JerryZhou11A', 'JimmyQian11A', 'KenZhou12E', 'KevinLi12E', 'KevinZhu12E', 'MaggieWang11B', 'SelinaLin11A', 'SkyYang09C', 'SophieCao12A', 'SteelTao12C', 'VivianXie12D', 'WilliamWang10A', 'ZaraRobbertze10D', 'ZoeShi11C'], 2: [], 3: ['AngelMeng11D', 'DennisWu12D', 'HansonLiu10B', 'HenryHuang10A', 'JackWu09C', 'JamesWang11C', 'JarvisQian10B', 'JeffYan10D', 'JerryLiu11A', 'KenZhou12E', 'KevinLi12E', 'KevinZhu12E', 'MaggieWang11B', 'SelinaLin11A', 'SophieCao12A', 'SteelTao12C', 'WilliamWang10A', 'ZaraRobbertze10D', 'ZoeShi11C'], 'Name': 'Frisbee'}, 8: {0: [], 1: ['AllenPiao11D', 'AnsonFan11D', 'AsteriaXia10C', 'HarryXie10D', 'HelenLang09C', 'JackShen11D', 'MurphyYang10C', 'SkyYang09C'], 2: [], 3: ['AnsonFan11D', 'ChrisChe12A', 'HarryXie10D', 'JackXu10A', 'SkyYang09C'], 'Name': 'English Debate'}, 9: {0: [], 1: [], 2: [], 3: ['AmandaPan12A', 'AshleyMu10A', 'AsteriaXia10C', 'BrandaLiang11C', 'CalisaZeng09C', 'EileenZhang12E', 'ElaineShen12C', 'HermioneXue10A', 'IvoryXu12D', 'JackyPan10B', 'PeiQiWang10B'], 'Name': 'Art History'}, 10: {0: ['AbbyLiu11B', 'AlexCao11D', 'AmandaPan12A', 'AmberLiu10B', 'AnsonFan11D', 'AshleyMu10A', 'CeciliaChen10A', 'CeciliaLyu12D', 'EmilyRen12E', 'EricWang11D', 'IanQiu11C', 'JanetLiu10B', 'JenniferDeng10A', 'JerryWu10D', 'KarenHou12A', 'KevinCui11B', 'KevinZheng10C', 'KimiLiu12D', 'LucyChen11A', 'LyonZhang10C', 'MaryWu10C', 'MichaelLiu11A', 'NatalieGuo12E', 'OwenXu10D', 'RitaKong11B'], 1: [], 2: [], 3: [], 'Name': 'Movie Club'}, 11: {0: [], 1: [], 2: ['AlexTang10B', 'AllenPiao11D', 'AllenShi12C', 'AnsonFan11D', 'CeciliaChen10A', 'ConnieZheng12E', 'EiffelZhai09F', 'EricPang12C', 'FloraWang11D', 'JDQian12C', 'JanetLiu10B', 'JaydenTu10D', 'JeffYan10D', 'JenniferDeng10A', 'JoyceXu12A', 'KatieHong12A', 'KenZhou12E', 'MartinXu12D', 'PeterMao10B', 'SamXu12D', 'SimonChen10B', 'SkyWan12C', 'SusieZheng12B', 'WilliamShi12C'], 3: [], 'Name': 'FBE'}, 12: {0: ['ChadFan12A', 'DavidDing10C', 'EddyYue10D', 'JamesWang11C', 'JerrodZou12E', 'JimmySun12C', 'JordanCheng12E', 'JulianZhu10C', 'KhaledWei09F', 'LeoQi12C', 'LouisHuang10A', 'LucasChen10A', 'RexWang12B', 'SannyLiu12C', 'StevenWang12D', 'TomHuang12A'], 1: ['ChadFan12A', 'DavidDing10C', 'EddyYue10D', 'JerrodZou12E', 'JimmySun12C', 'JordanCheng12E', 'JulianZhu10C', 'KhaledWei09F', 'LeoQi12C', 'LouisHuang10A', 'LucasChen10A', 'RexWang12B', 'SannyLiu12C', 'StevenWang12D', 'TomHuang12A', 'TonyXiao10C'], 2: ['DavidDing10C', 'EddyYue10D', 'JamesWang11C', 'JerrodZou12E', 'JimmySun12C', 'JordanCheng12E', 'JulianZhu10C', 'LeoQi12C', 'LouisHuang10A', 'LucasChen10A', 'RexWang12B', 'SannyLiu12C', 'TomHuang12A', 'TonyXiao10C'], 3: ['DavidDing10C', 'JerrodZou12E', 'JimmySun12C', 'JordanCheng12E', 'JulianZhu10C', 'LeoQi12C', 'LouisHuang10A', 'LucasChen10A', 'RexWang12B', 'SannyLiu12C', 'TomHuang12A'], 'Name': "Boys' Basketball"}, 13: {0: ['AlexTang10B', 'BobLi12B', 'EricChen12A', 'EricFan12A', 'HansonLiu10B', 'HardisZhang12B', 'JamesMao12B', 'JohnLi10A', 'JohnWang12D', 'KevinLi12E', 'LucWeber10D', 'PeterMao10B', 'SimonChen10B', 'SkyWan12C'], 1: [], 2: [], 3: ['BobLi12B', 'CesarShao10B', 'ChrisCao10A', 'HansenZheng10C', 'JamesMao12B', 'JimmyShi12E', 'JohnWang12D', 'TonyZhou10C'], 'Name': 'Bodybuilding'}, 14: {0: [], 1: ['AlanTang11C', 'AlexCao11D', 'AlexTao10B', 'AliceHuang12E', 'AllenWang10C', 'AmberLiu10B', 'BonnyBai10D', 'CatherineJiang10D', 'CocoLiLi10D', 'HenryLi11D', 'JackyPan10B', 'JaxonZhang12E', 'JerryWu10D', 'JimmyCheng10D', 'JoannaLi11D', 'KevinCui11B', 'LucWeber10D', 'MaryWu10C', 'MervinMa11A', 'NathanXu11A', 'PeiQiWang10B', 'TicoWang10B', 'WinstonMao10D', 'ZackYe11A'], 2: [], 3: [], 'Name': 'Japanese Culture'}, 15: {0: [], 1: [], 2: ['AmyWang11C', 'CandyWang12E', 'ChadFan12A', 'CiciShen12C', 'CindyGu11C', 'DannyLiu11A', 'EricChen12A', 'FrannieZheng10C', 'HarrisZhai12A', 'IrisQi11C', 'JasonZhao11B', 'LareinaSong10C', 'LeoQian12B', 'LilyJi12B', 'LucasJi11B', 'PeterLiu11D', 'RickySu12C', 'RonnieRan12C', 'SusanYao11C'], 3: ['AllenShi12C', 'AmberLiu10B', 'AppleXu11C', 'CatherineWang11C', 'ChadFan12A', 'FrankPan12B', 'HardisZhang12B', 'JaxonZhang12E', 'LouisJin11D', 'PeterLiu11D', 'YorsenHong12E'], 'Name': 'Maths Club'}, 16: {0: ['AliceHuang12E', 'AllenDing12A', 'AllenWang10C', 'AmberWang10D', 'AmyZhou11D', 'AndreaHan12B', 'AngelMeng11D', 'AnnieLi10A', 'AnnieYong11A', 'CatherineJiang10D', 'CharlieYang11A', 'CynthiaPei10D', 'DanielHuang11D', 'GraceLyu10B', 'JackZhangXiao10C', 'JarvisQian10B', 'KallyMao10D', 'KevinZhu12E', 'LilyJi12B', 'LisaShi12C', 'LucyDu11B', 'MaggieWang11B', 'MiaShang10B', 'MichaelRen12C', 'OliviaLi10A', 'SallyWang11B', 'SamXu12D', 'SelinaLin11A', 'SophieCao12A'], 1: [], 2: [], 3: [], 'Name': 'WYSL (Wanyuan Sports League)'}, 17: {0: ['BonnyBai10D', 'BrandaLiang11C', 'CalisaZeng09C', 'CesarShao10B', 'FrankYan10C', 'HenryLi11D', 'HermioneXue10A', 'JulieHuang10A', 'PeterLiu11D', 'StevenHu10A', 'TonyXiao10C', 'TonyZhou10C', 'ValeriaWu11B'], 1: [], 2: [], 3: ['AndyLiang10A', 'CatherineJiang10D', 'CherryGuo10A', 'DanielHuang11D', 'FrankYan10C', 'FrannieZheng10C', 'FredChen11A', 'GraceLyu10B', 'HuberyLiu11B', 'JerryWu10D', 'KevinCui11B', 'LareinaSong10C', 'LucWeber10D', 'LukeChai10B', 'MelodyPan10B', 'OwenXu10D', 'SmileLuo10B', 'TicoWang10B'], 'Name': 'Study Hall'}, 18: {0: [], 1: [], 2: [], 3: ['AliceHuang12E', 'AllenDing12A', 'AmberWang10D', 'AndreaHan12B', 'BellaMa10A', 'CassieYao10A', 'CynthiaPei10D', 'FeliaFeng09C', 'JackZhangShenHao10C', 'JeffCheng10D', 'JimmyCheng10D', 'JimmyQian11A', 'KarenHou12A', 'LilyJi12B', 'MandiDing09C', 'MapleXu10C', 'PeterMao10B', 'SabrinaXing10D', 'SimonChen10B', 'TonyXiao10C'], 'Name': 'Badminton'}, 19: {0: ['AllanXu11B', 'DannyLiu11A', 'FredChen11A', 'HuberyLiu11B', 'JackyShen10B', 'JerryLiu11A', 'JimmyQian11A', 'KennyJiang11B', 'MickeyMou12A', 'StevenCheng11A', 'YorsenHong12E'], 1: [], 2: [], 3: [], 'Name': 'Beatbox'}, 20: {0: [], 1: ['AlexTang10B', 'AllenDing12A', 'CesarShao10B', 'ElizabethShen12C', 'EllyWang10B', 'HansenZheng10C', 'HuberyLiu11B', 'JackyShen10B', 'JeffreyChen10A', 'JessicaWang10B', 'KennyJiang11B', 'KevinZheng10C', 'LyonZhang10C', 'StevenHu10A', 'TonyZhou10C'], 2: [], 3: [], 'Name': 'Launch X'}, 21: {0: [], 1: [], 2: ['AngelMeng11D', 'AshleyCui11B', 'BeibeiWang12D', 'BonnyBai10D', 'ClaudiaCheng11C', 'CocoLi11D', 'EmilyRen12E', 'HarryXie10D', 'JackXu10A', 'JackyPan10B', 'JackyShen10B', 'JerryLiu11A', 'JimmyQian11A', 'JimmyShi12E', 'KevinCui11B', 'MickeyMou12A', 'NatalieGuo12E', 'PaulJiang11C', 'StevenCheng11A', 'YorsenHong12E'], 3: [], 'Name': 'Hip-Hop'}, 22: {0: [], 1: [], 2: [], 3: ['AgnesWu12D', 'AlexCao11D', 'AngelYou12E', 'AustinZhang12B', 'EdwardXu12D', 'EmilyRen12E', 'EricFan12A', 'EricPang12C', 'IanQiu11C', 'JackyShen10B', 'JeffreyChen10A', 'JennyNiu12B', 'KateChen12A', 'KevinZheng10C', 'KimiLiu12D', 'LucyChen11A', 'LyonZhang10C', 'MichaelRen12C', 'MickeyMou12A', 'NatalieGuo12E', 'SamXu12D', 'SebastianQi11A', 'SkyWan12C', 'TinaWang11C'], 'Name': 'Boardgames B'}, 23: {0: ['AndyLiang10A', 'AsteriaXia10C', 'BobbyYe11D', 'BonnyBai10D', 'FrannieZheng10C', 'JackyPan10B', 'JeffCheng10D', 'LareinaSong10C', 'NathanXu11A', 'PeiQiWang10B', 'TomXu11C'], 1: [], 2: [], 3: [], 'Name': 'Spanish'}, 24: {0: [], 1: [], 2: ['AlexCao11D', 'AlexTao10B', 'AndreaHan12B', 'AsteriaXia10C', 'AustinZhang12B', 'BellaMa10A', 'CassieYao10A', 'CynthiaPei10D', 'EricWang11D', 'IanQiu11C', 'KallyMao10D'], 3: [], 'Name': 'Students of the Caribbean'}, 25: {0: [], 1: [], 2: ['AgnesWu12D', 'AileenJin12B', 'AliciaHan12A', 'AllanXu11B', 'AngelYou12E', 'AnniePeng11D', 'BettyXu10C', 'BrandaLiang11C', 'CarolineCai12B', 'ChristinaLu12B', 'ClaireWang10D', 'EileenZhang12E', 'ElaineShen12C', 'HanSun12B', 'IvoryXu12D', 'JerryZhou11A', 'JulieHuang10A', 'KevinLi12E', 'KimiLiu12D', 'LisaShi12C', 'LucyWang11C', 'MaryZhang12C', 'MelodyPan10B', 'ReginaChen11B', 'SamGao11A', 'ZoeZhou12E'], 3: [], 'Name': 'Artsy Corner'}, 26: {0: ['FrannieZheng10C', 'LareinaSong10C', 'MiaShang10B', 'ReginaChen11B', 'WendyXing10C', 'WinstonMao10D'], 1: [], 2: [], 3: ['AnnieLi10A', 'BettyXu10C', 'EddyYue10D', 'EllyWang10B', 'JessieLiu09C', 'JohnLi10A', 'KallyMao10D', 'MiaShang10B', 'WendyXing10C', 'WinstonMao10D'], 'Name': 'Luminous'}, 27: {0: [], 1: ['AllanXu11B', 'AmenLin10A', 'ChrisCao10A', 'DannyLiu11A', 'EricFan12A', 'FrankYan10C', 'IrisZhu11C', 'JackXu10A', 'JerryLiu11A', 'KimiLiu12D', 'LucasJi11B', 'MandiDing09C', 'SamGao11A', 'StevenCheng11A', 'TinaWang11C', 'YorsenHong12E'], 2: [], 3: [], 'Name': 'Electronic Music'}, 28: {0: [], 1: [], 2: ['AmyZhou11D', 'AndyLiang10A', 'AngelinaLiu11D', 'AnnWang11A', 'AnnieYong11A', 'CeciliaMeng11B', 'CindyYan12D', 'DoraYao11A', 'EllyWang10B', 'EvaHuang11A', 'FrankYan10C', 'HenryLi11D', 'IrisZhu11C', 'JasmineGuo11A', 'JessicaWang10B', 'JessicaZhan12E', 'JustinaZhu11D', 'LucyDu11B', 'LucyLu10D', 'MichaelLiu11A', 'RitaKong11B', 'SallyWang11B', 'SashaSha12C', 'WikkiZhong10C', 'YoyoWu12D'], 3: ['AngelinaLiu11D', 'AnnWang11A', 'CeciliaMeng11B', 'CindyYan12D', 'DollyChen12A', 'DoraYao11A', 'EvaHuang11A', 'HenryLi11D', 'IrisZhu11C', 'JasmineGuo11A', 'JessicaWang10B', 'JessicaZhan12E', 'JustinaZhu11D', 'LucyDu11B', 'MichaelLiu11A', 'RitaKong11B', 'SallyWang11B', 'SherryHe12A'], 'Name': 'Music Theatre'}, 29: {0: ['AlexChang12A', 'AlexZhang11D', 'AshleyTao10B', 'ChrisZhou12D', 'EricYe12D', 'HansenZheng10C', 'JackDuan10A', 'JackyWang12D', 'JasonJin11A', 'JasonLiu12B', 'JasonLuo11B', 'JerryJin09C', 'JimmyYu12E', 'KevinZheng12B', 'LukeChai10B', 'PeterFang11C', 'SebastianQi11A', 'ThomasGeng11C', 'TomXu11C', 'WilliamXie10C', 'WinstonJiang11D'], 1: ['AlexChang12A', 'AlexZhang11D', 'AshleyTao10B', 'ChrisZhou12D', 'EricYe12D', 'JackDuan10A', 'JasonJin11A', 'JasonLiu12B', 'JasonLuo11B', 'JerryJin09C', 'JimmyYu12E', 'JohnWang12D', 'KevinZheng12B', 'LukeChai10B', 'PeterFang11C', 'SebastianQi11A', 'ThomasGeng11C', 'TomXu11C', 'WilliamXie10C', 'WinstonJiang11D'], 2: ['AlexChang12A', 'AlexZhang11D', 'AshleyTao10B', 'ChrisCao10A', 'ChrisZhou12D', 'EricYe12D', 'HansenZheng10C', 'JackDuan10A', 'JackYuan10D', 'JackyWang12D', 'JasonJin11A', 'JasonLiu12B', 'JasonLuo11B', 'JerryJin09C', 'JimmyYu12E', 'JohnWang12D', 'KevinZheng12B', 'LukeChai10B', 'PeterFang11C', 'SebastianQi11A', 'ThomasGeng11C', 'TomXu11C', 'WilliamXie10C', 'WinstonJiang11D'], 3: ['AlexChang12A', 'AlexZhang11D', 'AshleyTao10B', 'ChrisZhou12D', 'EricYe12D', 'JackDuan10A', 'JackyWang12D', 'JasonJin11A', 'JasonLiu12B', 'JasonLuo11B', 'JerryJin09C', 'JimmyYu12E', 'KevinZheng12B', 'LukeChai10B', 'PeterFang11C', 'ThomasGeng11C', 'WilliamXie10C', 'WinstonJiang11D'], 'Name': "Boys' Soccer"}, 30: {0: ['AngelinaLiu11D', 'AnnWang11A', 'AppleXu11C', 'CatherineWang11C', 'CeciliaMeng11B', 'ClaireWang10D', 'ClaudiaCheng11C', 'CocoLi11D', 'DoraYao11A', 'EvaHuang11A', 'IrisZhu11C', 'JessieLiu09C', 'JustinaZhu11D', 'LucyLu10D', 'MapleXu10C', 'SmileLuo10B', 'WikkiZhong10C'], 1: [], 2: [], 3: [], 'Name': 'Kpop Dance '}, 31: {0: ['BeibeiWang12D', 'JojoCheng10A', 'LoisLiu10B', 'MartinaZhou12C', 'RubyWu12D', 'ZoeShi11C'], 1: ['AmandaPan12A', 'AmberWang10D', 'BeibeiWang12D', 'CynthiaPei10D', 'JojoCheng10A', 'KarenHou12A', 'LoisLiu10B', 'LucyLu10D', 'MartinaZhou12C', 'RubyWu12D', 'ValeriaWu11B', 'WikkiZhong10C'], 2: ['AmandaPan12A', 'FeliaFeng09C', 'JojoCheng10A', 'KarenHou12A', 'LoisLiu10B', 'MandiDing09C', 'MartinaZhou12C', 'RubyWu12D', 'ZoeShi11C'], 3: ['BeibeiWang12D', 'JojoCheng10A', 'LoisLiu10B', 'MartinaZhou12C', 'RubyWu12D', 'ValeriaWu11B'], 'Name': "Girls' Basketball"}, 32: {0: [], 1: [], 2: [], 3: ['AileenJin12B', 'AlexTao10B', 'AliciaHan12A', 'AmenLin10A', 'AnniePeng11D', 'CandyWang12E', 'CiciShen12C', 'CindyGu11C', 'ClaireWang10D', 'JerryZhou11A', 'JustinYao12B', 'LucyLu10D', 'LucyWang11C', 'LuluLu12B', 'ReginaChen11B', 'StevenHu10A', 'WikkiZhong10C'], 'Name': 'Yuan Chuang'}, 33: {0: [], 1: ['AbbyLiu11B', 'AustinZhang12B', 'BobbyYe11D', 'DanielHuang11D', 'EileenZhang12E', 'ElaineShen12C', 'EricChen12A', 'HenryHuang10A', 'IvoryXu12D', 'LilyJi12B', 'MartinXu12D', 'OwenXu10D'], 2: [], 3: [], 'Name': 'Production Team'}, 34: {0: ['AllenPiao11D', 'AmyWang11C', 'CarolCao11A', 'CatherineWangKe11B', 'EthanChang11B', 'FloraWang11D', 'IrisQi11C', 'JackShen11D', 'JasonZhao11B', 'JoannaLi11D', 'JojoWu11C', 'MadilynJiang11B', 'PaulJiang11C', 'SamGao11A', 'SusanYao11C', 'TonyZha11B', 'ZackYe11A'], 1: [], 2: [], 3: ['AllenPiao11D', 'AmyWang11C', 'CarolCao11A', 'CatherineWangKe11B', 'DannyLiu11A', 'EthanChang11B', 'FloraWang11D', 'IrisQi11C', 'JackShen11D', 'JoannaLi11D', 'JojoWu11C', 'MadilynJiang11B', 'PaulJiang11C', 'StevenCheng11A', 'SusanYao11C', 'TonyZha11B', 'ZackYe11A'], 'Name': 'AP Seminar'}, 35: {0: [], 1: ['AgnesWu12D', 'AngelYou12E', 'BobLi12B', 'CarolCao11A', 'CherryGuo10A', 'EdwardXu12D', 'EmilyRen12E', 'EricPang12C', 'FrankPan12B', 'NatalieGuo12E', 'RickySu12C', 'RonnieRan12C', 'SamXu12D', 'SkyWan12C'], 2: [], 3: [], 'Name': 'Reading Group'}, 36: {0: [], 1: ['AnnWang11A', 'AppleXu11C', 'AshleyCui11B', 'BettyXu10C', 'BrandaLiang11C', 'CatherineWang11C', 'DoraYao11A', 'EvaHuang11A', 'FredChen11A', 'JasonZhao11B', 'JustinaZhu11D', 'LouisJin11D', 'LucyDu11B', 'SallyWang11B', 'TinaWang11C', 'TonyZha11B'], 2: ['AbbyLiu11B', 'CarolCao11A', 'HelenLang09C', 'HuberyLiu11B', 'JoannaLi11D', 'KennyJiang11B', 'LouisJin11D', 'LucyChen11A', 'MadilynJiang11B', 'MaggieWang11B', 'MikeChen11D', 'ValeriaWu11B'], 3: [], 'Name': 'Study Hall (B)'}, 37: {0: [], 1: ['EricWang11D', 'FredChen11A', 'IanQiu11C', 'JulieHuang10A', 'MervinMa11A', 'PeterLiu11D'], 2: ['LucWeber10D', 'MervinMa11A'], 3: [], 'Name': ''}, 38: {0: [], 1: ['AmyWang11C', 'BellaMa10A', 'CindyGu11C', 'FloraWang11D', 'HarrisZhai12A', 'IrisQi11C', 'JackyPan10B', 'LucyWang11C', 'MapleXu10C', 'MichaelLiu11A', 'OliviaLi10A', 'ReginaChen11B', 'SusanYao11C'], 2: [], 3: [], 'Name': 'Self-Media'}, 39: {0: [], 1: ['AmyZhou11D', 'AnnieYong11A', 'JojoWu11C', 'LucyChen11A', 'MadilynJiang11B', 'MikeChen11D'], 2: [], 3: [], 'Name': 'College Application (Juniors)'}, 41: {0: ['AileenJin12B', 'AlexTao10B', 'AmandaPan12A', 'AnniePeng11D', 'AshleyCui11B', 'BellaMa10A', 'CandyWang12E', 'CarolineCai12B', 'CassieYao10A', 'CherryGuo10A', 'CiciShen12C', 'CocoLiLi10D', 'EllyWang10B', 'FeliaFeng09C', 'JasmineGuo11A', 'JennyNiu12B', 'JessicaWang10B', 'KateChen12A', 'LucyWang11C', 'MandiDing09C', 'MaryZhang12C', 'MelodyPan10B', 'SabrinaXing10D', 'StephanieHu12D', 'StevenHu10A', 'TicoWang10B', 'VanessaHu12C'], 1: [], 2: [], 3: [], 'Name': 'Handicrafts'}, 42: {0: [], 1: ['AndyLiang10A', 'CarolineCai12B', 'CeciliaMeng11B', 'ChristinaLu12B', 'CindyYan12D', 'FeliaFeng09C', 'FrannieZheng10C', 'HanSun12B', 'JennyNiu12B', 'JessicaZhan12E', 'KateChen12A', 'LareinaSong10C', 'LisaShi12C', 'MaryZhang12C', 'MelodyPan10B', 'RitaKong11B', 'RoyeeChen12A', 'SabrinaYan12D', 'SmileLuo10B', 'StephanieHu12D', 'VanessaHu12C', 'YoyoWu12D'], 2: [], 3: ['AshleyCui11B', 'CarolineCai12B', 'ChristinaLu12B', 'CocoLiLi10D', 'ElizabethShen12C', 'HanSun12B', 'JulieHuang10A', 'LisaShi12C', 'MaryWu10C', 'MaryZhang12C', 'OliviaLi10A', 'YoyoWu12D'], 'Name': 'Journal'}, 44: {0: [], 1: [], 2: [], 3: ['AlanTang11C', 'AlexTang10B', 'EricChen12A', 'EricWang11D', 'HarrisZhai12A', 'JackZhangXiao10C', 'JackyLi12B', 'JaydenTu10D', 'LeoQian12B', 'MartinXu12D', 'MervinMa11A', 'RickySu12C', 'RonnieRan12C', 'RoyeeChen12A', 'SabrinaYan12D', 'StephanieHu12D', 'StevenWang12D', 'TomXu11C', 'VanessaHu12C', 'VivianXie12D'], 'Name': 'Boardgames A'}, 45: {0: [], 1: [], 2: ['CatherineWangKe11B', 'CocoLiLi10D', 'DanielHuang11D', 'DollyChen12A', 'EricFan12A', 'FeliaFeng09C', 'JackyLi12B', 'JarvisQian10B', 'JessieLiu09C', 'KateChen12A', 'KevinZhu12E', 'LilyJi12B', 'MandiDing09C', 'RoyeeChen12A', 'SabrinaYan12D', 'SelinaLin11A', 'SherryHe12A', 'SkyYang09C', 'SmileLuo10B', 'SophieCao12A', 'StephanieHu12D', 'TinaWang11C', 'VivianXie12D'], 3: [], 'Name': 'Dub'}, 46: {0: [], 1: [], 2: ['CharlieYang11A', 'ChrisChe12A', 'HardisZhang12B', 'JackShen11D', 'JasmineHu12C', 'JaxonZhang12E', 'JennyNiu12B', 'JojoWu11C', 'KingZhang12E', 'MelanieCao12B', 'PeiQiWang10B', 'StevenWang12D', 'VanessaHu12C', 'WendyXing10C'], 3: [], 'Name': 'Student Council'}, 47: {0: ['CindyYan12D', 'ElizabethShen12C', 'HanSun12B', 'JustinYao12B', 'LuluLu12B', 'MikeChen11D'], 1: [], 2: ['AliceHuang12E', 'AllenDing12A', 'BobLi12B', 'CesarShao10B', 'CherryGuo10A', 'ElizabethShen12C', 'FrankPan12B', 'JamesMao12B', 'JustinYao12B', 'LuluLu12B', 'StevenHu10A', 'TonyZhou10C'], 3: [], 'Name': 'CN Readers and Writers'}, 48: {0: [], 1: ['AllenShi12C', 'AngelinaLiu11D', 'AnniePeng11D', 'CandyWang12E', 'CatherineWang11C', 'CharlieYang11A', 'CiciShen12C', 'ClaudiaCheng11C', 'CocoLi11D', 'HardisZhang12B', 'JackyLi12B', 'JamesMao12B', 'JasmineGuo11A', 'JimmyShi12E', 'JustinYao12B', 'KenZhou12E', 'LeoQian12B', 'LuluLu12B', 'MichaelRen12C', 'ZoeZhou12E'], 2: [], 3: [], 'Name': 'Roots and Shoots'}, 49: {0: ['ConnieZheng12E', 'JDQian12C', 'JasmineHu12C', 'KatieHong12A', 'KingZhang12E', 'MelanieCao12B', 'SashaSha12C', 'SusieZheng12B', 'WilliamShi12C'], 1: ['ConnieZheng12E', 'JDQian12C', 'JasmineHu12C', 'KingZhang12E', 'MelanieCao12B', 'SashaSha12C', 'SusieZheng12B', 'WilliamShi12C'], 2: [], 3: ['ConnieZheng12E', 'JDQian12C', 'JasmineHu12C', 'KatieHong12A', 'KingZhang12E', 'MelanieCao12B', 'SashaSha12C', 'SusieZheng12B', 'WilliamShi12C'], 'Name': 'AP Research'}, 50: {0: [], 1: [], 2: ['AllenWang10C', 'BobbyYe11D', 'HansonLiu10B', 'HenryHuang10A', 'JeffreyChen10A', 'JerryWu10D', 'JohnLi10A'], 3: [], 'Name': 'Robotics'}, 52: {0: [], 1: ['CeciliaLyu12D', 'ChrisChe12A', 'JackyWang12D', 'KatieHong12A', 'MickeyMou12A', 'PaulJiang11C'], 2: [], 3: [], 'Name': 'AP Lit'}, 53: {0: ['AnnieLi10A', 'GraceLyu10B', 'LilyJi12B', 'ZaraRobbertze10D'], 1: [], 2: [], 3: [], 'Name': "Girls' Volleyball"}, 54: {0: ['AmyZhou11D', 'AnnieYong11A', 'BonnyBai10D', 'ClaudiaCheng11C', 'CocoLi11D', 'MikeChen11D'], 1: [], 2: [], 3: ['AmyZhou11D', 'AnnieYong11A', 'BonnyBai10D', 'ClaudiaCheng11C', 'CocoLi11D', 'JoyceXu12A', 'MikeChen11D', 'ZoeZhou12E'], 'Name': 'Psych Research'}, 55: {0: ['ChrisCao10A', 'JeffYan10D', 'JimmyCheng10D', 'WilliamWang10A'], 1: [], 2: [], 3: [], 'Name': "Boys' Volleyball"}}
# students = ['AbbyLiu11B', 'AgnesWu12D', 'AileenJin12B', 'AlanTang11C', 'AlexCao11D', 'AlexChang12A', 'AlexTang10B', 'AlexTao10B', 'AlexZhang11D', 'AliceHuang12E', 'AliciaHan12A', 'AllanXu11B', 'AllenDing12A', 'AllenPiao11D', 'AllenShi12C', 'AllenWang10C', 'AmandaPan12A', 'AmberLiu10B', 'AmberWang10D', 'AmenLin10A', 'AmyWang11C', 'AmyZhou11D', 'AndreaHan12B', 'AndyLiang10A', 'AngelMeng11D', 'AngelYou12E', 'AngelinaLiu11D', 'AnnWang11A', 'AnnieLi10A', 'AnniePeng11D', 'AnnieYong11A', 'AnsonFan11D', 'AppleXu11C', 'AshleyCui11B', 'AshleyMu10A', 'AshleyTao10B', 'AsteriaXia10C', 'AustinZhang12B', 'BeibeiWang12D', 'BellaMa10A', 'BettyXu10C', 'BobLi12B', 'BobbyYe11D', 'BonnyBai10D', 'BrandaLiang11C', 'CalisaZeng09C', 'CandyWang12E', 'CarolCao11A', 'CarolineCai12B', 'CassieYao10A', 'CatherineJiang10D', 'CatherineWang11C', 'CatherineWangKe11B', 'CeciliaChen10A', 'CeciliaLyu12D', 'CeciliaMeng11B', 'CesarShao10B', 'ChadFan12A', 'CharlieYang11A', 'CherryGuo10A', 'ChrisCao10A', 'ChrisChe12A', 'ChrisZhou12D', 'ChristinaLu12B', 'CiciShen12C', 'CindyGu11C', 'CindyYan12D', 'ClaireWang10D', 'ClaudiaCheng11C', 'CocoLi11D', 'CocoLiLi10D', 'ConnieZheng12E', 'CynthiaPei10D', 'DanielHuang11D', 'DannyLiu11A', 'DavidDing10C', 'DennisWu12D', 'DollyChen12A', 'DoraYao11A', 'EddyYue10D', 'EdwardXu12D', 'EiffelZhai09F', 'EileenZhang12E', 'ElaineShen12C', 'EldonAo09F', 'ElizabethShen12C', 'EllyWang10B', 'EmilyRen12E', 'EricChen12A', 'EricFan12A', 'EricPang12C', 'EricWang11D', 'EricYe12D', 'EthanChang11B', 'EvaHuang11A', 'FeliaFeng09C', 'FloraWang11D', 'FrankPan12B', 'FrankYan10C', 'FrannieZheng10C', 'FredChen11A', 'GraceLyu10B', 'HanSun12B', 'HansenZheng10C', 'HansonLiu10B', 'HardisZhang12B', 'HarrisZhai12A', 'HarryXie10D', 'HelenLang09C', 'HenryHuang10A', 'HenryLi11D', 'HermioneXue10A', 'HuberyLiu11B', 'IanQiu11C', 'IrisQi11C', 'IrisZhu11C', 'IvoryXu12D', 'JDQian12C', 'JackDuan10A', 'JackShen11D', 'JackWu09C', 'JackXu10A', 'JackYuan10D', 'JackZhangShenHao10C', 'JackZhangXiao10C', 'JackyLi12B', 'JackyPan10B', 'JackyShen10B', 'JackyWang12D', 'JamesMao12B', 'JamesWang11C', 'JanetLiu10B', 'JarvisQian10B', 'JasmineGuo11A', 'JasmineHu12C', 'JasonJin11A', 'JasonLiu12B', 'JasonLuo11B', 'JasonZhao11B', 'JaxonZhang12E', 'JaydenTu10D', 'JeffCheng10D', 'JeffYan10D', 'JeffreyChen10A', 'JenniferDeng10A', 'JennyNiu12B', 'JerrodZou12E', 'JerryJin09C', 'JerryLiu11A', 'JerryWu10D', 'JerryZhou11A', 'JessicaWang10B', 'JessicaZhan12E', 'JessieLiu09C', 'JimmyCheng10D', 'JimmyQian11A', 'JimmyShi12E', 'JimmySun12C', 'JimmyYu12E', 'JoannaLi11D', 'JohnLi10A', 'JohnWang12D', 'JojoCheng10A', 'JojoWu11C', 'JordanCheng12E', 'JoyceXu12A', 'JulianZhu10C', 'JulieHuang10A', 'JustinYao12B', 'JustinaZhu11D', 'KallyMao10D', 'KarenHou12A', 'KateChen12A', 'KatieHong12A', 'KenZhou12E', 'KennyJiang11B', 'KevinCui11B', 'KevinLi12E', 'KevinZheng10C', 'KevinZheng12B', 'KevinZhu12E', 'KhaledWei09F', 'KimiLiu12D', 'KingZhang12E', 'LareinaSong10C', 'LeoQi12C', 'LeoQian12B', 'LeoWang09F', 'LilyJi12B', 'LisaShi12C', 'LoisLiu10B', 'LouisHuang10A', 'LouisJin11D', 'LucWeber10D', 'LucasChen10A', 'LucasJi11B', 'LucyChen11A', 'LucyDu11B', 'LucyLu10D', 'LucyWang11C', 'LukeChai10B', 'LuluLu12B', 'LyonZhang10C', 'MadilynJiang11B', 'MaggieWang11B', 'MandiDing09C', 'MapleXu10C', 'MartinXu12D', 'MartinaZhou12C', 'MaryWu10C', 'MaryZhang12C', 'MelanieCao12B', 'MelodyPan10B', 'MervinMa11A', 'MiaShang10B', 'MichaelLi09C', 'MichaelLiu11A', 'MichaelRen12C', 'MickeyMou12A', 'MikeChen11D', 'MurphyYang10C', 'NatalieGuo12E', 'NathanXu11A', 'OliviaLi10A', 'OwenXu10D', 'PaulJiang11C', 'PeiQiWang10B', 'PeterFang11C', 'PeterLiu11D', 'PeterMao10B', 'ReginaChen11B', 'RexWang12B', 'RickySu12C', 'RitaKong11B', 'RonnieRan12C', 'RoyeeChen12A', 'RubyWu12D', 'SabrinaXing10D', 'SabrinaYan12D', 'SallyWang11B', 'SamGao11A', 'SamXu12D', 'SannyLiu12C', 'SashaSha12C', 'SebastianQi11A', 'SelinaLin11A', 'SenQiao09C', 'SherryHe12A', 'SimonChen10B', 'SkyWan12C', 'SkyYang09C', 'SmileLuo10B', 'SophieCao12A', 'SteelTao12C', 'StephanieHu12D', 'StevenCheng11A', 'StevenHu10A', 'StevenWang12D', 'SusanYao11C', 'SusieZheng12B', 'ThomasGeng11C', 'TicoWang10B', 'TinaWang11C', 'TomHuang12A', 'TomXu11C', 'TonyXiao10C', 'TonyZha11B', 'TonyZhou10C', 'ValeriaWu11B', 'VanessaHu12C', 'VivianXie12D', 'WendyXing10C', 'WikkiZhong10C', 'WilliamShi12C', 'WilliamWang10A', 'WilliamXie10C', 'WinstonJiang11D', 'WinstonMao10D', 'YorsenHong12E', 'YoyoWu12D', 'ZackYe11A', 'ZaraRobbertze10D', 'ZoeShi11C', 'ZoeZhou12E']
#
# Manager.Admin('Tester')
# Manager.Admin("Zeus")
# for student in students:
# 	Manager.Student(student)

# Manager.UserSearch("AliciaHan12A")

# for club in clubs.values():
# 	Manager.Club(club["Name"])
# 	for day in range(4):
# 		for student in club[day]:
# 			Manager.UserSearch(student).JoinClub(Manager.ClubSearch(club["Name"]),day+1)
# 			# i.JoinClub(Manager.ClubSearch(Joined[j]), j + 1)
#
# print("?")

if True:
	threading.Thread(target=auto_save).start()
	app = tornado.web.Application(handlers=[
		(r"/", MainHandler),
		(r"/notice/(.*)/(.*)/(.*)/(.*)", NoticeHandler),
		(r"/Asset/(.*)", tornado.web.StaticFileHandler, {"path": "./Asset"}),
		(r"/Checkin/(.*)", CheckinHandler),
		(r"/HomePage", HomePageHandler),
		(r"/ECACreation", ECACreationHandler),
		(r"/Attendance", AttendanceHandler),
		(r"/Manage/(.*)", ManageHandler),
		(r"/Search", SearchHandler),
		(r"/PasswordChange", PasswordChangeHandler),
		(r"/NewUser", NewUserHandler),
		(r"/login", LoginHandler)],
		cookie_secret="1234567")
	server = tornado.httpserver.HTTPServer(app)
	server.listen(80)
	tornado.ioloop.IOLoop.instance().start()
