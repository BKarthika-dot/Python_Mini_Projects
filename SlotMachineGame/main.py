import random

MAX_LINES=3
MIN_BET=25
MAX_BET=500

ROWS=3
COLS=3

symbol_count={    #no of symbols each reel will have
    "A":2,
    "B":4,
    "C":6,
    "D":8
}

symbol_values={  #the value associated with each symbol
    "A":10,
    "B":8,
    "C":6,
    "D":4
}

def check_winnings(columns,lines,bet,values):
    winnings=0
    winning_lines=[]
    for line in range(lines):
        symbol=columns[0][line]
        for column in columns:
            symbol_to_check=column[line]
            if symbol!=symbol_to_check:
                break
        else:
            winnings+= values[symbol]*bet
            winning_lines.append(line+1)
    return winnings,winning_lines


def get_slot_machine_spin(rows,cols,symbols):
    all_symbols=[]    #creating a list
    for symbol,symbol_count in symbols.items():        #symbol is the key, symbol_count is the value;    the symbols.items() fn gets both key and value
        for i in range(symbol_count):
            all_symbols.append(symbol)

    columns=[]   #this list contains a list of symbols for each column

    #we're gonna generate the values for each column

    for col in range(cols):      
        column=[]              #if there are 3 columns we run the loop 3 times to get the "column" list then we append those lists to the "columns"
        current_symbols=all_symbols[:]      #creating a copy of the original list
        for row in range(rows):
            value=random.choice(current_symbols)
            current_symbols.remove(value)          #once a value is chosen it's removed from the list. (if we choose one 'A' from the two A's then for the next selection only one A should be available)
            column.append(value)  #append the chosen value to the list

        columns.append(column)

    return columns   #function returns the columns list


#for printing we need to transpose the given columns list to get it in the format we see in slot machines

def print_slot_machine(columns):
    for  row in range(len(columns[0])):
        for i,column in enumerate(columns):
            if i!=len(columns)-1:
                print(column[row],end=" | ")
            else:
                print(column[row],end="\n")


def deposit():
    while True:
        amount=input("How much would you like to deposit? $")

        if amount.isdigit():
            amount=int(amount)
            if amount>0:
                break
            else:
                print("Amount must be greater than 0.")
        else:
            print("Please enter a number.")
    
    return amount

def get_no_of_lines():
    while True:
        lines=input("Enter the no of lines you want to bet on (1-" + str(MAX_LINES) + ")? ")

        if lines.isdigit():
            lines=int(lines)
            if 1<=lines<=MAX_LINES:
                break
            else:
                print("Value must be between 1 and "+ str(MAX_LINES) + ".")
        else:
            print("Please enter a number.")
    
    return lines

def get_bet():
    while True:
        amount=input("How much would you like to bet? $")

        if amount.isdigit():
            amount=int(amount)
            if MIN_BET<=amount<=MAX_BET:
                break
            else:
                print(f"Amount must in the given range ${MIN_BET} - ${MAX_BET}.")
        else:
            print("Please enter a number.")
    
    return amount

def game(balance):

    while True:
        betAmount=get_bet()
        lines=get_no_of_lines()
        total_bet=betAmount*lines

        if total_bet>balance:
            print(f"You don't have enough balance to bet that amount,your current balance is ${balance}.")
        else:
            break
    print(f"You are betting ${betAmount} on {lines} lines. Total bet is ${total_bet}.")

    slots=get_slot_machine_spin(ROWS,COLS,symbol_count)
    print_slot_machine(slots)
    winnings,winning_lines=check_winnings(slots,lines,betAmount,symbol_values)
    print(f"You've won ${winnings}.")
    print(f"You've won on lines: ",*winning_lines)

    return winnings-total_bet 

def main():
    balance=deposit()

    while True:
        print(f"Current balance is ${balance}")
        spin=input("Press enter to play (q to quit).")

        if spin=="q":
            break
        balance+=game(balance)
    print(f"You have ${balance} in your balance")

main()

