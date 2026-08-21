🎰 Python Slot Machine Game

A simple yet fully functional command-line Slot Machine game built in Python.
This project demonstrates core programming concepts such as loops, functions, user input validation, lists, dictionary usage, and randomization.


🚀 Features

Deposit & balance tracking

Betting system with min/max limits

Play up to 3 lines

Randomized slot machine spins using weighted symbol distribution

Automatic win checking

Displays winning lines and amount won

Clean, readable code following procedural style

🧠 How It Works
🎲 Slot Generation

Each symbol (A, B, C, D) has a specific count, affecting how frequently it appears.
Symbols are randomly chosen for each column without replacement, ensuring realistic slot behavior.

💰 Betting Rules

You can bet on 1 to 3 lines.

Bet per line must be between $25 and $500.

Total bet = bet per line × number of lines.

🏆 Winning Logic

You win if all symbols on a line match across all columns.

Each symbol has a different payout value:

A → 10× bet

B → 8× bet

C → 6× bet

D → 4× bet

The program calculates total winnings and updates your balance automatically.

