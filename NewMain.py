from typing import Optional, Awaitable

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
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    @property
    def is_not_current_user(self):
        if not self.get_secure_cookie('user'):
            return True
        user = self.get_secure_cookie('user')
        if not self.get_secure_cookie("pswd"):
            return True
        pswd = str(self.get_secure_cookie('pswd'),'utf-8')
        if Manager.getUserById(int(user)).password + "salt" != pswd:
            print(Manager.getUserById(int(user)).password + "salt",pswd)
            print("3")
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
            self.set_secure_cookie("pswd", Pswd+"salt")
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
        self.render("html/Attendance.html", students=students, club=club)

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
            return
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
            self.get_argument("DismissClub")
            club.Dismiss()
            self.redirect('/notice/Club is Dismissed/Say Sorry to club members if that was an accident/HomePage/Go back')
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
        self.redirect("")


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


class AttendenceHandler(BaseHandler):
    def get(self):
        clubs = []
        if get_day() in [1,2,3,4]:
            for club in Manager.Data['clubs'].values():
                if club.students[get_day()] == []:
                    continue
                clubs.append(club)
        day = get_day()
        clubs.sort()
        self.render("html/Attendence.html", clubs=clubs, day=day)


def get_day():
    return time.localtime().tm_wday+1


# class HomePageHandler(BaseHandler):
# 	def get(self):
# 		self.render("html/")

# print(list(Data['users'].values())[-1])
# Student('Tester')

# f = open('test.txt','r',encoding='utf-8').readlines()

# clubs = {}
# for i in f[1:]:
# 	i = i[:-1]
# 	for j in i.split('\t')[3::2]:
# 		if Manager.Search.ClubSearch(j) == -1:
# 			Manager.Club(j)

# for i in f[1:]:
# 	i = i[:-1]
# 	Joined = i.split('\t')[3::2]
# 	name = ''.join(i.split('\t')[:3]).replace(' ','')
# 	i = Manager.Student(name)
# 	for j in range(4):
# 		i.JoinClub(Manager.Search.ClubSearch(Joined[j]),j+1)

Manager.Data = pickle.load(open("Data", 'rb'))
Manager.Admin("Admin")
Manager.Teacher("JasonJohnson")

for q in Manager.Data['clubs'].values():
    q.students = {Days: [Manager.getUserById(student_id) for student_id in q.students[Days]] for Days in q.students}

if True:
    # threading.Thread(target=Auto_Save).start()
    app = tornado.web.Application(handlers=[
        (r"/", MainHandler),
        (r"/notice/(.*)/(.*)/(.*)/(.*)", NoticeHandler),
        (r"/Asset/(.*)", tornado.web.StaticFileHandler, {"path": "./Asset"}),
        (r"/Checkin/(.*)", CheckinHandler),
        (r"/HomePage", HomePageHandler),
        (r"/ECACreation", ECACreationHandler),
        (r"/Attendence", AttendenceHandler),
        (r"/Manage/(.*)", ManageHandler),
        (r"/Search", SearchHandler),
        (r"/PasswordChange", PasswordChangeHandler),
        (r"/NewUser", NewUserHandler),
        (r"/login", LoginHandler)],
        cookie_secret="1234567")
    server = tornado.httpserver.HTTPServer(app)
    server.listen(8800)
    tornado.ioloop.IOLoop.instance().start()
    print("asdasdasd")