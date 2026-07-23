import time

from tqdm import tqdm


def main() -> None:
    total = 0
    for i in tqdm(range(50), desc="processing"):
        total += i
        time.sleep(0.02)
    print("total:", total)

    for _ in tqdm(["a", "b", "c", "d"], desc="letters"):
        time.sleep(0.1)


if __name__ == "__main__":
    main()
