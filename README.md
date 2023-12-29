# Bristol 1350
![](images/logo.png)
#### Disclaimer: This is not an official implementation!

[Bristol 1350](https://facadegames.com/products/bristol-1350) is a big hit in the Sweeten household, and we always play a few games during family get togethers. During the holiday season of 2023, I forgot to bring a copy of the game 🤦 This repo is the result of coding the game of Bristol so that the Sweeten household would have a Merry Christmas and a Happy New Year.

If you're unfamiliar with how to play, you can view the official [rules here](https://gamers-hq.de/media/pdf/60/66/e2/Bristol_PnP_Rules_1.pdf). Gameplay consists of a command line interpreter, which announces game updates and allows users to enter input commands, as well as a GUI showing the cart progress and dice rolling, rendered using [tkinter](https://docs.python.org/3/library/tkinter.html). Values that are kept secret from other players, such as symptoms and remedy cards, are sent via text message to all registered players mobile devices. This is done using [Twilio](https://login.twilio.com/u/signup?state=hKFo2SA4d09LV1BLM3lsNlFINXNfQU1oVWhzSFJ5Q1RnbGlNVaFur3VuaXZlcnNhbC1sb2dpbqN0aWTZIFptY1F6bmp6bVJ4UWw2TVRtemNkZk1TVktCZDF5TG9Vo2NpZNkgTW05M1lTTDVSclpmNzdobUlKZFI3QktZYjZPOXV1cks).

![Screenshot of the game](images/gui_screenshot.png)

# Installation
```
git clone https://github.com/alexsweeten/bristol1350.git
cd bristol1350
python -m pip install .
```

# Setup Twilio
In order to send text messages to users, you must have a functioning [Twilio account](https://login.twilio.com/u/signup?state=hKFo2SA4d09LV1BLM3lsNlFINXNfQU1oVWhzSFJ5Q1RnbGlNVaFur3VuaXZlcnNhbC1sb2dpbqN0aWTZIFptY1F6bmp6bVJ4UWw2TVRtemNkZk1TVktCZDF5TG9Vo2NpZNkgTW05M1lTTDVSclpmNzdobUlKZFI3QktZYjZPOXV1cks). As of December 2023, Twilio gives all new users $15 in free credits, enough for a bunch of free games.

Once registered for a Twilio account, you will need to add your Twilio account SID and authorization token into `registration.yml`:

```
twilio_info:
  account_sid: 'ACf734ACf73ACf73ACf73ACf73ACf73'
  auth_token: '432ed5c91432ed5c915432ed5c915432'
```

Finally, you will need to add each players name and phone number into `registration.yml`

```
registered_users:
  Player1: '5555555555'
  Player2: '6666666666'
```

# Play
To Play a game of Bristol, launch with `bristol -p`, followed by the name of each player participating (1-9 players supported)
```
bristol -p Player1 Player2 Player3 ...
```

To Play a test game that sends mingle and symptom information to the CLI instead of SMS messages, append `-t` (users will still need to be in `registration.yml`
```
bristol -p Player1 Player2 Player3 -t
```

You can adjust the length of the goal (ie. the number of spaces a cart has to move in order to exit the city) with the `-f` flag. Default is 17.
```
bristol -p Player1 Player2 Player3 -f 10.
```

# Rules
In Bristol 1350, you are a peasant trying to escape the city during the height of the Black Plague. You are randomly assigned into 1 of 3 carts and given two status conditions at the beginning of the game. If at any point in the game, your two status conditions total 6 or higher, you have the plague! During each turn, 6 dice will be rolled. Your cart will move a total number of spaces equal to the number of dice rolled matching your carts color. If you are in a cart where two of the matching dice are rats, that means your cart will mingle at the end of the turn. You want to keep mingling to a minimum, as it will increase your chances of developing the plague! You win if you escape Bristol plague-free. 

## Actions
- (R) Reroll Dice: You can reroll up to 2 dice.
- (P) Push: Push the last person in your cart off. 
- (E) Elbow: Elbow your way to the front of your cart.
- (J) Jump: Jump to the back of the next available cart.
- (D) Draw a remedy card. You start the game with 1, and can hold a maximum of 3 throughout the game:
    * Arsenic: Select two dice to lock. Use during the action phase.
    * Chicken: When rerolling dice, choose to reroll them up to 3 more times. Use during the action phase when rerolling two dice.
    * Crushed Emeralds: Take an extra movent action: Elbow (E), Push (P) or Jump (D). Use during the action phase.
    * Whip: Prevent someone from jumping into your cart, elbowing past you, or pushing you off your cart. Use reactively.
    * Turkey: Reroll 4 dice instead of the usual 2.
- (A) Use Arsenic
- (U) Use Crushed Emerald
- (T) Use Turkey
- (S) Skip your turn

# Known Bugs
- Carts can currently hold >3 people.
- In carts that die from the plague, one person ends up surviving.
