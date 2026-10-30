
from threes_logic import *

import time
import random


def score_tile(num: int):
    """
    calculate OFFICIAL threes' score contribution of an encoded tile value. 
    recall that 0/1/2 encodings (corresponding to 0/1/2 tiles) contribute nothing. while 3 contributes 3, 6, contributes 9, 12 contributes 27, et cetera. 
    """
    if num < 3:
        return 0
    else:
        return 3 ** (num - 2)


def cm(a: int, b: int):
    """
    compute the merge compatability of two adjacent encoded tiles

    Returns:
        1    if the tiles can merge.
        -0.5 if two 1s or two 2s are adjacent.
        0    otherwise.

    This is used as a heuristic for counting nearby merge opportunities.
    also, this is a repeat of the can_merge function but just works on encoded tiles. 
    """

    # empty tiles aren't a part of this
    if a == 0 or b == 0:
        return 0

    # 1 + 2 = 3
    if (a == 1 and b == 2) or (a == 2 and b == 1):
        return 1

    # NEGATIVE penalty on 1s and 2s. When I play threes, I always fail because of this so...
    if (a == 1 and b == 1) or (a == 2 and b == 2):
        return -0.5

    # if tiles above 3 are identical, they can merge
    if a >= 3 and a == b:
        return 1

    return 0


def score(board_id: int):
    """
    evaluate an encoded board using a heuristic scoring function.

    consider:
        - canonical Threes score.
        - number of possible adjacent merges.
        - number of empty tiles.
        - whether the largest tile is in a corner.
        - board fluidity / monotonic structure (summed across all rows/columns)

    Returns 0 if the board is full and has no possible merges.
    """
    # extract all sixteen 4-bit encoded tiles from the 64-bit board.
    li = [
        (board_id >> (4 * i)) & 0xF
        for i in range(16)
    ]

    # count horizontal merge opportunities.
    r0 = cm(li[0], li[1]) + cm(li[1], li[2]) + cm(li[2], li[3])
    r1 = cm(li[4], li[5]) + cm(li[5], li[6]) + cm(li[6], li[7])
    r2 = cm(li[8], li[9]) + cm(li[9], li[10]) + cm(li[10], li[11])
    r3 = cm(li[12], li[13]) + cm(li[13], li[14]) + cm(li[14], li[15])

    # count vertical merge opportunities.
    c0 = cm(li[0], li[4]) + cm(li[4], li[8]) + cm(li[8], li[12])
    c1 = cm(li[1], li[5]) + cm(li[5], li[9]) + cm(li[9], li[13])
    c2 = cm(li[2], li[6]) + cm(li[6], li[10]) + cm(li[10], li[14])
    c3 = cm(li[3], li[7]) + cm(li[7], li[11]) + cm(li[11], li[15])

    # total heuristic merge score across the board.
    count_merge = r0 + r1 + r2 + r3 + c0 + c1 + c2 + c3

    # empty spaces increase board flexibility.
    count_zeros = li.count(0)

    # reward boards that keep the largest tile in a corner.
    max_in_corner = (
        max(li) == li[0]
        or max(li) == li[3] # THESE ARE FOR NORMAL
        or max(li) == li[12]
        or max(li) == li[15]
    )

    # calculate the board's official Threes score.
    canonical_score = sum(
        score_tile(tile)
        for tile in li
    )

    # calculate fluidity penalties for each row.
    r0 = fluidity_(encode_row([li[0], li[1], li[2], li[3]]))
    r1 = fluidity_(encode_row([li[4], li[5], li[6], li[7]]))
    r2 = fluidity_(encode_row([li[8], li[9], li[10], li[11]]))
    r3 = fluidity_(encode_row([li[12], li[13], li[14], li[15]]))

    # calculate fluidity penalties for each column.
    c0 = fluidity_(encode_row([li[0], li[4], li[8], li[12]]))
    c1 = fluidity_(encode_row([li[1], li[5], li[9], li[13]]))
    c2 = fluidity_(encode_row([li[2], li[6], li[10], li[14]]))
    c3 = fluidity_(encode_row([li[3], li[7], li[11], li[15]]))

    # Total board fluidity penalty.
    flu = r0 + r1 + r2 + r3 + c0 + c1 + c2 + c3

    # p0 = fluidity_(encode_row([li[0], li[1], li[2], li[3]]))
    # p1 = fluidity_(encode_row([li[2], li[3], li[4], li[5]]))
    # p2 = fluidity_(encode_row([li[4], li[5], li[6], li[7]]))
    # p3 = fluidity_(encode_row([li[6], li[7], li[8], li[9]]))
    # p4 = fluidity_(encode_row([li[8], li[9], li[10], li[11]]))
    # p5 = fluidity_(encode_row([li[10], li[11], li[12], li[13]]))
    # p6 = fluidity_(encode_row([li[12], li[13], li[14], li[15]]))

    # flu = p0 + p1 + p2 + p3 + p4 + p5 + p6

    # game over, if you can't merge and there aren't any zeros
    if count_merge == 0 and count_zeros == 0:
        return 0

    # combine all heuristic components into one board score.
    return (
        canonical_score
        * (1 + 59 * max_in_corner)
        * 1.15 ** (count_merge + count_zeros)
        * 0.993 ** flu
    )

    # notes: 
    # multiply by 60 if the maximum tile is in the corner (maybe make higher – 80 also works well)
    # multiply by 1.15 each merge / empty square
    # multiply by 0.993 for each fluidity point (arbitrary... tested a few times)


def spawn_locations(board_id: int, direction: int):
    """
    return all empty tile indices where a new tile may spawn after a move.

    directions:
        0 = up    -> top row
        1 = down  -> bottom row
        2 = left  -> leftmost column
        3 = right -> rightmost column

    only empty positions on the edge opposite to the swipe direction are considered. 

    """
    if direction == 0:
        return [
            i for i in [0, 1, 2, 3]
            if ((board_id >> (4 * (15 - i))) & 0xF) == 0
        ]

    if direction == 1:
        return [
            i for i in [12, 13, 14, 15]
            if ((board_id >> (4 * (15 - i))) & 0xF) == 0
        ]

    if direction == 2:
        return [
            i for i in [0, 4, 8, 12]
            if ((board_id >> (4 * (15 - i))) & 0xF) == 0
        ]

    if direction == 3:
        return [
            i for i in [3, 7, 11, 15]
            if ((board_id >> (4 * (15 - i))) & 0xF) == 0
        ]


def place(board_id, idx, val):
    """
    place an encoded tile value at spec. board index. recall that the board is a 64-bit integer.

    Any existing tile at the target index is overwritten.
    """
    # where is it?
    shift = (15 - idx) * 4

    # create a four-bit mask then clear
    mask = 0xF << shift
    cleared_val = board_id & ~mask

    # insert the new encoded tile into the cleared position.
    return cleared_val | (val << shift)


def chance(board_id: int, depth: int, direction: int, possible_tiles=[1, 2, 3]): 
    """ 
    helper function for expectimax
    evaluate chance node. sample 2-3 possible random tile spawns. randomly choose valid spawn locations and possible tile values, then expectimax' 
    """ 
    
    # attain spawn locations 
    sli = spawn_locations(board_id, direction) 
    
    if not sli: return score(board_id) 

    # MONTE CARLO SAMPLING 
    # randomly use 2 or 3 samples to approximate the expected value. 
    # more samples improve accuracy but increase search time. 
    
    NUM_SAMPLES = random.choice([3, 3, 3, 3]) 
    total = 0 
    for _ in range(NUM_SAMPLES): 
        # pick a random valid spawn location. 
        idx = random.choice(sli)  
        val = random.choice(possible_tiles) # Place the tile
        simulated_board = place(board_id, idx, val) 
        total += expectimax(simulated_board, depth - 1, True) 
        # return the average score of the sampled outcomes. 
    return total / NUM_SAMPLES

def player(board_id: int, depth: int, direction: int): 
    """ evaluate a player node by testing every possible swipe. Returns the highest expectimax score among all valid moves. """ 
    
    # functions corresponding to down, up, right, and left swipes. 
    moves = [swipe_down, swipe_up, swipe_right, swipe_left] 
    best_score = -1 
    
    for i in range(4): 
        # simulate the current move. 
        new_board_id = moves[i](board_id) 
        
        if new_board_id == board_id: continue 
        
        score = expectimax(new_board_id, depth - 1, False, i) 
        
        if score > best_score: 
            best_score = score 
    
    return best_score

def count_distinct_tiles(board): 
    """ count the number of distinct encoded tile values greater than or equal to 3 on the board. if there are like five tiles total, then no need to evaluate that far ahead right..""" 
    seen = set() 
    
    while board: 
        v = board & 0xF 
        
        if v >= 3: 
            seen.add(v) 
        board >>= 4 
    
    return len(seen)

def expectimax(board_id: int, depth: int, is_player: bool, direction=0): 
    """ recursively evaluate a board using expectimax search. Player nodes choose the best move, while chance nodes approximate the expected result of a random tile spawn. """ 
     
    s = score(board_id) # evaluate current game_state 

    if s == 0: return 0 
    if depth == 0: return s 
    
    # alternate between player and chance nodes. utilize helper functions.
    if is_player: 
        return player(board_id, depth, direction) 
    else: 
        return chance(board_id, depth, direction)

# direction names corresponding to move indices. 
move_names = ["DOWN", "UP", "RIGHT", "LEFT"] 

# Watch the ai goooo 

# def best_move(board_id: int, depth: int = 9, next_tile: list = [1, 2, 3]): 
#     """ Find the highest-scoring valid move for the current board. Returns the move index corresponding to down, up, right, or left. Returns -1 if no valid moves exist. """ 
#     # Mapping: # 0 = down # 1 = up # 2 = right # 3 = left 
#     moves = [swipe_down, swipe_up, swipe_right, swipe_left] 
    
#     best_score = -float("inf") 
#     best_move_idx = -1 
    
#     for i in range(4): # Simulate the current move. 
#         new_board_id = moves[i](board_id) # If the board does not change, the move is invalid. 
#         if new_board_id == board_id: continue 
        
#         # Evaluate possible tile spawns after the move. 
#         current_score = chance(new_board_id, depth, direction=i, possible_tiles=next_tile,) 

#         # Store the best move found so far. 
#         if current_score > best_score: 
#             best_score = current_score 
#             best_move_idx = i 
#     return best_move_idx

# ##### 

# # board_id = encode_board(to_computer([[1, 0, 0, 0], [2, 3, 3, 6], [0, 1, 12, 24], [3, 48, 96, 384]]))

# move_names = ["DOWN", "UP", "RIGHT", "LEFT"]
# def best_move(board_id: int, depth: int = 9, next_tile: list = [1, 2, 3]):
#     moves = [swipe_down, swipe_up, swipe_right, swipe_left]

#     best_score = -float('inf')
#     best_move_idx = -1

#     for i in range(4):
#         new_board_id = moves[i](board_id)
#         if new_board_id == board_id:
#             continue
#         current_score = chance(new_board_id, depth, direction=i, possible_tiles = next_tile)

#         if current_score > best_score:
#             best_score = current_score
#             best_move_idx = i
#     return best_move_idx

# def game_loop(board):
#     board_id = encode_board(to_computer(board))
#     moves_func = [swipe_down, swipe_up, swipe_right, swipe_left]
#     move_names = ["DOWN", "UP", "RIGHT", "LEFT"]
    
#     # deck
#     deck = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
#     random.shuffle(deck)
    
#     step = 0
#     while True:
#         STARTER_TIME = time.time()
#         if not deck:
#             deck = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
#             random.shuffle(deck)
        
#         r = random.random()
#         if r > 1/21:
#             next_tile = deck.pop()
#         else:
#             next_tile = random.choice([4, 5, 6])
        
#         print(f"\nStep: {step} | Next Tile: {next_tile}")
#         pretty_print(to_human(decode_board(board_id)))

#         distinct = count_distinct_tiles(board_id)

#         if next_tile in [1, 2, 3]:
#             idx = best_move(board_id, depth=min(max(2*(distinct - 2), 4), 8), next_tile=[next_tile]) # should it be 7? or 8?
#         else:
#             idx = best_move(board_id, depth=min(max(2*(distinct - 2), 4), 8), next_tile=[4, 5, 6]) # should it be 7? or 8?
#         if idx == -1:
#             print("GAME OVER")
#             final_tiles = [(board_id >> (4*i)) & 0xF for i in range(16)]
#             print(f"Final Score: {sum([score_tile(t) for t in final_tiles])}")
#             break

#         board_id = moves_func[idx](board_id)
        
#         spawn_locs = spawn_locations(board_id, idx)
#         if spawn_locs:
#             target_idx = random.choice(spawn_locs)
#             board_id = place(board_id, target_idx, next_tile)
        
#         print(f"AI Swiped: {move_names[idx]}")
#         ENDER_TIME = time.time()
#         print(ENDER_TIME - STARTER_TIME)
#         step += 1

# board = [[6, 3, 48, 192], [3, 0, 3, 48], [0, 3, 3, 3], [1, 0, 0, 2]]
# game_loop(board)