def basic_slices():
    data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    return {
        "first_three": data[:3],
        "last_three": data[-3:],
        "middle": data[3:7],
        "every_second": data[::2],
        "reversed": data[::-1],
    }


def string_slices():
    text = "python-playground"
    return {
        "prefix": text[:6],
        "suffix": text[-10:],
        "skip": text[::3],
        "reverse": text[::-1],
    }


def slice_assignment():
    data = [1, 2, 3, 4, 5]
    data[1:3] = [20, 30, 40]
    grown = list(data)
    data[::2] = [0, 0, 0]
    return grown, data


def slice_object():
    every_other = slice(None, None, 2)
    return list(range(10))[every_other]


def main():
    print("basic_slices:", basic_slices())
    print("string_slices:", string_slices())
    print("slice_assignment:", slice_assignment())
    print("slice_object:", slice_object())


if __name__ == "__main__":
    main()
