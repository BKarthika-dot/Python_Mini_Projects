"""
🪨📄✂️ Rock, Paper, Scissors Game

A simple Python project to practice conditionals, loops, and functions.
The player competes against the computer — first to reach 3 points wins.
Includes tie handling, input validation, and replay support.
"""



import random

print("🪨📄✂️  Welcome to Rock, Paper, Scissors!")
print("First to reach 3 points wins!\n")

def wins(a,b,a_count,b_count):
    
    if(a==b):
        print("Its a tie!")
        return a_count,b_count
    elif(a == "rock" and b == "scissor") or (a == "paper" and b == "rock") or (a == "scissor" and b == "paper"):
        a_count+=1
        print(f"You win this round {a} beats {b}")
    else:
        b_count+=1
        print(f"Computer wins this round {b} beats {a}")
    
    return a_count, b_count


def rock_paper_scissor():
    user_wins=0
    computer_wins=0
    values=["rock","paper","scissor"]

    while user_wins<3 and computer_wins<3:

        user_input=input("enter rock/paper/scissor ").lower()
        computer_input=random.choice(values)

        if user_input in values:
            user_wins,computer_wins=wins(user_input,computer_input,user_wins,computer_wins)
        else:
            return
    
    if user_wins==3:
        print("🎉 You won the game! Congratulations!")
        return
    else:
        print("💻 Computer wins! Better luck next time.")
        return

while True:
    rock_paper_scissor()
    again=input("Do you want to play again? (yes/no)").lower()
    if(again!="yes"):
        print("Thanks for playing!")
        break
