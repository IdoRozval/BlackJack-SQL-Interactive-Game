from random import *
from Tkinter import *
import sqlite3 as lite
import sys
import time
import tkMessageBox

# FUNCTIONS

def create_deck(): # creates new deck
    marks = ['H','S','C','D']
    ranks = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    deck = []
    values = dict()
    for rank in ranks:
        for mark in marks:
            deck.append((rank,mark))
            try:
                int(rank)
                values[rank+mark] = int(rank)
            except:
                if rank == 'A':
                    values[rank+mark] = 11
                else:
                    values[rank+mark] = 10               
    shuffle(deck)   
    return values, deck

        
def create_table(): # create a score board if not exists
    try:
        conn = lite.connect('BJ.db')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS games(Name TEXT PRIMARY KEY,Wins INTEGER,Loses INTEGER,Date TEXT)')
        conn.commit()
        cursor.close()
        conn.close()
    except:
        print "database wasn't found"

    
def show_hand(hand): # arrange each player's hand with symbols
    symbols = {'H':u'\u2764','C':u'\u2663','S':u'\u2660','D':u'\u2666'}
    hand_str = ''
    for rank,mark in hand:       
        hand_str = hand_str + ' ' + rank + symbols[mark].encode('utf8')
    return hand_str


def show_board(hand1,hand2): # arrange each player's hand with color
    global name
    board.insert(END,"{0}'s hand: {1} ".format(name,show_hand(hand1)))
    board.itemconfig(END, bg = 'yellow')
    board.insert(END,"Pc's hand: {0} ".format(show_hand(hand2)))
    board.itemconfig(END, bg = 'cyan')
    board.see(END)

    
def deal(deck,hand): # deal card
    card = choice(deck)
    del deck[deck.index(card)]
    hand.append(card)
    return deck, hand


def add_player(): # adds a new player to the scoreboard
    conn = lite.connect('BJ.db')
    cursor = conn.cursor()
    player = addp_ent.get()
    cursor.execute("SELECT Name,Wins,Loses,Date FROM games")
    rows = cursor.fetchall()
    conn.commit()   
    names = []
    for row in rows:
        names.append(row[0])
    if player in names: # inform if name is taken
        tkMessageBox.showinfo('Error','This name is taken, please choose another one.')
    else:
        t = time.strftime('%d/%m/%Y')
        cursor.execute('''INSERT INTO games(Name, Wins, Loses, Date)
        VALUES(?,?,?,?)''', (player,0,0,t))
        conn.commit()
        cursor.close()
        conn.close()
        show_table()

        
def load_player(): # loads existing player from the scoreboard
    global name,my_score,pc_score
    my_score = 0
    pc_score = 0
    board.delete(0,END)
    conn = lite.connect('BJ.db')
    cursor = conn.cursor()
    try:
        index = int(info_sql.curselection()[0]) - 1
        flag = True
    except IndexError:
        tkMessageBox.showinfo('Error',"Player wasn't chosen correctly, please try again.")
    if flag:
        cursor.execute('''SELECT Name, Wins, Loses, Date FROM games''')
        rows = cursor.fetchall()
        conn.commit()
        names = []
        for row in rows:
            names.append(row[0])
        lb_title['text'] = 'Welcome %s' % names[index]
        cursor.close()
        conn.close()
        addp_btn['state'] = DISABLED
        loadp_btn['state'] = DISABLED
        save_btn['state'] = NORMAL
        newg_btn['state'] = NORMAL
        name = names[index]


def value(values,t): # returns the card's value(without symbols)
    return values[t[0]+t[1]]


def aces(player_sum,player_aces): # if ace needs to exchange value(11->1), does it.
    if player_sum > 21 and player_aces != 0:
        player_sum = player_sum - 10
        player_aces = player_aces - 1
    return player_sum, player_aces


def show_table(): # shows the scoreboard
    conn = lite.connect('BJ.db')
    cursor = conn.cursor()
    info_sql.delete(0,END)
    cursor.execute('''SELECT Name, Wins, Loses, Date FROM games''')
    rows = cursor.fetchall()
    conn.commit
    info_sql.insert(END,('Name - Wins - Loses - Date'))
    for row in rows:
        info_sql.insert(END,('{0} - {1} - {2} - {3}'.format(row[0], row[1], row[2], row[3])))
    conn.commit()
    info_sql.see(END)
    cursor.close()
    conn.close()

    
def save(): # saves the current balance to the current player
    global index,name
    conn = lite.connect('BJ.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT Wins, Loses FROM games WHERE Name=?''',(name,))
    user = cursor.fetchone()
    conn.commit()
    t = time.strftime('%d/%m/%Y')
    cursor.execute('''UPDATE games SET Wins = ? ,Loses = ?, Date = ? WHERE Name = ?''',(user[0] + my_score, user[1] + pc_score, t,name))
    conn.commit()
    cursor.close()
    conn.close()
    addp_btn['state'] = NORMAL
    loadp_btn['state'] = NORMAL
    save_btn['state'] = DISABLED
    newg_btn['state'] = DISABLED
    balance['text'] = 'Balance - 0:0'
    lb_title['text'] = 'Goodbye %s' % name 
    show_table()

    
def result(x): # shows round result on gameboard and changes the balance accordingly
    global win,my_score,pc_score,name
    if x == 1:
        board.insert(END,'<<< %s wins >>>' % name)
        board.itemconfig(END, bg = 'green')
        win = True
        my_score = my_score + 1
        board.see(END)
    elif x == 2:
        board.insert(END,'<<< pc wins >>>')
        board.itemconfig(END, bg = 'red')
        win = True
        pc_score = pc_score + 1
        board.see(END)
    else:
        board.insert(END,'<<< tie >>>')
        board.itemconfig(END, bg = 'purple')
        win = True
        board.see(END)
    balance['text'] = 'Balance - %d:%d' % (my_score,pc_score)
        
    
        
def exit_game(): # if balance isnt saved, shows a warning sign
    if addp_btn['state'] == 'disabled':
        answer = tkMessageBox.askquestion('Warning','All unsaved changes will be lost, are you sure you want to quit?')
        if answer == 'yes':
            root.destroy()
        else:
            pass
    else:
        root.destroy()

        
def button_state(state1,state2,state3,state4):
    newg_btn['state'] = state1
    save_btn['state'] = state2
    hit_btn['state'] = state3
    pass_btn['state'] = state4   


def new_game(): # zeroes sums and hands, deals 2 intial cards, and shows a status message
    global deck, values, my_hand, pc_hand, my_sum, pc_sum, my_aces, pc_aces, win
    my_hand = []
    pc_hand = []
    my_sum = 0
    pc_sum = 0
    my_aces = 0
    pc_aces = 0
    win = False
    board.insert(END,'----NEW-GAME----')
    values, deck = create_deck()
    for i in range(2): # deal 2 first cards
        deck, my_hand = deal(deck,my_hand)
        if(my_hand[-1][0] == 'A'):
            my_aces = my_aces + 1   
        deck, pc_hand = deal(deck,pc_hand)
        if(pc_hand[-1][0] == 'A'):
            pc_aces = pc_aces + 1      
        my_sum = my_sum + value(values,my_hand[i])
        my_sum, my_aces = aces(my_sum,my_aces)
        pc_sum = pc_sum + value(values,pc_hand[i])
        pc_sum, pc_aces = aces(pc_sum,pc_aces)
    show_board(my_hand,pc_hand)
    if my_sum > 17:
        status['text'] = 'Ohhhhh nice hand!'
    elif my_sum < 10:
        status['text'] = 'Not so lucky this time...'
    else:
        status['text'] = 'Good luck!'
    button_state('disabled','disabled','normal','normal')

    
def hit(): 
    global deck, values, my_hand, pc_hand, my_sum, pc_sum, my_aces, pc_aces, win
    deck, my_hand = deal(deck,my_hand)
    my_sum = my_sum + value(values,my_hand[-1])
    if(my_hand[-1][0] == 'A'): 
        my_aces = my_aces + 1
    my_sum, my_aces = aces(my_sum,my_aces) # taking care of aces if needed
    if(pc_sum == 21 and my_sum == 21): 
        show_board(my_hand,pc_hand)
        result(3)
    elif(my_sum > 21):
        show_board(my_hand,pc_hand) 
        result(2)
    else: # pc turn starts here
        if((pc_sum <= my_sum and pc_sum < 17) or (pc_sum < my_sum and pc_sum >= 17) and pc_sum != 21): # pc hits
            deck, pc_hand = deal(deck,pc_hand)
            if(pc_hand[-1][0] == 'A'):
                 pc_aces = pc_aces + 1
            pc_sum = pc_sum + value(values,pc_hand[-1])
            pc_sum, pc_aces = aces(pc_sum,pc_aces)
            show_board(my_hand,pc_hand)
            if(pc_sum == 21 and my_sum == 21): # ***                
                result(3)
            elif(pc_sum > 21):               
                result(1)
        else:
            show_board(my_hand,pc_hand)
    if(win):
        button_state('normal','normal','disabled','disabled')

        
def passs():
    global deck, values, my_hand, pc_hand, my_sum, pc_sum, my_aces, pc_aces, win
    while(not win): # pc turn starts here
        if((pc_sum <= my_sum and pc_sum < 17) or (pc_sum < my_sum and pc_sum >= 17) and pc_sum != 21): # pc hits
            deck, pc_hand = deal(deck,pc_hand)
            if(pc_hand[-1][0] == 'A'):
                pc_aces = pc_aces + 1
            pc_sum = pc_sum + value(values,pc_hand[-1])
            pc_sum, pc_aces = aces(pc_sum,pc_aces)
            if(pc_sum == 21 and my_sum == 21):
                show_board(my_hand,pc_hand)
                result(3)
            elif(pc_sum > 21):
                show_board(my_hand,pc_hand) 
                result(1)               
        elif(pc_sum == my_sum):
            show_board(my_hand,pc_hand) 
            result(3)             
        else:
            show_board(my_hand,pc_hand) 
            result(2)                
    button_state('normal','normal','disabled','disabled')



#MAIN


name = ''
deck = []
values = dict()
my_hand = []
pc_hand = []
my_sum = 0
pc_sum = 0
my_aces = 0
pc_aces = 0
win = False
my_score = 0
pc_score = 0



root = Tk()
root.title('BlackJack')
bg_color = "#%02x%02x%02x" % (50, 192, 240) 
root["background"] = bg_color
fnt = ("Arial", 16)


create_table() # creates scoreboard(if needed)



lb_title = Label(root, text = "Rozval's BlackJack",bg = bg_color, font=fnt)
lb_title.grid(row = 0, column = 0,columnspan = 2)

scrbr_sql = Scrollbar(root)
info_sql = Listbox(root,width = 35,height = 12,yscrollcommand = scrbr_sql.set,font = fnt)
scrbr_sql.config(command = info_sql.yview)
scrbr_sql.grid(row = 1,column = 4, sticky = W + N + S)
info_sql.grid(row = 1, column = 0,columnspan = 4,sticky = W + E + S + N,padx = (10,0))

show_table() # show scoreboard

status = Label(root, text = 'lets start!',bg = bg_color, font=fnt)
status.grid(row = 0, column = 7,columnspan = 2)


scrbr_board = Scrollbar(root)
board = Listbox(root,width = 40,height = 12,yscrollcommand = scrbr_board.set,font = fnt)
scrbr_board.config(command = board.yview)
scrbr_board.grid(row = 1,column = 9, sticky = N + S + W,padx = (0,10))
board.grid(row = 1, column = 5,columnspan = 4,sticky = E + W + S + N,padx = (10,0))

nm_welcome = Label(root, text = 'Game board',bg = bg_color, font=fnt)
nm_welcome.grid(row = 0, column = 5,columnspan = 2)

hit_btn = Button(root,text = 'Hit!',width = 8,state = DISABLED,command = hit)
hit_btn.grid(row = 2,column = 5,sticky = W+E,padx = (10,0),pady = (0,5))

pass_btn = Button(root,text = 'Pass',width = 8,state = DISABLED,command = passs)
pass_btn.grid(row = 2,column = 6,sticky = W+E,pady = (0,5))

save_btn = Button(root,text = 'Save',width = 8,state = DISABLED,command = save)
save_btn.grid(row = 2,column = 7,sticky = W+E,pady = (0,5))

newg_btn = Button(root,text = 'New Game',width = 8, command = new_game,state = DISABLED)
newg_btn.grid(row = 2,column = 8,columnspan = 2,sticky = W+E,pady = (0,5),padx = (0,10))

exit_btn = Button(root,text = 'Exit',width = 8,command = exit_game)
exit_btn.grid(row = 2,column = 3,columnspan = 2,sticky = W+E,pady = (0,5))

addp_btn = Button(root,text = 'Add player',width = 8,command = add_player)
addp_btn.grid(row = 2,column = 0,sticky = W+E,pady = (0,5),padx = (10,0))

addp_ent = Entry(root,width = 5)
addp_ent.grid(row = 2, column = 1,sticky = W+E,padx = (10,10),pady = (0,5))

loadp_btn = Button(root,text = 'Load player',width = 9,command = load_player)
loadp_btn.grid(row = 2,column = 2,sticky = W+E,pady = (0,5))

balance = Label(root,text = 'Balance - 0:0',bg = bg_color, font = fnt)
balance.grid(row = 0,column = 2,columnspan = 2)


root.mainloop()



       
        

