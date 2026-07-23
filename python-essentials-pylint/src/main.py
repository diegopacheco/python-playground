from dataclasses import dataclass


@dataclass
class Account:
    owner: str
    balance: float

    def deposit(self, amount: float) -> float:
        self.balance += amount
        return self.balance

    def withdraw(self, amount: float) -> float:
        if amount > self.balance:
            raise ValueError("insufficient funds")
        self.balance -= amount
        return self.balance


def transfer(source: Account, target: Account, amount: float) -> None:
    source.withdraw(amount)
    target.deposit(amount)


def total_balance(accounts: list[Account]) -> float:
    return sum(account.balance for account in accounts)


def main() -> None:
    alice = Account("alice", 100.0)
    bob = Account("bob", 50.0)
    transfer(alice, bob, 30.0)
    print(f"alice balance: {alice.balance}")
    print(f"bob balance: {bob.balance}")
    print(f"total balance: {total_balance([alice, bob])}")


if __name__ == "__main__":
    main()
