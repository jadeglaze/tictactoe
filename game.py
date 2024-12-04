import copy
import random
from typing import List, Tuple


GAME_MODE = "perfect"  # The computer will use the optimal minimax algorithm to select moves.
# GAME_MODE = "random"  # The computer will select random moves.


class IllegalMoveError(Exception):
    pass


class Game:
    def __init__(self, _id: int, moves: List[Tuple[int, int]]):
        self.id = _id
        self.moves = moves or []

        # (re)build the sequence of game boards
        self.boards = [[
            [".", ".", "."],
            [".", ".", "."],
            [".", ".", "."]
        ]]
        for i, loc in enumerate(self.moves):
            x, y = loc
            self.boards.append(copy.deepcopy(self.boards[-1]))
            self.boards[-1][y][x] = ("X", "O")[i % 2]

        # determine remaining open positions
        self.open_spaces = set()
        for x in range(3):
            for y in range(3):
                if self.boards[-1][y][x] == ".":
                    self.open_spaces.add((x, y))

        # determine winner (if any)
        self.winner = None
        self._determine_winner()

    def play_round(self, x: int, y: int) -> None:
        self._move(x, y)
        self._determine_winner()
        if self.winner is None:
            self._computer_move()
            self._determine_winner()

    def _determine_winner(self) -> None:
        if _has_won(self.boards[-1], "X"):
            self.winner = "X"
        elif _has_won(self.boards[-1], "O"):
            self.winner = "O"
        elif _is_draw(self.boards[-1]):
            self.winner = "draw"

    def _move(self, x: int, y: int, mark: str = "X") -> None:
        if not (x, y) in self.open_spaces:
            raise IllegalMoveError()
        self.boards.append(copy.deepcopy(self.boards[-1]))
        self.boards[-1][y][x] = mark
        self.moves.append((x, y))
        self.open_spaces.remove((x, y))

    def _computer_move(self) -> None:
        if GAME_MODE == "perfect":
            location = _minimax(self.boards[-1], "O", "X")
        else:
            location = random.choice(list(self.open_spaces))
        self._move(*location, mark="O")


def _has_won(board, mark):
    # The board is small and constant size so this is a fast-enough
    # check that works by only looking at the board. It doesn't
    # bother restricting checks to only where the last move was made.

    # if ... any complete row has mark m
    return any(  # if any complete row has mark
        all(board[y][x] == mark for x in range(3)) for y in range(3)
    ) or any(  # or any complete column has mark
        all(board[y][x] == mark for y in range(3)) for x in range(3)  # Columns
    ) or all(  # or the x=y diagonal is all mark
        board[i][i] == mark for i in range(3)
    ) or all(  # or the x+y=2 diagonal is all mark
        board[i][2 - i] == mark for i in range(3)
    )


def _is_draw(board):
    # if the board is full of non-blanks then it's a draw
    return all(board[y][x] != "." for y in range(3) for x in range(3))


def _minimax(board, player, opponent):
    """
    Implements the minimax algorithm which will find the optimal next move
    in this solved game of tic tac toe. It will always win or draw against
    another player.
    :param board: The current game board.
    :param player: The mark of the player who should play optimally.
    :param opponent: The mark of the "other" player who we're trying to beat.
    :return: The optimal next move for "player" to make.
    """
    best_move = None
    best_score = -float("inf")
    for y in range(3):
        for x in range(3):
            if board[y][x] == ".":
                board[y][x] = player
                score = _minimax_recurse(board, False, player, opponent)
                board[y][x] = "."  # algo operates in-place so restore the blank
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
    return best_move


def _minimax_recurse(board, is_maximizing, player, opponent):
    if _has_won(board, player):
        return 1
    if _has_won(board, opponent):
        return -1
    if _is_draw(board):
        return 0

    # it's tempting to DRY up these loops, but it just becomes harder to read
    if is_maximizing:
        best_score = -float("inf")
        for y in range(3):
            for x in range(3):
                if board[y][x] == ".":
                    board[y][x] = player
                    score = _minimax_recurse(board, False, player, opponent)
                    board[y][x] = "."  # algo operates in-place so restore the blank
                    best_score = max(best_score, score)
        return best_score
    else:
        best_score = float("inf")
        for y in range(3):
            for x in range(3):
                if board[y][x] == ".":
                    board[y][x] = opponent
                    score = _minimax_recurse(board, True, player, opponent)
                    board[y][x] = "."  # algo operates in-place so restore the blank
                    best_score = min(best_score, score)
        return best_score
