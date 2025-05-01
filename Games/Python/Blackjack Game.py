import random
import time
from colorama import init, Fore, Style, Back
import sys
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MaxNLocator

init(autoreset=True)

SUIT_SYMBOLS = {
    'Hearts':   Fore.RED + '♥' + Style.RESET_ALL,
    'Diamonds': Fore.RED + '♦' + Style.RESET_ALL,
    'Clubs':    Fore.BLUE + '♣' + Style.RESET_ALL,
    'Spades':   Fore.BLACK + '♠' + Style.RESET_ALL
}

CARD_ART_TEMPLATE = """\
┌─────────┐
│ {rank:<2}      │
│         │
│    {suit}    │
│         │
│      {rank:>2} │
└─────────┘
"""

CARD_BACK_ART = """\
┌─────────┐
│ ╔═════╗ │
│ ║     ║ │
│ ║  ♣  ║ │
│ ║     ║ │
│ ╚═════╝ │
└─────────┘
"""

def clear_screen():
    print("\033c", end="")

def card_ascii(card, hidden=False):
    if hidden:
        return CARD_BACK_ART.split('\n')
    
    rank_display = card.rank
    if card.rank in ['Jack', 'Queen', 'King', 'Ace']:
        rank_display = card.rank[0] 
        
    return CARD_ART_TEMPLATE.format(rank=rank_display, suit=SUIT_SYMBOLS[card.suit]).split('\n')

def display_hand_ascii(cards, role, hide_second=False):
    if hide_second and len(cards) > 1:
        visible_cards = [cards[0]]
        hidden_cards = cards[1:]
        card_lines = [card_ascii(card) for card in visible_cards]
        card_lines.extend([card_ascii(None, hidden=True) for _ in hidden_cards])
    else:
        card_lines = [card_ascii(card) for card in cards]
    
    transposed = list(zip(*card_lines))
    
    role_color = Fore.GREEN if role == "Player" else Fore.RED if role == "Dealer" else Fore.CYAN
    print(role_color + f"{role}'s Cards:" + Style.RESET_ALL)
    
    for line_tuple in transposed:
        print("  ".join(line_tuple))
    print()

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank} of {self.suit}"

    @property
    def value(self):
        if self.rank in ['Jack', 'Queen', 'King']:
            return 10
        elif self.rank == 'Ace':
            return 1
        else:
            return int(self.rank)

class Deck:
    def __init__(self, num_decks=6):
        self.card_categories = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.cards_list = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']
        self.num_decks = num_decks
        self.initial_cards = self.num_decks * 52
        self.reset_deck()

    def reset_deck(self):
        self.deck = [Card(rank, suit)
                     for _ in range(self.num_decks)
                     for suit in self.card_categories
                     for rank in self.cards_list]
        random.shuffle(self.deck)
        print(Fore.YELLOW + f"\n🔄 Shuffling {self.num_decks} decks ({len(self.deck)} cards)..." + Style.RESET_ALL)
        self._animate_shuffle()

    def _animate_shuffle(self):
        shuffling_chars = ['[ ]', '[=]', '[==]', '[===]', '[====]', '[=====]', '[======]', '[=======]', '[========]']
        for i in range(len(shuffling_chars)):
            sys.stdout.write(Fore.YELLOW + f"\rShuffling {shuffling_chars[i]}" + Style.RESET_ALL)
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 50 + "\r")
        sys.stdout.flush()
        print(Fore.GREEN + "✓ Deck ready!" + Style.RESET_ALL)

    def deal_card(self):
        return self.deck.pop()

    def cards_remaining(self):
        return len(self.deck)
    
    def remaining_percentage(self):
        return (len(self.deck) / self.initial_cards) * 100

    def needs_reshuffle(self):
        return len(self.deck) < (self.num_decks * 52 * 0.2) or len(self.deck) < 20

class Participant:
    def __init__(self, name):
        self.name = name
        self.cards = []
        self.wins = 0
        self.losses = 0
        self.ties = 0
        self.blackjacks = 0

    def receive_card(self, card):
        self.cards.append(card)

    def clear_hand(self):
        self.cards = []

    def compute_score(self):
        total = 0
        aces = 0

        for c in self.cards:
            if c.rank == 'Ace':
                aces += 1
            else:
                total += c.value

        total += aces

        for _ in range(aces):
            if total + 10 <= 21:
                total += 10
                break

        return total

    def is_blackjack(self):
        if len(self.cards) == 2:
            ranks = [c.rank for c in self.cards]
            if 'Ace' in ranks and any(r in ['10', 'Jack', 'Queen', 'King'] for r in ranks):
                return True
        return False

    def is_busted(self):
        return self.compute_score() > 21

class Player(Participant):
    def __init__(self, name):
        super().__init__(name)
        self.split_hands = []
        self.current_streak = 0
        self.best_streak = 0
        self.worst_streak = 0
        self.total_bets = 0
        self.total_winnings = 0

    def add_win(self, amount=0):
        self.wins += 1
        self.current_streak = max(1, self.current_streak + 1)
        self.best_streak = max(self.best_streak, self.current_streak)
        self.total_winnings += amount
        
    def add_loss(self, amount=0):
        self.losses += 1
        self.current_streak = min(-1, self.current_streak - 1)
        self.worst_streak = min(self.worst_streak, self.current_streak)
        self.total_bets += amount
        
    def add_tie(self):
        self.ties += 1
        self.current_streak = 0
        
    def add_blackjack(self):
        self.blackjacks += 1

class Dealer(Participant):
    def should_hit(self):
        return self.compute_score() < 17

class GameStats:
    def __init__(self):
        self.rounds_played = 0
        self.hands_played = 0
        self.capital_history = []
        self.win_rate_history = []
        self.outcome_history = []
        self.bet_sizes = []
        
    def add_round(self, outcome, capital, bet):
        self.rounds_played += 1
        self.hands_played += 1
        self.capital_history.append(capital)
        self.outcome_history.append(outcome)
        self.bet_sizes.append(bet)
        
        if len(self.outcome_history) > 0:
            wins = self.outcome_history.count("Win") + self.outcome_history.count("Blackjack")
            win_rate = wins / len(self.outcome_history) * 100
            self.win_rate_history.append(win_rate)
        else:
            self.win_rate_history.append(0)
    
    def add_split_round(self, outcome1, outcome2, capital, bet):
        self.rounds_played += 1
        self.hands_played += 2
        self.capital_history.append(capital)
        self.outcome_history.append(outcome1)
        self.outcome_history.append(outcome2)
        self.bet_sizes.append(bet)
        self.bet_sizes.append(bet)
        
        if len(self.outcome_history) > 0:
            wins = self.outcome_history.count("Win") + self.outcome_history.count("Blackjack")
            win_rate = wins / len(self.outcome_history) * 100
            self.win_rate_history.append(win_rate)
        else:
            self.win_rate_history.append(0)

class BlackjackDashboard:
    def __init__(self, stats, player, dealer, deck):
        self.stats = stats
        self.player = player
        self.dealer = dealer
        self.deck = deck
        
        plt.ion()  
        self.setup_dashboard()
        
    def setup_dashboard(self):
        self.fig = plt.figure(figsize=(14, 8))
        self.fig.canvas.set_window_title("Blackjack Analytics Dashboard")
        
        gs = gridspec.GridSpec(3, 3)
        
        self.capital_ax = plt.subplot(gs[0, :])
        self.win_rate_ax = plt.subplot(gs[1, 0])
        self.outcome_ax = plt.subplot(gs[1, 1:])
        self.stats_ax = plt.subplot(gs[2, 0])
        self.deck_ax = plt.subplot(gs[2, 1])
        self.bet_ax = plt.subplot(gs[2, 2])
        
        plt.subplots_adjust(hspace=0.4, wspace=0.3)
        self.fig.patch.set_facecolor('#f0f0f0')
        
        self.capital_ax.set_title("Capital Trend", fontsize=12, fontweight='bold')
        self.win_rate_ax.set_title("Win Rate (%)", fontsize=12, fontweight='bold')
        self.outcome_ax.set_title("Game Outcomes", fontsize=12, fontweight='bold')
        self.stats_ax.set_title("Player Statistics", fontsize=12, fontweight='bold')
        self.deck_ax.set_title("Deck Status", fontsize=12, fontweight='bold')
        self.bet_ax.set_title("Bet Distribution", fontsize=12, fontweight='bold')
        
        self.update_dashboard()
        
    def update_dashboard(self):
        self._update_capital_chart()
        self._update_win_rate_chart()
        self._update_outcome_chart()
        self._update_stats_table()
        self._update_deck_gauge()
        self._update_bet_histogram()
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
    def _update_capital_chart(self):
        self.capital_ax.clear()
        
        if len(self.stats.capital_history) > 0:
            x = list(range(len(self.stats.capital_history)))
            
            line = self.capital_ax.plot(x, self.stats.capital_history, marker='o', color='#1f77b4', 
                         linewidth=2, markersize=5)[0]
            
            self.capital_ax.fill_between(x, self.stats.capital_history, 
                              color='#1f77b4', alpha=0.3)
            
            if len(x) > 0:
                self.capital_ax.plot(x[0], self.stats.capital_history[0], 'go', markersize=8)
                self.capital_ax.plot(x[-1], self.stats.capital_history[-1], 'ro', markersize=8)
            
            if len(self.stats.capital_history) > 0:
                start_val = self.stats.capital_history[0]
                current_val = self.stats.capital_history[-1]
                
                self.capital_ax.annotate(f'€{start_val}', 
                               xy=(0, start_val),
                               xytext=(5, 10),
                               textcoords='offset points',
                               fontweight='bold')
                
                self.capital_ax.annotate(f'€{current_val}', 
                               xy=(len(self.stats.capital_history)-1, current_val),
                               xytext=(5, 10),
                               textcoords='offset points',
                               fontweight='bold')
                
                profit = current_val - start_val
                color = 'green' if profit >= 0 else 'red'
                sign = '+' if profit >= 0 else ''
                
                if len(self.stats.capital_history) > 1:
                    self.capital_ax.text(0.02, 0.05, f'P&L: {sign}€{profit} ({sign}{(profit/start_val)*100:.1f}%)',
                                transform=self.capital_ax.transAxes,
                                fontsize=10, fontweight='bold', color=color,
                                bbox=dict(facecolor='white', alpha=0.8, edgecolor=color, boxstyle='round,pad=0.5'))
        
        self.capital_ax.set_xlabel('Rounds')
        self.capital_ax.set_ylabel('Capital (€)')
        self.capital_ax.grid(True, linestyle='--', alpha=0.7)
        self.capital_ax.set_title("Capital Trend", fontsize=12, fontweight='bold')
        
        self.capital_ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    def _update_win_rate_chart(self):
        self.win_rate_ax.clear()
        
        if len(self.stats.win_rate_history) > 0:
            self.win_rate_ax.plot(self.stats.win_rate_history, marker='o', color='green', 
                       linewidth=2, markersize=4)
            
            self.win_rate_ax.axhline(y=50, color='r', linestyle='--', alpha=0.7)
            
            current_win_rate = self.stats.win_rate_history[-1]
            self.win_rate_ax.text(0.5, 0.05, f'Current: {current_win_rate:.1f}%',
                        transform=self.win_rate_ax.transAxes,
                        fontsize=10, fontweight='bold',
                        ha='center', bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.3'))
        
        self.win_rate_ax.set_ylim(0, 100)
        self.win_rate_ax.set_xlabel('Rounds')
        self.win_rate_ax.set_ylabel('Win Rate (%)')
        self.win_rate_ax.grid(True, linestyle='--', alpha=0.7)
        self.win_rate_ax.set_title("Win Rate Trend", fontsize=12, fontweight='bold')
        self.win_rate_ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    def _update_outcome_chart(self):
        self.outcome_ax.clear()
        
        if len(self.stats.outcome_history) > 0:
            outcomes = pd.Series(self.stats.outcome_history).value_counts()
            
            colors = {
                'Win': '#2ca02c',       
                'Blackjack': '#9467bd', 
                'Lose': '#d62728',      
                'Tie': '#1f77b4',       
                'Bust': '#ff7f0e'       
            }
            
            bars = self.outcome_ax.bar(outcomes.index, outcomes.values, 
                         color=[colors.get(outcome, '#7f7f7f') for outcome in outcomes.index])
            
            for bar in bars:
                height = bar.get_height()
                self.outcome_ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                          f'{height}',
                          ha='center', va='bottom', fontweight='bold')
            
            total = sum(outcomes.values)
            for i, v in enumerate(outcomes.values):
                percentage = (v / total) * 100
                self.outcome_ax.text(i, v/2, f'{percentage:.1f}%', 
                          ha='center', color='white', fontweight='bold')
        
        self.outcome_ax.set_ylabel('Count')
        self.outcome_ax.set_title("Game Outcomes", fontsize=12, fontweight='bold')
        self.outcome_ax.grid(True, axis='y', linestyle='--', alpha=0.7)

    def _update_stats_table(self):
        self.stats_ax.clear()
        
        self.stats_ax.axis('off')
        
        stats_data = [
            ['Total Hands', f"{self.stats.hands_played}"],
            ['Wins', f"{self.player.wins}"],
            ['Losses', f"{self.player.losses}"],
            ['Ties', f"{self.player.ties}"],
            ['Blackjacks', f"{self.player.blackjacks}"],
            ['Best Streak', f"{self.player.best_streak}"],
            ['Worst Streak', f"{self.player.worst_streak}"]
        ]
        
        table = self.stats_ax.table(
            cellText=stats_data,
            cellLoc='center',
            loc='center',
            colWidths=[0.5, 0.5]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        
        for i in range(len(stats_data)):
            table[(i, 0)].set_facecolor('#e6e6e6')
        
        self.stats_ax.set_title("Player Statistics", fontsize=12, fontweight='bold')

    def _update_deck_gauge(self):
        self.deck_ax.clear()
        
        cards_remaining = self.deck.cards_remaining()
        total_cards = self.deck.initial_cards
        percentage = (cards_remaining / total_cards) * 100
        
        gauge_colors = ['#d62728', '#ff7f0e', '#ffbb78', '#2ca02c']
        theta = np.linspace(0, 180, 100) * np.pi / 180
        r = 1.0
        
        for i, color in enumerate(gauge_colors):
            self.deck_ax.fill_between(
                theta[i*25:(i+1)*25], 0, r, 
                color=color, alpha=0.8
            )
        
        needle_theta = (percentage / 100) * 180 * np.pi / 180
        self.deck_ax.plot([0, np.sin(needle_theta)], [0, np.cos(needle_theta)], 
                'k-', linewidth=3)
        
        circle = plt.Circle((0, 0), 0.05, color='black')
        self.deck_ax.add_artist(circle)
        
        self.deck_ax.text(0, -0.2, f"{cards_remaining}/{total_cards} cards", 
                ha='center', fontsize=10, fontweight='bold')
        self.deck_ax.text(0, -0.4, f"{percentage:.1f}% remaining", 
                ha='center', fontsize=10)
        
        self.deck_ax.set_xlim(-1.2, 1.2)
        self.deck_ax.set_ylim(-0.5, 1.2)
        self.deck_ax.axis('off')
        self.deck_ax.set_title("Deck Status", fontsize=12, fontweight='bold')

    def _update_bet_histogram(self):
        self.bet_ax.clear()
        
        if len(self.stats.bet_sizes) > 0:
            self.bet_ax.hist(self.stats.bet_sizes, bins=5, color='#ff7f0e', alpha=0.7)
            
            avg_bet = sum(self.stats.bet_sizes) / len(self.stats.bet_sizes)
            self.bet_ax.axvline(avg_bet, color='r', linestyle='--', alpha=0.7)
            self.bet_ax.text(0.05, 0.95, f'Avg Bet: €{avg_bet:.1f}',
                   transform=self.bet_ax.transAxes,
                   fontsize=9, fontweight='bold',
                   va='top', bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.3'))
        
        self.bet_ax.set_xlabel('Bet Size (€)')
        self.bet_ax.set_ylabel('Frequency')
        self.bet_ax.grid(True, linestyle='--', alpha=0.7)
        self.bet_ax.set_title("Bet Distribution", fontsize=12, fontweight='bold')

class BlackjackGame:
    def __init__(self, initial_capital):
        self.deck_obj = Deck(num_decks=6)
        self.capital = initial_capital
        self.player = Player("Player")
        self.dealer = Dealer("Dealer")
        self.stats = GameStats()
        self.stats.capital_history.append(self.capital)
        
        self.dashboard = BlackjackDashboard(self.stats, self.player, self.dealer, self.deck_obj)
        
        self.round_number = 0
        self.results_log = []

    def deal_card_animated(self, recipient):
        card_symbols = ['🂠', '🂡', '🂢', '🂣', '🂤']
        for symbol in card_symbols:
            sys.stdout.write(Fore.CYAN + f"\rDealing card {symbol}" + Style.RESET_ALL)
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 20 + "\r")
        sys.stdout.flush()

        card = self.deck_obj.deal_card()
        recipient.receive_card(card)
        time.sleep(0.2)

    def deal_initial_cards(self):
        self.player.clear_hand()
        self.dealer.clear_hand()

        print(Fore.CYAN + "\nDealing initial cards..." + Style.RESET_ALL)
        
        self.deal_card_animated(self.player)
        self.deal_card_animated(self.dealer)
        self.deal_card_animated(self.player)
        self.deal_card_animated(self.dealer)

    def can_split(self, cards):
        if len(cards) == 2:
            def card_basic_value(card):
                if card.rank in ['Jack','Queen','King']:
                    return 10
                elif card.rank == 'Ace':
                    return 11
                else:
                    return int(card.rank)
            return card_basic_value(cards[0]) == card_basic_value(cards[1])
        return False

    def display_game_screen(self, bet, hide_dealer=True):
        clear_screen()
        
        print(Fore.MAGENTA + "╔══════════════════════════════════════════════════╗" + Style.RESET_ALL)
        print(Fore.MAGENTA + "║            🎮  MARIO'S BLACKJACK  🎮              ║" + Style.RESET_ALL)
        print(Fore.MAGENTA + "╚══════════════════════════════════════════════════╝" + Style.RESET_ALL)
        
        print(Fore.CYAN + f"Round #{self.round_number} | Capital: €{self.capital} | Current Bet: €{bet}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"Cards in deck: {self.deck_obj.cards_remaining()} ({self.deck_obj.remaining_percentage():.1f}%)" + Style.RESET_ALL)
        
        print(Fore.CYAN + "\n═════════════════════════════════════════════════════" + Style.RESET_ALL)
        
        display_hand_ascii(self.dealer.cards, "Dealer", hide_second=hide_dealer)
        
        if hide_dealer:
            dealer_shown_score = self.dealer.cards[0].value
            if self.dealer.cards[0].rank == 'Ace':
                dealer_shown_score = 11
            print(Fore.RED + f"Dealer shows: {dealer_shown_score}" + Style.RESET_ALL)
        else:
            dealer_score = self.dealer.compute_score()
            print(Fore.RED + f"Dealer's Score: {dealer_score}" + Style.RESET_ALL)
        
        print(Fore.CYAN + "═════════════════════════════════════════════════════" + Style.RESET_ALL)
        
        display_hand_ascii(self.player.cards, "Player")
        
        player_score = self.player.compute_score()
        score_color = Fore.GREEN if player_score <= 21 else Fore.RED
        print(score_color + f"Player's Score: {player_score}" + Style.RESET_ALL)
        
        print(Fore.CYAN + "═════════════════════════════════════════════════════" + Style.RESET_ALL)

    def player_turn(self, bet):
        player_busted = False
        first_action = True
        
        while True:
            self.display_game_screen(bet)
            
            if self.player.is_busted():
                player_busted = True
                print(Fore.RED + "💥 You busted!" + Style.RESET_ALL)
                time.sleep(1)
                break

            print("\n" + Fore.YELLOW + "Options:" + Style.RESET_ALL)
            print(Fore.GREEN + "[H]" + Style.RESET_ALL + " Hit  - Take another card")
            print(Fore.RED + "[S]" + Style.RESET_ALL + " Stand - End your turn")
            
            if first_action and self.capital >= bet:
                print(Fore.MAGENTA + "[D]" + Style.RESET_ALL + " Double Down - Double your bet and take one card")
            
            choice = input(Fore.YELLOW + "\nYour choice: " + Style.RESET_ALL).lower()

            if choice in ['h', 'hit']:
                print(Fore.GREEN + "\n🎯 You chose to hit!" + Style.RESET_ALL)
                self.deal_card_animated(self.player)
                first_action = False

            elif choice in ['s', 'stand']:
                print(Fore.RED + "\n🛑 You chose to stand!" + Style.RESET_ALL)
                time.sleep(0.5)
                break

            elif choice in ['d', 'double'] and first_action and self.capital >= bet:
                self.capital -= bet
                bet = bet * 2
                print(Fore.MAGENTA + "\n💰 You doubled down!" + Style.RESET_ALL)
                self.deal_card_animated(self.player)
                time.sleep(1)
                player_busted = self.player.is_busted()
                break
            else:
                print(Fore.RED + "\n❌ Invalid choice. Please try again." + Style.RESET_ALL)
                time.sleep(0.5)

        return bet, player_busted

    def dealer_turn(self):
        print(Fore.CYAN + "\n🎭 Dealer's turn..." + Style.RESET_ALL)
        time.sleep(0.5)
        
        self.display_game_screen(0, hide_dealer=False)
        
        while self.dealer.should_hit():
            print(Fore.RED + "Dealer hits!" + Style.RESET_ALL)
            time.sleep(1)
            self.deal_card_animated(self.dealer)
            self.display_game_screen(0, hide_dealer=False)
            
        if self.dealer.is_busted():
            print(Fore.GREEN + "💥 Dealer busted!" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"Dealer stands with {self.dealer.compute_score()}." + Style.RESET_ALL)
        
        time.sleep(1)
        
    def determine_winner(self, bet):
        player_score = self.player.compute_score()
        dealer_score = self.dealer.compute_score()
        
        self.display_game_screen(bet, hide_dealer=False)
        
        print(Fore.CYAN + "\n╔══════════════════════════════════════╗" + Style.RESET_ALL)
        print(Fore.CYAN + "║             GAME RESULT              ║" + Style.RESET_ALL)
        print(Fore.CYAN + "╚══════════════════════════════════════╝" + Style.RESET_ALL)
        
        outcome = ""
        if player_score > 21:
            self.player.add_loss(bet)
            print(Fore.RED + "❌ You busted! Dealer wins." + Style.RESET_ALL)
            outcome = "Bust"
        elif dealer_score > 21:
            winnings = bet * 2
            self.capital += winnings
            self.player.add_win(winnings)
            print(Fore.GREEN + f"✅ Dealer busts! You win €{bet}." + Style.RESET_ALL)
            outcome = "Win"
        elif player_score > dealer_score:
            winnings = bet * 2
            self.capital += winnings
            self.player.add_win(winnings)
            print(Fore.GREEN + f"✅ You beat the dealer! You win €{bet}." + Style.RESET_ALL)
            outcome = "Win"
        elif dealer_score > player_score:
            self.player.add_loss(bet)
            print(Fore.RED + "❌ Dealer wins with a higher score." + Style.RESET_ALL)
            outcome = "Lose"
        else:
            self.capital += bet  
            self.player.add_tie()
            print(Fore.YELLOW + "🤝 Push! It's a tie. Your bet is returned." + Style.RESET_ALL)
            outcome = "Tie"
        
        print(Fore.BLUE + f"\nYour capital: €{self.capital}" + Style.RESET_ALL)
        
        self.stats.add_round(outcome, self.capital, bet)
        self.dashboard.update_dashboard()
        
        return outcome
        
    def handle_blackjack(self, bet):
        player_blackjack = self.player.is_blackjack()
        dealer_blackjack = self.dealer.is_blackjack()
        
        if player_blackjack or dealer_blackjack:
            self.display_game_screen(bet, hide_dealer=False)
            
            print(Fore.CYAN + "\n╔═════════════════════════════════════╗" + Style.RESET_ALL)
            
            if player_blackjack and dealer_blackjack:
                self.capital += bet  
                self.player.add_tie()
                print(Fore.YELLOW + "║         🤝 PUSH - BOTH BLACKJACK!        ║" + Style.RESET_ALL)
                print(Fore.CYAN + "╚═════════════════════════════════════╝" + Style.RESET_ALL)
                print(Fore.YELLOW + "\nBoth you and the dealer have Blackjack! Your bet is returned." + Style.RESET_ALL)
                
                self.stats.add_round("Tie", self.capital, bet)
                self.dashboard.update_dashboard()
                return "Tie"
                
            elif player_blackjack:
                blackjack_payout = bet * 2.5
                self.capital += blackjack_payout
                self.player.add_win(blackjack_payout - bet)
                self.player.add_blackjack()
                
                print(Fore.GREEN + "║          🎉 BLACKJACK! YOU WIN!          ║" + Style.RESET_ALL)
                print(Fore.CYAN + "╚═════════════════════════════════════╝" + Style.RESET_ALL)
                print(Fore.GREEN + f"\n💰 Blackjack pays 3:2! You win €{blackjack_payout - bet}." + Style.RESET_ALL)
                
                self.stats.add_round("Blackjack", self.capital, bet)
                self.dashboard.update_dashboard()
                return "Blackjack"
                
            elif dealer_blackjack:
                self.player.add_loss(bet)
                print(Fore.RED + "║         ❌ DEALER HAS BLACKJACK!          ║" + Style.RESET_ALL)
                print(Fore.CYAN + "╚═════════════════════════════════════╝" + Style.RESET_ALL)
                print(Fore.RED + "\nDealer has Blackjack. You lose your bet." + Style.RESET_ALL)
                
                self.stats.add_round("Lose", self.capital, bet)
                self.dashboard.update_dashboard()
                return "Lose"
        
        return None
        
    def play_single_hand(self, bet):
        blackjack_result = self.handle_blackjack(bet)
        if blackjack_result is not None:
            return blackjack_result
            
        bet, player_busted = self.player_turn(bet)
        
        if player_busted:
            self.display_game_screen(bet, hide_dealer=False)
            print(Fore.RED + "\n💥 You busted! Dealer wins." + Style.RESET_ALL)
            self.player.add_loss(bet)
            
            self.stats.add_round("Bust", self.capital, bet)
            self.dashboard.update_dashboard()
            return "Bust"
            
        self.dealer_turn()
        
        return self.determine_winner(bet)
        
    def print_banner(self, text):
        print(Fore.MAGENTA + "╔══════════════════════════════════════════════════╗" + Style.RESET_ALL)
        print(Fore.MAGENTA + f"║{text.center(50)}║" + Style.RESET_ALL)
        print(Fore.MAGENTA + "╚══════════════════════════════════════════════════╝" + Style.RESET_ALL)
        
    def play_round(self):
        self.round_number += 1
        
        if self.deck_obj.needs_reshuffle():
            print(Fore.MAGENTA + "\n🔄 Reshuffling the deck..." + Style.RESET_ALL)
            self.deck_obj.reset_deck()
            time.sleep(1)
            
        clear_screen()
        self.print_banner(f"ROUND {self.round_number}")
        print(Fore.BLUE + f"\nYour current capital: €{self.capital}" + Style.RESET_ALL)
        
        while True:
            try:
                bet_prompt = f"How much do you want to bet? (1-{self.capital}): "
                bet = int(input(Fore.CYAN + bet_prompt + Style.RESET_ALL))
                if bet <= 0:
                    print(Fore.RED + "❌ The bet must be a positive number." + Style.RESET_ALL)
                elif bet > self.capital:
                    print(Fore.RED + "❌ You cannot bet more than your current capital." + Style.RESET_ALL)
                else:
                    break
            except ValueError:
                print(Fore.RED + "❌ Please enter a valid number." + Style.RESET_ALL)
                
        self.capital -= bet
        
        self.deal_initial_cards()
        self.display_game_screen(bet)
        
        if self.can_split(self.player.cards):
            if self.capital >= bet:
                print(Fore.YELLOW + "\n💠 You have two cards of the same value!" + Style.RESET_ALL)
                choice = input(Fore.YELLOW + "Do you want to split? (y/n): " + Style.RESET_ALL).lower()
                
                if choice == 'y':
                    print(Fore.MAGENTA + "\n🔀 Splitting your hand!" + Style.RESET_ALL)
                    self.capital -= bet  
                    original_bet = bet
                    
                    first_hand = [self.player.cards[0]]
                    second_hand = [self.player.cards[1]]
                    
                    print(Fore.CYAN + "\n▶️ Playing your first hand..." + Style.RESET_ALL)
                    time.sleep(1)
                    self.player.cards = first_hand
                    self.deal_card_animated(self.player)
                    self.display_game_screen(original_bet)
                    outcome1 = self.play_single_hand(original_bet)
                    
                    print(Fore.CYAN + "\n▶️ Playing your second hand..." + Style.RESET_ALL)
                    time.sleep(1)
                    self.player.cards = second_hand
                    self.deal_card_animated(self.player)
                    self.display_game_screen(original_bet)
                    outcome2 = self.play_single_hand(original_bet)
                    
                    self.stats.add_split_round(outcome1, outcome2, self.capital, bet)
                    self.dashboard.update_dashboard()
                    return
            else:
                print(Fore.RED + "❌ You don't have enough capital to split." + Style.RESET_ALL)
                
        outcome = self.play_single_hand(bet)
        return outcome
        
    def display_welcome(self):
        clear_screen()
        
        welcome_art = """
        ♠️ ♥️ ♣️ ♦️ ♠️ ♥️ ♣️ ♦️ ♠️ ♥️ ♣️ ♦️ ♠️ ♥️ ♣️ ♦️
        
             🎮  MARIO'S BLACKJACK CASINO  🎮
        
                 🃏 WELCOME PLAYER 🃏
        
        ♦️ ♠️ ♥️ ♣️ ♦️ ♠️ ♥️ ♣️ ♦️ ♠️ ♥️ ♣️ ♦️ ♠️ ♥️ ♣️
        """
        
        print(Fore.MAGENTA + welcome_art + Style.RESET_ALL)
        print(Fore.CYAN + "\n" + "-" * 50 + Style.RESET_ALL)
        print(Fore.WHITE + "🎲 Try your luck with the classic card game of Blackjack!" + Style.RESET_ALL)
        print(Fore.WHITE + "🃏 Get as close to 21 as possible without going over." + Style.RESET_ALL)
        print(Fore.WHITE + "💰 Blackjack pays 3:2" + Style.RESET_ALL)
        print(Fore.WHITE + "🎯 Dealer must hit on 16 and stand on 17" + Style.RESET_ALL)
        print(Fore.CYAN + "-" * 50 + "\n" + Style.RESET_ALL)
        
        input(Fore.GREEN + "Press Enter to start playing..." + Style.RESET_ALL)
        
    def show_final_summary(self):
        clear_screen()
        
        print(Fore.CYAN + "\n╔══════════════════════════════════════════════════╗" + Style.RESET_ALL)
        print(Fore.CYAN + "║                 GAME SUMMARY                     ║" + Style.RESET_ALL)
        print(Fore.CYAN + "╚══════════════════════════════════════════════════╝" + Style.RESET_ALL)
        
        initial_capital = self.stats.capital_history[0]
        profit = self.capital - initial_capital
        profit_percentage = (profit / initial_capital) * 100 if initial_capital > 0 else 0
        
        print(f"Starting Capital: €{initial_capital}")
        print(f"Final Capital:    €{self.capital}")
        
        if profit >= 0:
            print(Fore.GREEN + f"Profit:           €{profit} (+{profit_percentage:.1f}%)" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"Loss:             €{abs(profit)} (-{abs(profit_percentage):.1f}%)" + Style.RESET_ALL)
        
        total_hands = self.stats.hands_played
        wins = self.player.wins
        blackjacks = self.player.blackjacks
        losses = self.player.losses
        ties = self.player.ties
        
        win_rate = ((wins + blackjacks) / total_hands * 100) if total_hands > 0 else 0
        
        print("\n" + Fore.CYAN + "--- STATISTICS ---" + Style.RESET_ALL)
        print(f"Hands Played:     {total_hands}")
        print(f"Rounds Played:    {self.round_number}")
        print(Fore.GREEN + f"Wins:             {wins}" + Style.RESET_ALL)
        print(Fore.MAGENTA + f"Blackjacks:       {blackjacks}" + Style.RESET_ALL)
        print(Fore.RED + f"Losses:           {losses}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"Ties:             {ties}" + Style.RESET_ALL)
        print(f"Win Rate:         {win_rate:.1f}%")
        print(f"Best Streak:      {self.player.best_streak}")
        print(f"Worst Streak:     {self.player.worst_streak}")
        
        print("\n" + Fore.MAGENTA + "Thank you for playing Mario's Blackjack!" + Style.RESET_ALL)
        
        print(Fore.BLUE + "\nYour game analytics dashboard is still open." + Style.RESET_ALL)
        print(Fore.BLUE + "Press Enter to close the game completely..." + Style.RESET_ALL)
        
    def run(self):
        self.display_welcome()
        
        while self.capital > 0:
            self.play_round()
            
            self.dashboard.update_dashboard()
            
            if self.capital <= 0:
                print(Fore.RED + "\n💸 You have no more capital. Game over!" + Style.RESET_ALL)
                time.sleep(2)
                break
                
            choice = input(Fore.YELLOW + "\nPlay another hand? (y/n): " + Style.RESET_ALL).lower()
            if choice != 'y':
                print(Fore.GREEN + "\nThanks for playing!" + Style.RESET_ALL)
                break
                
        self.show_final_summary()
        input()  
        plt.ioff()
        plt.show(block=True)  


if __name__ == "__main__":
    clear_screen()
    print(Fore.CYAN + """
    ╔══════════════════════════════════════════════════╗
    ║                                                  ║
    ║        🎮  MARIO'S BLACKJACK CASINO  🎮         ║
    ║                                                  ║
    ╚══════════════════════════════════════════════════╝
    """ + Style.RESET_ALL)
    
    while True:
        try:
            initial_capital = int(input(Fore.CYAN + "💰 Enter your initial capital (€): " + Style.RESET_ALL))
            if initial_capital <= 0:
                print(Fore.RED + "❌ Initial capital must be a positive number." + Style.RESET_ALL)
            else:
                break
        except ValueError:
            print(Fore.RED + "❌ Please enter a valid number." + Style.RESET_ALL)
    
    game = BlackjackGame(initial_capital=initial_capital)
    game.run()
