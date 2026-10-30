BOARD_SIZE = 4
ROW_BITS = 16
TILE_BITS = 4
ROW_MASK = 0xFFFF
TILE_MASK = 0xF


def can_merge(a: int, b: int):
    """
    determines whether two encoded tiles can merge.
    returns the encoded value of the merged tile if a merge is possible. -1 if not. 
    """
    if a == 0 or b == 0:
        return -1

    if {a, b} == {1, 2}:
        return 3

    if a >= 3 and a == b:
        return a + 1

    return -1


def swipe(row: list):
    """
    performs a leftward swipe on an encoded row according to threes' game logic
    """
    for i in range(BOARD_SIZE - 1):
        if row[i] == 0:
            row[i:-1] = row[i + 1:]
            row[-1] = 0
            break

        merge_val = can_merge(row[i], row[i + 1])

        if merge_val != -1:
            row[i] = merge_val
            row[i + 1:-1] = row[i + 2:]
            row[-1] = 0
            break

    return row


# human readable tile values -> computer encodings 
htc = {
    0: 0, 1: 1, 2: 2, 3: 3,
    6: 4, 12: 5, 24: 6, 48: 7,
    96: 8, 192: 9, 384: 10, 768: 11,
    1536: 12, 3072: 13, 6144: 14,
    12288: 15
}

# computer encodings -> human readable tile values
cth = {
    0: 0, 1: 1, 2: 2, 3: 3,
    4: 6, 5: 12, 6: 24, 7: 48,
    8: 96, 9: 192, 10: 384, 11: 768,
    12: 1536, 13: 3072, 14: 6144, 15: 12288
}


def to_computer(board):
    """
    convert board to computer encodings
    """
    return [
        [htc[tile] for tile in row]
        for row in board
    ]


def to_human(board):
    """
    convert computer encodings to readable board
    """
    return [
        [cth[tile] for tile in row]
        for row in board
    ]


def encode_row(row: list):
    """
    represent 4x1 row as a 16-bit integer :) 
    """
    b = 0

    for i, x in enumerate(row):
        b |= x << (12 - 4 * i) # magic 

    return b


def decode_row(b: int):
    """
    decode 16 bit integer as 4x1 row 
    """
    return [
        (b >> (12 - 4 * i)) & TILE_MASK
        for i in range(BOARD_SIZE)
    ]


def encode_board(board: list):
    """
    repeats encode_row method 4 times to encode the whole board
    """
    board_id = 0

    for i, row in enumerate(board):
        board_id |= encode_row(row) << (48 - 16 * i)

    return board_id


def decode_board(board_id: int):
    """
    repeats decode_row method 4 times to decode the whole board
    """
    return [
        decode_row(
            (board_id >> (48 - 16 * i)) & ROW_MASK
        )
        for i in range(BOARD_SIZE)
    ]


def reverse_row(row_id):
    """
    reverse order of 4 tiles on a row. this is used later to do right swaps
    """
    return (
        ((row_id & 0xF000) >> 12)
        | ((row_id & 0x0F00) >> 4)
        | ((row_id & 0x00F0) << 4)
        | ((row_id & 0x000F) << 12)
    )


def fluidity(t):
    """
    CUSTOM heuristic capturing "fluidity" or how "monotone" the distribution of tile values is
    """
    penalty = 0

    for i in range(BOARD_SIZE - 1):
        a, b = t[i], t[i + 1]

        # don't care about empty tiles
        if a == 0 or b == 0:
            continue

        diff = abs(a - b)

        # large jumps between adjacent tiles are penalized
        if diff > 1:
            penalty += diff ** 2

        if i < BOARD_SIZE - 2:
            c = t[i + 2]

            if c > 0:
                is_peak = a < b > c
                is_valley = a > b < c

                # Penalize changes in monotonic direction.
                if is_peak or is_valley:
                    penalty += 2 * max(a, b, c) ** 2

    return penalty


# precompute every 16-bit row operation (left-right)
left_swipe_table = {}
right_swipe_table = {}
fluidity_table = {}

for row_enc in range(1 << ROW_BITS):
    row = decode_row(row_enc)

    fluidity_table[row_enc] = fluidity(row)
    left_swipe_table[row_enc] = encode_row(swipe(row.copy()))

    reversed_row = decode_row(reverse_row(row_enc))
    right_swipe_table[row_enc] = reverse_row(
        encode_row(swipe(reversed_row))
    )


def swipe_left(board_id: int):
    """
    leftward swipe on board
    """
    rows = [
        (board_id >> (48 - 16 * i)) & ROW_MASK
        for i in range(BOARD_SIZE)
    ]

    rows = [left_swipe_table[row] for row in rows]

    return (
        (rows[0] << 48)
        | (rows[1] << 32)
        | (rows[2] << 16)
        | rows[3]
    )


def swipe_right(board_id: int):
    """
    rightward swipe on board
    """
    rows = [
        (board_id >> (48 - 16 * i)) & ROW_MASK
        for i in range(BOARD_SIZE)
    ]

    rows = [right_swipe_table[row] for row in rows]

    return (
        (rows[0] << 48)
        | (rows[1] << 32)
        | (rows[2] << 16)
        | rows[3]
    )


def fluidity_(row_id):
    """
    retrieve fluidity_table[row_id]
    """
    return fluidity_table[row_id]


def transpose(board_id: int):
    """
    transpose board_id across diagonal such that "up" moves become left moves. 
    """
    out = 0

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            val = (
                board_id >> (16 * i + 4 * j)
            ) & TILE_MASK

            out |= val << (16 * j + 4 * i)

    return out


def swipe_up(board_id: int):
    """
    swipe up on a board_id (args: board_id)
    """
    return transpose(
        swipe_left(transpose(board_id))
    )


def swipe_down(board_id: int):
    """
    swipe down on a board_id (args: board_id)
    """
    return transpose(
        swipe_right(transpose(board_id))
    )


def pretty_print(board):
    # relic of some nonsense and debugging ? 
    import traceback

    # print("\nPRETTY_PRINT CALLED FROM:")
    # traceback.print_stack()
    for row in board:
        print(*row)


def get_tile(board_id, r, c):
    """
    returns tile at (row, column) in computer-encodings
    """
    return (
        board_id >> (16 * r + 4 * c)
    ) & TILE_MASK
