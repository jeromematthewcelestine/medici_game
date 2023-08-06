from enum import IntEnum, Enum
from typing import NamedTuple, Union, Optional
from random import shuffle, choice

class Phase(IntEnum):
    Draw = 0
    Bid = 1

class DrawAction(IntEnum):
    Draw = 0
    Pass = 1

    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        if self == DrawAction.Draw:
            return "Draw"
        elif self == DrawAction.Pass:
            return "Pass"

class BidAction(NamedTuple):
    value: int # 0 for pass

class Type(IntEnum):
    Cloth   = 0
    Fur     = 1
    Grain   = 2
    Dye     = 3
    Spice   = 4
    Gold    = 5

class Card(NamedTuple):
    type: Type
    value: int

    def __str__(self):
        return "(" + str(self.type) + " " + str(self.value) + ")"
    
    def __repr__(self):
        return str(self)

all_cards = [
        Card(type, i) 
        for type in [Type.Cloth, Type.Fur, Type.Grain, Type.Dye, Type.Spice]
        for i in [0, 1, 2, 3, 4, 5, 5] 
    ] + [Card(Type.Gold, 10)]

class MediciState:
    def __init__(self, game):
        self.game = game
        self.turn_player = 0 # first buyer in turn
        self.current_player = 0  
        self.phase = Phase.Draw
        self.bids = {}
        self.money = [40] * game.n_players
        self.cards_in_play = []
        self.deck = all_cards.copy()
        shuffle(self.deck)

        self.cards_in_play = []
        self.cards_in_play.append(self.deck.pop())

        self.ships = []
        for i in range(self.game.n_players):
            self.ships.append([])

        self.purchase_counts = {}
        for player in range(self.game.n_players):
            for resource in [Type.Cloth, Type.Fur, Type.Grain, Type.Dye, Type.Spice]:
                self.purchase_counts[(player, resource)] = 0


    def LegalActions(self):
        if self.phase == Phase.Draw:
            return [DrawAction.Draw, DrawAction.Pass]
        
        elif self.phase == Phase.Bid:

            # can't overfill a ship
            if len(self.ships[self.current_player]) + len(self.cards_in_play) > self.game.kShipCapacity:
                return [BidAction(0)]
            
            max_bid = self.money[self.current_player]
            if self.bids:
                min_bid = max(self.bids.values()) + 1
            else:
                min_bid = 1
            return [BidAction(i) for i in range(min_bid, max_bid + 1)] + [BidAction(0)]
    
    def NextPlayer(self, player):
        return (player + 1) % self.game.n_players
        
    def DoApplyAction(self, action):
        if action == DrawAction.Pass:
            self.current_player = self.NextPlayer(self.current_player)
            self.phase = Phase.Bid

        elif action == DrawAction.Draw:
            self.cards_in_play.append(self.deck.pop())
            
            if len(self.cards_in_play) == 3:
                self.current_player = self.NextPlayer(self.current_player)
                self.phase = Phase.Bid

        elif isinstance(action, BidAction):

            self.bids[self.current_player] = action.value

            if self.current_player == self.turn_player:
                self.CompleteAuction()
            else:
                self.current_player = self.NextPlayer(self.current_player)
    
    def all_ships_but_one_full(self):
        n_full_ships = 0
        unfull_ship = -1
        for i, ship in enumerate(self.ships):
            if len(ship) >= self.game.kShipCapacity:
                n_full_ships += 1
            else:
                unfull_ship = ship
        if n_full_ships == self.game.n_players - 1:
            return True, unfull_ship
        else:
            return False, None
        
    def CompleteShip(self, ship_idx):
        print(f"COMPLETING SHIP {ship_idx}")
        ship = self.ships[ship_idx]
        while len(ship) <= self.game.kShipCapacity:
            if self.deck:
                ship.append(self.deck.pop())
            else:
                break
            
    def CompleteAuction(self):
        max_bid = 0
        winner = -1
        for player, bid in self.bids.items():
            if bid > max_bid:
                winning_bid = bid
                winner = player

        if winner != -1:
            self.money[winner] -= winning_bid
            print(f"Winner: {winner}")
            self.ships[winner] += self.cards_in_play

            # update purchase counts
            for card in self.cards_in_play:
                if card.type != Type.Gold:
                    self.purchase_counts[(winner, card.type)] += 1
            


        # check if day is over
        all_ships_but_one_full, unfull_ship_idx = self.all_ships_but_one_full()
        if all_ships_but_one_full:
            self.CompleteShip(unfull_ship_idx)
            self.CompleteDay()

        # set up next auction
        self.cards_in_play = [self.deck.pop()]

        self.bids = {}

        self.turn_player = self.NextPlayer(self.turn_player)
        self.current_player = self.turn_player
        self.phase = Phase.Draw
    
    def CompleteDay(self):
        ship_values = []
        for player, ship in enumerate(self.ships):
            if ship:
                ship_values[player] = sum([card.value for card in ship])
        self.ships = [[] for _ in range(self.game.n_players)]

        # work out winning values
        first_value = max(ship_values)
        second_value = max([value for value in ship_values if value != first_value])
        third_value = max([value for value in ship_values if value != first_value and value != second_value])
        
        # work out tiering of winning players
        first_players = []
        second_players = []
        third_players = []
        for player, value in enumerate(ship_values):
            if value == first_value:
                first_players.append(player)
        if len(first_players) < 3:
            for player, value in enumerate(ship_values):
                if value == second_value:
                    second_players.append(player)
        if len(first_players) + len(second_players) < 3:
            for player, value in enumerate(ship_values):
                if value == third_value:
                    third_players.append(player)

        # allocate prize money
        if len(first_players) == 1:
            prize_money = self.game.kPrizes[0]
            self.money[first_players[0]] += prize_money

            if len(second_players) == 1:
                second_prize_money = self.game.kPrizes[1]
                self.money[second_players[0]] += prize_money
                
                third_prize_money = self.game.kPrizes[2] // len(third_players)
                for player in third_players:
                    self.money[player] += third_prize_money
 
        elif len(first_players) == 2:
            prize_money = (self.game.kPrizes[0] + self.game.kPrizes[1]) // len(first_players)
            self.money[first_players[0]] += prize_money
            self.money[first_players[1]] += prize_money

            second_prize_money = self.game.kPrizes[2] // len(second_players)
            self.money[second_players[0]] += prize_money

        elif len(first_players) >= 3:
            prize_money = (self.game.kPrizes[0] + self.game.kPrizes[1] + self.game.kPrizes[2]) // len(first_players)
            for player in first_players:
                self.money[player] += prize_money   

        # determine points for purchase counts
        for type in [Type.Cloth, Type.Fur, Type.Grain, Type.Dye, Type.Spice]:
            top_purchase_count = max([self.purchase_counts[(player, type)] for player in range(self.game.n_players)])
            second_purchase_count = max([self.purchase_counts[(player, type)] for player in range(self.game.n_players) if self.purchase_counts[(player, type)] != top_purchase_count])

            top_purchasers = [player for player in range(self.game.n_players) if self.purchase_counts[(player, type)] == top_purchase_count]
            second_purchasers = [player for player in range(self.game.n_players) if self.purchase_counts[(player, type)] == second_purchase_count]

            if len(top_purchasers == 1):
                top_bonus = self.game.kTopBonus
                self.money[top_purchasers[0]] += top_bonus

                second_bonus = self.game.kSecondBonus // len(second_purchasers)
                for player in second_purchasers:
                    self.money[player] += second_bonus
            else:
                top_bonus = self.game.kTopBonus // len(top_purchasers)
                for player in top_purchasers:
                    self.money[player] += top_bonus

            # bonus points at top of pyramid
            for player in range(self.game.n_players):
                if self.purchase_counts[(player, type)] == 5:
                    self.money[player] += self.game.kFiveBonus
                if self.purchase_counts[(player, type)] == 6:
                    self.money[player] += self.game.kSixBonus
                if self.purchase_counts[(player, type)] >= 7:
                    self.money[player] += self.game.kSevenBonus
                    



    def ToString(self):
        s = "Phase: " + str(self.phase) + "\n"
        s += "Turn Player: " + str(self.turn_player) + "\n"
        s += "Current Player: " + str(self.current_player) + "\n"
        s += "Bids: " + str(self.bids) + "\n"
        s += "Money: " + str(self.money) + "\n"
        s += "Cards in Play: " +  str(self.cards_in_play) + "\n"
        s += "Ships: \n"
        for i, ship in enumerate(self.ships):
            s += str(i) + ": " + str(ship) + "\n"


        return s

class MediciGame:
    def __init__(self):
        self.n_players = 4

        self.kShipCapacity = 5
        self.kHighestPoints = 10
        self.kSecondHighestPoints = 5

        self.kFiveBonus = 5
        self.kSixBonus = 10
        self.kSevenBonus = 20
    
    
    def InitialState(self):
        return MediciState(self)

if __name__ == "__main__":
    game = MediciGame()
    state = game.InitialState()

    for i in range(80):
        action = choice(state.LegalActions())
        print(f"Action: {action}")
        state.DoApplyAction(action)
        print("State:")
        print(state.ToString())
        print("")