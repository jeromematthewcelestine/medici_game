import medici
import random

def test_random_playouts(n_tests = 100):
    game = medici.MediciGame()

    for i in range(n_tests):
        state = game.InitialState()
        while not state.IsTerminal():
            legal_actions = state.LegalActions()
            action = random.choice(legal_actions)
            old_day = state.day
            state.DoApplyAction(action)
            if state.day > old_day:
                print(state.ToString())
        print(state.ToString())


def test_medici():
    test_random_playouts()

if __name__ == "__main__":
    test_medici()