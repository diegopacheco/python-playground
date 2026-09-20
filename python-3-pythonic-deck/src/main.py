from typing import NamedTuple

class Card(NamedTuple):
    rank: str
    suit: str

class CardDeck:
    ranks = [str(n) for n in range(2,11)] + list('JQKA')
    suits = 'spade diamonds clubs hearts'.split()

    def __init__(self) -> None:
        self._cards = [Card(rank,suit)
                       for suit in self.suits
                       for rank in self.ranks]

    def __len__(self) -> int:
        return len(self._cards)

    def __getitem__(self, position: int) -> Card:
        return self._cards[position]

if __name__=="__main__":
    c = Card('7','diamonds')
    print(c)
