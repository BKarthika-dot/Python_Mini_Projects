"""
🎯 Simple Python Quiz Game

A fun mini project to practice Python basics — print statements, input, if-else logic, and variables.
Made just to get familiar with Python and have a few laughs along the way 😄
"""


print("Welcome to my quiz! Don’t worry, it’s only designed to expose what you don’t know.")
print()
playing=input("Would you like to play? Warning: side effects include confusion and regret. ")

if playing.lower() != "yes":
    quit()

print("Alright then, let’s play — confidence looks good on you… let’s see how long it lasts.")
print()

ans1=input("What is the only food that never spoils?")
points=0
if ans1.lower() == "honey":
    print("Correct! Look at you, using that big brain!")
    points+=1
else:
    print("Oof… that’s a big nope.")
print()

ans2=input("What’s the closest living relative of the T-Rex?")
if ans2.lower()=="chicken":
    print("You actually got it right? I’m as shocked as you are.")
    points+=1
else:
    print("Wrong! But hey, confidence counts for something… right?")
print()

ans3=input("Which planet decided to spin the wrong way, just to be different?")
if ans3.lower()=="venus":
    print("Nice! You’re on fire — in a good way this time.")
    points+=1
else:
    print("Nope! But points for enthusiasm.")
print()


ans4=input("How many hearts does an octopus have?")
if ans4.lower()=="three" or ans4=="3":
    print("Right answer! Did you bribe Google again?")
    points+=1
else:
    print("Ehh… not quite. Try again before I start judging harder.")
print()

ans5=input("What was the first feature-length animated movie ever released?")
if ans5.lower()=="Snow White and the Seven Dwarfs":
    print("You got it! I’m proud… and slightly suspicious.")
    points+=1
else:
    print("That’s wrong — but don’t worry, I won’t tell anyone (except everyone).")
print()


if points == 5:
    print(f"🎉 {points}/5! Perfect score! Are you secretly Google or what?")
elif points == 4:
    print(f"👏 {points}/5! Almost perfect — your brain’s clearly in beta testing.")
elif points == 3:
    print(f"😏 {points}/5! Not bad… but let’s be honest, you guessed at least once.")
elif points == 2:
    print(f"🤔 {points}/5! You tried. Participation trophy unlocked!")
elif points == 1:
    print(f"😬 {points}/5! Well… at least you pressed the right keys.")
else:
    print(f"💀 {points}/5! Congratulations, you discovered all the wrong answers.")


