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

# Tkinter GUI
class BristolGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Bristol 1350")
        self.canvas = tk.Canvas(self.master, width=1400, height=600, bg="lightgray")
        self.canvas.pack()

        self.rectangle1 = self.canvas.create_rectangle(50, 50, 250, 150, fill="cyan")
        self.text_in_rectangle1 = self.canvas.create_text(
            100, 100, text="Lorem Ipsum", font=("Arial", 12), fill="black"
        )
        self.rectangle2 = self.canvas.create_rectangle(50, 200, 250, 300, fill="yellow")
        self.text_in_rectangle2 = self.canvas.create_text(
            100, 250, text="Lorem Ipsum", font=("Arial", 12), fill="black"
        )
        self.rectangle3 = self.canvas.create_rectangle(50, 350, 250, 450, fill="purple")
        self.text_in_rectangle3 = self.canvas.create_text(
            100, 400, text="Lorem Ipsum", font=("Arial", 12), fill="black"
        )

        self.finishline = self.canvas.create_rectangle(1200, 0, 1220, 600, fill="red")

    def update_rectangle_position(self, rectangle, amount):
        if rectangle == 1:
            self.canvas.coords(
                self.rectangle1, 50 + (amount * 50), 50, 250 + (amount * 50), 150
            )
            self.canvas.coords(self.text_in_rectangle1, 100 + (amount * 50), 100)
        elif rectangle == 2:
            self.canvas.coords(
                self.rectangle2, 50 + (amount * 50), 200, 250 + (amount * 50), 300
            )
            self.canvas.coords(self.text_in_rectangle2, 100 + (amount * 50), 250)
        elif rectangle == 3:
            self.canvas.coords(
                self.rectangle3, 50 + (amount * 50), 350, 250 + (amount * 50), 450
            )
            self.canvas.coords(self.text_in_rectangle3, 100 + (amount * 50), 400)

    def update_rectangle_txt(self, rectangle, txt):
        if rectangle == 1:
            self.canvas.itemconfig(self.text_in_rectangle1, text=txt)
        elif rectangle == 2:
            self.canvas.itemconfig(self.text_in_rectangle2, text=txt)
        elif rectangle == 3:
            self.canvas.itemconfig(self.text_in_rectangle3, text=txt)

    def update_finish_line(self, amount):
        self.canvas.coords(
            self.finishline, 220 + (amount * 50), 0, 240 + (amount * 50), 600
        )

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

    def reroll(self, index1, index2):
        tmp = False
        to_return = []
        while tmp == False:
            if index1 == index2:
                print("Select two different dice")
            else:
                tmp = True
        if index1 == 1:
            self.dice1 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice1)
        elif index1 == 2:
            self.dice2 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice2)
        elif index1 == 3:
            self.dice3 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice3)
        elif index1 == 4:
            self.dice4 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice4)
        elif index1 == 5:
            self.dice5 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice5)
        elif index1 == 6:
            self.dice6 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice6)

        if index2 == None:
            o = 9
        elif index2 == 1:
            self.dice1 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice1)
        elif index2 == 2:
            self.dice2 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice2)
        elif index2 == 3:
            self.dice3 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice3)
        elif index2 == 4:
            self.dice4 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice4)
        elif index2 == 5:
            self.dice5 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice5)
        elif index2 == 6:
            self.dice6 = random.randint(1, 6)
            self.updateResults()
            to_return.append(self.dice6)
        print(to_return)
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

    def push(self, character, txt):
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
                                self.cart1[-1].removeCard(4, txt)
                                return True
                            else:
                                print(
                                    f"Sorry {self.cart1[-1].name}, you don't appear to have a whip!"
                                )
                    print(
                        Fore.RED
                        + f"{character.name} has kicked out {self.cart1[-1].name}! Super rude in the nude!"
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
                                self.cart2[-1].removeCard(4, txt)
                                return True
                            else:
                                print(
                                    Fore.RED
                                    + f"Sorry {self.cart2[-1].name}, you don't appear to have a whip!"
                                )
                    print(
                        Fore.RED
                        + Style.BRIGHT
                        + f"{character.name} has kicked out {self.cart2[-1].name}! Super rude in the nude!"
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
                                    + f"{self.cart3[-1].name} uses a whip to prevent being pushed!"
                                    + bcolors.RESET
                                )
                                self.cart3[-1].removeCard(4, txt)
                                return True
                            else:
                                print(
                                    f"Sorry {self.cart3[-1].name}, you don't appear to have a whip!"
                                )

                    print(
                        Fore.RED
                        + Style.BRIGHT
                        + f"{character.name} has kicked out {self.cart3[-1].name}! Super rude in the nude!"
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

    def jump(self, character, txt):
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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
                                        booger.removeCard(4, txt)
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

    def elbow(self, character, txt):
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
                                    booger.removeCard(4, txt)
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
                                    booger.removeCard(4, txt)
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
                                    booger.removeCard(4, txt)
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
        supply = []
        new_supply = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4]
        random.shuffle(new_supply)
        if cart == 1:
            i = 0
            for character in self.cart1:
                supply.append(character.status1)
                supply.append(character.status2)
                i += 0
            # Shuffle cards, deal 2 to player
            supply.append(new_supply[i])
            random.shuffle(supply)

            for character in self.cart1:
                character.status1 = supply[-1]
                supply.pop(-1)
                character.status2 = supply[-1]
                supply.pop(-1)
                character.updateStatement()
                character.increaseMingleCount()
                if args.text:
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

        elif cart == 2:
            i = 0
            for character in self.cart2:
                supply.append(character.status1)
                supply.append(character.status2)
                i += 1
            # Shuffle cards, deal 2 to player
            supply.append(new_supply[i])
            random.shuffle(supply)

            for character in self.cart2:
                character.status1 = supply[-1]
                supply.pop(-1)
                character.status2 = supply[-1]
                supply.pop(-1)
                character.updateStatement()
                character.increaseMingleCount()
                if args.text:
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

        elif cart == 3:
            i = 0
            for character in self.cart3:
                supply.append(character.status1)
                supply.append(character.status2)
                i += 1
            # Shuffle cards, deal 2 to player
            supply.append(new_supply[i])
            random.shuffle(supply)
            for character in self.cart3:
                character.status1 = supply[-1]
                supply.pop(-1)
                character.status2 = supply[-1]
                supply.pop(-1)
                character.updateStatement()
                character.increaseMingleCount()
                if args.text:
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
        if txt:
            # TODO: used remedy text
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
        remedy_message = f"You recieved the {self.remedy_Dictionary[new_card]} remedy: {self.remedy_Description[new_card]}"
        remedy_message = remedy_message + f"\n\n {total_remedy_message}"
        if args.text:
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
        # TODO: remove
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

    parser.add_argument("-t", "--text", action="store_true", help="Play using text")
    parser.add_argument("-d", "--demo", action="store_true", help="Preset a demo game")
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
    parser.add_argument("-v", "--version", action="store_true", help="Show version")

    args = parser.parse_args()

    if args.version:
        print(f"Bristol 1350: v0.1.0")  # Replace with your actual version
        exit()

    return args


def introsequence(args, sid, token):
    registered_users = read_yaml_file(args.registered)["registered_users"]
    print(registered_users)
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
                print(f"{args.players[i]} is not registered!")
                sys.exit(6)
            list_of_characters.append("d")
            list_of_characters[i] = Character(
                name=args.players[i],
                phone_number=registered_users[args.players[i]],
            )
            list_of_characters[i].generateStartStatus(args)
            if args.text:
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


def EmeraldAction(board, character, initial_roll, game, args):
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
            if board.elbow(character, args.text) == True:
                finished = True
                board.displayCarts(game, args)
            else:
                finished = False

        if player_input.lower() == "j":
            if board.jump(character, args.text) == True:
                finished = True
                board.displayCarts(game, args)
            else:
                finished = False

        if player_input.lower() == "p":
            if board.push(character, args.text) == True:
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

        print(f"Rolling dice:")
        time.sleep(0.5)
        initial_roll = Dice()
        initial_roll.updateResults()
        print(
            f"(1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
        )

        for character in list_of_characters:
            finished = False
            while finished == False:
                print(
                    f"\nIt is {character.name}'s turn. What would {character.name} like to do?'"
                )
                player_input = input(
                    "(R) Reroll, (T) Use Turkey, (D) Draw Remedy, (A) Use Arsenic, (U) Use Emerald, (P) Push, (E) Elbow, (J) Jump, (S) Skip Turn, (V) View rolled dice:"
                )

                if player_input.lower() == "v":
                    finished = False
                    board.displayCarts(game, args)
                    print(
                        f"(1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                    )

                if player_input.lower() == "d":
                    if character.drawRemedy(args, account_sid, auth_token) == True:
                        finished = True
                    else:
                        finished = False

                if player_input.lower() == "u":
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
                                )
                                character.removeCard(
                                    3, args.text, account_sid, auth_token
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

                if player_input.lower() == "e":
                    if board.elbow(character, args.text) == True:
                        finished = True
                        board.displayCarts(game, args)
                    else:
                        finished = False

                if player_input.lower() == "j":
                    if board.jump(character, args.text) == True:
                        finished = True
                        board.displayCarts(game, args)
                    else:
                        finished = False

                if player_input.lower() == "p":
                    if board.push(character, args.text) == True:
                        finished = True
                        board.displayCarts(game, args)
                    else:
                        finished = False

                if player_input.lower() == "s":
                    finished = True

                if player_input.lower() == "t":
                    if character.hasTurkey():
                        print("\nGobble gobble\n")
                        # TODO: Hvae turkey unable to reroll locked arsenic dice. I'm too lazy to add that now
                        reroll1 = input("Select the first dice to reroll (1-6):")
                        reroll2 = input("Select the second dice to reroll (1-6):")
                        reroll3 = input("Select the second dice to reroll (1-6):")
                        reroll4 = input("Select the second dice to reroll (1-6):")
                        initial_roll.reroll(int(reroll1), int(reroll2))
                        initial_roll.reroll(int(reroll3), int(reroll4))
                        print(
                            f"Rerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                        )
                        character.removeCard(5, args.text)
                        finished = True
                    else:
                        print(
                            f"Sorry {character.name}, you don't appear to have a turkey!"
                        )
                        finished = False

                if player_input.lower() == "a":
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
                            character.removeCard(1, args.text)
                            finished = False
                        else:
                            print(
                                f"Sorry {character.name}, you don't appear to have any arsenic!"
                            )
                            finished = False

                    else:
                        print(
                            f"Sorry {character.name}, you don't appear to have any remedy cards!"
                        )
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
                                                character.removeCard(2, args.text)
                                                finished = True
                                            else:
                                                print(
                                                    f"Sorry {character.name}, you don't appear to have a chicken remedy!"
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
                                else:
                                    finished = False
        print("Everyone has taken a turn!")
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
