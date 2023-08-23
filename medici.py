from enum import IntEnum, Enum
from typing import NamedTuple, Union, Optional
from random import shuffle, choice

class Phase(IntEnum):
    Draw = 0
    Bid = 1
    GameOver = 2

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

type_strings = ["Cloth", "Fur", "Grain", "Dye", "Spice", "Gold"]
phase_strings = ["Draw", "Bid", "GameOver"]
draw_action_strings = ["Draw", "Pass"]

class Card(NamedTuple):
    type: Type
    value: int

    def __str__(self):
        return "(" + str(self.type) + " " + str(self.value) + ")"
    
    def __repr__(self):
        return str(self)

# class MediciFrontendHelper:
#     def __init__(self):
#         pass

#     def frontend_action(action):


class MediciState:
    def __init__(self, game):
        self.game = game
        self.turn_player = 0 # first buyer in turn
        self.current_player = 0  
        self.phase = Phase.Draw
        self.bids = {}
        self.money = [40] * game.n_players
        self.cards_in_play = []
        self.deck = game.all_cards.copy()
        shuffle(self.deck)

        self.cards_in_play = []
        self.cards_in_play.append(self.deck.pop())

        self.ships = []
        for i in range(self.game.n_players):
            self.ships.append([])

        self.pyramids = {}
        for resource in [Type.Cloth, Type.Fur, Type.Grain, Type.Dye, Type.Spice]:
            self.pyramids[resource] = [0] * self.game.n_players

        self.day = 0
        self.is_game_over = False
        self.winner = None

        self.logs = []

    def frontend_action(self, action):
        if isinstance(action, BidAction):
            return {
                "type": "bid",
                "value": action.value
            }
        elif isinstance(action, DrawAction):
            return {
                "type": "draw",
                "value": draw_action_strings[action]
            }
        else:
            return {
                "type": "unknown",
                "value": -1
            }
        
    def from_frontend_action(self, frontend_action):
        if frontend_action["type"] == "bid":
            return BidAction(frontend_action["value"])
        elif frontend_action["type"] == "draw":
            return DrawAction[frontend_action["value"]]
        else:
            return None
        
    def frontend_card(self, card):
        return (type_strings[int(card.type)], card.value)

    def frontend_state(self):
        cards_in_play = [self.frontend_card(card) for card in self.cards_in_play]
        # for card in self.cards_in_play:
            # cards_in_play.append((type_strings[int(card.type)], card.value))
        ships = [[], [], [], [], []]
        ship_totals = [0, 0, 0, 0, 0]
        for i, ship in enumerate(self.ships):
            ships[i] = [self.frontend_card(card) for card in ship]
            ship_totals[i] = sum([card.value for card in ship])

        players = []
        for i in range(self.game.n_players):
            players.append({
                "id": i,
                "money": self.money[i],
                "ship": ships[i],
                "ship_total": ship_totals[i],
                "bid": self.bids[i] if i in self.bids else -1
            })

        raw_legal_actions = self.LegalActions()
        if raw_legal_actions:
            legal_actions = [self.frontend_action(action) for action in raw_legal_actions]
        else:
            legal_actions = []

        pyramids = {}
        for resource in [Type.Cloth, Type.Fur, Type.Grain, Type.Dye, Type.Spice]:
            pyramid = []
            for i in range(self.game.n_pyramid_levels):
                pyramid_level = []
                for player in range(self.game.n_players):
                    if self.pyramids[resource][player] == i:
                        pyramid_level.append(player)
                pyramid.append(pyramid_level)
            pyramids[type_strings[int(resource)]] = pyramid

        logs = self.logs.copy()
        logs.reverse()

        return {
            "day": self.day,
            "phase": phase_strings[self.phase],
            "turn_player": self.turn_player,
            "current_player": self.current_player,
            "players": players,
            "cards_in_play": cards_in_play,
            "pyramids": pyramids,
            "legal_actions": legal_actions,
            "deck": [self.frontend_card(card) for card in self.deck],
            "logs": logs,
            "winner": self.winner,
            "is_game_over": self.is_game_over,
        }
    
    def DoApplyFrontendAction(self, action):
        self.DoApplyAction(self.from_frontend_action(action))


    def LegalActions(self):
        if self.phase == Phase.Draw:
            # can't make a lot that doesn't fit on a ship
            can_draw = False
            for ship in self.ships:
                if len(ship) + len(self.cards_in_play) + 1 <= self.game.kShipCapacity:
                    can_draw = True
                    break

            # can only draw if there is a card to draw
            if len(self.deck) == 0:
                can_draw = False

            if can_draw:
                return [DrawAction.Draw, DrawAction.Pass]
            else:
                return [DrawAction.Pass]
        
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
            self.logs.append(f"Player {str(self.current_player)} passes.")
            self.current_player = self.NextPlayer(self.current_player)
            self.phase = Phase.Bid
            

        elif action == DrawAction.Draw:
            card = self.deck.pop()
            self.cards_in_play.append(card)
            self.logs.append(f"Player {str(self.current_player)} draws a {str(card)}.")
            
            if len(self.cards_in_play) == 3:
                self.current_player = self.NextPlayer(self.current_player)
                self.phase = Phase.Bid

        elif isinstance(action, BidAction):

            self.bids[self.current_player] = action.value
            self.logs.append(f"Player {str(self.current_player)} bids ${str(action.value)}.")

            if self.current_player == self.turn_player:
                self.CompleteAuction()
            elif len(self.deck) == 0:
                self.CompleteAuction()
            else:
                self.current_player = self.NextPlayer(self.current_player)
                # while len(self.ships[self.current_player]) >= self.game.kShipCapacity:
                #     self.current_player = self.NextPlayer(self.current_player)
    
    def all_ships_but_one_full(self):
        n_full_ships = 0
        unfull_ship = -1
        for i, ship in enumerate(self.ships):
            if len(ship) >= self.game.kShipCapacity:
                n_full_ships += 1
            else:
                unfull_ship = i
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
            self.ships[winner] += self.cards_in_play

            # update purchase counts
            for card in self.cards_in_play:
                if card.type != Type.Gold:
                    self.pyramids[card.type][winner] += 1
            

        # check if day is over
        all_ships_but_one_full, unfull_ship_idx = self.all_ships_but_one_full()
        if all_ships_but_one_full:
            self.CompleteShip(unfull_ship_idx)
            self.CompleteDay()
        elif len(self.deck) == 0:
            self.CompleteDay()
        else:
            self.cards_in_play = [self.deck.pop()]
            self.bids = {}
            self.phase = Phase.Draw

            # first player to bid is the next player who has capacity
            self.turn_player = self.NextPlayer(self.turn_player)
            while len(self.ships[self.turn_player]) >= self.game.kShipCapacity:
                self.turn_player = self.NextPlayer(self.turn_player)
            self.current_player = self.turn_player


    def DoShipValueScoring(self):
        ship_values = [0, 0, 0, 0]
        for player, ship in enumerate(self.ships):
            ship_values[player] = sum([card.value for card in ship])
        
        # work out winning ship values
        ship_values_unique = sorted(list(set(ship_values)), reverse=True)
        first_value = ship_values_unique[0]
        if len(ship_values_unique) > 1:
            second_value = ship_values_unique[1]
        if len(ship_values_unique) > 2:
            third_value = ship_values_unique[2]
        
        # work out tiering of players by ship value
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

        # determine points for ship values
        if len(first_players) == 1:
            top_ship_value_reward = self.game.kShipValueRewards[0]
            self.money[first_players[0]] += top_ship_value_reward
            self.logs.append(f"Player {str(first_players[0])} gets ${top_ship_value_reward} for having the highest ship value ({first_value}).")

            if len(second_players) == 1:
                second_ship_value_reward = self.game.kShipValueRewards[1]
                self.money[second_players[0]] += second_ship_value_reward
                self.logs.append(f"Player {str(second_players[0])} gets ${second_ship_value_reward} for having the second highest ship value ({second_value}).")
                
                third_ship_value_reward = self.game.kShipValueRewards[2] // len(third_players)
                for player in third_players:
                    self.money[player] += third_ship_value_reward
                if len(third_players) == 1:
                    self.logs.append(f"Player {third_players[0]} gets ${third_ship_value_reward} for having the third highest ship value ({third_value}).")
                else:
                    self.logs.append(f"Players {str(third_players)} get ${third_ship_value_reward} for having the third highest ship value ({third_value}).")
            else:
                second_ship_value_reward = (self.game.kShipValueRewards[1] + self.game.kShipValueRewards[2]) // len(second_players)
                for player in second_players:
                    self.money[player] += second_ship_value_reward
                if len(second_players) == 2:
                    self.logs.append(f"Players {str(second_players[0])} and {str(second_players[1])} get ${second_ship_value_reward} for having the second highest ship value.")
                else:
                    self.logs.append(f"Players {str(second_players)} get ${second_ship_value_reward} for having the second highest ship value.")
 
        elif len(first_players) == 2:
            top_ship_value_reward = (self.game.kShipValueRewards[0] + self.game.kShipValueRewards[1]) // len(first_players)
            self.money[first_players[0]] += top_ship_value_reward
            self.money[first_players[1]] += top_ship_value_reward
            self.logs.append(f"Players {str(first_players[0])} and {str(first_players[1])} get ${top_ship_value_reward} for having the third highest ship value.")

            second_ship_value_reward = self.game.kShipValueRewards[2] // len(second_players)
            for player in second_players:
                self.money[player] += second_ship_value_reward
            if len(second_players) == 1:
                self.logs.append(f"Player {second_players[0]} gets ${second_ship_value_reward} for having the second highest ship value.")
            else:
                self.logs.append(f"Players {str(second_players)} get ${second_ship_value_reward} for having the second highest ship value.")
            

        elif len(first_players) >= 3:
            top_ship_value_reward = (self.game.kShipValueRewards[0] + self.game.kShipValueRewards[1] + self.game.kShipValueRewards[2]) // len(first_players)
            for player in first_players:
                self.money[player] += top_ship_value_reward
            self.logs.append(f"Players {str(first_players)} get ${top_ship_value_reward} for having the highest ship value.")

    def DoPyramidScoring(self):
        # determine points for pyramids
        for type in [Type.Cloth, Type.Fur, Type.Grain, Type.Dye, Type.Spice]:
            
            pyramid = self.pyramids[type]
            # print(f"type: {type}")
            # print(f"pyramid: {pyramid}")
            top_pyramid_value = max(pyramid)
            try:
                second_pyramid_value = max([value for value in pyramid if value != top_pyramid_value])
            except:
                second_pyramid_value = 0
            # print(f"top: {top_pyramid_value}")
            # print(f"second: {second_pyramid_value}")

            top_purchasers = [player for player in range(self.game.n_players) if pyramid[player] == top_pyramid_value]
            second_purchasers = [player for player in range(self.game.n_players) if pyramid[player] == second_pyramid_value]

            if len(top_purchasers) == 1:
                pyramid_reward_top = self.game.kPyramidRewards[0]
                self.money[top_purchasers[0]] += pyramid_reward_top
                self.logs.append(f"Player {top_purchasers[0]} gets ${pyramid_reward_top} for having the most {type_strings[int(type)]}.")

                pyramid_reward_second = self.game.kPyramidRewards[1] // len(second_purchasers)
                for player in second_purchasers:
                    self.money[player] += pyramid_reward_second
                self.logs.append(f"Player(s) {second_purchasers} get(s) ${pyramid_reward_second} for having the second most {type_strings[int(type)]}.")

            else:
                pyramid_reward_top = (self.game.kPyramidRewards[0] + self.game.kPyramidRewards[1]) // len(top_purchasers)
                for player in top_purchasers:
                    self.money[player] += pyramid_reward_top
                self.logs.append(f"Player(s) {top_purchasers} get(s) ${pyramid_reward_top} for purchasing the most {type_strings[int(type)]}.")


            # determine bonus points for pyramid
            for player in range(self.game.n_players):
                if pyramid[player] == 5:
                    self.money[player] += self.game.kPyramidBonusFive
                    self.logs.append(f"Player {player} gets ${self.game.kPyramidBonusFive} for purchasing 5 {type_strings[int(type)]}.")
                if pyramid[player] == 6:
                    self.money[player] += self.game.kPyramidBonusSix
                    self.logs.append(f"Player {player} gets ${self.game.kPyramidBonusSix} for purchasing 6 {type_strings[int(type)]}.")
                if pyramid[player] >= 7:
                    self.money[player] += self.game.kPyramidBonusSeven
                    self.logs.append(f"Player {player} gets ${self.game.kPyramidBonusSeven} for purchasing 7 {type_strings[int(type)]}.")
    
    def DoScoring(self):        
        self.DoShipValueScoring()
        self.DoPyramidScoring()

    def CompleteDay(self):

        self.DoScoring()

        self.ships = [[] for _ in range(self.game.n_players)]

        if self.day == 2:
            self.phase = Phase.GameOver
            self.is_game_over = True
            highest_money = max(self.money)
            self.winner = self.money.index(highest_money)
        else: # next day
            self.day += 1

            self.deck = self.game.all_cards.copy()
            shuffle(self.deck)

            self.cards_in_play = [self.deck.pop()]
            self.bids = {}
            self.phase = Phase.Draw

            # determine start player for new day
            lowest_money = min(self.money)
            start_player = self.money.index(lowest_money)
            self.turn_player = start_player
            self.current_player = start_player

    def IsTerminal(self):
        return self.phase == Phase.GameOver

    def ToString(self):
        s = "Day: " + str(self.day) + "\n"
        s += "Phase: " + str(self.phase) + "\n"
        s += "Turn Player: " + str(self.turn_player) + "\n"
        s += "Current Player: " + str(self.current_player) + "\n"
        s += "Bids: " + str(self.bids) + "\n"
        s += "Money: " + str(self.money) + "\n"
        s += "Cards in Play: " +  str(self.cards_in_play) + "\n"
        s += "Deck: " + str(self.deck) + "\n"
        s += "Ships: \n"
        for i, ship in enumerate(self.ships):
            s += str(i) + ": " + str(ship) + "\n"


        return s

class MediciGame:
    all_cards = [
        Card(type, i) 
        for type in [Type.Cloth, Type.Fur, Type.Grain, Type.Dye, Type.Spice]
        for i in [0, 1, 2, 3, 4, 5, 5] 
    ] + [Card(Type.Gold, 10)]

    def __init__(self):
        self.n_players = 4

        self.kShipCapacity = 5
        self.kHighestPoints = 10
        self.kSecondHighestPoints = 5

        self.kFiveBonus = 5
        self.kSixBonus = 10
        self.kSevenBonus = 20

        # ship value rewards
        self.kShipValueRewards = [30, 20, 10]

        # pyramid rewards
        self.kPyramidRewards = [10, 5]
        
        # pyramid bonus
        self.kPyramidBonusFive = 5
        self.kPyramidBonusSix = 10
        self.kPyramidBonusSeven = 20

        self.n_pyramid_levels = 8

    
    def InitialState(self):
        return MediciState(self)
    
class RandomBot:
    def ChooseAction(self, state):
        return choice(state.LegalActions())

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