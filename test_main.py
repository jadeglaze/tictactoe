import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base, get_db
from game import Game
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


# Fixture to set up and tear down the database
@pytest.fixture(scope="function")
def _test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    try:
        # Yield the test session class
        yield TestingSessionLocal
    finally:
        # Drop tables
        Base.metadata.drop_all(bind=engine)


# Fixture to set up the test client
@pytest.fixture(scope="function")
def client(_test_db):
    def override_get_db():
        # Create a new session instance for each request
        db = _test_db()
        try:
            yield db
        finally:
            db.close()

    # Override the app's database dependency
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    # Clear the dependency override after the test
    app.dependency_overrides.clear()


def test_new_game(client):
    # Send a POST request to the endpoint
    response = client.post("/game")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data == {"gid": 1}


def count_mark(board, mark) -> int:
    return sum([1 for row in board for m in row if m == mark])


def test_move(client):
    # make a game
    response = client.post("/game")
    gid = response.json()["gid"]

    # Prepare test data
    data = {"x": 1, "y": 2}

    # Send a POST request to the endpoint
    response = client.post(f"/game/{gid}/move", json=data)

    # Assertions
    assert response.status_code == 200
    data = response.json()
    board = data["board"]
    winner = data["winner"]
    assert board[2][1] == "X"
    x_count = count_mark(board, "X")
    assert x_count == 1
    o_count = count_mark(board, "O")
    assert o_count == 1
    blank_count = count_mark(board, ".")
    assert blank_count == 7
    assert winner is None


def find_first_open_space(board):
    for x in range(3):
        for y in range(3):
            if board[y][x] == ".":
                return x, y


def test_move_twice(client):
    # make a game
    response = client.post("/game")
    gid = response.json()["gid"]

    # move once
    data = {"x": 1, "y": 1}
    response = client.post(f"/game/{gid}/move", json=data)
    data = response.json()
    x, y = find_first_open_space(data["board"])

    # move again
    data = {"x": x, "y": y}
    response = client.post(f"/game/{gid}/move", json=data)

    # Assertions
    assert response.status_code == 200
    data = response.json()
    board = data["board"]
    winner = data["winner"]
    assert board[1][1] == "X"
    assert board[y][x] == "X"
    x_count = count_mark(board, "X")
    assert x_count == 2
    o_count = count_mark(board, "O")
    assert o_count == 2
    blank_count = count_mark(board, ".")
    assert blank_count == 5
    assert winner is None


def test_invalid_location(client):
    # make a game
    response = client.post("/game")
    gid = response.json()["gid"]

    # move once
    data = {"x": 4, "y": 2}
    response = client.post(f"/game/{gid}/move", json=data)

    # Assertions
    assert response.status_code == 422
    data = response.json()
    assert data == {
        'detail': [
            {
                'type': 'less_than_equal',
                'loc': ['body', 'x'],
                'msg': 'Input should be less than or equal to 2',
                'input': 4,
                'ctx': {'le': 2}
            }
        ]
    }


def test_illegal_move(client):
    # make a game
    response = client.post("/game")
    gid = response.json()["gid"]

    # move once
    data = {"x": 1, "y": 1}
    response = client.post(f"/game/{gid}/move", json=data)

    # move again in the same place
    data = {"x": 1, "y": 1}
    response = client.post(f"/game/{gid}/move", json=data)

    # Assertions
    assert response.status_code == 422
    data = response.json()
    assert data == {'detail': "Illegal move"}


def test_bad_game_id(client):
    # get game with wrong id
    response = client.get(f"/game/42")

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert data == {'detail': "Game not found"}


def test_winner_x(client):
    # override the random computer moves
    def yield_computer_move():
        yield 1, 0
        yield 2, 0
        yield 0, 2

    fake_computer_move = yield_computer_move()

    def crappy_computer_move(self):
        location = next(fake_computer_move)
        self._move(*location, mark="O")

    save_computer_move_method = Game._computer_move
    Game._computer_move = crappy_computer_move

    # make a game
    response = client.post("/game")
    gid = response.json()["gid"]

    # make series of moves along x==y diagonal to win
    for i in range(3):
        data = {"x": i, "y": i}
        response = client.post(f"/game/{gid}/move", json=data)
        assert response.status_code == 200
        winner = response.json()["winner"]
        if i < 2:
            assert winner is None
        else:
            assert winner == "X"

    Game._computer_move = save_computer_move_method


def test_winner_o(client):
    # override the random computer moves
    def yield_computer_move():
        yield 0, 2
        yield 1, 1
        yield 2, 0

    fake_computer_move = yield_computer_move()

    def crappy_computer_move(self):
        location = next(fake_computer_move)
        self._move(*location, mark="O")

    save_computer_move_method = Game._computer_move
    Game._computer_move = crappy_computer_move

    # make a game
    response = client.post("/game")
    gid = response.json()["gid"]

    # make series of bad moves to lose
    x_moves = [(1, 0), (0, 1), (2, 1)]
    for i in range(3):
        data = {"x": x_moves[i][0], "y": x_moves[i][1]}
        response = client.post(f"/game/{gid}/move", json=data)
        assert response.status_code == 200
        winner = response.json()["winner"]
        if i < 2:
            assert winner is None
        else:
            assert winner == "O"

    Game._computer_move = save_computer_move_method


def test_draw(client):
    # override the random computer moves
    def yield_computer_move():
        yield 0, 0
        yield 2, 1
        yield 0, 2
        yield 1, 0

    fake_computer_move = yield_computer_move()

    def crappy_computer_move(self):
        location = next(fake_computer_move)
        self._move(*location, mark="O")

    save_computer_move_method = Game._computer_move
    Game._computer_move = crappy_computer_move

    # make a game
    response = client.post("/game")
    gid = response.json()["gid"]

    # make series of bad moves to lose
    x_moves = [(1, 1), (0, 1), (2, 0), (1, 2), (2, 2)]
    for i in range(5):
        data = {"x": x_moves[i][0], "y": x_moves[i][1]}
        response = client.post(f"/game/{gid}/move", json=data)
        assert response.status_code == 200
        winner = response.json()["winner"]
        if i < 4:
            assert winner is None
        else:
            assert winner == "draw"

    Game._computer_move = save_computer_move_method


def test_view_game(client):
    # make a game
    response = client.post("/game")
    gid = response.json()["gid"]

    # move a couple times
    data = {"x": 1, "y": 1}
    response = client.post(f"/game/{gid}/move", json=data)
    data = response.json()
    x, y = find_first_open_space(data["board"])
    data = {"x": x, "y": y}
    response = client.post(f"/game/{gid}/move", json=data)

    # get the full game view
    response = client.get(f"/game/{gid}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    boards = data["boards"]
    assert len(boards) == 5

    # first board state is "blank"
    b = 0
    assert all(m == "." for row in boards[b] for m in row)

    # second board state has X in center, no O yet
    b += 1
    assert boards[b][1][1] == "X"
    assert count_mark(boards[b], "X") == 1
    assert count_mark(boards[b], "O") == 0
    assert count_mark(boards[b], ".") == 8

    # third board state has X in center, one O
    b += 1
    assert boards[b][1][1] == "X"
    assert count_mark(boards[b], "X") == 1
    assert count_mark(boards[b], "O") == 1
    assert count_mark(boards[b], ".") == 7

    # third board state has X in center, one O
    b += 1
    assert boards[b][1][1] == "X"
    assert boards[b][y][x] == "X"
    assert count_mark(boards[b], "X") == 2
    assert count_mark(boards[b], "O") == 1
    assert count_mark(boards[b], ".") == 6

    # final board state has 2 X, 2 O
    b += 1
    assert boards[b][1][1] == "X"
    assert boards[b][y][x] == "X"
    assert count_mark(boards[b], "X") == 2
    assert count_mark(boards[b], "O") == 2
    assert count_mark(boards[b], ".") == 5

    # no winner. no chicken dinner.
    winner = data["winner"]
    assert winner is None


def test_list_games(client):
    # make a game
    response = client.post("/game")
    gid = response.json()["gid"]

    # get the list
    response = client.get("/game")

    assert response.status_code == 200
    data = response.json()
    assert data == [1]

    # make another game and get the list
    response = client.post("/game")
    gid = response.json()["gid"]
    response = client.get("/game")
    data = response.json()
    assert data == [1, 2]
