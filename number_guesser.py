"""
🎯 Number Guessing Game

A simple Python project to practice basic input handling, loops, conditionals, and functions.
The player picks a range, then keeps guessing until they find the random number — with hints after each try.
Includes replay support to start fresh with a new range.
"""


import random

print("🎯 Welcome to the Number Guessing Game!")
print()

def play_game():

    max=int(input("enter maximum possible number: "))
    min=int(input("enter minimum possible number: "))

    if(min>max):
        print("Minimum can’t be greater than maximum!")
        return #exit the function 

    random_num=random.randrange(min,max+1)

    guesses=1

    while True:
        num=int(input("enter any number in the given range: "))
        if(num<min or num>max):
            print("enter number within given range")
            guesses+=1

        elif(num==random_num):
            print(f"Correct! The number is {num}")
            print(f"You got it in {guesses} attempts!")
            print()
            break

        elif num < random_num:
            print("Too low! Guess again.")
            guesses+=1

        else:
            print("Too high! Guess again.")
            guesses+=1
            

while True:
    play_game()
    again=input(("Do you want to play again? (yes/no) "))
    if(again.lower()!="yes"):
        print("Thanks for playing!");
        break
            
