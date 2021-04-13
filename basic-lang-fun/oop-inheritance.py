class Person(object):
  def __init__(self, fname, lname):
    self.firstname = fname
    self.lastname = lname

  def __str__(self):
    print(self.firstname, self.lastname)

class Student(Person):
  def __init__(self, fname, lname, year):
    super(Student,self).__init__(fname, lname)
    self.graduationyear = year

  def welcome(self):
    print("Welcome", self.firstname, self.lastname, "to the class of", self.graduationyear)

s = Student("John","Doe",2000)
s.welcome()