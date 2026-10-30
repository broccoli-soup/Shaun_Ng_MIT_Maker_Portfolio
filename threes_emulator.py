import matplotlib.pyplot as plt
import random
import os 
from threes_logic import * 
from threes_ai import * 
board = [[6, 3, 48, 192], [3, 0, 3, 48], [0, 3, 3, 3], [1, 0, 0, 2]]
fig, ax = plt.subplots()
ax.set_xlim(0, 4)
ax.set_ylim(0, 4)
ax.set_xticks([])
ax.set_yticks([])

tiles = []
texts = []

def plot_board():
    # plots the literal board (lines)
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

def update_board():
    # plots the text
    for row in range(4):
        for col in range(4):
            value = board[row][col]

            colors = {0: "#ffffff", 1: "#e68383", 2: "#8ebdde"}
            tiles[row][col].set_facecolor(colors.get(value, "#dddddd"))

            texts[row][col].set_text("" if value == 0 else str(value))

    fig.canvas.draw_idle()

deck = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
random.shuffle(deck)

def move_board(event):
    global board, deck

    moves_func = {
        "up": swipe_up,
        "down": swipe_down,
        "left": swipe_left,
        "right": swipe_right
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

    # wait 0.05 seconds so you can see the move
    plt.pause(0.05)

    # draw next tile with complex deck system which *slightly* more accurately emulates threes*
    if not deck:
        deck = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
        random.shuffle(deck)

    if random.random() > 1/21:
        next_tile = deck.pop()
    else:
        next_tile = random.choice([4, 5, 6])

    # actually spawn the tile
    spawn_locs = spawn_locations(board_id, 
        ["down", "up", "right", "left"].index(event.key))

    if spawn_locs:
        target_idx = random.choice(spawn_locs)
        board_id = place(board_id, target_idx, next_tile)

    board = to_human(decode_board(board_id))
    update_board()

plot_board()
update_board()

fig.canvas.mpl_connect("key_press_event", move_board)

plt.show()
