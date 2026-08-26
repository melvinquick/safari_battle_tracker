from math import floor

from .yaml_file_handler import YamlFileHandler

pokemon_data = YamlFileHandler("resources/configs/safari_zone_data.yaml")
pokemon = pokemon_data.load_yaml_file()


class BattleSimulator:
    def __init__(self, game, pokemon_name):
        self.game = game
        self.pokemon_name = pokemon_name
        stats = pokemon["games"][game][pokemon_name]
        self.catch_rate = stats["catch_rate"]
        self.escape_rate = stats["escape_rate"]
        self.catch_factor = initial_catch_factor(self.catch_rate)
        self.escape_factor = initial_escape_factor(self.escape_rate)
        self.turn = 1
        self.active = True
        self.log_entries = []

    def get_catch_pct(self):
        return catch_percentage(self.catch_factor)

    def get_flee_pct(self):
        return flee_percentage(self.escape_factor)

    def preview_action(self, action):
        match action:
            case "bait":
                cf = modify_catch_factor(self.catch_factor, "bait")
                ef = modify_escape_factor(self.escape_factor, "bait")
            case "rock":
                cf = modify_catch_factor(self.catch_factor, "rock")
                ef = modify_escape_factor(self.escape_factor, "rock")
            case _:
                cf = self.catch_factor
                ef = self.escape_factor
        return catch_percentage(cf), flee_percentage(ef)

    def throw_ball(self):
        self.log(f"You threw a Safari Ball! (Catch: {self.get_catch_pct()}%)")

    def caught(self):
        self.log(f"The Pokémon was caught on turn {self.turn}!")
        self.active = False
        return "caught"

    def broke_free(self):
        self.log("The Pokémon broke free!")

    def throw_bait(self):
        self.catch_factor = modify_catch_factor(self.catch_factor, "bait")
        self.escape_factor = modify_escape_factor(self.escape_factor, "bait")
        self.log("You threw some Bait!")

    def throw_rock(self):
        self.catch_factor = modify_catch_factor(self.catch_factor, "rock")
        self.escape_factor = modify_escape_factor(self.escape_factor, "rock")
        self.log("You threw a Rock!")

    def run_away(self):
        self.log("You ran away!")
        self.active = False
        return "ran"

    def pokemon_stayed(self):
        self.log("The Pokémon stayed!")
        self.advance_turn()

    def pokemon_fled(self):
        self.log(f"The Pokémon fled on turn {self.turn}!")
        self.active = False
        return "fled"

    def advance_turn(self):
        self.turn += 1
        self.log(f"--- Turn {self.turn} ---")

    def predict_catch_within(self, turns):
        return predict_catch(self.get_catch_pct(), self.get_flee_pct(), turns)

    def log(self, message):
        self.log_entries.append(message)

    def get_log(self):
        return "\n".join(self.log_entries)


def initial_catch_factor(catch_rate):
    return floor(catch_rate * 100 / 1275)


def initial_escape_factor(escape_rate):
    return max(floor(escape_rate * 100 / 1275), 2)


def modify_catch_factor(current_factor, action):
    match action:
        case "bait":
            return max(floor(current_factor / 2), 3)
        case "rock":
            return min(current_factor * 2, 20)
        case _:
            return current_factor


def modify_escape_factor(current_factor, action):
    match action:
        case "bait":
            return max(floor(current_factor / 4), 1)
        case "rock":
            return min(current_factor * 2, 20)
        case _:
            return current_factor


def catch_percentage(catch_factor):
    modified_catch_rate = floor(catch_factor * 1275 / 100)
    return round(modified_catch_rate / 255 * 100, 1)


def flee_percentage(escape_factor):
    return float(5 * escape_factor)


def predict_catch(catch_pct, flee_pct, turns):
    catch_dec = catch_pct / 100
    flee_dec = flee_pct / 100
    continue_prob = (1 - catch_dec) * (1 - flee_dec)
    return round((1 - continue_prob**turns) * 100, 1)


def get_games():
    return list(pokemon["games"].keys())


def get_pokemon_list(game):
    return sorted(pokemon["games"][game].keys())


def get_display_name(poke_key):
    display_names = {
        "nidoran_f": "Nidoran♀",
        "nidoran_m": "Nidoran♂",
    }
    return display_names.get(poke_key, poke_key.replace("_", " ").title())


import subprocess


def clear():
    subprocess.run(["clear"], check=False, shell=True)


def preview_actions(catch_factor, escape_factor):
    ball_catch = catch_percentage(catch_factor)
    ball_flee = flee_percentage(escape_factor)

    bait_catch_factor = modify_catch_factor(catch_factor, "bait")
    bait_escape_factor = modify_escape_factor(escape_factor, "bait")
    bait_catch = catch_percentage(bait_catch_factor)
    bait_flee = flee_percentage(bait_escape_factor)

    rock_catch_factor = modify_catch_factor(catch_factor, "rock")
    rock_escape_factor = modify_escape_factor(escape_factor, "rock")
    rock_catch = catch_percentage(rock_catch_factor)
    rock_flee = flee_percentage(rock_escape_factor)

    print(f"1. Ball: Catch {ball_catch}%  |  Flee {ball_flee}%")
    print(f"2. Bait: Catch {bait_catch}%  |  Flee {bait_flee}%")
    print(f"3. Rock: Catch {rock_catch}%  |  Flee {rock_flee}%")
    print("4. Run")


def action_tracker(pokemon_name, catch_rate, escape_rate):
    catch_factor = initial_catch_factor(catch_rate)
    escape_factor = initial_escape_factor(escape_rate)

    battle_state = "ongoing"
    turn = 1

    while battle_state == "ongoing":
        clear()
        print(f"Pokemon: {pokemon_name}")
        print(f"Current Catch Chance: {catch_percentage(catch_factor)}%")
        print(f"Current Escape Chance: {flee_percentage(escape_factor)}%")
        print(f"\n--- Turn {turn} ---")

        preview_actions(catch_factor, escape_factor)

        user_action = get_user_action()
        match user_action:
            case "1":
                print("\nYou threw a Safari Ball!")
                catch_result = input("Was the Pokemon caught? (y/n): ").lower()
                if catch_result == "y":
                    print("The Pokemon was caught!")
                    battle_state = "ended"
                    continue
                else:
                    print("The Pokemon broke free!")
            case "2":
                print("\nYou threw some Bait!")
                catch_factor = modify_catch_factor(catch_factor, "bait")
                escape_factor = modify_escape_factor(escape_factor, "bait")
            case "3":
                print("\nYou threw a Rock!")
                catch_factor = modify_catch_factor(catch_factor, "rock")
                escape_factor = modify_escape_factor(escape_factor, "rock")
            case "4":
                print("\nYou ran away!")
                battle_state = "ended"
                continue

        if battle_state == "ongoing":
            pokemon_action = get_pokemon_action()
            match pokemon_action:
                case "1":
                    print("The Pokemon stayed!")
                case "2":
                    print("The Pokemon fled!")
                    battle_state = "ended"
                    continue

        turn += 1


def get_user_action():
    action = input("\nWhat action will you take? (1-4): ")
    return action


def get_pokemon_action():
    action = input("What did the Pokemon do? (1. Stayed, 2. Fled): ")
    return action


def get_game_selection():
    games = get_games()
    counter = 1
    for game in games:
        print(f"{counter}. {get_display_name(game)}")
        counter += 1
    game = input("\nPlease select a game from the list above: ")
    return games[int(game) - 1]


def get_pokemon_selection(game):
    pokes = get_pokemon_list(game)
    counter = 1
    for poke in pokes:
        print(f"{counter}. {get_display_name(poke)}")
        counter += 1
    poke = input("\nPlease select a Pokemon from the list above: ")
    return pokes[int(poke) - 1]


def main():
    game = get_game_selection()
    selected_pokemon = get_pokemon_selection(game)
    print(f"\nSelected Game: {get_display_name(game)}")
    print(f"Selected Pokemon: {get_display_name(selected_pokemon)}")

    sim = BattleSimulator(game, selected_pokemon)
    action_tracker(get_display_name(selected_pokemon), sim.catch_rate, sim.escape_rate)


if __name__ == "__main__":
    main()
