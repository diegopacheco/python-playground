def myfunction():
  print("Hello from a function")

myfunction()

def varargsFun(*kids):
  print("The youngest child is " + kids[2])
  
varargsFun("Emil", "Tobias", "Linus")