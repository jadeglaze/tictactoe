from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# FastAPI app instance
from db import get_db, DbGame
from game import Game, IllegalMoveError

app = FastAPI()


# Pydantic models for REST endpoints
class Location(BaseModel):
    x: int = Field(ge=0, le=2)
    y: int = Field(ge=0, le=2)


class GameId(BaseModel):
    gid: int


class BoardView(BaseModel):
    board: List[List[str]]
    winner: str | None


class GameView(BaseModel):
    boards: List[List[List[str]]]
    winner: str | None


# TODO: Flesh out decorators for Swagger docs

@app.post("/game", response_model=GameId)
async def new_game(db: Session = Depends(get_db)):
    """
    Create a new game of Noughts and Crosses, and returns the game ID.
    :return: ID of the new game
    """
    # Allows me to create a new game of Noughts and Crosses, and returns the game ID.
    db_game = DbGame()
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return GameId(gid=db_game.id)


@app.post("/game/{_id}/move", response_model=BoardView)
async def move(_id: str, location: Location, db: Session = Depends(get_db)):
    """
    Make the next move by specifying the co-ordinates to place an X.
    e.g. {"x": 1, "y": 1} would denote a move to the middle square by the requesting player,
    and returns the new state of the board after the computer has made its move in turn,
    along with the winner (null, "X", "O" or "draw").
    :param _id: The ID of the game to make a move on.
    :param location: The coordinate of the move. Note that the upper left is {x:0, y:0}.
    :param db: The db session
    :return: The new state of the "board" after the computer has also moved or game has been won
    and the "winner" - one of null (no winner yet), "X", "O" or "draw".
    """
    db_game = db.query(DbGame).filter(DbGame.id == int(_id)).first()
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    moves = [tuple(m) for m in db_game.moves] if db_game.moves is not None else None
    game = Game(db_game.id, moves)
    try:
        game.play_round(location.x, location.y)
        db_game.moves = game.moves
        db.commit()
        db.flush()
        return BoardView(board=game.boards[-1], winner=game.winner)
    except IllegalMoveError as e:
        raise HTTPException(status_code=422, detail="Illegal move")


@app.get("/game/{_id}", response_model=GameView)
async def view_game(_id: str, db: Session = Depends(get_db)):
    """
    Returns all moves in a game, chronologically ordered
    and the winner, if any.
    :param _id: The ID of the game.
    :param db: The db session
    :return: All moves made in this game in order as complete
    game "boards" and the "winner" - one of null (no winner yet),
    "X", "O" or "draw".
    """
    db_game = db.query(DbGame).filter(DbGame.id == int(_id)).first()
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    moves = [tuple(m) for m in db_game.moves] if db_game.moves is not None else None
    game = Game(db_game.id, moves)
    return GameView(boards=game.boards, winner=game.winner)


@app.get("/game", response_model=List[int])
async def list_games(db: Session = Depends(get_db)):
    """
    Returns a list of all games created, chronologically ordered.
    :param db: The db session
    :return: All games created in chronological order.
    """
    db_games = db.query(DbGame).all()
    return [g.id for g in db_games]
