from cryptography.fernet import Fernet
# Mini Password Manager (Python)

This is a simple password manager built in Python that allows you to **add**, **view**, and **update** passwords securely using **Fernet encryption** from the `cryptography` library.

## Features
- Store usernames and encrypted passwords in a text file.
- Encrypts passwords so that even if the file is accessed, passwords remain secure.
- Supports adding new credentials, viewing existing ones, and updating passwords.
- Easy to use in the terminal.

## How it works
1. A symmetric key (`key.key`) is used for encryption/decryption.
2. User passwords are encrypted before storing in `passwords.txt`.
3. When viewing or updating, passwords are decrypted on the fly.
4. Each username:password pair is stored in the format:

# Mini Password Manager (Python)

This is a simple password manager built in Python that allows you to **add**, **view**, and **update** passwords securely using **Fernet encryption** from the `cryptography` library.

## Features
- Store usernames and encrypted passwords in a text file.
- Encrypts passwords so that even if the file is accessed, passwords remain secure.
- Supports adding new credentials, viewing existing ones, and updating passwords.
- Easy to use in the terminal.

## How it works
1. A symmetric key (`key.key`) is used for encryption/decryption.
2. User passwords are encrypted before storing in `passwords.txt`.
3. When viewing or updating, passwords are decrypted on the fly.
4. Each username:password pair is stored in the format:


"""def write_key():
    key=Fernet.generate_key()
    with open("key.key","wb") as key_file:     #wb-write bytes
        key_file.write(key)"""

def load_key():
    file=open("key.key","rb")
    key=file.read()
    file.close()
    return key

key=load_key()
fer=Fernet(key)

def view_password():
    with open("passwords.txt",'r') as f:
        for line in f.readlines():
            data=line.rstrip()
            user,passw=data.split(" : ")
            print("Username: "+user+" , Password: "+fer.decrypt(passw.encode()).decode())

def add_password():
    username=input("enter username: ")
    password=input("enter password: ")

    with open("passwords.txt",'a') as f:               #mode 'a'-appends  'w'-write    'r'-read
        f.write(username+" : "+ fer.encrypt(password.encode()).decode()+"\n")

def update_password():
    req_username=input("enter the username to be updated ")

    with open("passwords.txt","r") as f:
        lines=f.readlines()
    
    updated=False
    new_lines=[]

    for line in lines:
        user,passw=line.rstrip().split(" : ")
        if req_username==user:
            new_password=input("enter new password: ")
            new_lines.append(f"{user} : {fer.encrypt(new_password.encode()).decode()}\n")
            updated=True
        else:
            new_lines.append(line)

    with open("passwords.txt","w") as f:
        f.writelines(new_lines)

    if(updated):
        print("password updated successfully")
    else:
        print("username not found")


while True:
    mode=input("Would you like to add a new password , view on existing one , or update an old one?  (enter add/view/update/quit) ").lower();
    
    if(mode=="quit"):
        break
    elif(mode=="view"):
        view_password()
    elif(mode=="add"):
        add_password()

    elif(mode=="update"):
        update_password()