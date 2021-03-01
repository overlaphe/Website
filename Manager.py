import pickle

Data = {'users':{},'clubs':{}}
Temp = {"T":[],"A":[],"checkedClub":[]}

class User(object):
	global Data
	def __init__(self, name):
		self.password = '123456'
		self.id = max(Data['users'])+1 if Data['users'] != {} else 0
		self.leads = []
		self.name = name
		self.permissionLevel = 0
		self.Temp = {}
		Data['users'][self.id] = self
	def LeadClub(self,club):
		self.leads.append(club.id)
	def UnleadClub(self,club):
		self.leads.remove(club.id)
	def Remove(self):
		del Data['users'][self.id]
	def ChangeName(self,name):
		self.name = name
	def isLeading(self,club):
		return club.id in self.leads
	def getStudentCurrentAtt(self,club):
		if club.id not in Temp['checkedClub']:
			return 'A'
		if self.id in Temp['T']:
			return 'T'
		elif self.id in Temp['A']:
			return 'A'
		return 'P'
	def __lt__(a,b):
		return a.name < b.name

class Student(User):
	def __init__(self, name):
		super(Student, self).__init__(name)
		self.joined_clubs = {1:-1,2:-1,3:-1,4:-1}
	def JoinClub(self,club,day):
		self.joined_clubs[day] = club.id
		club.students[day].append(self)
	def LeaveClub(self,day):
		if self.joined_clubs[day] == -1:
			return
		print(self.joined_clubs[day])
		getClubById(self.joined_clubs[day]).students[day].remove(self)
		self.joined_clubs[day] = -1
	def Remove(self):
		del Data['users'][self.id]
		for i in self.joined_clubs:
			if self.joined_clubs[i] != -1:
				Data["clubs"][self.joined_clubs[i]].students[i].remove(self)

class Teacher(User):
	def __init__(self, name):
		super(Teacher, self).__init__(name)
		self.permissionLevel = 1
	def Remove(self):
		del Data['users'][self.id]

class Admin(User):
	def __init__(self, name):
		super(Admin, self).__init__(name)
		self.permissionLevel = 2
	def isLeading(self,club_id):
		return True

class Club(object):
	global Data
	def __init__(self, name):
		self.id = max(Data['clubs'])+1 if Data['clubs'] != {} else 0
		self.students = {1:[],2:[],3:[],4:[]}
		self.name = name
		Data['clubs'][self.id] = self
	def Dismiss(self):
		for day in self.students:
			for student in self.students[day]:
				student.joined_clubs[day] = -1
		del Data['clubs'][self.id]
	def isChecked(self):
		return self.id in Temp['checkedClub']
	def __lt__(a,b):
		return a.name < b.name

def UserSearch(Name,T=[Teacher,Admin,Student]):
	for i in Data['users'].values():
		if type(i) in T and i.name == Name:
			return i
	else:
		return -1

def ClubSearch(Name):
	for i in Data['clubs'].values():
		if i.name == Name:
			return i
	else:
		return -1

def UserMatch(key,T):
	retList = []
	for i in Data['users'].values():
		if type(i)==T and i.name.lower().find(key.lower()) != -1:
			retList.append(i)
	return retList

def getClubById(id):
	return Data['clubs'][id]

def getUserById(id):
	return Data['users'][id]

def setStudentAtt(student,club,state):
	current = student.getStudentCurrentAtt(club)
	if club.id in Temp['checkedClub']:
		if current == state:
			return
		if current in ['T', 'A']:
			Temp[current].remove(student.id)
	if state in ['T','A']:
		Temp[state].append(student.id)

def ClubChecked(club):
	if club.id not in Temp["checkedClub"]:
		Temp["checkedClub"].append(club.id)