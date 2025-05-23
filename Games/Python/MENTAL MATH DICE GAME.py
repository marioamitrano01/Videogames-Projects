import random
import sys
import time
import select
import math
from typing import Optional, Tuple, List, Dict, Any
from abc import ABC, abstractmethod




try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except ImportError:
    class Fore:
        RED = ''
        GREEN = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        RESET = ''
    class Style:
        RESET_ALL = ''

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING_LIBS = True
except ImportError:
    HAS_PLOTTING_LIBS = False


def get_tolerance(operation: str) -> float:
    
    if operation == "division":
        return 0.05
    else:
        return 1e-4

def compute_operation(dice_values: List[int], operation: str) -> float:
    
    if not dice_values:
        return 0.0

    if operation == "sum":
        return float(sum(dice_values))
    elif operation == "difference":
        result = dice_values[0]
        for d in dice_values[1:]:
            result -= d
        return float(result)
    elif operation == "multiplication":
        result = 1
        for d in dice_values:
            result *= d
        return float(result)
    elif operation == "division":
        result = dice_values[0]
        for d in dice_values[1:]:
            result /= d
        return float(result)
    else:
        return 0.0

class TimeoutException(Exception):
    pass

class GameConfig:
    
    
    DEFAULT_TIMEOUT_SECONDS: int = 12  
    NUM_DICE: int = 12                
    FACES: int = 6                    

class ConfigManager:
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config_values = {}
        return cls._instance

    def set_config(self, key: str, value: Any) -> None:
        self.config_values[key] = value

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config_values.get(key, default)

class LoggerLevel:
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class GameLogger:
    def __init__(self, level: int = LoggerLevel.INFO):
        self._level = level

    def set_level(self, level: int) -> None:
        self._level = level

    def debug(self, msg: str) -> None:
        if self._level <= LoggerLevel.DEBUG:
            print(f"{Fore.GREEN}[DEBUG]{Style.RESET_ALL} {msg}")

    def info(self, msg: str) -> None:
        if self._level <= LoggerLevel.INFO:
            print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {msg}")

    def warning(self, msg: str) -> None:
        if self._level <= LoggerLevel.WARNING:
            print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {msg}")

    def error(self, msg: str) -> None:
        if self._level <= LoggerLevel.ERROR:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {msg}")

    def critical(self, msg: str) -> None:
        if self._level <= LoggerLevel.CRITICAL:
            print(f"{Fore.RED}[CRITICAL]{Style.RESET_ALL} {msg}")

class BaseDice(ABC):
    @abstractmethod
    def roll(self, override_count: Optional[int] = None) -> List[int]:
        pass



class MultipleDice(BaseDice):
    
    def __init__(self, num_dice: int = GameConfig.NUM_DICE, faces: int = GameConfig.FACES):
        self.num_dice = num_dice
        self.faces = faces
        self._last_roll: List[int] = []

    def roll(self, override_count: Optional[int] = None) -> List[int]:
        count = override_count if override_count is not None else self.num_dice
        self._last_roll = [random.randint(1, self.faces) for _ in range(count)]
        return self._last_roll



class Player:
    def __init__(self, starting_balance: float):
        self.balance = float(starting_balance)
        self.name = "Player1"

    def place_bet(self, amount: float) -> bool:
        """Subtract 'amount' if enough funds; returns True if successful."""
        amount = float(amount)
        if amount > self.balance:
            return False
        self.balance -= amount
        return True

    def win_bet(self, amount: float) -> None:
        """Add 'amount' to player's balance."""
        self.balance += amount



class GameHistory:
    
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.initial_balance: float = 0.0

    def set_initial_balance(self, balance: float) -> None:
        self.initial_balance = balance

    def add_record(self,
                   dice_results: List[int],
                   operation_chosen: str,
                   user_guess: float,
                   correct_value: float,
                   guess_was_correct: bool,
                   bet_amount: float,
                   balance_after: float,
                   timed_out: bool) -> None:
        record = {
            "dice_results": dice_results,
            "operation": operation_chosen,
            "user_guess": user_guess,
            "correct_value": correct_value,
            "guess_was_correct": guess_was_correct,
            "bet_amount": bet_amount,
            "balance_after": balance_after,
            "timed_out": timed_out,
            "timestamp": time.time()
        }
        self.records.append(record)

    def print_summary(self) -> None:
        print(f"{Fore.YELLOW}--- GAME HISTORY ---{Fore.RESET}")
        for i, rec in enumerate(self.records, start=1):
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rec["timestamp"]))
            dice_str = ", ".join(str(d) for d in rec["dice_results"])
            print(f"{i}. [{ts}]")
            print(f"    Dice rolled: {dice_str}")
            print(f"    Operation: {rec['operation']}, Bet=${rec['bet_amount']:.2f}")

            if rec["timed_out"]:
                print(f"    TIMEOUT! No valid answer given in time. Balance=${rec['balance_after']:.2f}")
            else:
                user_str = f"{rec['user_guess']:.4f}"
                correct_str = f"{rec['correct_value']:.4f}"
                outcome_str = "CORRECT" if rec["guess_was_correct"] else "WRONG"
                print(f"    Your answer: {user_str}, correct value: {correct_str} -> {outcome_str}")
                print(f"    Balance=${rec['balance_after']:.2f}")

    def show_history_plot(self) -> None:
        if not HAS_PLOTTING_LIBS:
            print(f"{Fore.RED}matplotlib/seaborn not installed. Cannot show balance plot.{Fore.RESET}")
            return

        import pandas as pd
        data = []
        data.append({"round": 0, "balance": self.initial_balance})

        for i, r in enumerate(self.records, start=1):
            data.append({"round": i, "balance": r["balance_after"]})

        df = pd.DataFrame(data)
        sns.set_theme(style="whitegrid", context="talk")
        plt.figure(figsize=(10, 6))

        ax = sns.lineplot(
            x="round", y="balance", data=df,
            marker="o", markersize=8, linewidth=2,
            markeredgecolor="black", color="blue"
        )
        plt.title("Player's Balance Over Rounds (USD)", fontsize=16, fontweight='bold')
        plt.xlabel("Round Number", fontsize=14)
        plt.ylabel("Balance (USD)", fontsize=14)

        for x, y in zip(df["round"], df["balance"]):
            plt.text(
                x, y + 0.2, f"{y:.2f}",
                fontsize=10, ha='center', va='bottom',
                color="black"
            )

        plt.tight_layout()
        plt.show()



class GameUI:
    
    ALLOWED_OPERATIONS = ["sum", "difference", "multiplication", "division"]

    def prompt_starting_balance(self) -> float:
        while True:
            inp = input(f"{Fore.GREEN}Please enter your starting balance in USD: {Fore.RESET}")
            try:
                val = float(inp)
                if val <= 0:
                    print(f"{Fore.RED}The balance must be a positive number!{Fore.RESET}")
                    continue
                return val
            except ValueError:
                print(f"{Fore.RED}Invalid input! Please enter a numeric value.{Fore.RESET}")

    def prompt_bet_amount(self, current_balance: float) -> float:
        while True:
            inp = input(f"{Fore.GREEN}Enter your bet amount (Current balance: ${current_balance:.2f}): {Fore.RESET}")
            try:
                val = float(inp)
                if val <= 0:
                    print(f"{Fore.RED}Bet amount must be > 0!{Fore.RESET}")
                    continue
                return val
            except ValueError:
                print(f"{Fore.RED}Invalid input! Please enter a numeric value {Fore.RESET}")

    def prompt_operation_choice(self) -> str:
        
        while True:
            print(f"{Fore.MAGENTA}Choose an operation among: {', '.join(self.ALLOWED_OPERATIONS)}{Fore.RESET}")
            choice = input(f"{Fore.CYAN}Your choice: {Fore.RESET}").strip().lower()
            if choice in self.ALLOWED_OPERATIONS:
                return choice
            else:
                print(f"{Fore.RED}Invalid operation! Please try again.{Fore.RESET}")

    def show_dice_results(self, dice_values: List[int]) -> None:
        dice_str = ", ".join(str(d) for d in dice_values)
        print(f"\n{Fore.BLUE}Your {len(dice_values)} dice rolls: {dice_str}{Fore.RESET}")
        print(f"{Fore.MAGENTA}Compute the result based on your chosen operation (mind the tolerance!){Fore.RESET}")

    def prompt_operation_result(self, timeout_seconds: int) -> float:
        """
        Ask the user to provide the numeric result of the chosen operation (float).
        I do NOT show any countdown. If no input within 'timeout_seconds', raise TimeoutException.
        """
        print(f"{Fore.CYAN}You have {timeout_seconds} seconds to enter the result...{Fore.RESET}")
        user_input = self._get_input_with_timeout(timeout_seconds)
        try:
            return float(user_input)
        except ValueError:
            return 1e99

    def show_timeout_message(self) -> None:
        print(f"{Fore.RED}Time is up! You did not answer in time. You lose your bet.{Fore.RESET}")

    def show_wrong_message(self) -> None:
        print(f"{Fore.RED}Wrong result! You lose your bet.{Fore.RESET}")

    def show_win_message(self, winnings: float) -> None:
        print(f"{Fore.GREEN}Congratulations! You won ${winnings:.2f}!{Fore.RESET}")

    def show_current_balance(self, balance: float) -> None:
        print(f"{Fore.CYAN}Your current balance is: ${balance:.2f}{Fore.RESET}")

    def ask_continue(self) -> bool:
        ans = input(f"\n{Fore.MAGENTA}Do you want to keep playing? (y/n): {Fore.RESET}").strip().lower()
        return (ans == 'y')

    def show_goodbye(self) -> None:
        print(f"{Fore.MAGENTA}Thank you for playing Pagane! See you next time.{Fore.RESET}")

    def _get_input_with_timeout(self, timeout_seconds: int) -> str:
        
        rlist, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
        if rlist:
            return sys.stdin.readline().strip()
        else:
            raise TimeoutException()



class GameCore:
    
    _instance = None

    def __init__(self):
        self.logger = GameLogger(LoggerLevel.DEBUG)
        self.config_manager = ConfigManager()
        self._initialized = False

    def initialize(self):
        if not self._initialized:
            self.config_manager.set_config("timeout_seconds", GameConfig.DEFAULT_TIMEOUT_SECONDS)
            self.config_manager.set_config("num_dice", GameConfig.NUM_DICE)
            self.config_manager.set_config("faces", GameConfig.FACES)
            self._initialized = True

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialize()
        return cls._instance

class MarioGame:

    def __init__(self):
        self.core = GameCore.instance()
        self.logger = self.core.logger
        self.config_mgr = self.core.config_manager

        self.timeout_seconds = self.config_mgr.get_config("timeout_seconds", 12)
        self.default_num_dice = self.config_mgr.get_config("num_dice", 12)
        self.faces = self.config_mgr.get_config("faces", 6)

        self.ui = GameUI()
        self.history = GameHistory()
        self.player: Optional[Player] = None

        self.dice = MultipleDice(num_dice=self.default_num_dice, faces=self.faces)

    def start_game(self) -> None:
        self.logger.info("Starting Pagane game (one-step question, bigger division tolerance).")
        starting_balance = self.ui.prompt_starting_balance()
        self.player = Player(starting_balance)

        self.history.set_initial_balance(starting_balance)

        try:
            self.game_loop()
        except KeyboardInterrupt:
            self.logger.warning("Game interrupted by user")
        finally:
            self.ui.show_goodbye()
            self.history.print_summary()
            self.history.show_history_plot()
            self.logger.info("Game ended")

    def game_loop(self) -> None:
        """Main loop of betting rounds."""
        while True:
            if not self.player:
                self.logger.error("Player not initialized")
                return

            if self.player.balance <= 0:
                self.logger.info("Player is out of money. Ending game")
                print(f"{Fore.RED}You have run out of money. Game over{Fore.RESET}")
                break

            bet_amount = self.ui.prompt_bet_amount(self.player.balance)
            if not self.player.place_bet(bet_amount):
                print(f"{Fore.RED}Insufficient funds for that bet!{Fore.RESET}")
                self.logger.warning("Player tried to bet more than their balance")
                continue

            operation_choice = self.ui.prompt_operation_choice()
            if operation_choice in ("sum", "difference"):
                dice_count = 12
            elif operation_choice == "multiplication":
                dice_count = 5
            else:  
                dice_count = 3

            dice_results = self.dice.roll(override_count=dice_count)
            self.ui.show_dice_results(dice_results)

            correct_value = compute_operation(dice_results, operation_choice)
            tol = get_tolerance(operation_choice)

            timed_out = False
            guess_was_correct = False
            user_guess: float = 1e99

            try:
                user_guess = self.ui.prompt_operation_result(self.timeout_seconds)
            except TimeoutException:
                timed_out = True
                self.ui.show_timeout_message()
            except Exception as e:
                self.logger.error(f"Unexpected error reading operation result: {e}")
                timed_out = True

            if timed_out:
                self.ui.show_current_balance(self.player.balance)
                self._store_history(
                    dice_results, operation_choice, user_guess, correct_value,
                    False, bet_amount, self.player.balance, True
                )
                if not self.ui.ask_continue():
                    break
                continue

            if abs(user_guess - correct_value) < tol:
                guess_was_correct = True
                self.player.win_bet(bet_amount * 2)
                self.ui.show_win_message(bet_amount)
            else:
                self.ui.show_wrong_message()

            self.ui.show_current_balance(self.player.balance)

            self._store_history(
                dice_results, operation_choice, user_guess, correct_value,
                guess_was_correct, bet_amount, self.player.balance, False
            )

            if not self.ui.ask_continue():
                break

    def _store_history(self,
                       dice_results: List[int],
                       operation_chosen: str,
                       user_guess: float,
                       correct_value: float,
                       guess_was_correct: bool,
                       bet_amount: float,
                       balance_after: float,
                       timed_out: bool) -> None:
        self.history.add_record(
            dice_results=dice_results,
            operation_chosen=operation_chosen,
            user_guess=user_guess,
            correct_value=correct_value,
            guess_was_correct=guess_was_correct,
            bet_amount=bet_amount,
            balance_after=balance_after,
            timed_out=timed_out
        )

def main():
    random.seed(time.time())
    game = MarioGame()
    game.start_game()

if __name__ == "__main__":
    main()
