# Slice to reververse a string
stra = "Hello World!"
print(stra[::-1])

# Inplace swap
a = 10
b = 5
a, b = b, a + 2
print(f"Second: {a, b}")

# Generators
gen = [x * 2 for x in range(10)]
print(gen)

# F-String
first_name = "John"
age = 50
print(f"Hi, I'm {first_name} and I'm {age} years old!")

# Print End parameter
langs = ["english", "french", "spanish", "german", "twi"]
for language in langs:
  print(language, end=" ")

# Print sep parameter
day = "04"
month = "10"
year = "2022"
print(day, month, year, end='\n')
print(day, month, year, sep = "", end='\n')
print(day, month, year, sep = ".", end='\n')

# Merge Dicts
dict_a = {"a": 1, "b": 2}
dict_b = {"c": 3, "d": 4}
a_and_b = dict_a | dict_b
print(a_and_b)

# If result to a var
condition = True
name = "John" if condition else "Doe"
print(name, end="\n")

# Underscore to ignore values
for _ in range(3):
  print("The index doesn't matter")

# Underscore Visual
number = 1_500_000
print(number)

# Regex Pipe
import re
heros = re.compile(r"Super(man|woman|human)")
h1 = heros.search("This will find Superman")
h2 =  heros.search("This will find Superwoman")
h3 = heros.search("This will find Superhuman")
print(h1.group())
print(h2.group())
print(h3.group())

# Lists Diff
list_1 = [1, 3, 5, 7, 8]
list_2 = [1, 2, 3, 4, 5, 6, 7, 8, 9]

solution_1 = list(set(list_2) - set(list_1))
solution_2 = list(set(list_1) ^ set(list_2))

print(f"Solution 1: {solution_1}")
print(f"Solution 2: {solution_2}")


# List Comprehension
even_numbers = [x for x in range(10) if x % 2 == 0 and x != 0]
print(even_numbers, end="\n")
