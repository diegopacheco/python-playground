#
# The * operator is used for unpacking the array
# Instead of printing the array with brackets, it prints each element separated by spaces
# Without the *, it would print: ['This', 'is', 'a', 'Array', 'in', 'Python']
#
def main():
    arr = ["This", "is", "a", "Array","in", "Python"]
    print(*arr)

if __name__ == "__main__":
    main()