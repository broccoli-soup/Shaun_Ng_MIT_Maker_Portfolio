import matplotlib.pyplot as plt
import random
import os
import time
from threes_logic import *
from threes_ai import *

mode = input("Choose mode: (1) Play the game yourself! or (2) Watch the computer play! ")

while mode not in ["1", "2"]:
    mode = input("Invalid choice. Enter 1 or 2: ")

board = [[6, 3, 48, 192], [3, 0, 3, 48], [0, 3, 3, 3], [1, 0, 0, 2]]

fig, ax = plt.subplots()
ax.set_xlim(0, 4)
ax.set_ylim(0, 4.5)
ax.set_xticks([])
ax.set_yticks([])

tiles = []
texts = []

def plot_board():
    for row in range(4):
        tile_row = []
        text_row = []

        for col in range(4):
            rect = plt.Rectangle((col, 3-row), 1, 1,
                                 facecolor="whitesmoke",
                                 edgecolor="black")
            ax.add_patch(rect)

            txt = ax.text(col+0.5, 3-row+0.5, "",
                          ha="center", va="center", fontsize=20)

            tile_row.append(rect)
            text_row.append(txt)

        tiles.append(tile_row)
        texts.append(text_row)

score_text = ax.text(
    2, 4.25, "",
    ha="center", va="center",
    fontsize=16, fontweight="bold"
)

def update_board():
    for row in range(4):
        for col in range(4):
            value = board[row][col]

            colors = {0: "#ffffff", 1: "#e68383", 2: "#8ebdde"}
            tiles[row][col].set_facecolor(colors.get(value, "#dddddd"))

            texts[row][col].set_text("" if value == 0 else str(value))

    board_id = encode_board(to_computer(board))
    li = [(board_id >> (4*i)) & 0xF for i in range(16)]
    canonical_score = sum(score_tile(tile) for tile in li)

    score_text.set_text(f"Score: {canonical_score}")

    fig.canvas.draw_idle()

deck = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
random.shuffle(deck)

def draw_next_tile(board_id):
    global board, deck

    if not deck:
        deck = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
        random.shuffle(deck)

    if random.random() > 1/21:
        next_tile = deck.pop()
    else:
        next_tile = random.choice([4, 5, 6])

    spawn_locs = spawn_locations(board_id, 
        ["down", "up", "right", "left"].index(current_move))

    if spawn_locs:
        target_idx = random.choice(spawn_locs)
        board_id = place(board_id, target_idx, next_tile)

    board = to_human(decode_board(board_id))
    update_board()

def move_board(event):
    global board, deck, current_move

    moves_func = {
        "down": swipe_down,
        "up": swipe_up,
        "right": swipe_right,
        "left": swipe_left
    }

    if event.key not in moves_func:
        return

    board_id = encode_board(to_computer(board))

    new_board_id = moves_func[event.key](board_id)

    if new_board_id == board_id:
        return

    board_id = new_board_id
    board = to_human(decode_board(board_id))

    update_board()
    plt.pause(0.05)

    current_move = event.key
    draw_next_tile(board_id)

def play_human():
    fig.canvas.mpl_connect("key_press_event", move_board)
    plt.show()

def play_computer(MAX_DEPTH):
    global board, deck

    step = 0

    while plt.fignum_exists(fig.number):
        STARTER_TIME = time.time()

        board_id = encode_board(to_computer(board))

        if not deck:
            deck = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
            random.shuffle(deck)

        if random.random() > 1/21:
            next_tile = deck.pop()
        else:
            next_tile = random.choice([4, 5, 6])

        distinct = count_distinct_tiles(board_id)
        depth = min(max(2 * (distinct - 2), 4), MAX_DEPTH)

        if next_tile in [1, 2, 3]:
            idx = best_move(board_id, depth=depth, next_tile=[next_tile])
        else:
            idx = best_move(board_id, depth=depth, next_tile=[4, 5, 6])

        if idx == -1:
            print("GAME OVER")

            final_tiles = [(board_id >> (4*i)) & 0xF for i in range(16)]
            print(f"Final Score: {sum(score_tile(t) for t in final_tiles)}")
            break

        moves_func = [swipe_down, swipe_up, swipe_right, swipe_left]
        move_names = ["DOWN", "UP", "RIGHT", "LEFT"]

        board_id = moves_func[idx](board_id)
        board = to_human(decode_board(board_id))

        update_board()
        plt.pause(0.01)

        spawn_locs = spawn_locations(board_id, idx)

        if spawn_locs:
            target_idx = random.choice(spawn_locs)
            board_id = place(board_id, target_idx, next_tile)

        board = to_human(decode_board(board_id))
        update_board()

        print(f"Step: {step} | AI Swiped: {move_names[idx]} | Next Tile: {next_tile}")

        ENDER_TIME = time.time()
        print(f"Time: {ENDER_TIME - STARTER_TIME:.3f}s")

        step += 1

    plt.show()

plot_board()
update_board()

if mode == "1":
    play_human()
else:
    MAX_DEPTH = int(input("\nInput evaluation depth (suggested: 6 for fast play, 10 for slower play) "))
    play_computer(MAX_DEPTH)