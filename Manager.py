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
		Data['users'][self.id] = self
	def LeadClub(self,club):
		self.leads.append(club.id)
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
	def JoinClub(self,club_id,day):
		self.joined_clubs[day] = club_id
		Data['clubs'][club_id].students[day].append(self.id)
	def LeaveClub(self,day):
		if self.joined_clubs[day] == -1:
			return
		Data['clubs'][self.joined_clubs[day]].students[day].remove(self.id)
		self.joined_clubs[day] = -1
	def Remove(self):
		del Data['users'][self.id]
		for i in self.joined_clubs:
			if self.joined_clubs[i] != -1:
				Data["clubs"][self.joined_clubs[i]].students[i].remove(self.id)

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
				Data['users'][student].joined_clubs[day] = -1
		del Data['clubs'][self.id]
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

def setStudentAtt(studentId,club,state):
	current = getUserById(studentId).getStudentCurrentAtt(club)
	if current == state:
		return
	Temp[currrent].remove[student.id]
	if currrent in ['T','A']:
		Temp[state].append(student.id)

def ClubChecked(club):
	if club.id not in Temp["checkedClub"]:
		Temp["checkedClub"].append(club.id)