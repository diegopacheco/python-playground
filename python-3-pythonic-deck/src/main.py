from random import choice
from typing import NamedTuple, overload

class Card(NamedTuple):
    rank: str
    suit: str

class CardDeck:
    ranks = [str(n) for n in range(2,11)] + list('JQKA')
    suits = 'spades diamonds clubs hearts'.split()

    def __init__(self) -> None:
        self._cards = [Card(rank,suit)
                       for suit in self.suits
                       for rank in self.ranks]

    def __len__(self) -> int:
        return len(self._cards)

    @overload
    def __getitem__(self, position: int) -> Card: ...

    @overload
    def __getitem__(self, position: slice) -> list[Card]: ...

    def __getitem__(self, position: int | slice) -> Card | list[Card]:
            return self._cards[position]

if __name__=="__main__":
    c = Card('7','diamonds')
    print(c)

    deck = CardDeck()
    print('Len of the deck == ' + str(len(deck)))
    print('deck[0] == ' + str(deck[0]))
    print('deck[1] == ' + str(deck[1]))
    print('deck[2] == ' + str(deck[2]))
    print('deck[2:10] == ' + str(deck[2:10]))
    print('choise(deck) == ' + str( choice(deck)))

    for card in deck:
         print(card)

    if Card('Q','hearts') in deck:
        print(str(Card('Q','hearts')) + ' its in deck!')
    else:
        print(str(Card('Q','hearts')) + ' NOT in deck!')