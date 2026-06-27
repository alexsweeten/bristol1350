import argparse
import contextlib
import html
import math
import os
import random
import sys

try:
    from colorama import Fore, Style
except ModuleNotFoundError:
    class _NoColor:
        def __getattr__(self, _):
            return ""

    Fore = _NoColor()
    Style = _NoColor()

from bristol.send_sms import (
    send_message,
    send_mingle_message,
    send_remedy_message,
    send_used_remedy_message,
)

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError as exc:
    tk = None
    filedialog = None
    TK_IMPORT_ERROR = exc
else:
    TK_IMPORT_ERROR = None

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

try:
    import toml
except ModuleNotFoundError:
    toml = None


MAX_PLAYERS = 9
VALID_DICE = set(range(1, 7))
SAMPLE_GAME_STATE_FILE = "game_state.txt"
SAMPLE_MAX_ROUNDS = 50
SAMPLE_PLAYER_POOL = [
    "Alice",
    "Ben",
    "Clara",
    "Diego",
    "Eve",
    "Finn",
    "Grace",
    "Hugo",
    "Iris",
]
MINGLE_SUPPLY = [1, 2, 3, 4]
MINGLE_DEFAULT_PROFILES = (
    ("1-3 players", 1, 3, (3, 2, 2, 3), "1_3_players"),
    ("4-6 players", 4, 6, (4, 3, 1, 2), "4_6_players"),
    ("7-9 players", 7, 9, (4, 3, 2, 1), "7_9_players"),
)
MINGLE_SIM_TRIALS = 10_000
MINGLE_SIM_MAX_CART_SIZE = 3
CART_CAPACITY = 3
MINGLE_SIM_BASE_CART_MINGLE_COUNTS = (1, 2, 3, 4, 5, 6)
MINGLE_SIM_SWITCH_EXISTING_PRIOR_MINGLES = (1, 2, 3, 4)
MINGLE_SIM_SWITCH_PRIOR_MINGLES = (0, 1, 2, 3, 4)
MINGLE_BASE_GRAPH_FILE = "mingle_base_cart.svg"
MINGLE_SWITCH_GRAPH_FILE = "mingle_switch_in.svg"
GRAPH_COLORS = (
    "#0f766e",
    "#b45309",
    "#7c3aed",
    "#dc2626",
    "#2563eb",
    "#4d7c0f",
)
CART_LABELS = {
    1: "blue cart",
    2: "yellow cart",
    3: "purple cart",
}
CHARACTER_TYPES = {
    "Sheriff": "You can view 1 symptom of a player on a different cart.",
    "Friar": "You can change 1 die to be exactly what you want.",
    "Outlaw": "You have a 1/3 chance of gaining a free remedy card (happens automatically at the start of your turn).",
    "Mason": "You can reroll 1 die, then lock one die.",
    "Chandler": "You can draw a random symptom and choose to replace it with one of your own.",
    "Countess": "You can draw 2 remedies and keep 1 of them.",
    "Drunkard": "You can turn 1 die into a rat of your current cart color. You are also immune from mingling whenever you use this.",
    "Rat King": "You can replace up to two apple dice with a rat of the same cart color.",
    "Knight": "You can move any player up to the front of their current cart.",
}


def cart_label(cart_num):
    return CART_LABELS.get(cart_num, f"cart {cart_num}")


def format_name_list(characters):
    names = [character.name for character in characters]
    if not names:
        return "no one"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def dice_results_for_log(roll, dice):
    return ", ".join(
        f"die {die_num}={getattr(roll, f'dice{die_num}_result')}"
        for die_num in dice
    )


def remedy_count_text(count):
    card_word = "card" if count == 1 else "cards"
    return f"{count} remedy {card_word}"


def default_mingle_profile_for_player_count(player_count):
    for label, minimum, maximum, odds, suffix in MINGLE_DEFAULT_PROFILES:
        if minimum <= player_count <= maximum:
            return label, odds, suffix

    raise ValueError(f"Bristol supports 1-{MAX_PLAYERS} players.")


def mingle_odds_from_args(args, player_count=None):
    custom_odds = getattr(args, "mingle_odds", None)
    if custom_odds is not None:
        return custom_odds

    if player_count is None:
        players = getattr(args, "players", None)
        if players:
            player_count = len(players)

    if player_count is None:
        player_count = MINGLE_DEFAULT_PROFILES[0][1]

    _, odds, _ = default_mingle_profile_for_player_count(player_count)
    return odds


def mingle_profiles_from_args(args):
    custom_odds = getattr(args, "mingle_odds", None)
    if custom_odds is not None:
        return [("custom odds", custom_odds, "custom")]

    if args.players:
        label, odds, suffix = default_mingle_profile_for_player_count(len(args.players))
        return [(label, odds, suffix)]

    return [
        (label, odds, suffix)
        for label, _minimum, _maximum, odds, suffix in MINGLE_DEFAULT_PROFILES
    ]


def format_mingle_odds(odds):
    return ", ".join(str(odd) for odd in odds)


def generate_mingle_symptoms(mingle_odds=None):
    if mingle_odds is None:
        mingle_odds = MINGLE_DEFAULT_PROFILES[0][3]
    return random.choices(MINGLE_SUPPLY, weights=mingle_odds, k=2)

# Tkinter GUI
class BristolGame:
    WIDTH = 1400
    HEIGHT = 900
    MAIN_WIDTH = 1060
    SIDEBAR_X = 1080
    ORDER_PANEL_BOTTOM = int(HEIGHT * 0.75)
    TRACK_START_X = 125
    TRACK_SCALE = 42
    CART_WIDTH = 185
    CART_HEIGHT = 112
    ACTION_LOG_LIMIT = 30
    CART_STYLES = {
        1: {
            "name": "Blue cart",
            "lane_y": 190,
            "fill": "#19c7d5",
            "light": "#78e7ee",
            "dark": "#0e7490",
            "road": "#8f8980",
        },
        2: {
            "name": "Yellow cart",
            "lane_y": 375,
            "fill": "#facc15",
            "light": "#fde68a",
            "dark": "#a16207",
            "road": "#978d73",
        },
        3: {
            "name": "Purple cart",
            "lane_y": 560,
            "fill": "#f9a8d4",
            "light": "#fbcfe8",
            "dark": "#be185d",
            "road": "#917b84",
        },
    }
    DICE_STATUS = {
        1: (1, "apple"),
        2: (1, "rat"),
        3: (2, "apple"),
        4: (2, "rat"),
        5: (3, "apple"),
        6: (3, "rat"),
    }

    def __init__(self, master):
        self.master = master
        self.master.title("Bristol 1350")
        self.canvas = tk.Canvas(
            self.master,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg="#d8e2cf",
            highlightthickness=0,
        )
        self.canvas.pack()

        self.finish_x = self.position_to_x(17)
        self.cart_positions = {1: 1, 2: 1, 3: 1}
        self.cart_status_text = {1: "1/17", 2: "1/17", 3: "1/17"}
        self.cart_player_text = {1: "", 2: "", 3: ""}
        self.cart_items = {1: [], 2: [], 3: []}
        self.dice_faces = {}
        self.dice_icon_items = {die_num: [] for die_num in range(1, 7)}
        self.lock_badges = {}
        self.lock_texts = {}
        self.order_items = []
        self.action_log = []
        self.action_log_items = []

        self.draw_scene()
        self.draw_sidebar()
        self.draw_dice_tray()
        self.draw_finish_line()
        for cart_num in (1, 2, 3):
            self.redraw_cart(cart_num)
        self.refresh()

    def refresh(self):
        try:
            self.master.update_idletasks()
            self.master.update()
        except tk.TclError:
            print("The Tkinter GUI was closed.")
            sys.exit(0)

    def position_to_x(self, amount):
        return self.TRACK_START_X + (amount * self.TRACK_SCALE)

    def draw_scene(self):
        self.canvas.create_rectangle(
            0, 0, self.MAIN_WIDTH, self.HEIGHT, fill="#d9e7cf", outline=""
        )
        self.canvas.create_rectangle(
            0, 660, self.MAIN_WIDTH, self.HEIGHT, fill="#b7c995", outline=""
        )

        for cart_num, style in self.CART_STYLES.items():
            lane_y = style["lane_y"]
            self.canvas.create_rectangle(
                85,
                lane_y - 58,
                self.MAIN_WIDTH - 35,
                lane_y + 58,
                fill=style["road"],
                outline="#6f675e",
                width=2,
            )
            for offset in (-30, 0, 30):
                self.canvas.create_line(
                    95,
                    lane_y + offset,
                    self.MAIN_WIDTH - 45,
                    lane_y + offset,
                    fill="#b8b0a5",
                    width=1,
                    dash=(10, 18),
                )
            self.canvas.create_text(
                35,
                lane_y,
                text=str(cart_num),
                font=("Arial", 18, "bold"),
                fill="#f8fafc",
            )

        self.draw_city_wall()
        self.canvas.create_text(
            515,
            38,
            text="Road out of Bristol",
            font=("Arial", 24, "bold"),
            fill="#263228",
        )

    def draw_city_wall(self):
        self.canvas.create_rectangle(
            0, 85, 100, 635, fill="#75695f", outline="#4b423b", width=2
        )
        for tower_y in (85, 270, 455):
            self.canvas.create_rectangle(
                15, tower_y - 28, 83, tower_y + 35, fill="#8b7c70", outline="#4b423b"
            )
            for notch_x in (15, 38, 61):
                self.canvas.create_rectangle(
                    notch_x,
                    tower_y - 44,
                    notch_x + 18,
                    tower_y - 28,
                    fill="#8b7c70",
                    outline="#4b423b",
                )

        for style in self.CART_STYLES.values():
            lane_y = style["lane_y"]
            self.canvas.create_arc(
                28,
                lane_y - 45,
                98,
                lane_y + 45,
                start=0,
                extent=180,
                fill="#2f2a25",
                outline="#2f2a25",
            )
            self.canvas.create_rectangle(
                28, lane_y, 98, lane_y + 45, fill="#2f2a25", outline="#2f2a25"
            )
        self.canvas.create_text(
            50,
            690,
            text="BRISTOL",
            angle=90,
            font=("Arial", 16, "bold"),
            fill="#3b332d",
        )

    def draw_sidebar(self):
        self.canvas.create_rectangle(
            self.SIDEBAR_X,
            0,
            self.WIDTH,
            self.HEIGHT,
            fill="#eadfc7",
            outline="#b8a887",
            width=2,
        )
        self.canvas.create_rectangle(
            self.SIDEBAR_X + 25,
            38,
            self.WIDTH - 25,
            self.ORDER_PANEL_BOTTOM - 12,
            fill="#f8f0db",
            outline="#c2ad7d",
            width=2,
        )
        self.canvas.create_text(
            self.SIDEBAR_X + 55,
            72,
            text="Turn Order",
            anchor="w",
            font=("Arial", 24, "bold"),
            fill="#332b20",
        )
        self.canvas.create_rectangle(
            self.SIDEBAR_X + 25,
            self.ORDER_PANEL_BOTTOM + 10,
            self.WIDTH - 25,
            self.HEIGHT - 35,
            fill="#fff7e6",
            outline="#c2ad7d",
            width=2,
        )
        self.canvas.create_text(
            self.SIDEBAR_X + 55,
            self.ORDER_PANEL_BOTTOM + 43,
            text="Action Log",
            anchor="w",
            font=("Arial", 22, "bold"),
            fill="#332b20",
        )
        self.redraw_action_log()

    def update_order(self, list_of_characters, current_character=None):
        for item in self.order_items:
            self.canvas.delete(item)
        self.order_items = []

        current_name = getattr(current_character, "name", current_character)
        has_character_icons = any(
            getattr(character, "charactertype", None)
            for character in list_of_characters
        )
        order_top = 115
        order_bottom = self.ORDER_PANEL_BOTTOM - 28
        available_height = max(order_bottom - order_top, 1)
        row_count = max(len(list_of_characters), 1)
        if has_character_icons:
            row_height = min(76, max(58, available_height // row_count))
        else:
            row_height = min(34, max(26, available_height // row_count))
        start_x = self.SIDEBAR_X + 42
        start_y = order_top

        for index, character in enumerate(list_of_characters, 1):
            row_y = start_y + (index - 1) * row_height
            is_current = character is current_character or character.name == current_name
            if has_character_icons and getattr(character, "charactertype", None):
                self.draw_turn_order_character_row(
                    index,
                    character,
                    start_x,
                    row_y,
                    row_height,
                    is_current=is_current,
                )
            else:
                if is_current:
                    self.order_items.append(
                        self.canvas.create_rectangle(
                            start_x - 10,
                            row_y - 4,
                            self.WIDTH - 38,
                            row_y + 28,
                            fill="#d8f5c7",
                            outline="#2f7d32",
                            width=2,
                        )
                    )
                self.order_items.append(
                    self.canvas.create_text(
                        start_x,
                        row_y,
                        text=f"{index}. {character.name}",
                        anchor="nw",
                        font=("Arial", 17, "bold"),
                        fill="#14532d" if is_current else "#1f2933",
                    )
                )
        self.refresh()

    def redraw_action_log(self):
        for item in self.action_log_items:
            self.canvas.delete(item)
        self.action_log_items = []

        x = self.SIDEBAR_X + 48
        y = self.ORDER_PANEL_BOTTOM + 74
        bottom = self.HEIGHT - 50
        text_width = self.WIDTH - self.SIDEBAR_X - 92
        visible_messages = self.action_log[-self.ACTION_LOG_LIMIT :]

        if not visible_messages:
            self.action_log_items.append(
                self.canvas.create_text(
                    x,
                    y,
                    text="No actions yet.",
                    anchor="nw",
                    font=("Arial", 15, "bold"),
                    fill="#7c6a48",
                    width=text_width,
                )
            )
            return

        for message in reversed(visible_messages):
            item = self.canvas.create_text(
                x,
                y,
                text=f"- {message}",
                anchor="nw",
                font=("Arial", 15, "bold"),
                fill="#1f2933",
                width=text_width,
            )
            bbox = self.canvas.bbox(item)
            if bbox and bbox[3] > bottom:
                self.canvas.delete(item)
                break

            self.action_log_items.append(item)
            y = (bbox[3] if bbox else y + 24) + 7

    def log_action(self, message):
        message = " ".join(str(message).split())
        if not message:
            return

        self.action_log.append(message)
        self.action_log = self.action_log[-self.ACTION_LOG_LIMIT :]
        self.redraw_action_log()
        self.refresh()

    def draw_turn_order_character_row(
        self, index, character, x, y, row_height, is_current=False
    ):
        row_width = 270
        card_height = max(50, min(68, row_height - 6))
        self.order_items.append(
            self.canvas.create_rectangle(
                x - 10,
                y - 4,
                x + row_width,
                y + card_height,
                fill="#d8f5c7" if is_current else "#fff7e6",
                outline="#2f7d32" if is_current else "#d6b56d",
                width=2 if is_current else 1,
            )
        )
        self.draw_character_icon(character.charactertype, x + 22, y + 25)
        self.order_items.append(
            self.canvas.create_text(
                x + 54,
                y + 3,
                text=f"{index}. {character.name} - {character.charactertype}",
                anchor="nw",
                font=("Arial", 10, "bold"),
                fill="#1f2933",
                width=205,
            )
        )
        self.order_items.append(
            self.canvas.create_text(
                x + 54,
                y + 22,
                text=character.characterdesc or "",
                anchor="nw",
                font=("Arial", 8),
                fill="#4b5563",
                width=205,
            )
        )

    def draw_character_icon(self, character_type, cx, cy):
        icon_drawers = {
            "Sheriff": self.draw_sheriff_icon,
            "Friar": self.draw_friar_icon,
            "Outlaw": self.draw_outlaw_icon,
            "Mason": self.draw_mason_icon,
            "Chandler": self.draw_chandler_icon,
            "Countess": self.draw_countess_icon,
            "Drunkard": self.draw_drunkard_icon,
            "Rat King": self.draw_rat_king_icon,
            "Knight": self.draw_knight_icon,
        }
        drawer = icon_drawers.get(character_type, self.draw_unknown_character_icon)
        drawer(cx, cy)

    def add_order_item(self, item):
        self.order_items.append(item)
        return item

    def draw_sheriff_icon(self, cx, cy):
        points = []
        for point in range(10):
            radius = 20 if point % 2 == 0 else 10
            angle = math.radians(-90 + point * 36)
            points.extend((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
        self.add_order_item(
            self.canvas.create_polygon(
                points, fill="#facc15", outline="#92400e", width=2
            )
        )
        self.add_order_item(
            self.canvas.create_oval(
                cx - 8, cy - 8, cx + 8, cy + 8, fill="#fde68a", outline="#92400e"
            )
        )

    def draw_friar_icon(self, cx, cy):
        self.add_order_item(
            self.canvas.create_oval(
                cx - 14, cy - 20, cx + 14, cy + 8, fill="#f3d6a4", outline="#8b5e34"
            )
        )
        self.add_order_item(
            self.canvas.create_arc(
                cx - 22,
                cy - 25,
                cx + 22,
                cy + 23,
                start=20,
                extent=320,
                style=tk.ARC,
                outline="#5b3418",
                width=8,
            )
        )
        self.add_order_item(
            self.canvas.create_polygon(
                cx - 20,
                cy + 18,
                cx + 20,
                cy + 18,
                cx + 11,
                cy - 2,
                cx - 11,
                cy - 2,
                fill="#7c4a24",
                outline="#4a2a12",
            )
        )

    def draw_outlaw_icon(self, cx, cy):
        self.add_order_item(
            self.canvas.create_oval(
                cx - 15, cy - 13, cx + 15, cy + 17, fill="#d7b38c", outline="#4b2f20"
            )
        )
        self.add_order_item(
            self.canvas.create_rectangle(
                cx - 22, cy - 4, cx + 22, cy + 7, fill="#111827", outline="#111827"
            )
        )
        self.add_order_item(
            self.canvas.create_arc(
                cx - 24,
                cy - 30,
                cx + 24,
                cy + 6,
                start=0,
                extent=180,
                fill="#2f241c",
                outline="#111827",
            )
        )
        self.add_order_item(
            self.canvas.create_rectangle(
                cx - 30, cy - 12, cx + 30, cy - 5, fill="#2f241c", outline="#111827"
            )
        )
        for eye_x in (cx - 7, cx + 7):
            self.add_order_item(
                self.canvas.create_oval(
                    eye_x - 2, cy, eye_x + 2, cy + 4, fill="#f8fafc", outline=""
                )
            )

    def draw_mason_icon(self, cx, cy):
        brick_fill = "#b45309"
        for row in range(3):
            y = cy - 18 + row * 12
            offset = 0 if row % 2 == 0 else 8
            for col in range(3):
                x = cx - 24 + col * 16 + offset
                self.add_order_item(
                    self.canvas.create_rectangle(
                        x, y, x + 15, y + 10, fill=brick_fill, outline="#7c2d12"
                    )
                )
        self.add_order_item(
            self.canvas.create_line(
                cx - 17, cy + 22, cx + 20, cy - 15, fill="#374151", width=3
            )
        )
        self.add_order_item(
            self.canvas.create_polygon(
                cx + 11,
                cy - 23,
                cx + 29,
                cy - 17,
                cx + 18,
                cy - 7,
                fill="#9ca3af",
                outline="#374151",
            )
        )

    def draw_chandler_icon(self, cx, cy):
        self.add_order_item(
            self.canvas.create_rectangle(
                cx - 8, cy - 5, cx + 8, cy + 23, fill="#fef3c7", outline="#92400e"
            )
        )
        self.add_order_item(
            self.canvas.create_oval(
                cx - 9, cy + 17, cx + 9, cy + 27, fill="#fbbf24", outline="#92400e"
            )
        )
        self.add_order_item(
            self.canvas.create_polygon(
                cx,
                cy - 26,
                cx + 12,
                cy - 7,
                cx,
                cy + 1,
                cx - 10,
                cy - 8,
                fill="#f97316",
                outline="#9a3412",
            )
        )
        self.add_order_item(
            self.canvas.create_polygon(
                cx,
                cy - 18,
                cx + 5,
                cy - 7,
                cx,
                cy - 3,
                cx - 4,
                cy - 8,
                fill="#fef08a",
                outline="",
            )
        )

    def draw_countess_icon(self, cx, cy):
        self.add_order_item(
            self.canvas.create_oval(
                cx - 13, cy - 5, cx + 13, cy + 20, fill="#f2c6a0", outline="#7c2d12"
            )
        )
        self.add_order_item(
            self.canvas.create_polygon(
                cx - 22,
                cy - 12,
                cx - 12,
                cy - 28,
                cx,
                cy - 12,
                cx + 12,
                cy - 28,
                cx + 22,
                cy - 12,
                fill="#facc15",
                outline="#92400e",
                width=2,
            )
        )
        self.add_order_item(
            self.canvas.create_arc(
                cx - 28,
                cy + 3,
                cx + 28,
                cy + 34,
                start=20,
                extent=140,
                fill="#7c3aed",
                outline="#4c1d95",
            )
        )

    def draw_drunkard_icon(self, cx, cy):
        self.add_order_item(
            self.canvas.create_rectangle(
                cx - 19, cy - 15, cx + 12, cy + 19, fill="#d6a157", outline="#78350f", width=2
            )
        )
        self.add_order_item(
            self.canvas.create_rectangle(
                cx - 15, cy - 10, cx + 8, cy + 15, fill="#fbbf24", outline=""
            )
        )
        self.add_order_item(
            self.canvas.create_arc(
                cx + 4,
                cy - 8,
                cx + 28,
                cy + 16,
                start=-80,
                extent=170,
                style=tk.ARC,
                outline="#78350f",
                width=5,
            )
        )
        for foam_x, foam_y in ((cx - 14, cy - 20), (cx - 4, cy - 23), (cx + 7, cy - 19)):
            self.add_order_item(
                self.canvas.create_oval(
                    foam_x - 6, foam_y - 5, foam_x + 6, foam_y + 5, fill="#fff7ed", outline="#d6d3d1"
                )
            )

    def draw_rat_king_icon(self, cx, cy):
        self.add_order_item(
            self.canvas.create_oval(
                cx - 21, cy - 9, cx + 18, cy + 20, fill="#6b7280", outline="#374151", width=2
            )
        )
        self.add_order_item(
            self.canvas.create_oval(
                cx - 18, cy - 18, cx - 6, cy - 6, fill="#9ca3af", outline="#374151"
            )
        )
        self.add_order_item(
            self.canvas.create_oval(
                cx + 4, cy - 18, cx + 16, cy - 6, fill="#9ca3af", outline="#374151"
            )
        )
        self.add_order_item(
            self.canvas.create_polygon(
                cx - 18,
                cy - 20,
                cx - 8,
                cy - 33,
                cx,
                cy - 20,
                cx + 8,
                cy - 33,
                cx + 18,
                cy - 20,
                fill="#facc15",
                outline="#92400e",
            )
        )
        self.add_order_item(
            self.canvas.create_oval(cx - 8, cy + 1, cx - 4, cy + 5, fill="#111827", outline="")
        )
        self.add_order_item(
            self.canvas.create_oval(cx + 6, cy + 1, cx + 10, cy + 5, fill="#111827", outline="")
        )
        self.add_order_item(
            self.canvas.create_oval(cx, cy + 9, cx + 6, cy + 14, fill="#f3a4a4", outline="#7f1d1d")
        )

    def draw_knight_icon(self, cx, cy):
        self.add_order_item(
            self.canvas.create_polygon(
                cx - 17,
                cy - 14,
                cx + 17,
                cy - 14,
                cx + 14,
                cy + 19,
                cx,
                cy + 29,
                cx - 14,
                cy + 19,
                fill="#94a3b8",
                outline="#334155",
                width=2,
            )
        )
        self.add_order_item(
            self.canvas.create_arc(
                cx - 20,
                cy - 32,
                cx + 20,
                cy + 3,
                start=0,
                extent=180,
                fill="#cbd5e1",
                outline="#334155",
                width=2,
            )
        )
        self.add_order_item(
            self.canvas.create_rectangle(
                cx - 18, cy - 14, cx + 18, cy - 3, fill="#64748b", outline="#334155"
            )
        )
        self.add_order_item(
            self.canvas.create_line(
                cx + 25, cy + 24, cx + 25, cy - 28, fill="#334155", width=3
            )
        )
        self.add_order_item(
            self.canvas.create_polygon(
                cx + 25,
                cy - 36,
                cx + 31,
                cy - 27,
                cx + 19,
                cy - 27,
                fill="#e5e7eb",
                outline="#334155",
            )
        )

    def draw_unknown_character_icon(self, cx, cy):
        self.add_order_item(
            self.canvas.create_oval(
                cx - 20, cy - 20, cx + 20, cy + 20, fill="#e5e7eb", outline="#6b7280"
            )
        )
        self.add_order_item(
            self.canvas.create_text(
                cx, cy, text="?", font=("Arial", 18, "bold"), fill="#374151"
            )
        )

    def update_rectangle_position(self, rectangle, amount):
        if rectangle in self.cart_positions:
            self.cart_positions[rectangle] = amount
            self.redraw_cart(rectangle)
        self.refresh()

    def update_rectangle_txt(self, rectangle, txt):
        if rectangle in self.cart_player_text:
            self.cart_status_text[rectangle], self.cart_player_text[rectangle] = (
                self.format_cart_text(txt)
            )
            self.redraw_cart(rectangle)
        self.refresh()

    def update_finish_line(self, amount):
        self.finish_x = self.position_to_x(amount)
        self.draw_finish_line()
        self.refresh()

    def update_lock_symbol(self, die_num, lock, busy):
        if die_num not in self.lock_texts:
            return
        if lock:
            label = "LOCK"
            fill = "#fecaca"
            outline = "#991b1b"
        elif busy:
            label = "ROLL"
            fill = "#fde68a"
            outline = "#92400e"
        else:
            label = "OK"
            fill = "#bbf7d0"
            outline = "#166534"
        self.canvas.itemconfig(self.lock_badges[die_num], fill=fill, outline=outline)
        self.canvas.itemconfig(self.lock_texts[die_num], text=label, fill=outline)
        self.refresh()

    def update_dice_value(self, status, die_num):
        if die_num not in self.dice_faces or status not in self.DICE_STATUS:
            return

        cart_num, icon = self.DICE_STATUS[status]
        style = self.CART_STYLES[cart_num]
        self.canvas.itemconfig(self.dice_faces[die_num], fill=style["light"])
        self.clear_die_icon(die_num)

        cx, cy = self.die_center(die_num)
        if icon == "apple":
            self.draw_apple_icon(die_num, cx, cy, 1.0)
        else:
            self.draw_rat_icon(die_num, cx, cy, 1.0)
        self.refresh()

    def format_cart_text(self, txt):
        lines = [line.strip() for line in txt.splitlines() if line.strip()]
        if not lines:
            return "", ""
        return lines[0], "\n".join(lines[1:])

    def redraw_cart(self, cart_num):
        for item in self.cart_items[cart_num]:
            self.canvas.delete(item)
        self.cart_items[cart_num] = []

        style = self.CART_STYLES[cart_num]
        x = self.position_to_x(self.cart_positions[cart_num])
        y = style["lane_y"] - (self.CART_HEIGHT / 2)
        items = self.cart_items[cart_num]

        items.append(
            self.canvas.create_oval(
                x + 18,
                y + 86,
                x + self.CART_WIDTH - 18,
                y + 118,
                fill="#000000",
                outline="",
                stipple="gray50",
            )
        )
        items.append(
            self.canvas.create_line(
                x - 28,
                y + 74,
                x + 12,
                y + 74,
                fill="#4a3322",
                width=4,
            )
        )
        items.append(
            self.canvas.create_polygon(
                x + 12,
                y + 42,
                x + self.CART_WIDTH - 16,
                y + 42,
                x + self.CART_WIDTH - 32,
                y + 90,
                x + 24,
                y + 90,
                fill=style["fill"],
                outline=style["dark"],
                width=3,
            )
        )
        items.append(
            self.canvas.create_rectangle(
                x + 42,
                y + 16,
                x + self.CART_WIDTH - 42,
                y + 45,
                fill=style["light"],
                outline=style["dark"],
                width=2,
            )
        )
        for post_x in (x + 54, x + self.CART_WIDTH - 54):
            items.append(
                self.canvas.create_line(
                    post_x, y + 18, post_x, y + 88, fill=style["dark"], width=3
                )
            )
        for wheel_x in (x + 48, x + self.CART_WIDTH - 52):
            items.append(
                self.canvas.create_oval(
                    wheel_x - 18,
                    y + 76,
                    wheel_x + 18,
                    y + 112,
                    fill="#33251b",
                    outline="#111827",
                    width=2,
                )
            )
            items.append(
                self.canvas.create_oval(
                    wheel_x - 7,
                    y + 87,
                    wheel_x + 7,
                    y + 101,
                    fill="#d6b27c",
                    outline="#111827",
                )
            )

        items.append(
            self.canvas.create_text(
                x + 22,
                y + 20,
                text=self.cart_status_text[cart_num],
                anchor="w",
                font=("Arial", 14, "bold"),
                fill="#111827",
            )
        )
        items.append(
            self.canvas.create_text(
                x + 92,
                y + 66,
                text=self.cart_player_text[cart_num],
                font=("Arial", 15, "bold"),
                fill="#111827",
            )
        )
        items.append(
            self.canvas.create_text(
                x + 92,
                y + 108,
                text=style["name"],
                font=("Arial", 10, "bold"),
                fill=style["dark"],
            )
        )

    def draw_finish_line(self):
        self.canvas.delete("finish_line")
        x = self.finish_x
        square = 22
        for index, y in enumerate(range(98, 633, square)):
            fill = "#f8fafc" if index % 2 == 0 else "#111827"
            self.canvas.create_rectangle(
                x - 9,
                y,
                x + 9,
                y + square,
                fill=fill,
                outline="#111827",
                tags="finish_line",
            )
        self.canvas.create_rectangle(
            x - 13,
            88,
            x + 13,
            640,
            outline="#7f1d1d",
            width=2,
            tags="finish_line",
        )
        self.canvas.create_text(
            x,
            70,
            text="ESCAPE",
            font=("Arial", 13, "bold"),
            fill="#7f1d1d",
            tags="finish_line",
        )

    def draw_dice_tray(self):
        self.canvas.create_rectangle(
            120, 700, 870, 855, fill="#f4ead7", outline="#b79b69", width=2
        )
        self.canvas.create_text(
            150,
            724,
            text="Dice",
            anchor="w",
            font=("Arial", 18, "bold"),
            fill="#332b20",
        )
        for die_num in range(1, 7):
            x1 = 165 + ((die_num - 1) * 108)
            y1 = 748
            x2 = x1 + 68
            y2 = y1 + 68
            self.canvas.create_rectangle(
                x1 + 5, y1 + 6, x2 + 5, y2 + 6, fill="#7c6a52", outline=""
            )
            self.dice_faces[die_num] = self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#e5e7eb",
                outline="#2f2a25",
                width=2,
            )
            self.lock_badges[die_num] = self.canvas.create_rectangle(
                x1 + 6,
                y2 + 14,
                x2 - 6,
                y2 + 38,
                fill="#bbf7d0",
                outline="#166534",
                width=2,
            )
            self.lock_texts[die_num] = self.canvas.create_text(
                (x1 + x2) / 2,
                y2 + 26,
                text="OK",
                font=("Arial", 10, "bold"),
                fill="#166534",
            )
            self.update_dice_value(1, die_num)

    def die_center(self, die_num):
        x1, y1, x2, y2 = self.canvas.coords(self.dice_faces[die_num])
        return (x1 + x2) / 2, (y1 + y2) / 2

    def clear_die_icon(self, die_num):
        for item in self.dice_icon_items[die_num]:
            self.canvas.delete(item)
        self.dice_icon_items[die_num] = []

    def draw_apple_icon(self, die_num, cx, cy, scale):
        items = self.dice_icon_items[die_num]
        r = 17 * scale
        items.append(
            self.canvas.create_oval(
                cx - r,
                cy - 8 * scale,
                cx + 3 * scale,
                cy + r,
                fill="#c0262d",
                outline="#7f1d1d",
                width=2,
            )
        )
        items.append(
            self.canvas.create_oval(
                cx - 3 * scale,
                cy - 8 * scale,
                cx + r,
                cy + r,
                fill="#dc2626",
                outline="#7f1d1d",
                width=2,
            )
        )
        items.append(
            self.canvas.create_line(
                cx,
                cy - 14 * scale,
                cx + 5 * scale,
                cy - 27 * scale,
                fill="#5c3b16",
                width=3,
            )
        )
        items.append(
            self.canvas.create_oval(
                cx + 4 * scale,
                cy - 29 * scale,
                cx + 22 * scale,
                cy - 18 * scale,
                fill="#3f9d3f",
                outline="#166534",
                width=1,
            )
        )

    def draw_rat_icon(self, die_num, cx, cy, scale):
        items = self.dice_icon_items[die_num]
        items.append(
            self.canvas.create_line(
                cx - 23 * scale,
                cy + 12 * scale,
                cx - 36 * scale,
                cy + 18 * scale,
                cx - 44 * scale,
                cy + 9 * scale,
                fill="#9ca3af",
                width=3,
                smooth=True,
            )
        )
        items.append(
            self.canvas.create_oval(
                cx - 20 * scale,
                cy - 8 * scale,
                cx + 18 * scale,
                cy + 18 * scale,
                fill="#6b7280",
                outline="#374151",
                width=2,
            )
        )
        items.append(
            self.canvas.create_oval(
                cx + 11 * scale,
                cy - 7 * scale,
                cx + 31 * scale,
                cy + 11 * scale,
                fill="#737b86",
                outline="#374151",
                width=2,
            )
        )
        items.append(
            self.canvas.create_oval(
                cx + 14 * scale,
                cy - 15 * scale,
                cx + 25 * scale,
                cy - 5 * scale,
                fill="#9ca3af",
                outline="#374151",
            )
        )
        items.append(
            self.canvas.create_oval(
                cx + 25 * scale,
                cy + 1 * scale,
                cx + 30 * scale,
                cy + 6 * scale,
                fill="#111827",
                outline="",
            )
        )
        items.append(
            self.canvas.create_oval(
                cx + 31 * scale,
                cy + 5 * scale,
                cx + 37 * scale,
                cy + 10 * scale,
                fill="#f3a4a4",
                outline="#7f1d1d",
            )
        )


class ToolTip:
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.window = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<ButtonPress>", self.hide)

    def show(self, _event=None):
        text = self.text_func()
        if not text or self.window is not None:
            return

        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.window,
            text=text,
            justify="left",
            wraplength=280,
            bg="#332b20",
            fg="#fff7e6",
            relief="solid",
            bd=1,
            padx=10,
            pady=7,
            font=("Georgia", 11),
        )
        label.pack()

    def hide(self, _event=None):
        if self.window is not None:
            self.window.destroy()
            self.window = None


class LaunchScreen:
    WIDTH = 920
    HEIGHT = 840
    BG = "#ede2cd"
    PANEL = "#f8f0db"
    INK = "#161514"
    MUTED = "#5f533f"
    BORDER = "#b8a887"
    BUTTON = "#332b20"
    BUTTON_TEXT = "#fff7e6"
    FONT = "Georgia"

    def __init__(self, master, args):
        self.master = master
        self.args = args
        self.result = None
        self.logo_image = None
        self.registered_names = []
        self.done_var = tk.BooleanVar(value=False)
        self.player_count_var = tk.StringVar(value=str(len(args.players or []) or 4))
        self.finish_var = tk.StringVar(value=str(args.finish))
        self.registered_var = tk.StringVar(value=args.registered)
        self.test_var = tk.BooleanVar(value=args.test)
        self.character_var = tk.BooleanVar(value=args.character)
        self.character_mode_var = tk.StringVar(value="Random")
        self.allow_overlapping_characters_var = tk.BooleanVar(
            value=getattr(args, "allow_overlapping_characters", False)
        )
        self.mingle_odds_var = tk.StringVar(
            value=(
                ""
                if args.mingle_odds is None
                else " ".join(str(odd) for odd in args.mingle_odds)
            )
        )
        self.error_var = tk.StringVar(value="")
        self.player_vars = [tk.StringVar(value="") for _ in range(MAX_PLAYERS)]
        self.character_vars = [tk.StringVar(value="Random") for _ in range(MAX_PLAYERS)]
        for index, player in enumerate(args.players or []):
            if index < MAX_PLAYERS:
                self.player_vars[index].set(player)

        self.master.title("Bristol 1350 Setup")
        self.master.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.master.configure(bg=self.BG)
        self.master.protocol("WM_DELETE_WINDOW", self.cancel)
        self.frame = tk.Frame(self.master, bg=self.BG)
        self.frame.pack(fill="both", expand=True)
        self.build()
        self.load_registered_names(show_errors=False)
        self.sync_player_rows()
        self.update_character_controls()

    def build(self):
        header = tk.Frame(self.frame, bg=self.BG)
        header.pack(fill="x", padx=34, pady=(24, 12))

        logo_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../images/logo.png")
        )
        try:
            self.logo_image = tk.PhotoImage(file=logo_path)
            subsample = max(1, self.logo_image.width() // 620)
            if subsample > 1:
                self.logo_image = self.logo_image.subsample(subsample, subsample)
            tk.Label(header, image=self.logo_image, bg=self.BG).pack(anchor="center")
        except tk.TclError:
            tk.Label(
                header,
                text="Bristol 1350",
                bg=self.BG,
                fg=self.INK,
                font=(self.FONT, 52, "bold"),
            ).pack(anchor="center")

        tk.Label(
            header,
            text="Set up the game, then launch the table view.",
            bg=self.BG,
            fg=self.MUTED,
            font=(self.FONT, 15),
        ).pack(anchor="center", pady=(6, 0))

        body = tk.Frame(self.frame, bg=self.BG)
        body.pack(fill="both", expand=True, padx=34, pady=12)
        body.columnconfigure(0, weight=4)
        body.columnconfigure(1, weight=3)

        players_panel = self.panel(body)
        players_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        options_panel = self.panel(body)
        options_panel.grid(row=0, column=1, sticky="nsew", padx=(14, 0))

        self.build_players_panel(players_panel)
        self.build_options_panel(options_panel)

        footer = tk.Frame(self.frame, bg=self.BG)
        footer.pack(fill="x", padx=34, pady=(4, 24))
        tk.Label(
            footer,
            textvariable=self.error_var,
            bg=self.BG,
            fg="#8b1e16",
            font=(self.FONT, 12, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            footer,
            text="Start Game",
            command=self.start_game,
            bg=self.BUTTON,
            fg=self.BUTTON_TEXT,
            activebackground="#4a3b2a",
            activeforeground=self.BUTTON_TEXT,
            font=(self.FONT, 16, "bold"),
            padx=28,
            pady=10,
            relief="flat",
        ).pack(side="right")

    def panel(self, parent):
        return tk.Frame(
            parent,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=2,
            padx=22,
            pady=18,
        )

    def label(self, parent, text, size=13, bold=False):
        return tk.Label(
            parent,
            text=text,
            bg=self.PANEL,
            fg=self.INK,
            anchor="w",
            font=(self.FONT, size, "bold" if bold else "normal"),
        )

    def build_players_panel(self, panel):
        self.label(panel, "Players", size=24, bold=True).grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        self.label(panel, "Count", bold=True).grid(row=1, column=0, sticky="w", pady=(18, 8))
        tk.Spinbox(
            panel,
            from_=1,
            to=MAX_PLAYERS,
            textvariable=self.player_count_var,
            command=self.sync_player_rows,
            width=5,
            font=(self.FONT, 13),
            bg="#fff7e6",
            fg=self.INK,
        ).grid(row=1, column=1, sticky="w", pady=(18, 8))

        self.label(panel, "Name", bold=True).grid(row=2, column=1, sticky="w", pady=(10, 2))
        self.label(panel, "Character", bold=True).grid(row=2, column=2, sticky="w", pady=(10, 2))

        self.player_rows = []
        self.character_rows = []
        character_options = ["Random"] + list(CHARACTER_TYPES)
        for index in range(MAX_PLAYERS):
            label = self.label(panel, f"{index + 1}.")
            entry = tk.Entry(
                panel,
                textvariable=self.player_vars[index],
                font=(self.FONT, 13),
                bg="#fffaf0",
                fg=self.INK,
                insertbackground=self.INK,
                relief="solid",
                bd=1,
                width=21,
            )
            option = tk.OptionMenu(
                panel,
                self.character_vars[index],
                *character_options,
            )
            option.configure(
                bg="#fffaf0",
                fg=self.INK,
                activebackground="#efe3cc",
                activeforeground=self.INK,
                font=(self.FONT, 11),
                relief="solid",
                bd=1,
                width=11,
                highlightthickness=0,
            )
            option["menu"].configure(
                bg="#fffaf0",
                fg=self.INK,
                activebackground="#75695f",
                activeforeground="#fff7e6",
                font=(self.FONT, 11),
            )
            label.grid(row=index + 3, column=0, sticky="w", pady=4)
            entry.grid(row=index + 3, column=1, sticky="ew", pady=4, padx=(0, 8))
            option.grid(row=index + 3, column=2, sticky="ew", pady=4)
            self.player_rows.append((label, entry))
            self.character_rows.append(option)
            ToolTip(
                option,
                lambda character_var=self.character_vars[index]: self.character_tooltip_text(
                    character_var
                ),
            )

        panel.columnconfigure(1, weight=1)
        panel.columnconfigure(2, weight=1)

        self.label(panel, "Registered Players", size=15, bold=True).grid(
            row=13, column=0, columnspan=3, sticky="w", pady=(20, 6)
        )
        self.registered_listbox = tk.Listbox(
            panel,
            selectmode="multiple",
            height=6,
            exportselection=False,
            font=(self.FONT, 12),
            bg="#fffaf0",
            fg=self.INK,
            selectbackground="#75695f",
            selectforeground="#fff7e6",
            relief="solid",
            bd=1,
        )
        self.registered_listbox.grid(row=14, column=0, columnspan=3, sticky="ew")
        self.registered_listbox.bind("<<ListboxSelect>>", self.use_selected_players)

    def build_options_panel(self, panel):
        self.label(panel, "Game Options", size=24, bold=True).pack(anchor="w")

        self.option_label(panel, "Finish line")
        tk.Spinbox(
            panel,
            from_=1,
            to=50,
            textvariable=self.finish_var,
            width=7,
            font=(self.FONT, 13),
            bg="#fff7e6",
            fg=self.INK,
        ).pack(anchor="w")

        tk.Checkbutton(
            panel,
            text="Character powers",
            variable=self.character_var,
            command=self.update_character_controls,
            bg=self.PANEL,
            fg=self.INK,
            activebackground=self.PANEL,
            font=(self.FONT, 13),
            selectcolor="#fff7e6",
        ).pack(anchor="w", pady=(18, 4))

        character_options = tk.Frame(panel, bg=self.PANEL)
        character_options.pack(fill="x", padx=(18, 0), pady=(0, 6))
        tk.Radiobutton(
            character_options,
            text="Random characters",
            variable=self.character_mode_var,
            value="Random",
            command=self.update_character_controls,
            bg=self.PANEL,
            fg=self.INK,
            activebackground=self.PANEL,
            font=(self.FONT, 12),
            selectcolor="#fff7e6",
        ).pack(anchor="w")
        tk.Radiobutton(
            character_options,
            text="Choose characters",
            variable=self.character_mode_var,
            value="Choose",
            command=self.update_character_controls,
            bg=self.PANEL,
            fg=self.INK,
            activebackground=self.PANEL,
            font=(self.FONT, 12),
            selectcolor="#fff7e6",
        ).pack(anchor="w")
        tk.Checkbutton(
            character_options,
            text="Allow overlapping characters",
            variable=self.allow_overlapping_characters_var,
            command=self.update_character_controls,
            bg=self.PANEL,
            fg=self.INK,
            activebackground=self.PANEL,
            font=(self.FONT, 12),
            selectcolor="#fff7e6",
        ).pack(anchor="w", pady=(4, 0))

        tk.Checkbutton(
            panel,
            text="Test mode",
            variable=self.test_var,
            bg=self.PANEL,
            fg=self.INK,
            activebackground=self.PANEL,
            font=(self.FONT, 13),
            selectcolor="#fff7e6",
        ).pack(anchor="w", pady=4)

        self.option_label(panel, "Registration file")
        reg_row = tk.Frame(panel, bg=self.PANEL)
        reg_row.pack(fill="x")
        tk.Entry(
            reg_row,
            textvariable=self.registered_var,
            font=(self.FONT, 11),
            bg="#fffaf0",
            fg=self.INK,
            relief="solid",
            bd=1,
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            reg_row,
            text="Browse",
            command=self.browse_registration,
            bg="#75695f",
            fg="#fff7e6",
            activebackground="#5f5349",
            activeforeground="#fff7e6",
            font=(self.FONT, 11, "bold"),
            relief="flat",
            padx=10,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            panel,
            text="Load Registered Players",
            command=lambda: self.load_registered_names(show_errors=True),
            bg="#75695f",
            fg="#fff7e6",
            activebackground="#5f5349",
            activeforeground="#fff7e6",
            font=(self.FONT, 12, "bold"),
            relief="flat",
            pady=5,
        ).pack(anchor="w", pady=(8, 0))

        self.option_label(panel, "Mingle odds")
        tk.Entry(
            panel,
            textvariable=self.mingle_odds_var,
            font=(self.FONT, 12),
            bg="#fffaf0",
            fg=self.INK,
            relief="solid",
            bd=1,
        ).pack(fill="x")
        tk.Label(
            panel,
            text="Optional: four weights for symptoms 1-4.",
            bg=self.PANEL,
            fg=self.MUTED,
            font=(self.FONT, 10),
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

    def option_label(self, parent, text):
        self.label(parent, text, bold=True).pack(anchor="w", pady=(18, 6))

    def character_tooltip_text(self, character_var):
        character_name = character_var.get()
        if character_name == "Random":
            return "A character will be assigned randomly when the game starts."
        return CHARACTER_TYPES.get(character_name, "")

    def sync_player_rows(self):
        try:
            count = int(self.player_count_var.get())
        except ValueError:
            count = 1
        count = max(1, min(MAX_PLAYERS, count))
        self.player_count_var.set(str(count))
        for index, (label, entry) in enumerate(self.player_rows):
            state = "normal" if index < count else "disabled"
            label.configure(fg=self.INK if index < count else self.MUTED)
            entry.configure(state=state)
        self.update_character_controls()

    def update_character_controls(self):
        if not hasattr(self, "character_rows"):
            return
        try:
            count = int(self.player_count_var.get())
        except ValueError:
            count = 1
        choose_enabled = self.character_var.get() and self.character_mode_var.get() == "Choose"
        for index, option in enumerate(self.character_rows):
            state = "normal" if choose_enabled and index < count else "disabled"
            option.configure(state=state)

    def use_selected_players(self, _event=None):
        selected = [self.registered_listbox.get(i) for i in self.registered_listbox.curselection()]
        if not selected:
            return
        selected = selected[:MAX_PLAYERS]
        self.player_count_var.set(str(len(selected)))
        for index, var in enumerate(self.player_vars):
            var.set(selected[index] if index < len(selected) else "")
        self.sync_player_rows()

    def browse_registration(self):
        if filedialog is None:
            return
        path = filedialog.askopenfilename(
            title="Choose registration file",
            filetypes=(("YAML files", "*.yml *.yaml"), ("All files", "*")),
        )
        if path:
            self.registered_var.set(path)
            self.load_registered_names(show_errors=True)

    def load_registered_names(self, show_errors):
        self.registered_listbox.delete(0, tk.END)
        self.registered_names = []
        path = self.registered_var.get().strip()
        if not path:
            return
        if not os.path.exists(path):
            if show_errors:
                self.error_var.set("Registration file was not found.")
            return
        data = read_yaml_file(path)
        if not isinstance(data, dict):
            if show_errors:
                self.error_var.set("Unable to read registered players from that file.")
            return
        registered_users = data.get("registered_users")
        if not isinstance(registered_users, dict):
            if show_errors:
                self.error_var.set("Registration file must include registered_users.")
            return
        self.error_var.set("")
        self.registered_names = sorted(str(name) for name in registered_users)
        for name in self.registered_names:
            self.registered_listbox.insert(tk.END, name)

    def start_game(self):
        self.sync_player_rows()
        try:
            player_count = int(self.player_count_var.get())
            finish = int(self.finish_var.get())
        except ValueError:
            self.error_var.set("Player count and finish line must be numbers.")
            return

        players = [
            self.player_vars[index].get().strip()
            for index in range(player_count)
        ]
        if any(not player for player in players):
            self.error_var.set("Enter a name for every active player.")
            return
        if len(players) != len(set(players)):
            self.error_var.set("Player names must be unique.")
            return
        if finish < 1:
            self.error_var.set("Finish line must be at least 1.")
            return

        character_assignments = None
        random_characters = True
        allow_overlaps = self.allow_overlapping_characters_var.get()
        if self.character_var.get() and self.character_mode_var.get() == "Choose":
            random_characters = False
            character_assignments = [
                self.character_vars[index].get()
                for index in range(player_count)
            ]
            if any(character == "Random" for character in character_assignments):
                self.error_var.set("Choose a character for every active player.")
                return
            if not allow_overlaps and len(character_assignments) != len(set(character_assignments)):
                self.error_var.set("Either choose unique characters or allow overlaps.")
                return

        mingle_odds = None
        odds_text = self.mingle_odds_var.get().strip()
        if odds_text:
            try:
                parsed_odds = tuple(float(part) for part in odds_text.replace(",", " ").split())
            except ValueError:
                self.error_var.set("Mingle odds must be four numeric weights.")
                return
            if len(parsed_odds) != 4:
                self.error_var.set("Mingle odds must include exactly four weights.")
                return
            if any(odd < 0 for odd in parsed_odds) or sum(parsed_odds) <= 0:
                self.error_var.set("Mingle odds must be non-negative with a positive total.")
                return
            mingle_odds = parsed_odds

        self.args.players = players
        self.args.finish = finish
        self.args.registered = self.registered_var.get().strip()
        self.args.test = self.test_var.get()
        self.args.gui = True
        self.args.no_gui = False
        self.args.character = self.character_var.get()
        self.args.random_characters = random_characters
        self.args.allow_overlapping_characters = allow_overlaps
        self.args.character_assignments = character_assignments
        self.args.mingle_odds = mingle_odds
        self.result = self.args
        self.frame.destroy()
        self.done_var.set(True)

    def cancel(self):
        self.result = None
        self.done_var.set(True)

    def run(self):
        self.master.wait_variable(self.done_var)
        return self.result


class ConsoleGame:
    def log_action(self, message):
        return None

    def update_order(self, list_of_characters, current_character=None):
        return None

    def update_rectangle_position(self, rectangle, amount):
        return None

    def update_rectangle_txt(self, rectangle, txt):
        return None

    def update_finish_line(self, amount):
        return None

    def update_lock_symbol(self, die_num, lock, busy):
        return None

    def update_dice_value(self, status, die_num):
        return None

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


def die_value_from_input(value, allow_zero=False, allow_back=False):
    value = value.strip().lower()
    if allow_back and value == "b":
        return "back"

    try:
        die_num = int(value)
    except ValueError:
        print("Please enter a number from 1 to 6.")
        return None

    if allow_zero and die_num == 0:
        return 0

    if die_num not in VALID_DICE:
        print("Please enter a number from 1 to 6.")
        return None

    return die_num


def die_is_locked(roll, die_num):
    return getattr(roll, f"dice{die_num}_lock")


def lock_die(roll, die_num):
    setattr(roll, f"dice{die_num}_lock", True)


def validate_reroll_dice(roll, dice):
    if len(dice) != len(set(dice)):
        print("Select different dice.")
        return False

    for die_num in dice:
        if die_is_locked(roll, die_num):
            die_result = getattr(roll, f"dice{die_num}_result")
            print(
                f"Can't reroll {die_result}, as it has been locked this round with arsenic!"
            )
            return False

    return True


def update_all_dice(game, roll):
    game.update_dice_value(status=int(roll.dice1), die_num=1)
    game.update_dice_value(status=int(roll.dice2), die_num=2)
    game.update_dice_value(status=int(roll.dice3), die_num=3)
    game.update_dice_value(status=int(roll.dice4), die_num=4)
    game.update_dice_value(status=int(roll.dice5), die_num=5)
    game.update_dice_value(status=int(roll.dice6), die_num=6)


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
        to_return = []
        if index1 not in VALID_DICE:
            print("Select a die from 1 to 6.")
            return to_return
        if index2 is not None and index2 not in VALID_DICE:
            print("Select a die from 1 to 6.")
            return to_return
        if index2 is not None and index1 == index2:
            print("Select two different dice.")
            return to_return

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
            return to_return
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
        if not list_of_characters:
            raise ValueError("At least one player is required to start a game.")

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
        self.last_action_log = None
        self.last_emerald_action_log = None

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

    def reset_action_log(self):
        self.last_action_log = None
        self.last_emerald_action_log = None

    def set_action_log(self, message, emerald_message=None):
        self.last_action_log = message
        self.last_emerald_action_log = emerald_message or message

    def action_log_message(self, fallback, emerald=False):
        if emerald and self.last_emerald_action_log:
            return self.last_emerald_action_log
        return self.last_action_log or fallback

    def log_whip_block(self, blocker, actor, action, cart_num):
        self.set_action_log(
            f"{blocker.name} used Whip to stop {actor.name}'s {action} in {cart_label(cart_num)}.",
            f"{blocker.name} used Whip to stop {actor.name}'s Emerald {action} in {cart_label(cart_num)}.",
        )

    def log_push_to_cart(self, actor, victim, from_cart, to_cart):
        self.set_action_log(
            f"{actor.name} pushed {victim.name} from {cart_label(from_cart)} to {cart_label(to_cart)}.",
            f"{actor.name} used Emerald to push {victim.name} from {cart_label(from_cart)} to {cart_label(to_cart)}.",
        )

    def log_push_off_cart(self, actor, victim, from_cart, actor_died):
        if actor_died:
            result = f"{victim.name} died, and {actor.name} died too."
        else:
            result = f"{victim.name} died and had the plague."
        self.set_action_log(
            f"{actor.name} pushed {victim.name} from {cart_label(from_cart)} with no open cart behind; {result}",
            f"{actor.name} used Emerald to push {victim.name} from {cart_label(from_cart)} with no open cart behind; {result}",
        )

    def log_jump(self, actor, from_cart, to_cart):
        self.set_action_log(
            f"{actor.name} jumped from the front of {cart_label(from_cart)} to the back of {cart_label(to_cart)}.",
            f"{actor.name} used Emerald to jump from the front of {cart_label(from_cart)} to the back of {cart_label(to_cart)}.",
        )

    def log_elbow(self, actor, passed_characters, cart_num):
        passed_names = format_name_list(passed_characters)
        self.set_action_log(
            f"{actor.name} elbowed past {passed_names} to the front of {cart_label(cart_num)}.",
            f"{actor.name} used Emerald to elbow past {passed_names} to the front of {cart_label(cart_num)}.",
        )

    def log_knight(self, actor, target, cart_num, moved):
        if moved:
            self.set_action_log(
                f"{actor.name} used Knight to move {target.name} to the front of {cart_label(cart_num)}."
            )
        else:
            self.set_action_log(
                f"{actor.name} used Knight on {target.name}, who was already at the front of {cart_label(cart_num)}."
            )

    def remove_character(self, character):
        for cart in (self.cart1, self.cart2, self.cart3):
            if character in cart:
                cart.remove(character)
                break

        if character in self.list_of_characters:
            self.list_of_characters.remove(character)

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
        if tmp is not None and tmp in self.list_of_characters:
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

    def getCartPriority(self, cartnum):
        if cartnum == 1:
            return self.cart1_priority
        if cartnum == 2:
            return self.cart2_priority
        if cartnum == 3:
            return self.cart3_priority
        return None

    def getCartNumByPriority(self, priority):
        for cart_num in (1, 2, 3):
            if self.getCartPriority(cart_num) == priority:
                return cart_num
        return None

    def getFurthestBehindOpenCart(self, source_cart_num):
        source_priority = self.getCartPriority(source_cart_num)
        for priority in range(3, source_priority, -1):
            cart_num = self.getCartNumByPriority(priority)
            if cart_num is not None and len(self.getCartInfo(cart_num)) < CART_CAPACITY:
                return cart_num
        return None

    def getCartInFront(self, source_cart_num):
        source_priority = self.getCartPriority(source_cart_num)
        if source_priority is None or source_priority <= 1:
            return None
        return self.getCartNumByPriority(source_priority - 1)

    def remove_from_cart(self, character):
        cart = self.getCartInfo(character.cart)
        if cart and character in cart:
            cart.remove(character)

    def append_to_cart(self, character, cart_num):
        cart = self.getCartInfo(cart_num)
        cart.append(character)
        character.cart = cart_num

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
        self.reset_action_log()
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
                                self.log_whip_block(self.cart1[-1], character, "push", 1)
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
                        pushed_character = self.cart1[-1]
                        if pushed_character.plague_status == True:
                            print(
                                Fore.GREEN
                                + Style.BRIGHT
                                + f"{pushed_character.name} had the plague. Well done {character.name}!\n"
                                + bcolors.RESET
                            )
                            self.log_push_off_cart(
                                character, pushed_character, 1, actor_died=False
                            )
                            self.remove_character(pushed_character)
                            return True
                        else:
                            print(
                                Fore.RED
                                + Style.BRIGHT
                                + f"{pushed_character.name} did not have the plague. {character.name} killed themselves out of despair.\n"
                                + bcolors.RESET
                            )
                            self.log_push_off_cart(
                                character, pushed_character, 1, actor_died=True
                            )
                            self.remove_character(pushed_character)
                            self.remove_character(character)
                            return True
                    else:
                        # Get the cart behind them:
                        if self.cart2_priority == (self.cart1_priority + 1):
                            pushed_character = self.cart1[-1]
                            self.log_push_to_cart(character, pushed_character, 1, 2)
                            pushed_character.cart = 2
                            self.cart2.insert(0, pushed_character)
                            self.cart1.pop(-1)
                            return True
                        elif self.cart3_priority == (self.cart1_priority + 1):
                            pushed_character = self.cart1[-1]
                            self.log_push_to_cart(character, pushed_character, 1, 3)
                            pushed_character.cart = 3
                            self.cart3.insert(0, pushed_character)
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
                                self.log_whip_block(self.cart2[-1], character, "push", 2)
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
                        pushed_character = self.cart2[-1]
                        if pushed_character.plague_status == True:
                            print(
                                Fore.GREEN
                                + f"{pushed_character.name} had the plague. Well done {character.name}!"
                                + bcolors.RESET
                            )
                            self.log_push_off_cart(
                                character, pushed_character, 2, actor_died=False
                            )
                            self.remove_character(pushed_character)
                            return True
                        else:
                            print(
                                Fore.RED
                                + Style.BRIGHT
                                + f"{pushed_character.name} did not have the plague. {character.name} killed themselves out of despair."
                                + bcolors.RESET
                            )
                            self.log_push_off_cart(
                                character, pushed_character, 2, actor_died=True
                            )
                            self.remove_character(pushed_character)
                            self.remove_character(character)
                            return True
                    else:
                        # Get the cart behind them:
                        if self.cart3_priority == (self.cart2_priority + 1):
                            pushed_character = self.cart2[-1]
                            self.log_push_to_cart(character, pushed_character, 2, 3)
                            pushed_character.cart = 3
                            self.cart3.insert(0, pushed_character)
                            self.cart2.pop(-1)
                            return True
                        elif self.cart1_priority == (self.cart2_priority + 1):
                            pushed_character = self.cart2[-1]
                            self.log_push_to_cart(character, pushed_character, 2, 1)
                            pushed_character.cart = 1
                            self.cart1.insert(0, pushed_character)
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
                                self.log_whip_block(self.cart3[-1], character, "push", 3)
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
                        pushed_character = self.cart3[-1]
                        if pushed_character.plague_status == True:
                            print(
                                Fore.GREEN
                                + Style.BRIGHT
                                + f"{pushed_character.name} had the plague. Well done {character.name}!"
                                + bcolors.RESET
                            )
                            self.log_push_off_cart(
                                character, pushed_character, 3, actor_died=False
                            )
                            self.remove_character(pushed_character)
                            return True
                        else:
                            print(
                                Fore.RED
                                + Style.BRIGHT
                                + f"{pushed_character.name} did not have the plague. {character.name} killed themselves out of despair."
                                + bcolors.RESET
                            )
                            self.log_push_off_cart(
                                character, pushed_character, 3, actor_died=True
                            )
                            self.remove_character(pushed_character)
                            self.remove_character(character)
                            return True
                    else:
                        # Get the cart behind them:
                        if self.cart2_priority == (self.cart3_priority + 1):
                            pushed_character = self.cart3[-1]
                            self.log_push_to_cart(character, pushed_character, 3, 2)
                            pushed_character.cart = 2
                            self.cart2.insert(0, pushed_character)
                            self.cart3.pop(-1)
                            return True
                        elif self.cart1_priority == (self.cart3_priority + 1):
                            pushed_character = self.cart3[-1]
                            self.log_push_to_cart(character, pushed_character, 3, 1)
                            pushed_character.cart = 1
                            self.cart1.insert(0, pushed_character)
                            self.cart3.pop(-1)
                            return True
                else:
                    return False

    def jump(self, character, txt, account_sid, auth_token):
        self.reset_action_log()
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
                                        self.log_whip_block(booger, character, "jump", 2)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.log_jump(character, 1, 2)
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
                                        self.log_whip_block(booger, character, "jump", 3)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.log_jump(character, 1, 3)
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
                                        self.log_whip_block(booger, character, "jump", 2)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.log_jump(character, 1, 2)
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
                                        self.log_whip_block(booger, character, "jump", 3)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.log_jump(character, 1, 3)
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
                                        self.log_whip_block(booger, character, "jump", 1)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.log_jump(character, 2, 1)
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
                                        self.log_whip_block(booger, character, "jump", 3)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.log_jump(character, 2, 3)
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
                                        self.log_whip_block(booger, character, "jump", 1)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"\nNice try {booger.name}, you don't own a whip.\n"
                                        )
                        self.log_jump(character, 2, 1)
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
                                        self.log_whip_block(booger, character, "jump", 3)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"\nNice try {booger.name}, you don't own a whip.\n"
                                        )
                        self.log_jump(character, 2, 3)
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
                                        self.log_whip_block(booger, character, "jump", 2)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"\nNice try {booger.name}, you don't own a whip.\n"
                                        )
                        self.log_jump(character, 3, 2)
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
                                        self.log_whip_block(booger, character, "jump", 1)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"\nNice try {booger.name}, you don't own a whip.\n"
                                        )
                        self.log_jump(character, 3, 1)
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
                                        self.log_whip_block(booger, character, "jump", 2)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.log_jump(character, 3, 2)
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
                                        self.log_whip_block(booger, character, "jump", 1)
                                        booger.removeCard(4, txt, account_sid, auth_token)
                                        return True
                                    else:
                                        print(
                                            f"Nice try {booger.name}, you don't own a whip."
                                        )
                        self.log_jump(character, 3, 1)
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

    # Capacity-aware movement rules. These definitions supersede the older
    # cart-specific push/jump methods above.
    def choose_push_target(self, character):
        cart = self.getCartInfo(character.cart)
        position = cart.index(character)
        eligible_targets = cart[position + 1 : position + 3]
        if not eligible_targets:
            print(
                f"{character.name} cannot push anyone, as no one is one or two spots behind them."
            )
            return None

        if len(eligible_targets) == 1:
            target = eligible_targets[0]
            confirm = input(
                f"Would you like to push {target.name} from {cart_label(character.cart)}? (y/n):"
            )
            return target if confirm.lower() == "y" else None

        print("Who would you like to push?")
        for index, target in enumerate(eligible_targets, 1):
            print(f"{index}) {target.name}")
        target_input = input(
            "Select a player to push (1-2, y for the furthest player behind you, n to cancel):"
        ).strip().lower()
        if target_input == "n":
            return None
        if target_input == "y":
            return eligible_targets[-1]
        try:
            target_index = int(target_input) - 1
        except ValueError:
            print("Please select a valid push target.")
            return None
        if target_index < 0 or target_index >= len(eligible_targets):
            print("Please select a valid push target.")
            return None
        return eligible_targets[target_index]

    def handle_pushed_off_cart(self, actor, pushed_character, source_cart_num):
        print(
            Fore.RED
            + Style.BRIGHT
            + f"{pushed_character.name} has been left behind!"
            + bcolors.RESET
        )
        if pushed_character.plague_status == True:
            print(
                Fore.GREEN
                + Style.BRIGHT
                + f"{pushed_character.name} had the plague. Well done {actor.name}!"
                + bcolors.RESET
            )
            self.log_push_off_cart(
                actor, pushed_character, source_cart_num, actor_died=False
            )
            self.remove_character(pushed_character)
        else:
            print(
                Fore.RED
                + Style.BRIGHT
                + f"{pushed_character.name} did not have the plague. {actor.name} died of shame."
                + bcolors.RESET
            )
            self.log_push_off_cart(
                actor, pushed_character, source_cart_num, actor_died=True
            )
            self.remove_character(pushed_character)
            if actor in self.list_of_characters:
                self.remove_character(actor)

    def push(self, character, txt, account_sid, auth_token):
        self.reset_action_log()
        source_cart_num = character.cart
        source_cart = self.getCartInfo(source_cart_num)
        if not source_cart or character not in source_cart:
            return False

        pushed_character = self.choose_push_target(character)
        if pushed_character is None:
            return False

        if pushed_character != character and pushed_character.hasRemedies():
            whip = input(
                f"{pushed_character.name}, would you like to use a remedy to prevent being pushed? (y/n):"
            )
            if whip.lower() == "y":
                if pushed_character.hasWhip():
                    print(
                        Fore.GREEN
                        + Style.BRIGHT
                        + f"{pushed_character.name} uses a whip to prevent being pushed!"
                        + bcolors.RESET
                    )
                    self.log_whip_block(
                        pushed_character, character, "push", source_cart_num
                    )
                    pushed_character.removeCard(4, txt, account_sid, auth_token)
                    return True
                print(f"\nSorry {pushed_character.name}, you don't appear to have a whip!\n")

        destination_cart_num = self.getFurthestBehindOpenCart(source_cart_num)
        if destination_cart_num is None:
            self.handle_pushed_off_cart(character, pushed_character, source_cart_num)
            return True

        self.remove_from_cart(pushed_character)
        self.append_to_cart(pushed_character, destination_cart_num)
        print(
            Fore.RED
            + Style.BRIGHT
            + f"{character.name} pushed {pushed_character.name} from "
            + f"{cart_label(source_cart_num)} to {cart_label(destination_cart_num)}!"
            + bcolors.RESET
        )
        self.log_push_to_cart(
            character, pushed_character, source_cart_num, destination_cart_num
        )
        return True

    def jump(self, character, txt, account_sid, auth_token):
        self.reset_action_log()
        source_cart_num = character.cart
        source_cart = self.getCartInfo(source_cart_num)
        if not source_cart or character not in source_cart:
            return False
        if source_cart.index(character) != 0:
            print(
                f"{character.name} needs to be in front of the cart before jumping to the next one!"
            )
            return False

        destination_cart_num = self.getCartInFront(source_cart_num)
        if destination_cart_num is None:
            print(f"{character.name} is already in the front cart.")
            return False

        destination_cart = self.getCartInfo(destination_cart_num)
        for booger in destination_cart:
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
                        self.log_whip_block(
                            booger, character, "jump", destination_cart_num
                        )
                        booger.removeCard(4, txt, account_sid, auth_token)
                        return True
                    print(f"Nice try {booger.name}, you don't own a whip.")

        if len(destination_cart) < CART_CAPACITY:
            self.remove_from_cart(character)
            self.append_to_cart(character, destination_cart_num)
            self.log_jump(character, source_cart_num, destination_cart_num)
            print(
                Fore.GREEN
                + Style.BRIGHT
                + f"{character.name} jumped from {cart_label(source_cart_num)} "
                + f"to the back of {cart_label(destination_cart_num)}!"
                + bcolors.RESET
            )
            return True

        swapped_character = destination_cart[-1]
        source_cart.pop(0)
        destination_cart[-1] = character
        character.cart = destination_cart_num
        source_cart.append(swapped_character)
        swapped_character.cart = source_cart_num
        self.set_action_log(
            f"{character.name} jumped from {cart_label(source_cart_num)} to "
            f"{cart_label(destination_cart_num)}, swapping with {swapped_character.name}.",
            f"{character.name} used Emerald to jump from {cart_label(source_cart_num)} to "
            f"{cart_label(destination_cart_num)}, swapping with {swapped_character.name}.",
        )
        print(
            Fore.GREEN
            + Style.BRIGHT
            + f"{character.name} jumped into full {cart_label(destination_cart_num)} "
            + f"and swapped with {swapped_character.name}!"
            + bcolors.RESET
        )
        return True

    def knight_action(self, character, num, actor=None):
        self.reset_action_log()
        actor = actor or character
        if num == 1:
            indy = self.cart1.index(character)
            if indy == 0:
                print(f"\n{character.name} is already at the front of their cart!\n")
                self.log_knight(actor, character, 1, moved=False)
            else:
                self.cart1.pop(indy)
                self.cart1.insert(0, character)
                self.log_knight(actor, character, 1, moved=True)
                print(Fore.CYAN + Style.BRIGHT)
                print(
                    f"{character.name} has been knighted to the front of the cart!"
                )
                print(bcolors.RESET)

        elif num == 2:
            indy = self.cart2.index(character)
            if indy == 0:
                print(f"\n{character.name} is already at the front of their cart!\n")
                self.log_knight(actor, character, 2, moved=False)
            else:
                self.cart2.pop(indy)
                self.cart2.insert(0, character)
                self.log_knight(actor, character, 2, moved=True)
                print(Fore.YELLOW + Style.BRIGHT)
                print(
                    f"{character.name} has been knighted to the front of the cart!"
                )
                print(bcolors.RESET)
        elif num == 3:
            indy = self.cart3.index(character)
            if indy == 0:
                print(f"\n{character.name} is already at the front of their cart!\n")
                self.log_knight(actor, character, 3, moved=False)
            else:
                self.cart3.pop(indy)
                self.cart3.insert(0, character)
                self.log_knight(actor, character, 3, moved=True)
                print(Fore.MAGENTA + Style.BRIGHT)
                print(
                    f"{character.name} has been knighted to the front of the cart!"
                )
                print(bcolors.RESET)

    def elbow(self, character, txt, account_sid, auth_token):
        self.reset_action_log()
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
                                    self.log_whip_block(booger, character, "elbow", 1)
                                    booger.removeCard(4, txt, account_sid, auth_token)
                                    return True
                                else:
                                    print(
                                        f"Nice try {booger.name}, you don't own a whip."
                                    )
                    self.log_elbow(character, self.cart1[:position], 1)
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
                                    self.log_whip_block(booger, character, "elbow", 2)
                                    booger.removeCard(4, txt, account_sid, auth_token)
                                    return True
                                else:
                                    print(
                                        f"Nice try {booger.name}, you don't own a whip."
                                    )
                    self.log_elbow(character, self.cart2[:position], 2)
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
                                    self.log_whip_block(booger, character, "elbow", 3)
                                    booger.removeCard(4, txt, account_sid, auth_token)
                                    return True
                                else:
                                    print(
                                        f"Nice try {booger.name}, you don't own a whip."
                                    )
                    self.log_elbow(character, self.cart3[:position], 3)
                    self.cart3.pop(position)
                    self.cart3.insert(0, character)
                    print(Fore.MAGENTA + Style.BRIGHT)
                    print(
                        f"{character.name} has elbowed their way into the front of the blue cart!"
                    )
                    print(bcolors.RESET)
                    return True

    def mingle(self, cart, args, sid, token):
        mingle_odds = mingle_odds_from_args(args)
        if cart == 1:
            for character in self.cart1:
                if not character.getDrunkStatus():
                    new_symptoms = generate_mingle_symptoms(mingle_odds)
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
                    new_symptoms = generate_mingle_symptoms(mingle_odds)
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
                    new_symptoms = generate_mingle_symptoms(mingle_odds)
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
        if len(self.list_of_characters) == 0:
            return None

        # If there's only one character left, then that's obviously the start.
        if len(self.list_of_characters) == 1:
            return self.list_of_characters[0]

        for cart_num in self.getCarOrder():
            cart = self.getCartInfo(cart_num)
            if cart:
                return cart[0]

        return self.list_of_characters[0]


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

    def getNumRemedies(self):
        if self.remedycard1 == None:
            return 0
        elif self.remedycard2 == None:
            return 1
        elif self.remedycard3 == None:
            return 2
        else:
            return 3

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
    parser.add_argument("--gui", action="store_true", help="Show the Tkinter GUI during a test game.")
    parser.add_argument("--no-gui", action="store_true", help="Run without the Tkinter GUI.")
    parser.add_argument("--sample", action="store_true", help="Run an automated sample game and write CLI output to game_state.txt.")
    parser.add_argument("--mingle", action="store_true", help="Run mingle simulations and print statistics.")
    parser.add_argument(
        "--mingle-odds",
        nargs=4,
        type=float,
        default=None,
        metavar=("ONE", "TWO", "THREE", "FOUR"),
        help=(
            "Override odds/weights for mingle symptoms 1-4. Defaults depend on "
            "player count: 1-3 => 3 2 2 3, 4-6 => 4 3 1 2, 7-9 => 4 3 2 1."
        ),
    )
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
    args.random_characters = True
    args.allow_overlapping_characters = False
    args.character_assignments = None

    if args.version:
        print(f"v{get_project_version()}")
        sys.exit()

    if args.sample and args.mingle:
        parser.error("--sample and --mingle cannot be used together.")

    if args.players and len(args.players) > MAX_PLAYERS:
        parser.error(f"Bristol supports 1-{MAX_PLAYERS} players.")

    if args.players and len(args.players) != len(set(args.players)):
        parser.error("players must be unique.")

    if args.finish < 1:
        parser.error("--finish must be at least 1.")

    if args.mingle_odds is not None:
        if any(odd < 0 for odd in args.mingle_odds):
            parser.error("--mingle-odds values must be non-negative.")

        if sum(args.mingle_odds) <= 0:
            parser.error("--mingle-odds must include at least one positive value.")

        args.mingle_odds = tuple(args.mingle_odds)

    return args


def introsequence(args, sid, token, registered_users):
    character_dict = dict(CHARACTER_TYPES)
    ascii_art = r"""
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

            if args.character:
                if getattr(args, "character_assignments", None):
                    selected_char = args.character_assignments[i]
                    selected_description = CHARACTER_TYPES[selected_char]
                else:
                    selected_char, selected_description = random.choice(
                        list(character_dict.items())
                    )
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
                try:
                    if selected_char == "Outlaw":
                        list_of_characters[i].setOutlaw()
                except Exception as e:
                    print("\nAn error occurred when using the outlaw.", e,"\n")
                if not getattr(args, "allow_overlapping_characters", False):
                    character_dict.pop(selected_char, None)

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
            else:
                print(f"{args.players[i]}, {list_of_characters[i].plague_statement}\n")
            list_of_characters[i].drawRemedy(args, sid, token)
        return list_of_characters


def read_yaml_file(file_path):
    if yaml is None:
        print("Unable to read YAML files because pyyaml is not installed.")
        return None

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


def load_registration_config(args):
    data = read_yaml_file(args.registered)
    if not isinstance(data, dict):
        print(f"Unable to load registration data from '{args.registered}'.")
        sys.exit(2)

    registered_users = data.get("registered_users")
    if not isinstance(registered_users, dict):
        print("registration.yml must include a 'registered_users' mapping.")
        sys.exit(2)

    normalized_users = {}
    for name, phone_number in registered_users.items():
        normalized_users[str(name)] = "" if phone_number is None else str(phone_number)

    missing_players = [player for player in args.players if player not in normalized_users]
    if missing_players:
        for player in missing_players:
            print(f"{player} is not registered!\n")
        print("Unable to proceed with the game. Please register missing players and try again.")
        sys.exit(6)

    if args.test:
        return normalized_users, None, None

    twilio_info = data.get("twilio_info")
    if not isinstance(twilio_info, dict):
        print("registration.yml must include a 'twilio_info' mapping when not using --test.")
        sys.exit(2)

    account_sid = twilio_info.get("account_sid")
    auth_token = twilio_info.get("auth_token")
    if not account_sid or not auth_token:
        print("registration.yml must include twilio_info.account_sid and twilio_info.auth_token.")
        sys.exit(2)

    empty_phone_numbers = [
        player for player in args.players if not normalized_users.get(player)
    ]
    if empty_phone_numbers:
        print("All players need phone numbers when not using --test.")
        sys.exit(2)

    return normalized_users, str(account_sid), str(auth_token)


def ensure_sms_dependencies(args):
    if args.test:
        return

    try:
        import twilio.rest  # noqa: F401
    except ModuleNotFoundError:
        print("Twilio is required when not using --test. Install dependencies or rerun with --test.")
        sys.exit(1)


def create_game_window():
    if tk is None:
        print(f"Unable to start the Tkinter GUI: {TK_IMPORT_ERROR}")
        sys.exit(1)

    try:
        return tk.Tk()
    except Exception as exc:
        print(f"Unable to start the Tkinter GUI: {exc}")
        sys.exit(1)


def run_launch_screen(args):
    root = create_game_window()
    launch_screen = LaunchScreen(root, args)
    configured_args = launch_screen.run()
    if configured_args is None:
        try:
            root.destroy()
        except tk.TclError:
            pass
        sys.exit(0)
    return configured_args, root


def create_game_display(args, root=None):
    if args.no_gui or (args.test and not args.gui):
        return ConsoleGame()

    if root is None:
        root = create_game_window()
    return BristolGame(root)


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
                game.log_action(
                    board.action_log_message(
                        f"{character.name} used Emerald to elbow.", emerald=True
                    )
                )
            else:
                finished = False

        if player_input.lower() == "j":
            if board.jump(character, args.test, account_sid, auth_token) == True:
                finished = True
                board.displayCarts(game, args)
                game.log_action(
                    board.action_log_message(
                        f"{character.name} used Emerald to jump.", emerald=True
                    )
                )
            else:
                finished = False

        if player_input.lower() == "p":
            if board.push(character, args.test, account_sid, auth_token) == True:
                finished = True
                board.displayCarts(game, args)
                game.log_action(
                    board.action_log_message(
                        f"{character.name} used Emerald to push.", emerald=True
                    )
                )
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
                for character in list(board.cart1):
                    print(
                        Fore.RED,
                        Style.BRIGHT
                        + f"{character.name} has died from the plague :( \n"
                        + bcolors.RESET,
                    )
                    board.remove_character(character)
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
                for character in list(board.cart2):
                    print(
                        Fore.RED,
                        Style.BRIGHT
                        + f"{character.name} has died from the plague :( \n"
                        + bcolors.RESET,
                    )
                    board.remove_character(character)
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
                for character in list(board.cart3):
                    print(
                        Fore.RED,
                        Style.BRIGHT
                        + f"{character.name} has died from the plague :( \n"
                        + bcolors.RESET,
                    )
                    board.remove_character(character)
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
        if toml is not None:
            with open("pyproject.toml", "r") as file:
                toml_content = toml.load(file)
        else:
            try:
                import tomllib
            except ModuleNotFoundError:
                print("Unable to read pyproject.toml because toml is not installed.")
                return None

            with open("pyproject.toml", "rb") as file:
                toml_content = tomllib.load(file)

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


def sample_players(args):
    if args.players:
        return list(args.players)

    player_count = random.randint(1, MAX_PLAYERS)
    return random.sample(SAMPLE_PLAYER_POOL, player_count)


def sample_cart_label(cart_num):
    return {1: "Blue", 2: "Yellow", 3: "Purple"}[cart_num]


def sample_cart_position(board, cart_num):
    return getattr(board, f"cart{cart_num}_position")


def sample_cart_priority(board, cart_num):
    return getattr(board, f"cart{cart_num}_priority")


def sample_cart_with_priority(board, priority):
    for cart_num in (1, 2, 3):
        if sample_cart_priority(board, cart_num) == priority:
            return cart_num

    return None


def sample_roll_summary(roll):
    return (
        f"(1) {roll.dice1_result}, (2) {roll.dice2_result}, "
        f"(3) {roll.dice3_result}, (4) {roll.dice4_result}, "
        f"(5) {roll.dice5_result}, (6) {roll.dice6_result}"
    )


def print_sample_board(board, args):
    board.updatePriority()
    print("\nBoard state:")
    for cart_num in board.getCarOrder():
        cart = board.getCartInfo(cart_num)
        cart_members = ", ".join(
            f"{character.name} ({character.getMingleCount()})" for character in cart
        )
        if not cart_members:
            cart_members = "empty"
        print(
            f"- {sample_cart_label(cart_num)} cart "
            f"{sample_cart_position(board, cart_num)}/{args.finish}: {cart_members}"
        )


def sample_valid_moves(board, character):
    if character.cart not in (1, 2, 3):
        return []

    cart = board.getCartInfo(character.cart)
    moves = []
    if len(cart) > 1 and cart[-1] != character:
        moves.append("push")
    if cart and cart[0] != character:
        moves.append("elbow")
    if cart and cart[0] == character and sample_cart_priority(board, character.cart) > 1:
        moves.append("jump")
    return moves


def sample_push(board, character):
    cart = board.getCartInfo(character.cart)
    victim = cart[-1]
    print(f"{character.name} pushes {victim.name} from the back of the cart.")

    if sample_cart_priority(board, character.cart) == 3:
        print(f"{victim.name} falls from the last cart.")
        if victim.plague_status:
            print(f"{victim.name} had the plague. {character.name} survives the gamble.")
            board.remove_character(victim)
        else:
            print(f"{victim.name} did not have the plague. {character.name} dies from despair.")
            board.remove_character(victim)
            board.remove_character(character)
        return

    target_cart_num = sample_cart_with_priority(
        board, sample_cart_priority(board, character.cart) + 1
    )
    if target_cart_num is None:
        print("No cart is behind this one, so the push fizzles.")
        return

    cart.pop(-1)
    target_cart = board.getCartInfo(target_cart_num)
    target_cart.insert(0, victim)
    victim.cart = target_cart_num
    print(
        f"{victim.name} lands in the front of the "
        f"{sample_cart_label(target_cart_num).lower()} cart."
    )


def sample_elbow(board, character):
    cart = board.getCartInfo(character.cart)
    cart.remove(character)
    cart.insert(0, character)
    print(f"{character.name} elbows to the front of their cart.")


def sample_jump(board, character):
    target_cart_num = sample_cart_with_priority(
        board, sample_cart_priority(board, character.cart) - 1
    )
    if target_cart_num is None:
        print(f"{character.name} tries to jump, but there is no cart ahead.")
        return

    current_cart = board.getCartInfo(character.cart)
    current_cart.remove(character)
    target_cart = board.getCartInfo(target_cart_num)
    target_cart.append(character)
    character.cart = target_cart_num
    print(
        f"{character.name} jumps into the back of the "
        f"{sample_cart_label(target_cart_num).lower()} cart."
    )


def run_sample_action(board, character, roll, args):
    valid_moves = sample_valid_moves(board, character)
    actions = ["skip", "reroll", "draw"]
    if valid_moves:
        actions.append("move")

    action = random.choice(actions)
    print(f"\nIt is {character.name}'s turn. Sample action: {action}.")

    if action == "draw":
        if character.getNumRemedies() >= 3:
            print(f"{character.name} already has 3 remedies and skips instead.")
            return
        character.drawRemedy(args, None, None)
        return

    if action == "reroll":
        dice_to_reroll = random.sample(list(VALID_DICE), random.randint(1, 2))
        second_die = dice_to_reroll[1] if len(dice_to_reroll) == 2 else None
        if second_die is None:
            print(f"{character.name} rerolls die {dice_to_reroll[0]}.")
        else:
            print(f"{character.name} rerolls dice {dice_to_reroll[0]} and {second_die}.")
        roll.reroll(dice_to_reroll[0], second_die)
        print(f"Current dice: {sample_roll_summary(roll)}")
        return

    if action == "move":
        move = random.choice(valid_moves)
        print(f"{character.name} attempts to {move}.")
        if move == "push":
            sample_push(board, character)
        elif move == "elbow":
            sample_elbow(board, character)
        elif move == "jump":
            sample_jump(board, character)
        return

    print(f"{character.name} skips.")


def resolve_sample_escape(board, cart_num, game, args):
    cart = board.getCartInfo(cart_num)
    if sample_cart_position(board, cart_num) < args.finish or not cart:
        return False

    cart_label = sample_cart_label(cart_num)
    print(f"\n{cart_label} cart has escaped Bristol!")
    plague_result = False
    for character in cart:
        if character.plague_status:
            print(f"{character.name} has the plague!")
            plague_result = True
        else:
            print(f"{character.name} is free of the plague!")

    if not plague_result:
        winners = ", ".join(character.name for character in cart)
        print(f"Congratulations {cart_label.lower()} cart. Winners: {winners}.")
        return True

    for character in list(cart):
        print(f"{character.name} has died from the plague.")
        board.remove_character(character)
    board.displayCarts(game, args)

    if not board.list_of_characters:
        print("There are no more players left alive. Nobody wins!")
        return True

    print(f"There are {len(board.list_of_characters)} players remaining.")
    return False


def play_sample_game(args):
    players = sample_players(args)
    sample_args = argparse.Namespace(
        test=True,
        finish=args.finish,
        mingle_odds=mingle_odds_from_args(args, len(players)),
    )
    game = ConsoleGame()
    game.update_finish_line(sample_args.finish)
    characters = [
        Character(name, f"555000{i + 1:04d}") for i, name in enumerate(players)
    ]

    print("Bristol 1350 sample game")
    print(f"Players ({len(characters)}): {', '.join(players)}")
    print(f"Finish line: {sample_args.finish}\n")
    print(f"Mingle odds for symptoms 1-4: {format_mingle_odds(sample_args.mingle_odds)}\n")
    print("Starting symptoms:")
    for character in characters:
        character.generateStartStatus(sample_args)
        print(f"- {character.name}: {character.plague_statement}")

    board = Board(characters, game, sample_args)
    print_sample_board(board, sample_args)

    for round_num in range(1, SAMPLE_MAX_ROUNDS + 1):
        if not characters:
            print("There are no more players left alive. Nobody wins!")
            return

        print("\n-------------")
        print(f"Round {round_num}")
        print("-------------")

        start_player = board.determineStartPlayer()
        if start_player is None:
            print("There are no more players left alive. Nobody wins!")
            return

        if start_player in characters:
            characters.remove(start_player)
            characters.insert(0, start_player)
        print(f"{start_player.name} is the starting player.")

        roll = Dice()
        roll.updateResults()
        print(f"Rolling dice: {sample_roll_summary(roll)}")

        for character in list(characters):
            if character not in characters:
                continue
            run_sample_action(board, character, roll, sample_args)
            if not characters:
                print("There are no more players left alive. Nobody wins!")
                return

        print("\nEveryone has taken a turn!")
        carts_mingling = roll.checkMingling()
        if carts_mingling:
            for cart_num in carts_mingling:
                board.mingle(cart_num, sample_args, None, None)
        else:
            print("No carts mingled this round.")

        print("\n----------")
        print("Move Phase")
        print("----------")
        for cart_num in board.getCarOrder():
            roll.moveCart(cart_num, board)

        board.updateBoard(characters, game, sample_args)
        print_sample_board(board, sample_args)

        for cart_num in board.getCarOrder():
            if resolve_sample_escape(board, cart_num, game, sample_args):
                return

    print(f"\nSample stopped after {SAMPLE_MAX_ROUNDS} rounds without a winner.")


def run_sample_game(args):
    output_path = os.path.abspath(SAMPLE_GAME_STATE_FILE)
    with open(output_path, "w", encoding="utf-8") as output_file:
        with contextlib.redirect_stdout(output_file):
            play_sample_game(args)

    print(f"Sample game written to {output_path}")


def new_mingle_state():
    return {"symptom_total": 0, "plague_status": False}


def apply_simulated_mingle(state, mingle_odds):
    status1, status2 = generate_mingle_symptoms(mingle_odds)
    symptom_total = status1 + status2
    state["symptom_total"] = symptom_total
    if symptom_total >= 6:
        state["plague_status"] = True


def apply_simulated_mingles(state, mingle_count, mingle_odds):
    for _ in range(mingle_count):
        apply_simulated_mingle(state, mingle_odds)


def mingle_stats(player_count, symptom_total, plague_count, any_plague_count):
    player_trials = MINGLE_SIM_TRIALS * player_count
    return {
        "avg_symptom_total": symptom_total / player_trials,
        "plague_rate": plague_count / player_trials,
        "avg_plague_count": plague_count / MINGLE_SIM_TRIALS,
        "any_plague_rate": any_plague_count / MINGLE_SIM_TRIALS,
    }


def print_mingle_stats_row(prefix, stats):
    print(
        f"{prefix} | {stats['avg_symptom_total']:15.2f} | "
        f"{stats['plague_rate']:18.2%} | {stats['avg_plague_count']:16.2f} | "
        f"{stats['any_plague_rate']:15.2%}"
    )


def save_mingle_graph(filename, title, x_label, series):
    width = 1000
    height = 650
    left = 90
    right = 260
    top = 70
    bottom = 95
    plot_width = width - left - right
    plot_height = height - top - bottom
    all_points = [point for _, points in series for point in points]
    if not all_points:
        return

    x_values = sorted({point[0] for point in all_points})
    x_min = min(x_values)
    x_max = max(x_values)
    if x_min == x_max:
        x_max = x_min + 1

    def x_pos(value):
        return left + ((value - x_min) / (x_max - x_min)) * plot_width

    def y_pos(value):
        return top + (1 - value) * plot_height

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" viewBox="0 0 {0} {1}">'.format(width, height),
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="32" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#111827" stroke-width="1.5"/>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827" stroke-width="1.5"/>',
    ]

    for percent in (0, 25, 50, 75, 100):
        y = y_pos(percent / 100)
        lines.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial" font-size="12" fill="#374151">{percent}%</text>'
        )

    for value in x_values:
        x = x_pos(value)
        lines.append(
            f'<line x1="{x:.2f}" y1="{top + plot_height}" x2="{x:.2f}" y2="{top + plot_height + 6}" stroke="#111827" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{x:.2f}" y="{top + plot_height + 24}" text-anchor="middle" font-family="Arial" font-size="12" fill="#374151">{value}</text>'
        )

    lines.append(
        f'<text x="{left + plot_width / 2}" y="{height - 28}" text-anchor="middle" font-family="Arial" font-size="14" fill="#111827">{html.escape(x_label)}</text>'
    )
    lines.append(
        f'<text x="24" y="{top + plot_height / 2}" transform="rotate(-90 24 {top + plot_height / 2})" text-anchor="middle" font-family="Arial" font-size="14" fill="#111827">Any plague event</text>'
    )

    for index, (label, points) in enumerate(series):
        color = GRAPH_COLORS[index % len(GRAPH_COLORS)]
        point_text = " ".join(
            f"{x_pos(x):.2f},{y_pos(y):.2f}" for x, y in sorted(points)
        )
        lines.append(
            f'<polyline points="{point_text}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        for x, y in sorted(points):
            lines.append(
                f'<circle cx="{x_pos(x):.2f}" cy="{y_pos(y):.2f}" r="4" fill="{color}"/>'
            )

        legend_y = top + 24 + (index * 26)
        legend_x = left + plot_width + 35
        lines.append(
            f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 28}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>'
        )
        lines.append(
            f'<text x="{legend_x + 38}" y="{legend_y + 4}" font-family="Arial" font-size="13" fill="#111827">{html.escape(label)}</text>'
        )

    lines.append("</svg>")
    with open(filename, "w", encoding="utf-8") as graph_file:
        graph_file.write("\n".join(lines))


def run_base_mingle_scenario(cart_size, cart_mingles, mingle_odds):
    symptom_total = 0
    plague_count = 0
    any_plague_count = 0

    for _ in range(MINGLE_SIM_TRIALS):
        players = [new_mingle_state() for _ in range(cart_size)]
        for player in players:
            apply_simulated_mingles(player, cart_mingles, mingle_odds)

        trial_plagues = sum(1 for player in players if player["plague_status"])
        symptom_total += sum(player["symptom_total"] for player in players)
        plague_count += trial_plagues
        if trial_plagues > 0:
            any_plague_count += 1

    stats = mingle_stats(cart_size, symptom_total, plague_count, any_plague_count)
    print_mingle_stats_row(f"{cart_size:9d} | {cart_mingles:12d}", stats)
    return stats


def run_switch_mingle_scenario(
    final_cart_size,
    switch_count,
    existing_prior_mingles,
    switch_prior_mingles,
    mingle_odds,
):
    existing_count = final_cart_size - switch_count
    symptom_total = 0
    plague_count = 0
    switch_plague_count = 0
    any_plague_count = 0

    for _ in range(MINGLE_SIM_TRIALS):
        existing_players = [new_mingle_state() for _ in range(existing_count)]
        switch_players = [new_mingle_state() for _ in range(switch_count)]

        for player in existing_players:
            apply_simulated_mingles(player, existing_prior_mingles, mingle_odds)
        for player in switch_players:
            apply_simulated_mingles(player, switch_prior_mingles, mingle_odds)

        players = existing_players + switch_players
        for player in players:
            apply_simulated_mingle(player, mingle_odds)

        trial_plagues = sum(1 for player in players if player["plague_status"])
        symptom_total += sum(player["symptom_total"] for player in players)
        plague_count += trial_plagues
        switch_plague_count += sum(
            1 for player in switch_players if player["plague_status"]
        )
        if trial_plagues > 0:
            any_plague_count += 1

    stats = mingle_stats(
        final_cart_size, symptom_total, plague_count, any_plague_count
    )
    switch_plague_rate = switch_plague_count / (MINGLE_SIM_TRIALS * switch_count)
    stats["switch_plague_rate"] = switch_plague_rate
    print(
        f"{final_cart_size:10d} | {switch_count:9d} | "
        f"{existing_prior_mingles:14d} | {switch_prior_mingles:12d} | "
        f"{stats['avg_symptom_total']:15.2f} | "
        f"{stats['plague_rate']:18.2%} | {stats['avg_plague_count']:16.2f} | "
        f"{stats['switch_plague_rate']:15.2%} | {stats['any_plague_rate']:15.2%}"
    )
    return stats


def mingle_graph_files(graph_suffix, multiple_profiles):
    if not multiple_profiles:
        return MINGLE_BASE_GRAPH_FILE, MINGLE_SWITCH_GRAPH_FILE

    return (
        f"mingle_base_cart_{graph_suffix}.svg",
        f"mingle_switch_in_{graph_suffix}.svg",
    )


def run_mingle_simulation_for_profile(
    profile_label, mingle_odds, graph_suffix, multiple_profiles
):
    base_graph_file, switch_graph_file = mingle_graph_files(
        graph_suffix, multiple_profiles
    )
    print("Bristol 1350 mingle simulation")
    print(f"Player-count profile: {profile_label}")
    print(f"Trials per scenario: {MINGLE_SIM_TRIALS:,}")
    print(f"Max people per cart: {MINGLE_SIM_MAX_CART_SIZE}")
    print(f"Mingle odds for symptoms 1-4: {format_mingle_odds(mingle_odds)}")

    print("\nBase cart scenarios")
    print(
        "Cart size | Cart mingles | Avg symptom sum | Plague rate/player | "
        "Avg plague count | Any plague event"
    )
    print("-" * 98)
    base_graph_points = {}
    for cart_size in range(1, MINGLE_SIM_MAX_CART_SIZE + 1):
        base_graph_points[cart_size] = []
        for cart_mingles in MINGLE_SIM_BASE_CART_MINGLE_COUNTS:
            stats = run_base_mingle_scenario(cart_size, cart_mingles, mingle_odds)
            base_graph_points[cart_size].append(
                (cart_mingles, stats["any_plague_rate"])
            )
        if cart_size < MINGLE_SIM_MAX_CART_SIZE:
            print()

    print("\nSwitch-in scenarios")
    print("Players switch in, then everyone in the destination cart mingles once.")
    print(
        "Switch graph total mingles = existing prior + switch prior + 1 shared mingle."
    )
    print(
        "Final size | Switchers | Existing prior | Switch prior | Avg symptom sum | "
        "Plague rate/player | Avg plague count | Switcher plague/player | "
        "Any plague event"
    )
    print("-" * 143)
    switch_graph_points = {}
    for final_cart_size in range(2, MINGLE_SIM_MAX_CART_SIZE + 1):
        for switch_count in range(1, final_cart_size):
            switch_key = (final_cart_size, switch_count)
            switch_graph_points[switch_key] = {}
            for existing_prior_mingles in MINGLE_SIM_SWITCH_EXISTING_PRIOR_MINGLES:
                for switch_prior_mingles in MINGLE_SIM_SWITCH_PRIOR_MINGLES:
                    stats = run_switch_mingle_scenario(
                        final_cart_size,
                        switch_count,
                        existing_prior_mingles,
                        switch_prior_mingles,
                        mingle_odds,
                    )
                    total_mingles = (
                        existing_prior_mingles + switch_prior_mingles + 1
                    )
                    switch_graph_points[switch_key].setdefault(
                        total_mingles, []
                    ).append(stats["any_plague_rate"])

    base_series = [
        (f"Cart size {cart_size}", points)
        for cart_size, points in sorted(base_graph_points.items())
    ]
    switch_series = []
    for (final_cart_size, switch_count), points_by_total in sorted(
        switch_graph_points.items()
    ):
        averaged_points = [
            (total_mingles, sum(values) / len(values))
            for total_mingles, values in sorted(points_by_total.items())
        ]
        switch_series.append(
            (
                f"Final {final_cart_size}, {switch_count} switcher"
                f"{'' if switch_count == 1 else 's'}",
                averaged_points,
            )
        )

    save_mingle_graph(
        base_graph_file,
        "Base Cart Any Plague Event",
        "Total mingles",
        base_series,
    )
    save_mingle_graph(
        switch_graph_file,
        "Switch-In Any Plague Event",
        "Total mingles",
        switch_series,
    )
    print("\nGraphs written:")
    print(f"- {os.path.abspath(base_graph_file)}")
    print(f"- {os.path.abspath(switch_graph_file)}")


def run_mingle_simulation(args):
    profiles = mingle_profiles_from_args(args)
    multiple_profiles = len(profiles) > 1
    for index, (profile_label, mingle_odds, graph_suffix) in enumerate(profiles):
        if index > 0:
            print("\n" + "=" * 80 + "\n")
        run_mingle_simulation_for_profile(
            profile_label, mingle_odds, graph_suffix, multiple_profiles
        )


def main():
    args = parse_args()
    if args.sample:
        run_sample_game(args)
        return

    if args.mingle:
        run_mingle_simulation(args)
        return

    root = None
    if not args.players:
        if args.no_gui:
            print("Players are required when running without the GUI launcher.")
            sys.exit(2)
        args, root = run_launch_screen(args)

    gameOver = False

    registered_users, account_sid, auth_token = load_registration_config(args)
    ensure_sms_dependencies(args)

    game = create_game_display(args, root=root)
    game.update_finish_line(args.finish)

    list_of_characters = introsequence(args, account_sid, auth_token, registered_users)
    print("\n")

    board = Board(list_of_characters, game, args)
    board.displayCarts(game, args)
    gameOver = False
    finalRound = False
    while gameOver == False:
        if not list_of_characters:
            print("There are no more players left alive. Nobody wins!")
            sys.exit(0)

        print(f"\n-------------")
        print(f"Action Phase")
        print(f"-------------")
        if finalRound:
            print(f"This is the final round!")
        start_player = board.determineStartPlayer()
        if start_player is None:
            print("There are no more players left alive. Nobody wins!")
            sys.exit(0)

        print(f"\n{start_player.name} is the starting player!\n")
        game.log_action(f"{start_player.name} starts the round.")
        tmp = start_player
        if tmp in list_of_characters:
            list_of_characters.remove(tmp)
            list_of_characters.insert(0, tmp)
        if args.character:
            print("(A) Use Ability, (R) Reroll, (D) Draw Remedy, (M) Move Character, (U) Use Remedy, (V) View rolled dice, (S) Skip turn \n")
        else:
            print("(R) Reroll, (D) Draw Remedy, (M) Move Character, (U) Use Remedy, (V) View rolled dice, (S) Skip turn \n")
        print(f"\nRolling dice:\n")
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
        game.update_order(list_of_characters)

        for character in list(list_of_characters):
            if character not in list_of_characters:
                continue

            game.update_order(list_of_characters, character)
            finished = False
            while finished == False:
                try:
                    if character.getOutlaw():
                        odds = random.randint(1,3)
                        mariokart = character.getCart()
                        print(f"\n{character.name} is the outlaw, and is attempting to steal a remedy... \n")
                        if odds == mariokart:
                            print(Fore.GREEN + f"Congratulations {character.name}! You got a free remedy\n" + bcolors.RESET)
                            if character.drawRemedy(args, account_sid, auth_token) == True:
                                game.log_action(
                                    f"{character.name} stole a remedy and now has "
                                    f"{remedy_count_text(character.getNumRemedies())}."
                                )
                                finished = False
                            else:
                                game.log_action(f"{character.name}'s Outlaw steal fizzled.")
                                finished = False
                        else:
                            print(Fore.RED, Style.BRIGHT + f"Sorry {character.name}, better luck next time!\n" + bcolors.RESET)
                            game.log_action(f"{character.name}'s Outlaw steal failed.")
                except Exception as e:
                    print("\nAn error occurred when using the outlaw.", e,"\n")

                print(
                    f"\nIt is {character.name}'s turn. What would {character.name} like to do? :"
                )
                player_input = input()
                ability_log_detail = None

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
                                    ability_log_detail = (
                                        f"{character.name} used Mason to reroll die {reroll1} "
                                        f"and lock die {getlock1}."
                                    )
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
                                    if finished:
                                        ability_log_detail = (
                                            f"{character.name} used Friar to change die {reroll1}; "
                                            f"now {dice_results_for_log(initial_roll, [int(reroll1)])}."
                                        )
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
                                    rat_king_dice = [int(reroll1)]
                                    if reroll2 in {"1", "2", "3", "4", "5", "6"}:
                                        rat_king_dice.append(int(reroll2))
                                    dice_word = "die" if len(rat_king_dice) == 1 else "dice"
                                    ability_log_detail = (
                                        f"{character.name} used Rat King on {dice_word} "
                                        f"{', '.join(str(die) for die in rat_king_dice)}; "
                                        f"now {dice_results_for_log(initial_roll, rat_king_dice)}."
                                    )
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
                                    ability_log_detail = (
                                        f"{character.name} used Drunkard to turn die {reroll1} "
                                        f"into a rat for {cart_label(carttype)}."
                                    )
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
                                    ability_log_detail = (
                                        f"{character.name} used Sheriff to privately inspect "
                                        f"{list_of_characters[int(charInput)].name}'s symptoms."
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
                                        board.knight_action(
                                            list_of_characters[int(knight_input)], 1, actor=character
                                        )
                                    elif list_of_characters[int(knight_input)].cart == 2:
                                        #position = Board.cart2.index(list_of_characters[int(knight_input)])
                                        board.knight_action(
                                            list_of_characters[int(knight_input)], 2, actor=character
                                        )
                                    elif list_of_characters[int(knight_input)].cart == 3:
                                        #position = Board.cart3.index(list_of_characters[int(knight_input)])
                                        board.knight_action(
                                            list_of_characters[int(knight_input)], 3, actor=character
                                        )
                                    ability_log_detail = board.action_log_message(
                                        f"{character.name} used Knight."
                                    )
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
                                        ability_log_detail = (
                                            f"{character.name} used Countess to privately choose "
                                            "1 of 2 remedy cards."
                                        )
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
                                    ability_log_detail = (
                                        f"{character.name} used Chandler to privately resolve a symptom."
                                    )
                                finished = True
                            except Exception as e:
                                print("\nAn error occurred when using the chandler.", e,"\n")
                                finished = False         

                if player_input.lower() == "a" and args.character and finished:
                    game.log_action(
                        ability_log_detail
                        or f"{character.name} used {character.charactertype}."
                    )

                if player_input.lower() == "d":
                    if character.drawRemedy(args, account_sid, auth_token) == True:
                        finished = True
                        game.log_action(
                            f"{character.name} drew a remedy and now has "
                            f"{remedy_count_text(character.getNumRemedies())}."
                        )
                    else:
                        finished = False

                if player_input.lower() == "m":
                    move_input = input(f"\nSelect a movement action: (E) Elbow, (J) Jump, (P) Push")
                    if move_input.lower() == "e":
                        if board.elbow(character, args.test, account_sid, auth_token) == True:
                            finished = True
                            board.displayCarts(game, args)
                            game.log_action(
                                board.action_log_message(f"{character.name} elbowed.")
                            )
                        else:
                            finished = False

                    elif move_input.lower() == "j":
                        if board.jump(character, args.test, account_sid, auth_token) == True:
                            finished = True
                            board.displayCarts(game, args)
                            game.log_action(
                                board.action_log_message(f"{character.name} jumped.")
                            )
                        else:
                            finished = False

                    elif move_input.lower() == "p":
                        if board.push(character, args.test, account_sid, auth_token) == True:
                            finished = True
                            board.displayCarts(game, args)
                            game.log_action(
                                board.action_log_message(f"{character.name} pushed.")
                            )
                        else:
                            finished = False

                if player_input.lower() == "s":
                    finished = True
                    game.log_action(
                        f"{character.name} skipped their action on {cart_label(character.cart)}."
                    )

                if player_input.lower() == "u":
                    if not character.remedycard1:
                        print(f"\nSorry{character.name}, you don't have any remedy cards!")
                        finished = False
                    else:
                        remedy_input = input(f"\nSelect a remedy card to use: (A) Arsenic, (C) Crushed Emeralds, (T) Turkey")
                        if remedy_input.lower() == "t":
                            if character.hasTurkey():
                                print("\nGobble gobble\n")
                                turkey_dice = [
                                    die_value_from_input(input("Select the first dice to reroll (1-6):")),
                                    die_value_from_input(input("Select the second dice to reroll (1-6):")),
                                    die_value_from_input(input("Select the third dice to reroll (1-6):")),
                                    die_value_from_input(input("Select the fourth dice to reroll (1-6):")),
                                ]
                                if None in turkey_dice or not validate_reroll_dice(initial_roll, turkey_dice):
                                    finished = False
                                    continue

                                initial_roll.reroll(turkey_dice[0], turkey_dice[1])
                                initial_roll.reroll(turkey_dice[2], turkey_dice[3])
                                print(
                                    f"\nRerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}\n"
                                )
                                update_all_dice(game, initial_roll)
                                character.removeCard(5, args.test, account_sid, auth_token)
                                game.log_action(
                                    f"{character.name} used Turkey to reroll dice "
                                    f"{', '.join(str(die) for die in turkey_dice)}; "
                                    f"now {dice_results_for_log(initial_roll, turkey_dice)}."
                                )
                                finished = True
                            else:
                                print(
                                    f"\nSorry {character.name}, you don't appear to have a turkey!\n"
                                )
                                finished = False

                        elif remedy_input.lower() == "a":
                            if character.hasRemedies():
                                if character.hasArsenic():
                                    getlock1 = die_value_from_input(input(f"Get first dice to lock (1-6):"))
                                    getlock2 = die_value_from_input(input(f"Get second dice to lock (1-6):"))
                                    if getlock1 is None or getlock2 is None:
                                        finished = False
                                        continue
                                    if getlock1 == getlock2:
                                        print("Select two different dice.")
                                        finished = False
                                        continue

                                    lock_die(initial_roll, getlock1)
                                    lock_die(initial_roll, getlock2)
                                    print(
                                        f"{character.name} has successfully locked dice {getlock1} and {getlock2}!"
                                    )
                                    game.update_lock_symbol(getlock1, True, False)
                                    game.update_lock_symbol(getlock2, True, False)
                                    character.removeCard(1, args.test, account_sid, auth_token)
                                    game.log_action(
                                        f"{character.name} used Arsenic to lock dice "
                                        f"{getlock1} and {getlock2}."
                                    )
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
                    if all(
                        [
                            initial_roll.dice1_lock,
                            initial_roll.dice2_lock,
                            initial_roll.dice3_lock,
                            initial_roll.dice4_lock,
                            initial_roll.dice5_lock,
                            initial_roll.dice6_lock,
                        ]
                    ):
                        print(f"There are no unlocked dice! Unable to reroll!")
                        finished = False
                        continue

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

                    reroll1 = die_value_from_input(
                        input("Select the first dice to reroll (1-6, b to cancel):"),
                        allow_back=True,
                    )
                    if reroll1 in (None, "back"):
                        finished = False
                        continue

                    reroll2 = die_value_from_input(
                        input("Select the second dice to reroll (1-6, 0 for one die, b to cancel):"),
                        allow_zero=True,
                        allow_back=True,
                    )
                    if reroll2 in (None, "back"):
                        finished = False
                        continue

                    selected_dice = [reroll1] if reroll2 == 0 else [reroll1, reroll2]
                    if not validate_reroll_dice(initial_roll, selected_dice):
                        finished = False
                        continue

                    second_die = None if reroll2 == 0 else reroll2
                    if second_die is None:
                        print(f"Rerolling dice {reroll1}")
                    else:
                        print(f"Rerolling dice {reroll1} and {second_die}")
                    initial_roll.reroll(reroll1, second_die)
                    print(
                        f"Rerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                    )
                    update_all_dice(game, initial_roll)
                    if second_die is None:
                        game.log_action(
                            f"{character.name} rerolled die {reroll1}; "
                            f"now {dice_results_for_log(initial_roll, selected_dice)}."
                        )
                    else:
                        game.log_action(
                            f"{character.name} rerolled dice {reroll1} and {second_die}; "
                            f"now {dice_results_for_log(initial_roll, selected_dice)}."
                        )

                    if second_die is not None and character.hasRemedies():
                        useChicken = input(
                            f"Would you like to use a chicken to reroll these dice? (y/n):"
                        )
                        if useChicken.lower() == "y":
                            if character.hasChicken():
                                chicken_rerolls = 0
                                for remaining in (2, 1, 0):
                                    print(f"Rerolling dice {reroll1} and {second_die}")
                                    initial_roll.reroll(reroll1, second_die)
                                    chicken_rerolls += 1
                                    print(
                                        f"Rerolled dice to: (1) {initial_roll.dice1_result}, (2) {initial_roll.dice2_result}, (3) {initial_roll.dice3_result}, (4) {initial_roll.dice4_result}, (5) {initial_roll.dice5_result}, (6) {initial_roll.dice6_result}"
                                    )
                                    update_all_dice(game, initial_roll)
                                    if remaining == 0:
                                        break

                                    use_more_chicken = input(
                                        f"Would you like to use a chicken to reroll these dice ({remaining} rerolls remaining)? (y/n):"
                                    )
                                    if use_more_chicken.lower() != "y":
                                        break
                                character.removeCard(2, args.test, account_sid, auth_token)
                                extra_time_word = (
                                    "time" if chicken_rerolls == 1 else "times"
                                )
                                game.log_action(
                                    f"{character.name} used Chicken to reroll dice "
                                    f"{reroll1} and {second_die} {chicken_rerolls} more "
                                    f"{extra_time_word}; now "
                                    f"{dice_results_for_log(initial_roll, selected_dice)}."
                                )
                            else:
                                print(
                                    f"\nSorry {character.name}, you don't appear to have a chicken remedy!"
                                )

                    finished = True
                    continue
        print("Everyone has taken a turn!")
        game.log_action("Everyone has taken a turn.")
        game.update_lock_symbol(1,False, True)
        game.update_lock_symbol(2,False, True)
        game.update_lock_symbol(3,False, True)
        game.update_lock_symbol(4,False, True)
        game.update_lock_symbol(5,False, True)
        game.update_lock_symbol(6,False, True)

        tingle_mingle = initial_roll.checkMingling()
        if len(tingle_mingle) == 0:
            print("No one is mingling! Very hygenic :)")
            game.log_action("No carts mingled this round.")
        else:
            for cart in tingle_mingle:
                board.mingle(cart, args, account_sid, auth_token)
                game.log_action(
                    f"{cart_label(cart).capitalize()} mingled; affected players received updated symptoms."
                )
        input("Press enter to continue into the cart movement phase.")
        print("\n-------------------")
        print("Cart Movement Phase")
        print("-------------------")
        game.log_action("Cart movement phase started.")

        initial_roll.moveCart(1, board)
        initial_roll.moveCart(2, board)
        initial_roll.moveCart(3, board)
        game.log_action(
            f"Carts moved: blue {board.cart1_position}/{args.finish}, "
            f"yellow {board.cart2_position}/{args.finish}, "
            f"purple {board.cart3_position}/{args.finish}."
        )

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
