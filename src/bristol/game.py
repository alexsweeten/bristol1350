import argparse
from colorama import Fore, Style
import math
import random
import sys
import time
import twilio
from bristol.send_sms import (
    send_message,
    send_mingle_message,
    send_remedy_message,
    send_used_remedy_message,
)
import tkinter as tk
import yaml
import os
import toml

# Tkinter GUI
class BristolGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Bristol 1350")
        self.canvas = tk.Canvas(self.master, width=800, height=600, bg="lightgray")
        self.canvas.pack()

        self.rectangle1 = self.canvas.create_rectangle(50, 50, 250, 150, fill="cyan")
        self.text_in_rectangle1 = self.canvas.create_text(
            100, 100, text="Lorem Ipsum", font=("Arial", 14, "bold"), fill="black"
        )
        self.rectangle2 = self.canvas.create_rectangle(50, 200, 250, 300, fill="yellow")
        self.text_in_rectangle2 = self.canvas.create_text(
            100, 250, text="Lorem Ipsum", font=("Arial", 14, "bold"), fill="black"
        )
        self.rectangle3 = self.canvas.create_rectangle(50, 350, 250, 450, fill="pink")
        self.text_in_rectangle3 = self.canvas.create_text(
            100, 400, text="Lorem Ipsum", font=("Arial", 14, "bold"), fill="black"
        )

        self.finishline = self.canvas.create_rectangle(700, 0, 720, 600, fill="red")

        self.dice1 = self.canvas.create_rectangle(100,500,140,540, fill="cyan", outline="black")
        self.dice2 = self.canvas.create_rectangle(160,500,200,540, fill="yellow", outline="black")
        self.dice3 = self.canvas.create_rectangle(220,500,260,540, fill="cyan", outline="black")
        self.dice4 = self.canvas.create_rectangle(280,500,320,540, fill="cyan", outline="black")
        self.dice5 = self.canvas.create_rectangle(340,500,380,540, fill="pink", outline="black")
        self.dice6 = self.canvas.create_rectangle(400,500,440,540, fill="cyan", outline="black")
        self.dice1txt = self.canvas.create_text(
            120, 520, text="🍏", font=("Arial", 18, "bold"), fill="black"
        )
        self.dice2txt = self.canvas.create_text(
            180, 520, text="🍏", font=("Arial", 18, "bold"), fill="black"
        )
        self.dice3txt = self.canvas.create_text(
            240, 520, text="🐀", font=("Arial", 18, "bold"), fill="black"
        )
        self.dice4txt = self.canvas.create_text(
            300, 520, text="🐀", font=("Arial", 18, "bold"), fill="black"
        )
        self.dice5txt = self.canvas.create_text(
            360, 520, text="🍏", font=("Arial", 18, "bold"), fill="black"
        )
        self.dice6txt = self.canvas.create_text(
            420, 520, text="🐀", font=("Arial", 18, "bold"), fill="black"
        )
        self.dice1locktxt = self.canvas.create_text(
            120, 570, text="✅", font=("Arial", 12, "bold"), fill="black"
        )
        self.dice2locktxt = self.canvas.create_text(
            180, 570, text="✅", font=("Arial", 12, "bold"), fill="black"
        )
        self.dice3locktxt = self.canvas.create_text(
            240, 570, text="✅", font=("Arial", 12, "bold"), fill="black"
        )
        self.dice4locktxt = self.canvas.create_text(
            300, 570, text="✅", font=("Arial", 12, "bold"), fill="black"
        )
        self.dice5locktxt = self.canvas.create_text(
            360, 570, text="✅", font=("Arial", 12, "bold"), fill="black"
        )
        self.dice6locktxt = self.canvas.create_text(
            420, 570, text="✅", font=("Arial", 12, "bold"), fill="black"
        )

    def update_rectangle_position(self, rectangle, amount):
        if rectangle == 1:
            self.canvas.coords(
                self.rectangle1, 50 + (amount * 25), 50, 250 + (amount * 25), 150
            )
            self.canvas.coords(self.text_in_rectangle1, 100 + (amount * 25), 100)
        elif rectangle == 2:
            self.canvas.coords(
                self.rectangle2, 50 + (amount * 25), 200, 250 + (amount * 25), 300
            )
            self.canvas.coords(self.text_in_rectangle2, 100 + (amount * 25), 250)
        elif rectangle == 3:
            self.canvas.coords(
                self.rectangle3, 50 + (amount * 25), 350, 250 + (amount * 25), 450
            )
            self.canvas.coords(self.text_in_rectangle3, 100 + (amount * 25), 400)

    def update_rectangle_txt(self, rectangle, txt):
        if rectangle == 1:
            self.canvas.itemconfig(self.text_in_rectangle1, text=txt)
        elif rectangle == 2:
            self.canvas.itemconfig(self.text_in_rectangle2, text=txt)
        elif rectangle == 3:
            self.canvas.itemconfig(self.text_in_rectangle3, text=txt)

    def update_finish_line(self, amount):
        self.canvas.coords(
            self.finishline, 220 + (amount * 25), 0, 240 + (amount * 25), 600
        )

    def update_lock_symbol(self,die_num, lock, busy):
        if die_num == 1:
            if lock:
                self.canvas.itemconfig(self.dice1locktxt, text="❌")
            elif busy:
                self.canvas.itemconfig(self.dice1locktxt, text="🔄")
            else:
                self.canvas.itemconfig(self.dice1locktxt, text="✅")
        if die_num == 2:
            if lock:
                self.canvas.itemconfig(self.dice2locktxt, text="❌")
            elif busy:
                self.canvas.itemconfig(self.dice2locktxt, text="🔄")
            else:
                self.canvas.itemconfig(self.dice2locktxt, text="✅")
        if die_num == 3:
            if lock:
                self.canvas.itemconfig(self.dice3locktxt, text="❌")
            elif busy:
                self.canvas.itemconfig(self.dice3locktxt, text="🔄")
            else:
                self.canvas.itemconfig(self.dice3locktxt, text="✅")
        if die_num == 4:
            if lock:
                self.canvas.itemconfig(self.dice4locktxt, text="❌")
            elif busy:
                self.canvas.itemconfig(self.dice4locktxt, text="🔄")
            else:
                self.canvas.itemconfig(self.dice4locktxt, text="✅")
        if die_num == 5:
            if lock:
                self.canvas.itemconfig(self.dice5locktxt, text="❌")
            elif busy:
                self.canvas.itemconfig(self.dice5locktxt, text="🔄")
            else:
                self.canvas.itemconfig(self.dice5locktxt, text="✅")
        if die_num == 6:
            if lock:
                self.canvas.itemconfig(self.dice6locktxt, text="❌")
            elif busy:
                self.canvas.itemconfig(self.dice6locktxt, text="🔄")
            else:
                self.canvas.itemconfig(self.dice6locktxt, text="✅")

    def update_dice_value(self,status,die_num):
        if die_num == 1:
            if status == 1:
                self.canvas.itemconfig(self.dice1txt, text="🍏")
                self.canvas.itemconfig(self.dice1, fill="cyan")
            elif status == 2:
                self.canvas.itemconfig(self.dice1txt, text="🐀")
                self.canvas.itemconfig(self.dice1, fill="cyan")
            elif status == 3:
                self.canvas.itemconfig(self.dice1txt, text="🍏")
                self.canvas.itemconfig(self.dice1, fill="yellow")
            elif status == 4:
                self.canvas.itemconfig(self.dice1txt, text="🐀")
                self.canvas.itemconfig(self.dice1, fill="yellow")
            elif status == 5:
                self.canvas.itemconfig(self.dice1txt, text="🍏")
                self.canvas.itemconfig(self.dice1, fill="pink")
            elif status == 6:
                self.canvas.itemconfig(self.dice1txt, text="🐀")
                self.canvas.itemconfig(self.dice1, fill="pink")

        elif die_num == 2:
            if status == 1:
                self.canvas.itemconfig(self.dice2txt, text="🍏")
                self.canvas.itemconfig(self.dice2, fill="cyan")
            elif status == 2:
                self.canvas.itemconfig(self.dice2txt, text="🐀")
                self.canvas.itemconfig(self.dice2, fill="cyan")
            elif status == 3:
                self.canvas.itemconfig(self.dice2txt, text="🍏")
                self.canvas.itemconfig(self.dice2, fill="yellow")
            elif status == 4:
                self.canvas.itemconfig(self.dice2txt, text="🐀")
                self.canvas.itemconfig(self.dice2, fill="yellow")
            elif status == 5:
                self.canvas.itemconfig(self.dice2txt, text="🍏")
                self.canvas.itemconfig(self.dice2, fill="pink")
            elif status == 6:
                self.canvas.itemconfig(self.dice2txt, text="🐀")
                self.canvas.itemconfig(self.dice2, fill="pink")

        elif die_num == 3:
            if status == 1:
                self.canvas.itemconfig(self.dice3txt, text="🍏")
                self.canvas.itemconfig(self.dice3, fill="cyan")
            elif status == 2:
                self.canvas.itemconfig(self.dice3txt, text="🐀")
                self.canvas.itemconfig(self.dice3, fill="cyan")
            elif status == 3:
                self.canvas.itemconfig(self.dice3txt, text="🍏")
                self.canvas.itemconfig(self.dice3, fill="yellow")
            elif status == 4:
                self.canvas.itemconfig(self.dice3txt, text="🐀")
                self.canvas.itemconfig(self.dice3, fill="yellow")
            elif status == 5:
                self.canvas.itemconfig(self.dice3txt, text="🍏")
                self.canvas.itemconfig(self.dice3, fill="pink")
            elif status == 6:
                self.canvas.itemconfig(self.dice3txt, text="🐀")
                self.canvas.itemconfig(self.dice3, fill="pink")

        elif die_num == 4:
            if status == 1:
                self.canvas.itemconfig(self.dice4txt, text="🍏")
                self.canvas.itemconfig(self.dice4, fill="cyan")
            elif status == 2:
                self.canvas.itemconfig(self.dice4txt, text="🐀")
                self.canvas.itemconfig(self.dice4, fill="cyan")
            elif status == 3:
                self.canvas.itemconfig(self.dice4txt, text="🍏")
                self.canvas.itemconfig(self.dice4, fill="yellow")
            elif status == 4:
                self.canvas.itemconfig(self.dice4txt, text="🐀")
                self.canvas.itemconfig(self.dice4, fill="yellow")
            elif status == 5:
                self.canvas.itemconfig(self.dice4txt, text="🍏")
                self.canvas.itemconfig(self.dice4, fill="pink")
            elif status == 6:
                self.canvas.itemconfig(self.dice4txt, text="🐀")
                self.canvas.itemconfig(self.dice4, fill="pink")

        elif die_num == 5:
            if status == 1:
                self.canvas.itemconfig(self.dice5txt, text="🍏")
                self.canvas.itemconfig(self.dice5, fill="cyan")
            elif status == 2:
                self.canvas.itemconfig(self.dice5txt, text="🐀")
                self.canvas.itemconfig(self.dice5, fill="cyan")
            elif status == 3:
                self.canvas.itemconfig(self.dice5txt, text="🍏")
                self.canvas.itemconfig(self.dice5, fill="yellow")
            elif status == 4:
                self.canvas.itemconfig(self.dice5txt, text="🐀")
                self.canvas.itemconfig(self.dice5, fill="yellow")
            elif status == 5:
                self.canvas.itemconfig(self.dice5txt, text="🍏")
                self.canvas.itemconfig(self.dice5, fill="pink")
            elif status == 6:
                self.canvas.itemconfig(self.dice5txt, text="🐀")
                self.canvas.itemconfig(self.dice5, fill="pink")

        elif die_num == 6:
            if status == 1:
                self.canvas.itemconfig(self.dice6txt, text="🍏")
                self.canvas.itemconfig(self.dice6, fill="cyan")
            elif status == 2:
                self.canvas.itemconfig(self.dice6txt, text="🐀")
                self.canvas.itemconfig(self.dice6, fill="cyan")
            elif status == 3:
                self.canvas.itemconfig(self.dice6txt, text="🍏")
                self.canvas.itemconfig(self.dice6, fill="yellow")
            elif status == 4:
                self.canvas.itemconfig(self.dice6txt, text="🐀")
                self.canvas.itemconfig(self.dice6, fill="yellow")
            elif status == 5:
                self.canvas.itemconfig(self.dice6txt, text="🍏")
                self.canvas.itemconfig(self.dice6, fill="pink")
            elif status == 6:
                self.canvas.itemconfig(self.dice6txt, text="🐀")
                self.canvas.itemconfig(self.dice6, fill="pink")

# Colors for dramatic CLI effects
class bcolors:
    # STATUS COLORS
    GREEN = "\033[92m"  # GREEN
    RED = "\033[91m"  # RED
    # CART COLORS
    BLUE = "\033[33m"  # OK
    YELLOW = "\033[34m"  # WARNING
    MAGENTA = "\033[35m"  # FAIL
    # RESET COLOR
    RESET = "\033[0m"

# Dice class
class Dice:
    def __init__(self):
        self.dice1 = random.randint(1, 6)
        self.dice2 = random.randint(1, 6)
        self.dice3 = random.randint(1, 6)
        self.dice4 = random.randint(1, 6)
        self.dice5 = random.randint(1, 6)
        self.dice6 = random.randint(1, 6)

        self.dice1_result = "Cart 1 Apple"
        self.dice2_result = "Cart 1 Apple"
        self.dice3_result = "Cart 1 Apple"
        self.dice4_result = "Cart 1 Apple"
        self.dice5_result = "Cart 1 Apple"
        self.dice6_result = "Cart 1 Apple"

        self.dice1_lock = False
        self.dice2_lock = False
        self.dice3_lock = False
        self.dice4_lock = False
        self.dice5_lock = False
        self.dice6_lock = False

    def moveCart(self, cart, board):
        list_of_results = [
            self.dice1,
            self.dice2,
            self.dice3,
            self.dice4,
            self.dice5,
            self.dice6,
        ]
        if cart == 1:
            total = list_of_results.count(1) + list_of_results.count(2)
            print(Fore.CYAN + Style.BRIGHT)
            if total == 0:
                print(f"Looks like the blue cart isn't moving this round :(")
            elif total > 0 and total < 5:
                print(f"Blue cart is moving {total} spaces this round.")
            elif total >= 5:
                print(
                    f"Blue cart is zooming outta here with {total} spaces this round!!"
                )
            board.cart1_position = board.cart1_position + total
            print(bcolors.RESET)
        elif cart == 2:
            total = list_of_results.count(3) + list_of_results.count(4)
            print(Fore.YELLOW + Style.BRIGHT)
            if total == 0:
                print(f"Looks like the yellow cart isn't moving this round :(")
            elif total > 0 and total < 5:
                print(f"Yellow cart is moving {total} spaces this round.")
            elif total >= 5:
                print(
                    f"Yellow cart is zooming outta here with {total} spaces this round!!"
                )
            board.cart2_position = board.cart2_position + total
            print(bcolors.RESET)
        elif cart == 3:
            total = list_of_results.count(5) + list_of_results.count(6)
            print(Fore.MAGENTA + Style.BRIGHT)
            if total == 0:
                print(f"Looks like the purple cart isn't moving this round :(")
            elif total > 0 and total < 5:
                print(f"Purple cart is moving {total} spaces this round.")
            elif total >= 5:
                print(
                    f"Purple cart is zooming outta here with {total} spaces this round!!"
                )
            board.cart3_position = board.cart3_position + total
            print(bcolors.RESET)

    def checkMingling(self):
        print("\n------------")
        print("Mingle Phase")
        print("------------")
        carts_mingling = []
        list_of_results = [
            self.dice1,
            self.dice2,
            self.dice3,
            self.dice4,
            self.dice5,
            self.dice6,
        ]
        if list_of_results.count(2) >= 2:
            print(
                Fore.CYAN
                + Style.BRIGHT
                + "Uh oh! Blue cart is mingling!!"
                + bcolors.RESET
            )
            carts_mingling.append(1)
        if list_of_results.count(4) >= 2:
            print(
                Fore.YELLOW
                + Style.BRIGHT
                + "Uh oh! Yellow cart is mingling!!"
                + bcolors.RESET
            )
            carts_mingling.append(2)
        if list_of_results.count(6) >= 2:
            print(
                Fore.MAGENTA
                + Style.BRIGHT
                + "Uh oh! Purple cart is mingling!!"
                + bcolors.RESET
            )
            carts_mingling.append(3)

        return carts_mingling

    def updateResults(self):
        if self.dice1 == 1:
            self.dice1_result = Fore.CYAN + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice1 == 2:
            self.dice1_result = Fore.CYAN + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice1 == 3:
            self.dice1_result = Fore.YELLOW + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice1 == 4:
            self.dice1_result = Fore.YELLOW + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice1 == 5:
            self.dice1_result = Fore.MAGENTA + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice1 == 6:
            self.dice1_result = Fore.MAGENTA + Style.BRIGHT + "Rat" + bcolors.RESET

        if self.dice2 == 1:
            self.dice2_result = Fore.CYAN + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice2 == 2:
            self.dice2_result = Fore.CYAN + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice2 == 3:
            self.dice2_result = Fore.YELLOW + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice2 == 4:
            self.dice2_result = Fore.YELLOW + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice2 == 5:
            self.dice2_result = Fore.MAGENTA + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice2 == 6:
            self.dice2_result = Fore.MAGENTA + Style.BRIGHT + "Rat" + bcolors.RESET

        if self.dice3 == 1:
            self.dice3_result = Fore.CYAN + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice3 == 2:
            self.dice3_result = Fore.CYAN + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice3 == 3:
            self.dice3_result = Fore.YELLOW + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice3 == 4:
            self.dice3_result = Fore.YELLOW + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice3 == 5:
            self.dice3_result = Fore.MAGENTA + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice3 == 6:
            self.dice3_result = Fore.MAGENTA + Style.BRIGHT + "Rat" + bcolors.RESET

        if self.dice4 == 1:
            self.dice4_result = Fore.CYAN + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice4 == 2:
            self.dice4_result = Fore.CYAN + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice4 == 3:
            self.dice4_result = Fore.YELLOW + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice4 == 4:
            self.dice4_result = Fore.YELLOW + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice4 == 5:
            self.dice4_result = Fore.MAGENTA + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice4 == 6:
            self.dice4_result = Fore.MAGENTA + Style.BRIGHT + "Rat" + bcolors.RESET

        if self.dice5 == 1:
            self.dice5_result = Fore.CYAN + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice5 == 2:
            self.dice5_result = Fore.CYAN + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice5 == 3:
            self.dice5_result = Fore.YELLOW + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice5 == 4:
            self.dice5_result = Fore.YELLOW + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice5 == 5:
            self.dice5_result = Fore.MAGENTA + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice5 == 6:
            self.dice5_result = Fore.MAGENTA + Style.BRIGHT + "Rat" + bcolors.RESET

        if self.dice6 == 1:
            self.dice6_result = Fore.CYAN + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice6 == 2:
            self.dice6_result = Fore.CYAN + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice6 == 3:
            self.dice6_result = Fore.YELLOW + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice6 == 4:
            self.dice6_result = Fore.YELLOW + Style.BRIGHT + "Rat" + bcolors.RESET
        elif self.dice6 == 5:
            self.dice6_result = Fore.MAGENTA + Style.BRIGHT + "Apple" + bcolors.RESET
        elif self.dice6 == 6:
            self.dice6_result = Fore.MAGENTA + Style.BRIGHT + "Rat" + bcolors.RESET

    def refreshLocks(self):
        self.dice1_lock = False
        self.dice2_lock = False
        self.dice3_lock = False
        self.dice4_lock = False
        self.dice5_lock = False
        self.dice6_lock = False

    def setdie(self, die_num, die_val):
        if die_num == 1:
            self.dice1 = die_val
            self.updateResults()
        elif die_num == 2:
            self.dice2 = die_val
            self.updateResults()
        elif die_num == 3:
            self.dice3 = die_val
            self.updateResults()
        elif die_num == 4:
            self.dice4 = die_val
            self.updateResults()
        elif die_num == 5:
            self.dice5 = die_val
            self.updateResults()
        elif die_num == 6:
            self.dice6 = die_val
            self.updateResults()

    def reroll(self, index1, index2):
        tmp = False
        to_return = []
        while tmp == False:
            if index1 == index2:
                print("Select two different dice")
            else:
                tmp = True
        if index1 == 1:
            tmp3 = self.dice1_result
            self.dice1 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice1)
            print(f"\n{tmp3} -> {self.dice1_result}\n")
        elif index1 == 2:
            tmp3 = self.dice2_result
            self.dice2 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice2)
            print(f"\n{tmp3} -> {self.dice2_result}\n")
        elif index1 == 3:
            tmp3 = self.dice3_result
            self.dice3 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice3)
            print(f"\n{tmp3} -> {self.dice3_result}\n")
        elif index1 == 4:
            tmp3 = self.dice4_result
            self.dice4 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice4)
            print(f"\n{tmp3} -> {self.dice4_result}\n")
        elif index1 == 5:
            tmp3 = self.dice5_result
            self.dice5 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice5)
            print(f"\n{tmp3} -> {self.dice5_result}\n")
        elif index1 == 6:
            tmp3 = self.dice6_result
            self.dice6 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice6)
            print(f"\n{tmp3} -> {self.dice6_result}\n")

        if index2 == None:
            o = 9
        elif index2 == 1:
            tmp3 = self.dice1_result
            self.dice1 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice1)
            print(f"\n{tmp3} -> {self.dice1_result}\n")
        elif index2 == 2:
            tmp3 = self.dice2_result
            self.dice2 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice2)
            print(f"\n{tmp3} -> {self.dice2_result}\n")
        elif index2 == 3:
            tmp3 = self.dice3_result
            self.dice3 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice3)
            print(f"\n{tmp3} -> {self.dice3_result}\n")
        elif index2 == 4:
            tmp3 = self.dice4_result
            self.dice4 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice4)
            print(f"\n{tmp3} -> {self.dice4_result}\n")
        elif index2 == 5:
            tmp3 = self.dice5_result
            self.dice5 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice5)
            print(f"\n{tmp3} -> {self.dice5_result}\n")
        elif index2 == 6:
            tmp3 = self.dice6_result
            self.dice6 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice6)
            print(f"\n{tmp3} -> {self.dice6_result}\n")
        return to_return

# Main board class
class Board:
    def __init__(self, list_of_characters, game, args):
        self.cart1 = []
        self.cart2 = []
        self.cart3 = []
        self.cart1_position = 1
        self.cart2_position = 1
        self.cart3_position = 1
        self.cart1_priority = 1
        self.cart2_priority = 2
        self.cart3_priority = 3
        self.list_of_characters = list_of_characters

        modulo = len(list_of_characters) % 3
        div = len(list_of_characters) / 3

        # Shuffle list
        random.shuffle(list_of_characters)

        if modulo == 1:
            # One cart gets a bonus character
            x = random.randint(1, 3)
            tmp = random.choice(list_of_characters)
            # Move bonus character to front of the list
            list_of_characters.insert(
                0, list_of_characters.pop(list_of_characters.index(tmp))
            )
            if x == 1:
                self.cart1 = [list_of_characters[0]]
                list_of_characters[0].cart = 1
            elif x == 2:
                self.cart2 = [list_of_characters[0]]
                list_of_characters[0].cart = 2
            elif x == 3:
                self.cart3 = [list_of_characters[0]]
                list_of_characters[0].cart = 3

        elif modulo == 2:
            # Two carts get a bonus character
            tmp = random.choice(list_of_characters)
            tmp2 = random.choice(list_of_characters)
            # Move 2 bonus characters to front of the list
            list_of_characters.insert(
                0, list_of_characters.pop(list_of_characters.index(tmp))
            )
            list_of_characters.insert(
                0, list_of_characters.pop(list_of_characters.index(tmp2))
            )
            x = random.randint(1, 3)
            if x == 1:
                self.cart1 = [list_of_characters[0]]
                list_of_characters[0].cart = 1
                self.cart2 = [list_of_characters[1]]
                list_of_characters[1].cart = 2
            elif x == 2:
                self.cart2 = [list_of_characters[0]]
                list_of_characters[0].cart = 2
                self.cart3 = [list_of_characters[1]]
                list_of_characters[1].cart = 3
            elif x == 3:
                self.cart3 = [list_of_characters[0]]
                list_of_characters[0].cart = 3
                self.cart1 = [list_of_characters[1]]
                list_of_characters[1].cart = 1

        for i in range(0, math.floor(div)):
            index = i * 3 + modulo
            self.cart1.append(list_of_characters[int(index)])
            list_of_characters[int(index)].cart = 1
            index += 1
            self.cart2.append(list_of_characters[int(index)])
            list_of_characters[int(index)].cart = 2
            index += 1
            self.cart3.append(list_of_characters[int(index)])
            list_of_characters[int(index)].cart = 3
            if i == (math.floor(div) - 1):
                tmpr = [f"{self.cart1_position}/{args.finish}", "\n", "\n"]
                for character in self.cart1:
                    tmpstr = f"{character.name} ({character.getMingleCount()})"
                    tmpr.append(tmpstr)
                    tmpr.append("\n")
                game.update_rectangle_txt(1, "".join(tmpr))
                tmpr = [f"{self.cart2_position}/{args.finish}", "\n", "\n"]
                for character in self.cart2:
                    tmpstr = f"{character.name} ({character.getMingleCount()})"
                    tmpr.append(tmpstr)
                    tmpr.append("\n")
                game.update_rectangle_txt(2, "".join(tmpr))
                tmpr = [f"{self.cart3_position}/{args.finish}", "\n", "\n"]
                for character in self.cart3:
                    tmpstr = f"{character.name} ({character.getMingleCount()})"
                    tmpr.append(tmpstr)
                    tmpr.append("\n")
                game.update_rectangle_txt(3, "".join(tmpr))

    def displayCarts(self, game, args):
        carorder = self.getCarOrder()

        for i in carorder:
            if i == 1:
                tmpr = [f"{self.cart1_position}/{args.finish}", "\n", "\n"]
                for character in self.cart1:
                    tmpstr = f"{character.name} ({character.getMingleCount()})"
                    tmpr.append(tmpstr)
                    tmpr.append(f"\n")
                game.update_rectangle_position(1, self.cart1_position)
                game.update_rectangle_txt(1, " ".join(tmpr))
            elif i == 2:
                tmpr = [f"{self.cart2_position}/{args.finish}", "\n", "\n"]
                for character in self.cart2:
                    tmpstr = f"{character.name} ({character.getMingleCount()})"
                    tmpr.append(tmpstr)
                    tmpr.append(f"\n")
                game.update_rectangle_position(2, self.cart2_position)
                game.update_rectangle_txt(2, " ".join(tmpr))
            elif i == 3:
                tmpr = [f"{self.cart3_position}/{args.finish}", "\n", "\n"]
                for character in self.cart3:
                    tmpstr = f"{character.name} ({character.getMingleCount()})"
                    tmpr.append(tmpstr)
                    tmpr.append(f"\n")
                game.update_rectangle_position(3, self.cart3_position)
                game.update_rectangle_txt(3, " ".join(tmpr))

    def updateBoard(self, list_of_characters, game, args):
        self.updatePriority()
        tmp = self.determineStartPlayer()
        self.list_of_characters.remove(tmp)
        self.list_of_characters.insert(0, tmp)

        self.displayCarts(game, args)

    def getCartInfo(self, cartnum):
        if cartnum == 1:
            return self.cart1
        elif cartnum == 2:
            return self.cart2
        elif cartnum == 3:
            return self.cart3

    def updatePriority(self):
        if (self.cart1_position > self.cart2_position) and (
            self.cart1_position > self.cart3_position
        ):
            self.cart1_priority = 1
            if self.cart2_position > self.cart3_position:
                self.cart2_priority = 2
                self.cart3_priority = 3
            elif self.cart3_position > self.cart2_position:
                self.cart2_priority = 3
                self.cart3_priority = 2
            else:
                if self.cart2_priority > self.cart3_priority:
                    self.cart2_priority = 2
                    self.cart3_priority = 3
                elif self.cart3_priority > self.cart2_priority:
                    self.cart2_priority = 3
                    self.cart3_priority = 2

        # Case 2
        if (self.cart2_position > self.cart1_position) and (
            self.cart2_position > self.cart3_position
        ):
            self.cart2_priority = 1
            if self.cart1_position > self.cart3_position:
                self.cart1_priority = 2
                self.cart3_priority = 3
            elif self.cart3_position > self.cart1_position:
                self.cart1_priority = 3
                self.cart3_priority = 2
            else:
                if self.cart1_priority > self.cart3_priority:
                    self.cart1_priority = 2
                    self.cart3_priority = 3
                elif self.cart3_priority > self.cart1_priority:
                    self.cart1_priority = 3
                    self.cart3_priority = 2

        # Case 3
        if (self.cart3_position > self.cart1_position) and (
            self.cart3_position > self.cart2_position
        ):
            self.cart3_priority = 1
            if self.cart1_position > self.cart2_position:
                self.cart1_priority = 2
                self.cart2_priority = 3
            elif self.cart2_position > self.cart1_position:
                self.cart1_priority = 3
                self.cart2_priority = 2
            else:
                if self.cart1_priority > self.cart2_priority:
                    self.cart1_priority = 2
                    self.cart2_priority = 3
                elif self.cart2_priority > self.cart1_priority:
                    self.cart1_priority = 3
                    self.cart2_priority = 2

        # Case of equals
        if (self.cart1_position > self.cart2_position) and (
            self.cart2_position == self.cart3_position
        ):
            self.cart1_priority = 1
            self.cart2_priority = 2
            self.cart3_priority = 3

        if (self.cart2_position > self.cart1_position) and (
            self.cart1_position == self.cart3_position
        ):
            self.cart2_priority = 1
            self.cart1_priority = 2
            self.cart3_priority = 3

        if (self.cart3_position > self.cart1_position) and (
            self.cart1_position == self.cart2_position
        ):
            self.cart3_priority = 1
            self.cart1_priority = 2
            self.cart2_priority = 3

        # ------------

        if (self.cart1_position < self.cart2_position) and (
            self.cart2_position == self.cart3_position
        ):
            self.cart1_priority = 3
            self.cart2_priority = 1
            self.cart3_priority = 2

        if (self.cart2_position < self.cart1_position) and (
            self.cart1_position == self.cart3_position
        ):
            self.cart2_priority = 3
            self.cart1_priority = 1
            self.cart3_priority = 2

        if (self.cart3_position < self.cart1_position) and (
            self.cart1_position == self.cart2_position
        ):
            self.cart3_priority = 3
            self.cart1_priority = 1
            self.cart2_priority = 2

        # -------

        if (self.cart1_position == self.cart2_position) and (
            self.cart2_position == self.cart3_position
        ):
            self.cart3_priority = 3
            self.cart1_priority = 1
            self.cart2_priority = 2

    def push(self, character, txt, account_sid, auth_token):
        # Check to make sure you are not at the back of the current cart.
        if character.cart == 1:
            if len(self.cart1) < 2:
                print(
                    f"{character.name} cannot push anyone, as they are the only one in their cart."
                )
                return False

            position = self.cart1.index(character)
            ranking = position + 1
            if ranking == len(self.cart1):
                # Back of cart
                print(
                    f"{character.name} cannot push anyone, as they are in the back of their cart."
                )
                return False
            else:
                v = input(
                    Fore.CYAN
                    + Style.BRIGHT
                    + f"{self.cart1[-1].name} is in the back of the cart. Would you like to push them? (y/n)"
                    + bcolors.RESET
                )
                if v.lower() == "y":
                    if self.cart1[-1].hasRemedies():
                        whip = input(
                            f"{self.cart1[-1].name}, would you like to use a remedy to prevent being pushed? (y/n):"
                        )
                        if whip.lower() == "y":
                            if self.cart1[-1].hasWhip():
                                print(
                                    Fore.GREEN
                                    + Style.BRIGHT
                                    + f"{self.cart1[-1].name} uses a whip to prevent being pushed!"
                                    + bcolors.RESET
                                )
                                self.cart1[-1].removeCard(4, txt, account_sid, auth_token)
                                return True
                            else:
                                print(
                                    f"\nSorry {self.cart1[-1].name}, you don't appear to have a whip!\n"
                                )
                    print(
                        Fore.RED
                        + f"\n{character.name} has kicked out {self.cart1[-1].name}! Super rude in the nude!\n"
                        + bcolors.RESET
                    )

                    if self.cart1_priority == 3:
                        # Pushed person dies. Check if the dead person had the plague. If so, kill current player.
                        print(
                            Fore.RED
                            + Style.BRIGHT
                            + f"{self.cart1[-1].name} has died!\n"
                            + bcolors.RESET
                        )
                        if self.cart1[-1].plague_status == True:
                            print(
                                Fore.GREEN
                                + Style.BRIGHT
                                + f"{self.cart1[-1].name} had the plague. Well done {character.name}!\n"
                                + bcolors.RESET
                            )
                            self.cart1.pop(-1)
                            # REMOVE from list of characters self.list_of_characters
                            return True
                        else:
                            print(
                                Fore.RED
                                + Style.BRIGHT
                                + f"{self.cart1[-1].name} did not have the plague. {character.name} killed themselves out of despair.\n"
                                + bcolors.RESET
                            )
                            self.cart1.pop(-1)
                            self.cart1.pop(position)
                            return True
                    else:
                        # Get the cart behind them:
                        if self.cart2_priority == (self.cart1_priority + 1):
                            self.cart1[-1].cart = 2
                            self.cart2.insert(0, self.cart1[-1])
                            self.cart1.pop(-1)
                            return True
                        elif self.cart3_priority == (self.cart1_priority + 1):
                            self.cart1[-1].cart = 3
                            self.cart3.insert(0, self.cart1[-1])
                            self.cart1.pop(-1)
                            return True
                else:
                    return False

        if character.cart == 2:
            if len(self.cart2) < 2:
                print(
                    f"{character.name} cannot push anyone, as they are the only one in their cart."
                )
                return False

            position = self.cart2.index(character)
            ranking = position + 1
            if ranking == len(self.cart2):
                # Back of cart
                print(
                    f"{character.name} cannot push anyone, as they are in the back of their cart."
                )
                return False
            else:
                v = input(
                    Fore.YELLOW
                    + Style.BRIGHT
                    + f"{self.cart2[-1].name} is in the back of the cart. Would you like to push them? (y/n)"
                    + bcolors.RESET
                )
                if v.lower() == "y":
                    if self.cart2[-1].hasRemedies():
                        whip = input(
                            f"{self.cart2[-1].name}, would you like to use a remedy to prevent being pushed? (y/n):"
                        )
                        if whip.lower() == "y":
                            if self.cart2[-1].hasWhip():
                                print(
                                    Fore.GREEN
                                    + f"{self.cart2[-1].name} uses a whip to prevent being pushed!"
                                    + bcolors.RESET
                                )
                                self.cart2[-1].removeCard(4, txt, account_sid, auth_token)
                                return True
                            else:
                                print(
                                    Fore.RED
                                    + f"\nSorry {self.cart2[-1].name}, you don't appear to have a whip!\n"
                                )
                    print(
                        Fore.RED
                        + Style.BRIGHT
                        + f"\n{character.name} has kicked out {self.cart2[-1].name}! Super rude in the nude!\n"
                        + bcolors.RESET
                    )

                    if self.cart2_priority == 3:
                        # Pushed person dies. Check if the dead person had the plague. If so, kill current player.
                        print(
                            Fore.RED
                            + Style.BRIGHT
                            + f"{self.cart2[-1].name} has died!"
                            + bcolors.RESET
                        )
                        if self.cart2[-1].plague_status == True:
                            print(
                                Fore.GREEN
                                + f"{self.cart2[-1].name} had the plague. Well done {character.name}!"
                                + bcolors.RESET
                            )
                            self.cart2.pop(-1)
                            # REMOVE from list of characters self.list_of_characters
                            return True
                        else:
                            print(
                                Fore.RED
                                + Style.BRIGHT
                                + f"{self.cart2[-1].name} did not have the plague. {character.name} killed themselves out of despair."
                                + bcolors.RESET
                            )
                            self.cart2.pop(-1)
                            self.cart2.pop(position)
                            return True
                    else:
                        # Get the cart behind them:
                        if self.cart3_priority == (self.cart2_priority + 1):
                            self.cart2[-1].cart = 3
                            self.cart3.insert(0, self.cart2[-1])
                            self.cart2.pop(-1)
                            return True
                        elif self.cart1_priority == (self.cart2_priority + 1):
                            self.cart2[-1].cart = 1
                            self.cart1.insert(0, self.cart2[-1])
                            self.cart2.pop(-1)
                            return True
                else:
                    return False

        if character.cart == 3:
            if len(self.cart3) < 2:
                print(
                    f"{character.name} cannot push anyone, as they are the only one in their cart."
                )
                return False

            position = self.cart3.index(character)
            ranking = position + 1
            if ranking == len(self.cart3):
                # Back of cart
                print(
                    f"{character.name} cannot push anyone, as they are in the back of their cart."
                )
                return False
            else:
                v = input(
                    Fore.MAGENTA
                    + Style.BRIGHT
                    + f"{self.cart3[-1].name} is in the back of the cart. Would you like to push them? (y/n)"
                    + bcolors.RESET
                )
                if v.lower() == "y":
                    if self.cart3[-1].hasRemedies():
                        whip = input(
                            f"{self.cart3[-1].name}, would you like to use a remedy to prevent being pushed? (y/n):"
                        )
                        if whip.lower() == "y":
                            if self.cart3[-1].hasWhip():
                                print(
                                    Fore.GREEN
                                    + f"\n{self.cart3[-1].name} uses a whip to prevent being pushed!\n"
                                    + bcolors.RESET
                                )
                                self.cart3[-1].removeCard(4, txt, account_sid, auth_token)
                                return True
                            else:
                                print(
                                    f"\nSorry {self.cart3[-1].name}, you don't appear to have a whip!\n"
                                )

                    print(
                        Fore.RED
                        + Style.BRIGHT
                        + f"\n{character.name} has kicked out {self.cart3[-1].name}! Super rude in the nude!\n"
                        + bcolors.RESET
                    )

                    if self.cart3_priority == 3:
                        # Pushed person dies. Check if the dead person had the plague. If so, kill current player.
                        print(
                            Fore.RED
                            + Style.BRIGHT
                            + f"{self.cart3[-1].name} has died!"
                            + bcolors.RESET
                        )
                        if self.cart3[-1].plague_status == True:
                            print(
                                Fore.GREEN
                                + Style.BRIGHT
                                + f"{self.cart3[-1].name} had the plague. Well done {character.name}!"
                                + bcolors.RESET
                            )
                            self.cart3.pop(-1)
                            # REMOVE from list of characters self.list_of_characters
                            return True
                        else:
                            print(
                                Fore.RED
                                + Style.BRIGHT
                                + f"{self.cart3[-1].name} did not have the plague. {character.name} killed themselves out of despair."
                                + bcolors.RESET
                            )
                            self.list_of_characters.remove(character)
                            self.list_of_characters.remove(self.cart3[-1])
                            self.cart3.pop(-1)
                            self.cart3.pop(position)
                            return True
                    else:
                        # Get the cart behind them:
                        if self.cart2_priority == (self.cart3_priority + 1):
                            self.cart3[-1].cart = 2
                            self.cart2.insert(0, self.cart3[-1])
                            self.cart3.pop(-1)
                            return True
                        elif self.cart1_priority == (self.cart3_priority + 1):
                            self.cart3[-1].cart = 1
                            self.cart1.insert(0, self.cart3[-1])
                            self.cart3.pop(-1)
                            return True
                else:
                    return False

    def jump(self, character, txt, account_sid, auth_token):
        # Check if your character is the leader of the current cart.
        if character.cart == 1:
            position = self.cart1.index(character)
            if position == 0:
                if self.cart1_priority == 1:
                    print(f"{character.name} is already in the front cart.")
                    return False
                elif self.cart1_priority == 2:
                    # Jump to highest priority cart
                    if self.cart2_priority == 1:
                        # check for whip in cart 2:
                        for booger in self.cart2:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.cart1.pop(position)
                        self.cart2.insert(len(self.cart2) + 1, character)
                        print(
                            Fore.YELLOW
                            + Style.BRIGHT
                            + f"\n{character.name} has jumped into the back of the yellow cart!\n"
                            + bcolors.RESET
                        )
                        character.cart = 2
                        return True
                    elif self.cart3_priority == 1:
                        for booger in self.cart3:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.cart1.pop(position)
                        self.cart3.insert(len(self.cart3) + 1, character)
                        print(
                            Fore.MAGENTA
                            + Style.BRIGHT
                            + f"\n{character.name} has jumped into the back of the purple cart!\n"
                            + bcolors.RESET
                        )
                        character.cart = 3
                        return True
                elif self.cart1_priority == 3:
                    # Jump to highest priority cart
                    if self.cart2_priority == 2:
                        for booger in self.cart2:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.cart1.pop(position)
                        self.cart2.insert(len(self.cart2) + 1, character)
                        print(
                            Fore.YELLOW
                            + Style.BRIGHT
                            + f"\n{character.name} has jumped into the back of the yellow cart!\n"
                            + bcolors.RESET
                        )
                        character.cart = 2
                        return True
                    elif self.cart3_priority == 2:
                        for booger in self.cart3:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.cart1.pop(position)
                        self.cart3.insert(len(self.cart3) + 1, character)
                        print(
                            Fore.YELLOW
                            + Style.BRIGHT
                            + f"\n{character.name} has jumped into the back of the purple cart!\n"
                            + bcolors.RESET
                        )
                        character.cart = 3
                        return True
            elif position > 0:
                # Not in front of the cart.
                print(
                    f"{character.name} needs to be in front of the cart before jumping to the next one!"
                )
                return False

        if character.cart == 2:
            position = self.cart2.index(character)
            if position == 0:
                if self.cart2_priority == 1:
                    print(f"{character.name} is already in the front cart.")
                    return False
                elif self.cart2_priority == 2:
                    # Jump to highest priority cart
                    if self.cart1_priority == 1:
                        for booger in self.cart1:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.cart2.pop(position)
                        self.cart1.insert(len(self.cart1) + 1, character)
                        print(
                            Fore.CYAN
                            + Style.BRIGHT
                            + f"\n{character.name} has jumped into the back of the blue cart!\n"
                            + bcolors.RESET
                        )
                        character.cart = 1
                        return True
                    elif self.cart3_priority == 1:
                        for booger in self.cart3:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.cart2.pop(position)
                        self.cart3.insert(len(self.cart3) + 1, character)
                        print(
                            Fore.MAGENTA
                            + Style.BRIGHT
                            + f"\n{character.name} has jumped into the back of the purple cart!\n"
                            + bcolors.RESET
                        )
                        character.cart = 3
                        return True
                elif self.cart2_priority == 3:
                    # Jump to highest priority cart
                    if self.cart1_priority == 2:
                        for booger in self.cart1:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"\nNice try {booger.name}, you don't own a whip.\n"
                                        )
                        self.cart2.pop(position)
                        self.cart1.insert(len(self.cart1) + 1, character)
                        print(
                            Fore.CYAN
                            + Style.BRIGHT
                            + f"\n{character.name} has jumped into the back of the blue cart!\n"
                            + bcolors.RESET
                        )
                        character.cart = 1
                        return True
                    elif self.cart3_priority == 2:
                        for booger in self.cart3:
                            if booger.hasRemedies():
                                denied = input(
                                    f"\n{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):\n"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"\n{booger.name}, used their whip on {character.name}. Jump DENIED!\n"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"\nNice try {booger.name}, you don't own a whip.\n"
                                        )
                        self.cart2.pop(position)
                        self.cart3.insert(len(self.cart3) + 1, character)
                        print(
                            Fore.MAGENTA
                            + Style.BRIGHT
                            + f"{character.name} has jumped into the back of the purple cart!"
                            + bcolors.RESET
                        )
                        character.cart = 3
                        return True
            elif position > 0:
                # Not in front of the cart.
                print(
                    f"\n{character.name} needs to be in front of the cart before jumping to the next one!\n"
                )
                return False

        if character.cart == 3:
            position = self.cart3.index(character)
            if position == 0:
                if self.cart3_priority == 1:
                    print(f"{character.name} is already in the front cart.")
                    return False
                elif self.cart3_priority == 2:
                    # Jump to highest priority cart
                    if self.cart2_priority == 1:
                        for booger in self.cart2:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"\nNice try {booger.name}, you don't own a whip.\n"
                                        )
                        self.cart3.pop(position)
                        self.cart2.insert(len(self.cart2) + 1, character)
                        print(
                            Fore.YELLOW
                            + Style.BRIGHT
                            + f"\n{character.name} has jumped into the back of the yellow cart!\n"
                            + bcolors.RESET
                        )
                        character.cart = 2
                        return True
                    elif self.cart1_priority == 1:
                        for booger in self.cart1:
                            if booger.hasRemedies():
                                denied = input(
                                    f"\n{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):\n"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"\nNice try {booger.name}, you don't own a whip.\n"
                                        )
                        self.cart3.pop(position)
                        self.cart1.insert(len(self.cart1) + 1, character)
                        print(
                            Fore.CYAN
                            + Style.BRIGHT
                            + f"\n{character.name} has jumped into the back of the blue cart!\n"
                            + bcolors.RESET
                        )
                        character.cart = 1
                        return True
                elif self.cart3_priority == 3:
                    # Jump to highest priority cart
                    if self.cart2_priority == 2:
                        for booger in self.cart2:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.cart3.pop(position)
                        self.cart2.insert(len(self.cart2) + 1, character)
                        print(
                            Fore.YELLOW
                            + Style.BRIGHT
                            + f"{character.name} has jumped into the back of the yellow cart!"
                            + bcolors.RESET
                        )
                        character.cart = 2
                        return True
                    elif self.cart1_priority == 2:
                        for booger in self.cart1:
                            if booger.hasRemedies():
                                denied = input(
                                    f"{booger.name}, would you like to use a whip to prevent {character.name} from joining your cart? (y/n):"
                                )
                                if denied.lower() == "y":
                                    if booger.hasWhip():
                                        print(
                                            Fore.RED
                                            + Style.BRIGHT
                                            + f"{booger.name}, used their whip on {character.name}. Jump DENIED!"
                                            + bcolors.RESET
                                        )
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.cart3.pop(position)
                        self.cart1.insert(len(self.cart1) + 1, character)
                        print(
                            Fore.CYAN
                            + Style.BRIGHT
                            + f"{character.name} has jumped into the back of the blue cart!"
                            + bcolors.RESET
                        )
                        character.cart = 1
                        return True
            elif position > 0:
                # Not in front of the cart.
                print(
                    f"{character.name} needs to be in front of the cart before jumping to the next one!"
                )
                return False

    def knight_action(self, character, num):
        if num == 1:
            indy = self.cart1.index(character)
            if indy == 0:
                print(f"\n{character.name} is already at the front of their cart!\n")
            else:
                self.cart1.pop(indy)
                self.cart1.insert(0, character)
                print(Fore.CYAN + Style.BRIGHT)
                print(
                    f"{character.name} has been knighted to the front of the cart!"
                )
                print(bcolors.RESET)

        elif num == 2:
            indy = self.cart2.index(character)
            if indy == 0:
                print(f"\n{character.name} is already at the front of their cart!\n")
            else:
                self.cart2.pop(indy)
                self.cart2.insert(0, character)
                print(Fore.YELLOW + Style.BRIGHT)
                print(
                    f"{character.name} has been knighted to the front of the cart!"
                )
                print(bcolors.RESET)
        elif num == 3:
            indy = self.cart3.index(character)
            if indy == 0:
                print(f"\n{character.name} is already at the front of their cart!\n")
            else:
                self.cart3.pop(indy)
                self.cart3.insert(0, character)
                print(Fore.MAGENTA + Style.BRIGHT)
                print(
                    f"{character.name} has been knighted to the front of the cart!"
                )
                print(bcolors.RESET)

    def elbow(self, character, txt, account_sid, auth_token):
        if character.cart == 1:
            if len(self.cart1) < 2:
                print(
                    f"{character.name} is unable to elbow. You are the only one in your cart!"
                )
                return False
            else:
                position = self.cart1.index(character)
                if position == 0:
                    print(
                        f"{character.name} is unable to elbow. You are already at the front of your cart!"
                    )
                    return False
                else:
                    # Check if others ahead of you in the cart can whip you:
                    for booger in self.cart1:
                        if booger.hasRemedies() and booger != character:
                            denied = input(
                                f"{booger.name}, would you like to use a whip to prevent {character.name} from elbowing you? (y/n):"
                            )
                            if denied.lower() == "y":
                                if booger.hasWhip():
                                    print(
                                        Fore.RED
                                        + Style.BRIGHT
                                        + f"{booger.name}, used their whip on {character.name}. Keep your elbows to yourself!"
                                        + bcolors.RESET
                                    )
                                    booger.removeCard(4, txt, account_sid, auth_token)
                                    return True
                                else:
                                    print(
                                        f"Nice try {booger.name}, you don't own a whip."
                                    )
                    self.cart1.pop(position)
                    self.cart1.insert(0, character)
                    print(Fore.CYAN + Style.BRIGHT)
                    print(
                        f"{character.name} has elbowed their way into the front of the blue cart!"
                    )
                    print(bcolors.RESET)
                    return True

        if character.cart == 2:
            if len(self.cart2) < 2:
                print(
                    f"{character.name} is unable to elbow. You are the only one in your cart!"
                )
                return False
            else:
                position = self.cart2.index(character)
                if position == 0:
                    print(
                        f"{character.name} is unable to elbow. You are already at the front of your cart!"
                    )
                    return False
                else:
                    for booger in self.cart2:
                        if booger.hasRemedies() and booger != character:
                            denied = input(
                                f"{booger.name}, would you like to use a whip to prevent {character.name} from elbowing you? (y/n):"
                            )
                            if denied.lower() == "y":
                                if booger.hasWhip():
                                    print(
                                        Fore.RED
                                        + Style.BRIGHT
                                        + f"{booger.name}, used their whip on {character.name}. Keep your elbows to yourself!"
                                        + bcolors.RESET
                                    )
                                    booger.removeCard(4, txt, account_sid, auth_token)
                                    return True
                                else:
                                    print(
                                        f"Nice try {booger.name}, you don't own a whip."
                                    )
                    self.cart2.pop(position)
                    self.cart2.insert(0, character)
                    print(Fore.YELLOW + Style.BRIGHT)
                    print(
                        f"{character.name} has elbowed their way into the front of the Yellow cart!"
                    )
                    print(bcolors.RESET)
                    return True

        if character.cart == 3:
            if len(self.cart3) < 2:
                print(
                    f"{character.name} is unable to elbow. You are the only one in your cart!"
                )
                return False
            else:
                position = self.cart3.index(character)
                if position == 0:
                    print(
                        f"{character.name} is unable to elbow. You are already at the front of your cart!"
                    )
                    return False
                else:
                    for booger in self.cart3:
                        if booger.hasRemedies() and booger != character:
                            denied = input(
                                f"{booger.name}, would you like to use a whip to prevent {character.name} from elbowing you? (y/n):"
                            )
                            if denied.lower() == "y":
                                if booger.hasWhip():
                                    print(
                                        Fore.RED
                                        + Style.BRIGHT
                                        + f"{booger.name}, used their whip on {character.name}. Keep your elbows to yourself!"
                                        + bcolors.RESET
                                    )
                                    booger.removeCard(4, txt, account_sid, auth_token)
                                    return True
                                else:
                                    print(
                                        f"Nice try {booger.name}, you don't own a whip."
                                    )
                    self.cart3.pop(position)
                    self.cart3.insert(0, character)
                    print(Fore.MAGENTA + Style.BRIGHT)
                    print(
                        f"{character.name} has elbowed their way into the front of the blue cart!"
                    )
                    print(bcolors.RESET)
                    return True

    def mingle(self, cart, args, sid, token):
        new_supply = [1,2,3,4]
        if cart == 1:
            for character in self.cart1:
                if not character.getDrunkStatus():
                    new_symptoms = random.choices(new_supply, cum_weights=(20, 20, 30, 30), k=2)
                    character.status1 = new_symptoms[0]
                    character.status2 = new_symptoms[1]
                    character.updateStatement()
                    character.increaseMingleCount()
                    if not args.test:
                        print(
                            f"{character.name}, please check your phone for your updated symptoms."
                        )
                        send_mingle_message(
                            name=character.name,
                            phone_number=character.phone_number,
                            mingle_statement=character.plague_statement,
                            account_sid=sid,
                            auth_token=token,
                        )
                    else:
                        print(character.name, character.plague_statement)
                else:
                    print(f"\n{character.name} is drunk, and is immune from mingling! 🍻🍺🥴\n")
                    character.resetDrunk()

        elif cart == 2:
            for character in self.cart2:
                if not character.getDrunkStatus():
                    new_symptoms = random.choices(new_supply, cum_weights=(20, 20, 30, 30), k=2)
                    character.status1 = new_symptoms[0]
                    character.status2 = new_symptoms[1]
                    character.updateStatement()
                    character.increaseMingleCount()
                    if not args.test:
                        print(
                            f"{character.name}, please check your phone for your updated symptoms."
                        )
                        send_mingle_message(
                            name=character.name,
                            phone_number=character.phone_number,
                            mingle_statement=character.plague_statement,
                            account_sid=sid,
                            auth_token=token,
                        )
                    else:
                        print(character.name, character.plague_statement)
                else:
                    print(f"\n{character.name} is drunk, and is immune from mingling! 🍻🍺🥴\n")
                    character.resetDrunk()

        elif cart == 3:
            for character in self.cart3:
                if not character.getDrunkStatus():
                    new_symptoms = random.choices(new_supply, cum_weights=(20, 20, 30, 30), k=2)
                    character.status1 = new_symptoms[0]
                    character.status2 = new_symptoms[1]
                    character.updateStatement()
                    character.increaseMingleCount()
                    if not args.test:
                        print(
                            f"{character.name}, please check your phone for your updated symptoms."
                        )
                        send_mingle_message(
                            name=character.name,
                            phone_number=character.phone_number,
                            mingle_statement=character.plague_statement,
                            account_sid=sid,
                            auth_token=token,
                        )
                    else:
                        print(character.name, character.plague_statement)
                else:
                    print(f"\n{character.name} is drunk, and is immune from mingling! 🍻🍺🥴\n")
                    character.resetDrunk()


    def getCarOrder(self):
        carorder = []
        if self.cart1_priority == 1:
            carorder.append(1)
        elif self.cart2_priority == 1:
            carorder.append(2)
        elif self.cart3_priority == 1:
            carorder.append(3)

        if self.cart1_priority == 2:
            carorder.append(1)
        elif self.cart2_priority == 2:
            carorder.append(2)
        elif self.cart3_priority == 2:
            carorder.append(3)

        if self.cart1_priority == 3:
            carorder.append(1)
        elif self.cart2_priority == 3:
            carorder.append(2)
        elif self.cart3_priority == 3:
            carorder.append(3)
        return carorder

    def determineStartPlayer(self):
        # If there's only one character left, then that's obviously the start.
        if len(self.list_of_characters) == 1:
            return self.list_of_characters[0]
        # Get cart with highest priority
        if (self.cart1_priority < self.cart2_priority) and (
            self.cart1_priority < self.cart3_priority
        ):
            if len(self.cart1) > 0:
                return self.cart1[0]
            else:
                if self.cart2_priority < self.cart3_priority:
                    return self.cart2[0]
                else:
                    return self.cart3[0]
        elif (self.cart2_priority < self.cart1_priority) and (
            self.cart2_priority < self.cart3_priority
        ):
            if len(self.cart2) > 0:
                return self.cart2[0]
            else:
                if self.cart1_priority < self.cart3_priority:
                    return self.cart1[0]
                else:
                    return self.cart3[0]
        elif (self.cart3_priority < self.cart1_priority) and (
            self.cart3_priority < self.cart2_priority
        ):
            if len(self.cart3) > 0:
                return self.cart3[0]
            else:
                if self.cart1_priority < self.cart2_priority:
                    return self.cart1[0]
                else:
                    return self.cart2[0]


class Character:
    def __init__(self, name, phone_number):
        self.name = name
        self.phone_number = phone_number
        self.status1 = 1
        self.status2 = 1
        self.plague_status = False
        self.plague_statement = ""
        self.cart = 0
        self.remedycard1 = None
        self.remedycard2 = None
        self.remedycard3 = None
        self.currentRemedyTotal = 0
        self.numMingles = 0
        self.charactertype = None
        self.characterdesc = None
        self.isDrunk = False
        self.isOutlaw = False

        self.remedy_Dictionary = {
            1: "Arsenic",
            2: "Chicken",
            3: "Crushed Emeralds",
            4: "Whip",
            5: "Turkey",
        }

        self.remedy_Description = {
            1: "Select two dice to lock. Use during the action phase.",
            2: "If rerolling dice, reroll them up to 3 more times. Use during the action phase when rerolling two dice.",
            3: "Take an extra movent action: elbow (E), push (P) or jump (D). Use during the action phase.",
            4: "Prevent someone from jumping into your cart, elbowing past you, or pushing you off your cart. Use on another players turn.",
            5: "Used to reroll 4 dice, instead of the standard 2.",
        }

    def getOutlaw(self):
        return self.isOutlaw

    def setOutlaw(self):
        self.isOutlaw = True

    def getCart(self):
        return self.cart

    def updateRemedy(self, index, val):
        if index == 0:
            self.remedycard1 = val
        elif index == 1:
            self.remedycard2 = val
        elif index == 2:
            self.remedycard3 = val

    def setStatusCorn(self, num, val):
        if num==1:
            self.status1 = val
        else:
            self.status2 = val

    def setDrunk(self):
        self.isDrunk = True

    def getDrunkStatus(self):
        return self.isDrunk

    def resetDrunk(self):
        self.isDrunk = False

    def getStatus(self):
        xd = random.randint(1,2)
        if xd == 1:
            return self.status1
        else:
            return self.status2

    def getCharacterType(self, charname, chardesc):
        self.charactertype = charname
        self.characterdesc = chardesc

    def increaseMingleCount(self):
        self.numMingles += 1

    def getMingleCount(self):
        return self.numMingles

    def hasRemedies(self):
        if (not self.remedycard1) and (not self.remedycard2) and (not self.remedycard3):
            return False
        else:
            return True

    def hasArsenic(self):
        if (
            (self.remedycard1 == 1)
            or (self.remedycard2 == 1)
            or (self.remedycard3 == 1)
        ):
            return True
        else:
            return False

    def hasChicken(self):
        if (
            (self.remedycard1 == 2)
            or (self.remedycard2 == 2)
            or (self.remedycard3 == 2)
        ):
            return True
        else:
            return False

    def hasEmerald(self):
        if (
            (self.remedycard1 == 3)
            or (self.remedycard2 == 3)
            or (self.remedycard3 == 3)
        ):
            return True
        else:
            return False

    def hasWhip(self):
        if (
            (self.remedycard1 == 4)
            or (self.remedycard2 == 4)
            or (self.remedycard3 == 4)
        ):
            return True
        else:
            return False

    def hasTurkey(self):
        if (
            (self.remedycard1 == 5)
            or (self.remedycard2 == 5)
            or (self.remedycard3 == 5)
        ):
            return True
        else:
            return False

    def removeCard(self, value, txt, sid, token):
        if self.remedycard1 == value:
            self.remedycard1 = None
            if self.remedycard2:
                self.remedycard1 = self.remedycard2
                self.remedycard2 = None
            if self.remedycard3:
                self.remedycard2 = self.remedycard3
                self.remedycard3 = None
        elif self.remedycard2 == value:
            self.remedycard2 = None
            if self.remedycard3:
                self.remedycard2 = self.remedycard3
                self.remedycard3 = None
        elif self.remedycard3 == value:
            self.remedycard3 = None
        self.currentRemedyTotal -= 1
        print(f"{self.name} has used up their {self.remedy_Dictionary[value]}!")
        #TODO: Change var name without breaking the game.
        if not txt:
            remedy_txt = f"You have successfully used up your {self.remedy_Dictionary[value]} remedy! \n \n"
            remedy_appendage = ""
            if not self.remedycard1:
                remedy_appendage = (
                    f"...that means you are currently out of remedy cards!"
                )
            elif not self.remedycard2:
                remedy_appendage = f"Remaining remedy cards: \n 1: {self.remedy_Dictionary[self.remedycard1]}"
            elif not self.remedycard3:
                remedy_appendage = f"Remaining remedy cards: \n 1: {self.remedy_Dictionary[self.remedycard1]} \n 2: {self.remedy_Dictionary[self.remedycard2]}"

            send_used_remedy_message(
                self.name, self.phone_number, remedy_txt + remedy_appendage, sid, token
            )

    def drawRemedy(self, args, sid, token):
        new_card = random.randint(1, 5)
        total_remedy_message = ""
        if not self.remedycard1:
            self.remedycard1 = new_card
            self.currentRemedyTotal = 1
            total_remedy_message = (
                f"Total remedy cards: \n 1: {self.remedy_Dictionary[self.remedycard1]}"
            )
        elif not self.remedycard2:
            self.remedycard2 = new_card
            self.currentRemedyTotal = 2
            total_remedy_message = f"Total remedy cards: \n 1: {self.remedy_Dictionary[self.remedycard1]} \n 2: {self.remedy_Dictionary[self.remedycard2]}"
        elif not self.remedycard3:
            self.remedycard3 = new_card
            self.currentRemedyTotal = 3
            total_remedy_message = f"Total remedy cards: \n 1: {self.remedy_Dictionary[self.remedycard1]} \n 2: {self.remedy_Dictionary[self.remedycard2]}"
            total_remedy_message = (
                total_remedy_message
                + f"\n 3: {self.remedy_Dictionary[self.remedycard3]}"
            )
        else:
            print("You already have 3 remedies! Do another action.")
            return False

        # Text current remedy card status.
        remedy_message = f"You received the {self.remedy_Dictionary[new_card]} remedy: {self.remedy_Description[new_card]}"
        remedy_message = remedy_message + f"\n\n {total_remedy_message}"
        if not args.test:
            send_remedy_message(
                name=self.name,
                phone_number=self.phone_number,
                remedy_statement=remedy_message,
                account_sid=sid,
                auth_token=token,
            )
        else:
            print(remedy_message)
        return True

    def updateStatement(self):
        if self.status1 == 1:
            self.plague_statement = "Your symptoms are a headache (1) & "
        elif self.status1 == 2:
            self.plague_statement = "Your symptoms are chills (2) & "
        elif self.status1 == 3:
            self.plague_statement = "Your symptoms are a cough (3) & "
        elif self.status1 == 4:
            self.plague_statement = "Your symptoms are buboes (4) & "
        if self.status2 == 1:
            self.plague_statement = self.plague_statement + "a headache (1)"
            if self.status1 == 1:
                self.plague_statement = "Your symptoms are a killer migraine (1 + 1)"
        elif self.status2 == 2:
            self.plague_statement = self.plague_statement + "chills (2)"
            if self.status1 == 2:
                self.plague_statement = (
                    "Your symptoms are being chillier than a snowman (2 + 2)"
                )
        elif self.status2 == 3:
            self.plague_statement = self.plague_statement + "a cough (3)"
            if self.status1 == 3:
                self.plague_statement = (
                    "Your symptoms are having a horrendous whooping cough (3 + 3)"
                )
        elif self.status2 == 4:
            self.plague_statement = self.plague_statement + "buboes (4)"
            if self.status1 == 4:
                self.plague_statement = "Your symptoms are being so bubonic that you are literally green goo (4 + 4)"
        if self.status1 + self.status2 >= 6:
            # Redo it my guy
            self.plague_status = True
        if self.plague_status == True:
            self.plague_statement = (
                self.plague_statement
                + f" = {self.status1 + self.status2}. "
                + " You have the plague!"
            )
        else:
            self.plague_statement = (
                self.plague_statement
                + f" = {self.status1 + self.status2}. "
                + " You do not have the plague...yet!"
            )

    def generateStartStatus(self, args):
        self.status1 = random.randint(1, 3)
        self.status2 = random.randint(1, 3)
        if self.status1 == 1:
            self.plague_statement = "your symptoms are a headache (1) & "
        elif self.status1 == 2:
            self.plague_statement = "your symptoms are chills (2) & "
        elif self.status1 == 3:
            self.plague_statement = "your symptoms are a cough (3) & "
        elif self.status1 == 4:
            self.plague_statement = "your symptoms are buboes (4) & "
        if self.status2 == 1:
            self.plague_statement = self.plague_statement + "a headache (1)"
            if self.status1 == 1:
                self.plague_statement = "your symptoms are a killer migraine (1 + 1)"
        elif self.status2 == 2:
            self.plague_statement = self.plague_statement + "chills (2)"
            if self.status1 == 2:
                self.plague_statement = (
                    "your symptoms are being chillier than a snowman (2 + 2)"
                )
        elif self.status2 == 3:
            self.plague_statement = self.plague_statement + "a cough (3)"
            if self.status1 == 3:
                self.plague_statement = (
                    "your symptoms are having a horrendous whooping cough (3 + 3)"
                )
        elif self.status2 == 4:
            self.plague_statement = self.plague_statement + "buboes (4)"
            if self.status1 == 4:
                self.plague_statement = "your symptoms are being so bubonic that you are literally green goo (4 + 4)"
        if self.status1 + self.status2 >= 6:
            self.status1 = random.randint(1, 3)
            self.status2 = random.randint(1, 2)
            if self.status1 == 1:
                self.plague_statement = "your symptoms are a headache (1) & "
            elif self.status1 == 2:
                self.plague_statement = "your symptoms are chills (2) & "
            elif self.status1 == 3:
                self.plague_statement = "your symptoms are a cough (3) & "
            elif self.status1 == 4:
                self.plague_statement = "your symptoms are buboes (4) & "
            if self.status2 == 1:
                self.plague_statement = self.plague_statement + "a headache (1)"
                if self.status1 == 1:
                    self.plague_statement = (
                        "your symptoms are a killer migraine (1 + 1)"
                    )
            elif self.status2 == 2:
                self.plague_statement = self.plague_statement + "chills (2)"
                if self.status1 == 2:
                    self.plague_statement = (
                        "your symptoms are being chillier than a snowman (2 + 2)"
                    )
            elif self.status2 == 3:
                self.plague_statement = self.plague_statement + "a cough (3)"
                if self.status1 == 3:
                    self.plague_statement = (
                        "your symptoms are having a horrendous whooping cough (3 + 3)"
                    )
            elif self.status2 == 4:
                self.plague_statement = self.plague_statement + "buboes (4)"
                if self.status1 == 4:
                    self.plague_statement = "your symptoms are being so bubonic that you are literally green goo (4 + 4)"
        self.plague_statement = (
            self.plague_statement
            + f" = {self.status1 + self.status2}. "
            + " You do not have the plague... yet! Try to keep it that way!"
        )


def parse_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("-t", "--test", action="store_true", help="Test game. Sets symptoms and remedy info to screen.")
    parser.add_argument("-p", "--players", nargs="+", help="People playing")
    parser.add_argument(
        "-f", "--finish", default=17, type=int, help="end number condition"
    )
    parser.add_argument(
        "-r",
        "--registered",
        default=os.path.abspath(os.path.join(__file__, "../../../registration.yml")),
        help="Config file containing list of registered users.",
    )
    parser.add_argument("-c", "--character", action="store_true", help="Play using characters, wach with their own special power")
    parser.add_argument("-v", "--version", action="store_true", help="Show version")

    args = parser.parse_args()

    if args.version:
        print(f"v{get_project_version()}")
        exit()

    return args


def introsequence(args, sid, token):
    registered_users = read_yaml_file(args.registered)["registered_users"]
    character_dict = {
        "Sheriff": "You can view 1 symptom of a player on a different cart.",
        "Friar": "You can change 1 die to be exactly what you want.",
        "Outlaw": "You have a 1/3 chance of gaining a free remedy card (happens automatically at the start of your turn).",
        "Mason": "You can reroll 1 die, then lock one die.",
        "Chandler": "You can draw a random symptom and choose to replace it with one of your own.",
        "Countess": "You can draw 2 remedies and keep 1 of them.",
        "Drunkard": "You can turn 1 die into a rat of your current cart color. You are also immune from mingling whenever you use this.",
        "Rat King": "You can replace up to two apple dice with a rat of the same cart color.",
        "Knight": "You can move any player up to the front of their current cart."
    }
    ascii_art = """
  ____       _     _        _   __ ____  _____  ___  
 |  _ \     (_)   | |      | | /_ |___ \| ____|/ _ \ 
 | |_) |_ __ _ ___| |_ ___ | |  | | __) | |__ | | | |
 |  _ <| '__| / __| __/ _ \| |  | ||__ <|___ \| | | |
 | |_) | |  | \__ \ || (_) | |  | |___) |___) | |_| |
 |____/|_|  |_|___/\__\___/|_|  |_|____/|____/ \___/
    """
    print(f"{ascii_art}\n")
    if args.players:
        list_of_characters = []
        print(f"There will be {len(args.players)} players today! \n")
        for i in range(len(args.players)):
            # Check if valid player
            if args.players[i] not in registered_users:
                print(f"{args.players[i]} is not registered!\n")
                print(f"Unable to proceed with the game. Please register {args.players[i]} and try again.")
                sys.exit(6)
            list_of_characters.append("d")
            list_of_characters[i] = Character(
                name=args.players[i],
                phone_number=registered_users[args.players[i]],
            )
            list_of_characters[i].generateStartStatus(args)
            time.sleep(1.5)

            if args.character:
                selected_char, selected_description = random.choice(list(character_dict.items()))
                list_of_characters[i].getCharacterType(selected_char, selected_description)
                if args.test:
                    print(f"\n{list_of_characters[i].name}, you are the {selected_char}: {selected_description}\n")
                
                else:
                    statement2 = f"{list_of_characters[i].name}, you are the {selected_char}: {selected_description}"
                    print(f"\n{statement2}\n")
                    send_remedy_message(
                        name=list_of_characters[i].name,
                        phone_number=list_of_characters[i].phone_number,
                        remedy_statement=statement2,
                        account_sid=sid,
                        auth_token=token,
                    )
                    time.sleep(1.5)
                try:
                    if selected_char == "Outlaw":
                        list_of_characters[i].setOutlaw()
                except Exception as e:
                    print("\nAn error occurred when using the outlaw.", e,"\n")
                del character_dict[selected_char]

            if not args.test:
                print(
                    f"\n{args.players[i]}, you have been sent a text message with your symptoms!"
                )
                send_message(
                    name=args.players[i],
                    phone_number=registered_users[args.players[i]],
                    plague_statement=list_of_characters[i].plague_statement,
                    account_sid=sid,
                    auth_token=token,
                )
                time.sleep(1.5)
            else:
                print(f"{args.players[i]}, {list_of_characters[i].plague_statement}\n")
            list_of_characters[i].drawRemedy(args, sid, token)
            # Must include waiting period, otherwise twilio will throw an error
            time.sleep(1.5)
        return list_of_characters


def read_yaml_file(file_path):
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except yaml.YAMLError as exc:
        print(f"Error reading YAML file '{file_path}': {exc}")
        return None


def EmeraldAction(board, character, initial_roll, game, args, account_sid, auth_token):
    finished = False
    while finished == False:
        player_input = input("(P) Push, (E) Elbow, (J) Jump, (V) View rolled dice:")

        if player_input.lower() == "v":
            finished = False
            board.displayCarts(game, args)
            print(
                f"(1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
            )

        if player_input.lower() == "e":
            if board.elbow(character, args.test, account_sid, auth_token) == True:
                finished = True
                board.displayCarts(game, args)
            else:
                finished = False

        if player_input.lower() == "j":
            if board.jump(character, args.test, account_sid, auth_token) == True:
                finished = True
                board.displayCarts(game, args)
            else:
                finished = False

        if player_input.lower() == "p":
            if board.push(character, args.test, account_sid, auth_token) == True:
                finished = True
                board.displayCarts(game, args)
            else:
                finished = False


def checkifVictorious(board, result, game, args):
    board.updateBoard(None, game, args)
    if result == 1:
        # Check that they crossed the finish line and that this cart is populated.
        if board.cart1_position >= args.finish and len(board.cart1) > 0:
            print(Fore.CYAN + Style.BRIGHT)
            print(f"Blue cart has escaped from Bristol!")
            plague_result = False
            for character in board.cart1:
                if character.plague_status == True:
                    print(f"{character.name} has the plague!")
                    plague_result = True
                elif character.plague_status == False:
                    print(f"{character.name} is FREE of the plague!")
            if plague_result == False:
                print(Fore.GREEN)
                print(f"Congratulations blue cart. You win!")
                print(bcolors.RESET)
                print("\n")
                input("Press any key to exit the game")
                sys.exit(0)
            else:
                for character in board.cart1:
                    print(
                        Fore.RED,
                        Style.BRIGHT
                        + f"{character.name} has died from the plague :( \n"
                        + bcolors.RESET,
                    )
                    board.cart1.remove(character)
                    board.list_of_characters.remove(character)
                    time.sleep(3)
                    board.displayCarts(game, args)
                print(f"There are {len(board.list_of_characters)} players remaining")
                if len(board.list_of_characters) == 0:
                    print(
                        Fore.RED,
                        Style.BRIGHT
                        + f"There are no more players left alive. Nobody wins!",
                    )
                    print(bcolors.RESET)
                    print("\n")
                    input("Press any key to exit the game")
                    sys.exit(0)
                return False

    elif result == 2:
        if board.cart2_position >= args.finish and len(board.cart2) > 0:
            print(Fore.YELLOW + Style.BRIGHT)
            print(f"Yellow cart has escaped Bristol!")
            plague_result = False
            for character in board.cart2:
                if character.plague_status == True:
                    print(f"{character.name} has the plague! \n")
                    plague_result = True
                elif character.plague_status == False:
                    print(f"{character.name} is FREE of the plague! \n")
            if plague_result == False:
                print(Fore.GREEN)
                print(f"Congratulations yellow cart. You win!")
                print(bcolors.RESET)
                print("\n")
                input("Press any key to exit the game")
                sys.exit(0)
            else:
                for character in board.cart2:
                    print(
                        Fore.RED,
                        Style.BRIGHT
                        + f"{character.name} has died from the plague :( \n"
                        + bcolors.RESET,
                    )
                    board.cart2.remove(character)
                    board.list_of_characters.remove(character)
                    time.sleep(3)
                    board.displayCarts(game, args)
                print(f"There are {len(board.list_of_characters)} players remaining")
                if len(board.list_of_characters) == 0:
                    print(
                        Fore.RED,
                        Style.BRIGHT
                        + f"There are no more players left alive. Nobody wins!",
                    )
                    print(bcolors.RESET)
                    print("\n")
                    input("Press any key to exit the game")
                    sys.exit(0)
                return False

    elif result == 3:
        if board.cart3_position >= args.finish and len(board.cart3) > 0:
            print(Fore.MAGENTA + Style.BRIGHT)
            print(f"Purple cart has escaped Bristol!")
            plague_result = False
            for character in board.cart3:
                if character.plague_status == True:
                    print(f"{character.name} has the plague!")
                    plague_result = True
                elif character.plague_status == False:
                    print(f"{character.name} is FREE of the plague!")
            if plague_result == False:
                print(Fore.GREEN)
                print(f"Congratulations purple cart. You win!")
                print(bcolors.RESET)
                print("\n")
                input("Press any key to exit the game")
                sys.exit(0)
            else:
                for character in board.cart3:
                    print(
                        Fore.RED,
                        Style.BRIGHT
                        + f"{character.name} has died from the plague :( \n"
                        + bcolors.RESET,
                    )
                    board.cart3.remove(character)
                    board.list_of_characters.remove(character)
                    time.sleep(3)
                    board.displayCarts(game, args)
                print(f"There are {len(board.list_of_characters)} players remaining")
                if len(board.list_of_characters) == 0:
                    print(
                        Fore.RED,
                        Style.BRIGHT
                        + f"There are no more players left alive. Nobody wins!",
                    )
                    print(bcolors.RESET)
                    print("\n")
                    input("Press any key to exit the game")
                    sys.exit(0)
                return False
    else:
        return False

def get_project_version():
    try:
        with open('pyproject.toml', 'r') as file:
            toml_content = toml.load(file)
            # Check if 'tool.poetry' and 'version' exist in pyproject.toml
            if 'tool' in toml_content and 'poetry' in toml_content['tool'] and 'version' in toml_content['tool']['poetry']:
                return toml_content['tool']['poetry']['version']
            elif 'project' in toml_content and 'version' in toml_content['project']:
                return toml_content['project']['version']
            else:
                print("Version information not found in pyproject.toml.")
                return None
    except FileNotFoundError:
        print("pyproject.toml not found.")
        return None


def main():
    args = parse_args()
    gameOver = False

    account_sid = read_yaml_file(args.registered)["twilio_info"]["account_sid"]
    auth_token = read_yaml_file(args.registered)["twilio_info"]["auth_token"]

    root = tk.Tk()
    game = BristolGame(root)
    game.update_finish_line(args.finish)

    list_of_characters = introsequence(args, account_sid, auth_token)
    print("\n")

    board = Board(list_of_characters, game, args)
    board.displayCarts(game, args)
    gameOver = False
    finalRound = False
    while gameOver == False:
        print(f"\n-------------")
        print(f"Action Phase")
        print(f"-------------")
        time.sleep(1)
        if finalRound:
            print(f"This is the final round!")
        print(f"\n{board.determineStartPlayer().name} is the starting player!\n")
        time.sleep(1)
        tmp = board.determineStartPlayer()
        list_of_characters.remove(tmp)
        list_of_characters.insert(0, tmp)
        if args.character:
            print("(A) Use Ability, (R) Reroll, (D) Draw Remedy, (M) Move Character, (U) Use Remedy, (V) View rolled dice, (S) Skip turn \n")
        else:
            print("(R) Reroll, (D) Draw Remedy, (M) Move Character, (U) Use Remedy, (V) View rolled dice, (S) Skip turn \n")
        print(f"\nRolling dice:\n")
        time.sleep(0.5)
        initial_roll = Dice()
        initial_roll.updateResults()
        print(
            f"(1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
        )

        game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
        game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
        game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
        game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
        game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
        game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
        game.update_lock_symbol(1,False, False)
        game.update_lock_symbol(2,False, False)
        game.update_lock_symbol(3,False, False)
        game.update_lock_symbol(4,False, False)
        game.update_lock_symbol(5,False, False)
        game.update_lock_symbol(6,False, False)

        for character in list_of_characters:
            finished = False
            while finished == False:
                print(
                    f"\nIt is {character.name}'s turn. What would {character.name} like to do? :"
                )
                try:
                    if character.getOutlaw():
                        odds = random.randint(1,3)
                        mariokart = character.getCart()
                        print(f"\n{character.name} is the outlaw, and is attempting to steal a remedy... \n")
                        time.sleep(3)
                        if odds == mariokart:
                            print(Fore.GREEN + f"Congratulations {character.name}! You got a free remedy\n" + bcolors.RESET)
                            if character.drawRemedy(args, account_sid, auth_token) == True:
                                finished = False
                            else:
                                finished = False
                        else:
                            print(Fore.RED, Style.BRIGHT + f"Sorry {character.name}, better luck next time!\n" + bcolors.RESET)
                except Exception as e:
                    print("\nAn error occurred when using the outlaw.", e,"\n")

                player_input = input()

                if player_input.lower() == "v":
                    try:
                        finished = False
                        if args.character:
                            print(f"\n{character.charactertype}: {character.characterdesc}\n")
                        print(
                            f"(1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                        )
                    except Exception as e:
                        print(f"Unable to view dice: {e}")

                #TODO: Change command
                if player_input.lower() == "a":
                    if not args.character:
                        print(f"\nSorry, character powers are not available this game! Run `bristol -c` for character powers!\n")
                    else:
                        if character.charactertype == "Mason":
                            try:
                                power_continue = input(f"{character.name}, would you like to use your Mason power? (y/n):")
                                if power_continue.lower() == "y":
                                    reroll1 = input("Select a die to reroll (1-6):")
                                    initial_roll.reroll(int(reroll1), None)
                                    print(
                                        f"Rerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                                    )
                                    game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                    game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                    game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                    game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                    game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                    game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                    getlock1 = input(f"Now select a dice to lock(1-6):")
                                    if getlock1 == "1":
                                        initial_roll.dice1_lock = True
                                    if getlock1 == "2":
                                        initial_roll.dice2_lock = True
                                    if getlock1 == "3":
                                        initial_roll.dice3_lock = True
                                    if getlock1 == "4":
                                        initial_roll.dice4_lock = True
                                    if getlock1 == "5":
                                        initial_roll.dice5_lock = True
                                    if getlock1 == "6":
                                        initial_roll.dice6_lock = True
                                    print(
                                        f"{character.name} has successfully locked dice {getlock1}!"
                                    )
                                    game.update_lock_symbol(int(getlock1), True, False)
                                    finished = True
                            except Exception as e:
                                print("\nAn error occurred when using the countess.", e,"\n")
                                finished = False 

                        elif character.charactertype == "Friar":
                            try:
                                power_continue = input(f"{character.name}, would you like to use your Friar power? (y/n):")
                                if power_continue.lower() == "y":
                                    reroll1 = input("Select a die to change (1-6):")
                                    roll_value_str = "1)" + Fore.CYAN + " Apple " + bcolors.RESET + " 2)" + Fore.CYAN + " Rat " + bcolors.RESET + "3)" + Fore.YELLOW + " Apple " + bcolors.RESET + "4)" + Fore.YELLOW + " Rat " + bcolors.RESET + "5)" + Fore.MAGENTA + Style.BRIGHT + " Apple " + bcolors.RESET + "6) " + Fore.MAGENTA + Style.BRIGHT + "Rat" + bcolors.RESET + ":"
                                    if int(reroll1) == 1:
                                        old = initial_roll.dice1_result
                                        print(f"What would you like to change die {initial_roll.dice1_result} to?:")
                                        chosen_val = input(roll_value_str)
                                        if (int(chosen_val)<= 6) and (int(chosen_val)>= 1):
                                            initial_roll.setdie(1,int(chosen_val))
                                            print(f"\n{old} -> {initial_roll.dice1_result}\n")
                                            game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                            finished = True
                                    elif int(reroll1) == 2:
                                        old = initial_roll.dice2_result
                                        print(f"What would you like to change die {initial_roll.dice2_result} to?:")
                                        chosen_val = input(roll_value_str)
                                        if (int(chosen_val)<= 6) and (int(chosen_val)>= 1):
                                            initial_roll.setdie(2,int(chosen_val))
                                            print(f"\n{old} -> {initial_roll.dice2_result}\n")
                                            game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                            finished = True
                                    elif int(reroll1) == 3:
                                        old = initial_roll.dice3_result
                                        print(f"What would you like to change die {initial_roll.dice3_result} to?:")
                                        chosen_val = input(roll_value_str)
                                        if (int(chosen_val)<= 6) and (int(chosen_val)>= 1):
                                            initial_roll.setdie(3,int(chosen_val))
                                            print(f"\n{old} -> {initial_roll.dice3_result}\n")
                                            game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                            finished = True
                                    elif int(reroll1) == 4:
                                        old = initial_roll.dice4_result
                                        print(f"What would you like to change die {initial_roll.dice4_result} to?:")
                                        chosen_val = input(roll_value_str)
                                        if (int(chosen_val)<= 6) and (int(chosen_val)>= 1):
                                            initial_roll.setdie(4,int(chosen_val))
                                            print(f"\n{old} -> {initial_roll.dice4_result}\n")
                                            game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                            finished = True
                                    elif int(reroll1) == 5:
                                        old = initial_roll.dice5_result
                                        print(f"What would you like to change die {initial_roll.dice5_result} to?:")
                                        chosen_val = input(roll_value_str)
                                        if (int(chosen_val)<= 6) and (int(chosen_val)>= 1):
                                            initial_roll.setdie(5,int(chosen_val))
                                            print(f"\n{old} -> {initial_roll.dice5_result}\n")
                                            game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                            finished = True
                                    elif int(reroll1) == 6:
                                        old = initial_roll.dice6_result
                                        print(f"What would you like to change die {initial_roll.dice2_result} to?:")
                                        chosen_val = input(roll_value_str)
                                        if (int(chosen_val)<= 6) and (int(chosen_val)>= 1):
                                            initial_roll.setdie(6,int(chosen_val))
                                            print(f"\n{old} -> {initial_roll.dice6_result}\n")
                                            game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                            finished = True
                            except Exception as e:
                                print("\nAn error occurred when using the friar.", e,"\n")
                                finished = False 

                        elif character.charactertype == "Rat King":
                            try:
                                power_continue = input(f"{character.name}, would you like to use your Rat King power? (y/n):")
                                if power_continue.lower() == "y":
                                    reroll1 = input("Select a die to change (1-6):")
                                    if int(reroll1) == 1:
                                        if int(initial_roll.dice1) == 1:
                                            initial_roll.setdie(1,2)
                                            print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                        elif int(initial_roll.dice1) == 3:
                                            initial_roll.setdie(1,4)
                                            print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                        elif int(initial_roll.dice1) == 5:
                                            initial_roll.setdie(1,6)
                                            print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                        else:
                                            print(f"{initial_roll.dice1_result} is already a rat!")

                                    elif int(reroll1) == 2:
                                        if int(initial_roll.dice2) == 1:
                                            initial_roll.setdie(2,2)
                                            print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                        elif int(initial_roll.dice2) == 3:
                                            initial_roll.setdie(2,4)
                                            print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                        elif int(initial_roll.dice2) == 5:
                                            initial_roll.setdie(2,6)
                                            print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                        else:
                                            print(f"{initial_roll.dice2_result} is already a rat!")

                                    elif int(reroll1) == 3:
                                        if int(initial_roll.dice3) == 1:
                                            initial_roll.setdie(3,2)
                                            print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                        elif int(initial_roll.dice3) == 3:
                                            initial_roll.setdie(3,4)
                                            print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                        elif int(initial_roll.dice3) == 5:
                                            initial_roll.setdie(3,6)
                                            print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                        else:
                                            print(f"{initial_roll.dice3_result} is already a rat!")

                                    elif int(reroll1) == 4:
                                        if int(initial_roll.dice4) == 1:
                                            initial_roll.setdie(4,2)
                                            print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                        elif int(initial_roll.dice4) == 3:
                                            initial_roll.setdie(4,4)
                                            print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                        elif int(initial_roll.dice4) == 5:
                                            initial_roll.setdie(4,6)
                                            print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                        else:
                                            print(f"{initial_roll.dice4_result} is already a rat!")

                                    elif int(reroll1) == 5:
                                        if int(initial_roll.dice5) == 1:
                                            initial_roll.setdie(5,2)
                                            print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                        elif int(initial_roll.dice5) == 3:
                                            initial_roll.setdie(5,4)
                                            print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                        elif int(initial_roll.dice5) == 5:
                                            initial_roll.setdie(5,6)
                                            print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                        else:
                                            print(f"{initial_roll.dice5_result} is already a rat!")

                                    elif int(reroll1) == 6:
                                        if int(initial_roll.dice6) == 1:
                                            initial_roll.setdie(6,2)
                                            print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                        elif int(initial_roll.dice6) == 3:
                                            initial_roll.setdie(6,4)
                                            print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                        elif int(initial_roll.dice6) == 5:
                                            initial_roll.setdie(6,6)
                                            print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                        else:
                                            print(f"{initial_roll.dice6_result} is already a rat!")

                                    finished = True
                                    reroll2 = input("Select a second die to change (1-6, n to cancel):")
                                    
                                    if reroll2 == "1":
                                        if int(initial_roll.dice1) == 1:
                                            initial_roll.setdie(1,2)
                                            print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                        elif int(initial_roll.dice1) == 3:
                                            initial_roll.setdie(1,4)
                                            print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                        elif int(initial_roll.dice1) == 5:
                                            initial_roll.setdie(1,6)
                                            print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                            game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                        else:
                                            print(f"{initial_roll.dice1_result} is already a rat!")
                                        finished = True

                                    elif reroll2 == "2":
                                            if int(initial_roll.dice2) == 1:
                                                initial_roll.setdie(2,2)
                                                print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                            elif int(initial_roll.dice2) == 3:
                                                initial_roll.setdie(2,4)
                                                print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                            elif int(initial_roll.dice2) == 5:
                                                initial_roll.setdie(2,6)
                                                print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                            else:
                                                print(f"{initial_roll.dice2_result} is already a rat!")
                                            finished = True

                                    elif reroll2 == "3":
                                            if int(initial_roll.dice3) == 1:
                                                initial_roll.setdie(3,2)
                                                print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                            elif int(initial_roll.dice3) == 3:
                                                initial_roll.setdie(3,4)
                                                print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                            elif int(initial_roll.dice3) == 5:
                                                initial_roll.setdie(3,6)
                                                print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                            else:
                                                print(f"{initial_roll.dice3_result} is already a rat!")
                                            finished = True

                                    elif reroll2 == "4":
                                            if int(initial_roll.dice4) == 1:
                                                initial_roll.setdie(4,2)
                                                print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                            elif int(initial_roll.dice4) == 3:
                                                initial_roll.setdie(4,4)
                                                print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                            elif int(initial_roll.dice4) == 5:
                                                initial_roll.setdie(4,6)
                                                print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                            else:
                                                print(f"{initial_roll.dice4_result} is already a rat!")
                                            finished = True

                                    elif reroll2 == "5":
                                            if int(initial_roll.dice5) == 1:
                                                initial_roll.setdie(5,2)
                                                print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                            elif int(initial_roll.dice5) == 3:
                                                initial_roll.setdie(5,4)
                                                print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                            elif int(initial_roll.dice5) == 5:
                                                initial_roll.setdie(5,6)
                                                print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                            else:
                                                print(f"{initial_roll.dice5_result} is already a rat!")
                                            finished = True

                                    elif reroll2 == "6":
                                            if int(initial_roll.dice6) == 1:
                                                initial_roll.setdie(6,2)
                                                print(f"\n" + Fore.CYAN + " Apple " + bcolors.RESET + "->" + Fore.CYAN + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                            elif int(initial_roll.dice6) == 3:
                                                initial_roll.setdie(6,4)
                                                print(f"\n" + Fore.YELLOW + " Apple " + bcolors.RESET + "->" + Fore.YELLOW + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                            elif int(initial_roll.dice6) == 5:
                                                initial_roll.setdie(6,6)
                                                print(f"\n" + Fore.MAGENTA + " Apple " + bcolors.RESET + "->" + Fore.MAGENTA + " Rat " + bcolors.RESET)
                                                game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                            else:
                                                print(f"{initial_roll.dice6_result} is already a rat!")
                                            finished = True
                                    else:
                                        finished = True
                            except Exception as e:
                                print("\nAn error occurred when using the rat king.", e,"\n")
                                finished = False 

                        #TODO: change drunk to change one other die into a rat. Still give yourself immunity.
                        elif character.charactertype == "Drunkard":
                            try:
                                power_continue = input(f"{character.name}, would you like to use your Drunkard power? (y/n):")
                                if power_continue.lower() == "y":
                                    character.setDrunk()
                                    print(f"\n{character.name} is drunk! 🍻🍺🥴 \n")
                                    carttype = character.getCart()
                                    reroll1 = input("Select the dice you want to ratify (1-6):")
                                    if reroll1 == "1":
                                        if carttype == 1:
                                            initial_roll.setdie(1,2)
                                        elif carttype == 2:
                                            initial_roll.setdie(1,4)
                                        elif carttype == 3:
                                            initial_roll.setdie(1,6)
                                        game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                    elif reroll1 == "2":
                                        if carttype == 1:
                                            initial_roll.setdie(2,2)
                                        elif carttype == 2:
                                            initial_roll.setdie(2,4)
                                        elif carttype == 3:
                                            initial_roll.setdie(2,6)
                                        game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                    elif reroll1 == "3":
                                        if carttype == 1:
                                            initial_roll.setdie(3,2)
                                        elif carttype == 2:
                                            initial_roll.setdie(3,4)
                                        elif carttype == 3:
                                            initial_roll.setdie(3,6)
                                        game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                    elif reroll1 == "4":
                                        if carttype == 1:
                                            initial_roll.setdie(4,2)
                                        elif carttype == 2:
                                            initial_roll.setdie(4,4)
                                        elif carttype == 3:
                                            initial_roll.setdie(4,6)
                                        game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                    elif reroll1 == "5":
                                        if carttype == 1:
                                            initial_roll.setdie(5,2)
                                        elif carttype == 2:
                                            initial_roll.setdie(5,4)
                                        elif carttype == 3:
                                            initial_roll.setdie(5,6)
                                        game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                    elif reroll1 == "6":
                                        if carttype == 1:
                                            initial_roll.setdie(6,2)
                                        elif carttype == 2:
                                            initial_roll.setdie(6,4)
                                        elif carttype == 3:
                                            initial_roll.setdie(6,6)
                                        game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                    finished = True
                            except Exception as e:
                                print("\nAn error occurred when using the drunkard.", e,"\n")
                                finished = False 

                        elif character.charactertype == "Sheriff":
                            try:
                                power_continue = input(f"{character.name}, would you like to use your Sheriff power? (y/n):")
                                if power_continue.lower() == "y":
                                    print("Who would you like to view symptoms of?")
                                    for i in range(len(list_of_characters)):
                                        print(f"{i}) {list_of_characters[i].name}")
                                    charInput = input()
                                    symptom_val = list_of_characters[int(charInput)].getStatus()
                                    symptom_desc = ""
                                    if symptom_val == 1:
                                        symptom_desc = "a headache"
                                    elif symptom_val == 2:
                                        symptom_desc = "the chills"
                                    elif symptom_val == 3:
                                        symptom_desc = "a cough"
                                    elif symptom_val == 4:
                                        symptom_desc == "buboes"
                                    if args.test:
                                        print(f"\n{list_of_characters[int(charInput)].name} has {symptom_desc} ({list_of_characters[int(charInput)].getStatus()})!\n")
                                    else:
                                        statement = f"\n{list_of_characters[int(charInput)].name} has {symptom_desc} ({list_of_characters[int(charInput)].getStatus()})!"
                                        send_remedy_message(
                                            name=character.name,
                                            phone_number=character.phone_number,
                                            remedy_statement=statement,
                                            account_sid=account_sid,
                                            auth_token=auth_token,
                                        )
                                    finished = True
                            except Exception as e:
                                print("\nAn error occurred when using the sheriff.", e,"\n")
                                finished = False 

                        elif character.charactertype == "Knight":
                            try:
                                power_continue = input(f"{character.name}, would you like to use your Knight power? (y/n):")
                                if power_continue.lower() == "y":
                                    print("\nPick a character:\n")
                                    for j in range(len(list_of_characters)):
                                        print(f"{j}) {list_of_characters[j].name}")
                                    knight_input = input()
                                    if list_of_characters[int(knight_input)].cart == 1:
                                        #position = Board.cart1.index(list_of_characters[int(knight_input)])
                                        board.knight_action(list_of_characters[int(knight_input)],1)
                                    elif list_of_characters[int(knight_input)].cart == 2:
                                        #position = Board.cart2.index(list_of_characters[int(knight_input)])
                                        board.knight_action(list_of_characters[int(knight_input)],2)
                                    elif list_of_characters[int(knight_input)].cart == 3:
                                        #position = Board.cart3.index(list_of_characters[int(knight_input)])
                                        board.knight_action(list_of_characters[int(knight_input)],3)
                                board.displayCarts(game, args)
                                finished = True

                                        
                            except Exception as e:
                                print("\nAn error occurred when using the knight.", e,"\n")
                                finished = False 
                    

                        elif character.charactertype == "Countess":
                            try:
                                power_continue = input(f"{character.name}, would you like to use your Countess power? (y/n):")
                                if power_continue.lower() == "y":
                                    tot = character.currentRemedyTotal
                                    if tot > 2:
                                        print(f"\nSorry {character.name}, you are unable to use your Countess ability, as you already have 3 remedies!\n")
                                        finished = False
                                    else:
                                        remedy1 = random.randint(1,5)
                                        remedy2 = random.randint(1,5)
                                        if args.test:
                                            print(f"You drew 1) {character.remedy_Dictionary[remedy1]} and 2) {character.remedy_Dictionary[remedy2]}. Which would you like to keep?")
                                        else:
                                            msg = f"You drew 1) {character.remedy_Dictionary[remedy1]} and 2) {character.remedy_Dictionary[remedy2]}. Which would you like to keep?"
                                            send_remedy_message(
                                                name=character.name,
                                                phone_number=character.phone_number,
                                                remedy_statement=msg,
                                                account_sid=account_sid,
                                                auth_token=auth_token,
                                            )
                                        countess_input = input()
                                        
                                        if int(countess_input) == 1:
                                            character.updateRemedy(tot, remedy1)
                                            remedy_message = f"You received the {character.remedy_Dictionary[remedy1]} remedy: {character.remedy_Description[remedy1]}"
                                            if not args.test:
                                                send_remedy_message(
                                                    name=character.name,
                                                    phone_number=character.phone_number,
                                                    remedy_statement=remedy_message,
                                                    account_sid=account_sid,
                                                    auth_token=auth_token,
                                                )
                                            else:
                                                print(remedy_message)
                                        else:
                                            character.updateRemedy(tot, remedy2)
                                            remedy_message = f"You received the {character.remedy_Dictionary[remedy2]} remedy: {character.remedy_Description[remedy2]}"
                                            if not args.test:
                                                send_remedy_message(
                                                    name=character.name,
                                                    phone_number=character.phone_number,
                                                    remedy_statement=remedy_message,
                                                    account_sid=account_sid,
                                                    auth_token=auth_token,
                                                )
                                            else:
                                                print(remedy_message)
                                        finished = True
                            except Exception as e:
                                print("\nAn error occurred when using the countess.", e,"\n")
                                finished = False 

                        elif character.charactertype == "Chandler":
                            print("\n Ms. Chanandeler Bong\n")
                            try:
                                power_continue = input(f"{character.name}, would you like to use your Chandler power? (y/n):")
                                if power_continue.lower() == "y":
                                    #Draw a random symptom
                                    symptom = random.randint(1,4)
                                    if args.test:
                                        print(f"{character.name}, you drew a {symptom}! You can keep it and replace with {character.status1} (1), replace with {character.status2} (2), or discard (3)")
                                    else:
                                        statement = f"{character.name}, you drew a {symptom}! You can keep it and replace with {character.status1} (1), replace with {character.status2} (2), or discard (3)"
                                        send_remedy_message(
                                            name=character.name,
                                            phone_number=character.phone_number,
                                            remedy_statement=statement,
                                            account_sid=account_sid,
                                            auth_token=auth_token,
                                        )
                                    chandler_in = input()
                                    if int(chandler_in) == 3:
                                        print("\nDiscarded!")
                                    else:
                                        character.setStatusCorn(int(chandler_in), symptom)
                                        character.updateStatement()
                                        if args.test:
                                            print(character.name, character.plague_statement)
                                        else:
                                            send_mingle_message(
                                                name=character.name,
                                                phone_number=character.phone_number,
                                                mingle_statement=character.plague_statement,
                                                account_sid=account_sid,
                                                auth_token=auth_token,
                                            )
                                finished = True
                            except Exception as e:
                                print("\nAn error occurred when using the chandler.", e,"\n")
                                finished = False         

                if player_input.lower() == "d":
                    if character.drawRemedy(args, account_sid, auth_token) == True:
                        finished = True
                    else:
                        finished = False

                if player_input.lower() == "m":
                    move_input = input(f"\nSelect a movement action: (E) Elbow, (J) Jump, (P) Push")
                    if move_input.lower() == "e":
                        if board.elbow(character, args.test, account_sid, auth_token) == True:
                            finished = True
                            board.displayCarts(game, args)
                        else:
                            finished = False

                    elif move_input.lower() == "j":
                        if board.jump(character, args.test, account_sid, auth_token) == True:
                            finished = True
                            board.displayCarts(game, args)
                        else:
                            finished = False

                    elif move_input.lower() == "p":
                        if board.push(character, args.test, account_sid, auth_token) == True:
                            finished = True
                            board.displayCarts(game, args)
                        else:
                            finished = False

                if player_input.lower() == "s":
                    finished = True

                if player_input.lower() == "u":
                    if not character.remedycard1:
                        print(f"\nSorry{character.name}, you don't have any remedy cards!")
                        finished = False
                    else:
                        remedy_input = input(f"\nSelect a remedy card to use: (A) Arsenic, (C) Crushed Emeralds, (T) Turkey")
                        if remedy_input.lower() == "t":
                            if character.hasTurkey():
                                print("\nGobble gobble\n")
                                # TODO: Have turkey unable to reroll locked arsenic dice. I'm too lazy to add that now
                                reroll1 = input("Select the first dice to reroll (1-6):")
                                reroll2 = input("Select the second dice to reroll (1-6):")
                                reroll3 = input("Select the second dice to reroll (1-6):")
                                reroll4 = input("Select the second dice to reroll (1-6):")
                                initial_roll.reroll(int(reroll1), int(reroll2))
                                initial_roll.reroll(int(reroll3), int(reroll4))
                                print(
                                    f"\nRerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}\n"
                                )
                                game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                character.removeCard(5, args.test, account_sid, auth_token)
                                finished = True
                            else:
                                print(
                                    f"\nSorry {character.name}, you don't appear to have a turkey!\n"
                                )
                                finished = False

                        elif remedy_input.lower() == "a":
                            if character.hasRemedies():
                                if character.hasArsenic():
                                    getlock1 = input(f"Get first dice to lock (1-6):")
                                    getlock2 = input(f"Get second dice to lock (1-6):")
                                    if getlock1 == "1" or getlock2 == "1":
                                        initial_roll.dice1_lock = True

                                    if getlock1 == "2" or getlock2 == "2":
                                        initial_roll.dice2_lock = True
                                    if getlock1 == "3" or getlock2 == "3":
                                        initial_roll.dice3_lock = True
                                    if getlock1 == "4" or getlock2 == "4":
                                        initial_roll.dice4_lock = True
                                    if getlock1 == "5" or getlock2 == "5":
                                        initial_roll.dice5_lock = True
                                    if getlock1 == "6" or getlock2 == "6":
                                        initial_roll.dice6_lock = True
                                    print(
                                        f"{character.name} has successfully locked dice {getlock1} and {getlock2}!"
                                    )
                                    print("cheese")
                                    print(getlock1, getlock2)
                                    game.update_lock_symbol(int(getlock1), True, False)
                                    game.update_lock_symbol(int(getlock2), True, False)
                                    character.removeCard(1, args.test, account_sid, auth_token)
                                    finished = False
                                else:
                                    print(
                                        f"\nSorry {character.name}, you don't appear to have any arsenic!\n"
                                    )
                                    finished = False

                            else:
                                print(
                                    f"\nSorry {character.name}, you don't appear to have any remedy cards!\n"
                                )
                                finished = False

                        elif remedy_input.lower() == "c":
                            if character.hasRemedies():
                                emerald_continue = input(
                                    f"Would you like to use an emerald for a free movement action? (y/n):"
                                )
                                if emerald_continue.lower() == "y":
                                    if character.hasEmerald():
                                        EmeraldAction(
                                            board=board,
                                            character=character,
                                            initial_roll=initial_roll,
                                            game=game,
                                            args=args,
                                            account_sid=account_sid, 
                                            auth_token=auth_token
                                        )
                                        character.removeCard(
                                            3, args.test, account_sid, auth_token
                                        )
                                        finished = False
                                    else:
                                        print(
                                            f"Nice try {character.name}! You don't have an emerald!"
                                        )
                                        finished = False

                            else:
                                print(f"{character.name} does not have any remedy cards!")
                                finished = False

                if player_input.lower() == "r":
                    rollpass = True
                    # Check if there are dice available to reroll
                    if (
                        (initial_roll.dice1_lock == True)
                        and (initial_roll.dice2_lock == True)
                        and (initial_roll.dice3_lock == True)
                        and (initial_roll.dice4_lock == True)
                        and (initial_roll.dice5_lock == True)
                        and (initial_roll.dice6_lock == True)
                    ):
                        print(f"There are no unlocked dice! Unable to reroll!")
                        rollpass = False
                        finished = False
                        break

                    if initial_roll.dice1_lock:
                        print(f"Dice 1 ({initial_roll.dice1_result}) is locked.")
                    if initial_roll.dice2_lock:
                        print(f"Dice 2 ({initial_roll.dice2_result}) is locked.")
                    if initial_roll.dice3_lock:
                        print(f"Dice 3 ({initial_roll.dice3_result}) is locked.")
                    if initial_roll.dice4_lock:
                        print(f"Dice 4 ({initial_roll.dice4_result}) is locked.")
                    if initial_roll.dice5_lock:
                        print(f"Dice 5 ({initial_roll.dice5_result}) is locked.")
                    if initial_roll.dice6_lock:
                        print(f"Dice 6 ({initial_roll.dice6_result}) is locked.")

                    reroll1 = input("Select the first dice to reroll (1-6):")
                    if reroll1.lower() != "b":
                        reroll2 = input("Select the second dice to reroll (1-6):")
                        if reroll2.lower() != "b":
                            if reroll2.lower() != "0":
                                # Checking dice for any locks
                                if (int(reroll1) == 1) or (int(reroll2) == 1):
                                    if initial_roll.dice1_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice1_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif (int(reroll1) == 2) or (int(reroll2) == 2):
                                    if initial_roll.dice2_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice2_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif (int(reroll1) == 3) or (int(reroll2) == 3):
                                    if initial_roll.dice3_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice3_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif (int(reroll1) == 4) or (int(reroll2) == 4):
                                    if initial_roll.dice4_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice4_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif (int(reroll1) == 5) or (int(reroll2) == 5):
                                    if initial_roll.dice5_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice5_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif (int(reroll1) == 6) or (int(reroll2) == 6):
                                    if initial_roll.dice6_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice6_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                else:
                                    rollpass = True

                                if rollpass:
                                    print(f"Rerolling dice {reroll1} and {reroll2}")
                                    initial_roll.reroll(int(reroll1), int(reroll2))
                                    print(
                                        f"Rerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                                    )
                                    game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                    game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                    game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                    game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                    game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                    game.update_dice_value(status=int(initial_roll.dice6),die_num=6)

                                    if character.hasRemedies():
                                        useChicken = input(
                                            f"Would you like to use a chicken to reroll these dice? (y/n):"
                                        )
                                        if useChicken.lower() == "y":
                                            if character.hasChicken():
                                                # Reroll up to 3 times
                                                print(
                                                    f"Rerolling dice {reroll1} and {reroll2}"
                                                )
                                                initial_roll.reroll(
                                                    int(reroll1), int(reroll2)
                                                )
                                                print(
                                                    f"Rerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                                                )
                                                game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                                game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                                game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                                game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                                game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                                game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                                useChicken2 = input(
                                                    f"Would you like to use a chicken to reroll these dice (2 rerolls remaining)? (y/n):"
                                                )
                                                if useChicken2.lower() == "y":
                                                    print(
                                                        f"Rerolling dice {reroll1} and {reroll2}"
                                                    )
                                                    initial_roll.reroll(
                                                        int(reroll1), int(reroll2)
                                                    )
                                                    print(
                                                        f"Rerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                                                    )
                                                    game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                                    game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                                    game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                                    game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                                    game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                                    game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                                    useChicken3 = input(
                                                        f"Would you like to use a chicken to reroll these dice (1 reroll remaining)? (y/n):"
                                                    )
                                                    if useChicken3.lower() == "y":
                                                        print(
                                                            f"Rerolling dice {reroll1} and {reroll2}"
                                                        )
                                                        initial_roll.reroll(
                                                            int(reroll1), int(reroll2)
                                                        )
                                                        print(
                                                            f"Rerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                                                        )
                                                        game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                                        game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                                        game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                                        game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                                        game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                                        game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                                character.removeCard(2, args.test, account_sid, auth_token)
                                                finished = True
                                            else:
                                                print(
                                                    f"\nSorry {character.name}, you don't appear to have a chicken remedy!"
                                                )
                                                finished = True
                                        else:
                                            finished = True
                                    else:
                                        finished = True
                                else:
                                    finished = False

                            else:
                                # Checking dice for any locks
                                if int(reroll1) == 1:
                                    if initial_roll.dice1_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice1_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif int(reroll1) == 2:
                                    if initial_roll.dice2_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice2_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif int(reroll1) == 3:
                                    if initial_roll.dice3_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice3_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif int(reroll1) == 4:
                                    if initial_roll.dice4_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice4_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif int(reroll1) == 5:
                                    if initial_roll.dice5_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice5_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                elif int(reroll1) == 6:
                                    if initial_roll.dice6_lock == True:
                                        print(
                                            f"Can't reroll {initial_roll.dice6_result}, as it has been locked this round with arsenic!"
                                        )
                                        finished = False
                                        rollpass = False
                                if rollpass:
                                    print(f"Rerolling dice {reroll1} and {reroll2}")
                                    initial_roll.reroll(int(reroll1), int(reroll2))
                                    print(
                                        f"Rerolled dice to: {initial_roll.dice1_result}, {initial_roll.dice2_result}, {initial_roll.dice3_result}, {initial_roll.dice4_result}, {initial_roll.dice5_result}, {initial_roll.dice6_result}"
                                    )
                                    game.update_dice_value(status=int(initial_roll.dice1),die_num=1)
                                    game.update_dice_value(status=int(initial_roll.dice2),die_num=2)
                                    game.update_dice_value(status=int(initial_roll.dice3),die_num=3)
                                    game.update_dice_value(status=int(initial_roll.dice4),die_num=4)
                                    game.update_dice_value(status=int(initial_roll.dice5),die_num=5)
                                    game.update_dice_value(status=int(initial_roll.dice6),die_num=6)
                                else:
                                    finished = False
        print("Everyone has taken a turn!")
        game.update_lock_symbol(1,False, True)
        game.update_lock_symbol(2,False, True)
        game.update_lock_symbol(3,False, True)
        game.update_lock_symbol(4,False, True)
        game.update_lock_symbol(5,False, True)
        game.update_lock_symbol(6,False, True)
        time.sleep(1)

        tingle_mingle = initial_roll.checkMingling()
        if len(tingle_mingle) == 0:
            print("No one is mingling! Very hygenic :)")
        else:
            time.sleep(1)
            for cart in tingle_mingle:
                board.mingle(cart, args, account_sid, auth_token)
        input("Press enter to continue into the cart movement phase.")
        print("\n-------------------")
        print("Cart Movement Phase")
        print("-------------------")

        time.sleep(0.5)
        initial_roll.moveCart(1, board)
        time.sleep(1)
        initial_roll.moveCart(2, board)
        time.sleep(1)
        initial_roll.moveCart(3, board)

        board.updateBoard(list_of_characters, game, args)
        cartorder = board.getCarOrder()
        if finalRound:
            if checkifVictorious(board, cartorder[0], game, args):
                gameOver = True
            else:
                if checkifVictorious(board, cartorder[1], game, args):
                    gameOver = True
                else:
                    if checkifVictorious(board, cartorder[2], game, args):
                        gameOver = True

        # Test if 17 spaces have been reached by a cart with at least one person on it.
        if (
            board.cart1_position >= args.finish
            and len(board.cart1) > 0
            and board.cart1_priority == 1
        ):
            finalRound = True
            if checkifVictorious(board, cartorder[0], game, args):
                gameOver = True
            else:
                if checkifVictorious(board, cartorder[1], game, args):
                    gameOver = True
                else:
                    if checkifVictorious(board, cartorder[2], game, args):
                        gameOver = True
        elif (
            board.cart2_position >= args.finish
            and len(board.cart2) > 0
            and board.cart2_priority == 1
        ):
            finalRound = True
            if checkifVictorious(board, cartorder[0], game, args):
                gameOver = True
            else:
                if checkifVictorious(board, cartorder[1], game, args):
                    gameOver = True
                else:
                    if checkifVictorious(board, cartorder[2], game, args):
                        gameOver = True
        elif (
            board.cart3_position >= args.finish
            and len(board.cart3) > 0
            and board.cart3_priority == 1
        ):
            finalRound = True
            if checkifVictorious(board, cartorder[0], game, args):
                gameOver = True
            else:
                if checkifVictorious(board, cartorder[1], game, args):
                    gameOver = True
                else:
                    if checkifVictorious(board, cartorder[2], game, args):
                        gameOver = True
        else:
            if finalRound:
                for character in list_of_characters:
                    print(character.name)
                print(
                    Fore.RED,
                    Style.BRIGHT
                    + f"You all failed to escape from Bristol, and have all perished from the plague :("
                    + bcolors.RESET,
                )
                input("Hit any button to exit the game")
                sys.exit(0)
            else:
                input("Press enter to move onto the next round.")


if __name__ == "__main__":
    main()
