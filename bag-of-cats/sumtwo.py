def sum_two(arr, target):
    arr = sorted(arr)
    left = 0
    right = len(arr) - 1
    while left <= right:
        sum = arr[left] + arr[right]
        if sum == target:
            return [arr[left], arr[right]]
        elif sum < target:
            left += 1
        else:
            right -= 1
    return [-1, -1]


print(sum_two([10, 2, 4, 5, 7], 6))
