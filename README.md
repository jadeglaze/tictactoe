# Tic Tac Toe REST API

## Running and Using the API Server
### Setup
1. Create a virtual environment with ```python -m venv ./venv```
2. Activate the virtual environment ```source venv/bin/activate```
3. Install dependencies ```pip install -r requirements.txt```

### Running Tests
```pytest```

### Running the Server and Making Calls
1. ```python -m uvicorn main:app --reload```
2. Go to [Swagger live docs](http://127.0.0.1:8000/docs) and play around

## Time to Build
I worked on it between other things, but total time was something like eight hours.
See "Feedback on the Challenge" for my thinking on why I didn't stop at four
despite the urging.

## Assumptions
It's particularly odd for a web API that there's no notion of a user 
but I assumed that acknowledging such here with a quick implementation sketch 
would be sufficient. The two key things that adding users would demonstrate 
are authentication and one-to-many database table relationships.
In the case of authentication, that is mostly an exercise in reading
docs and looking at examples and following them.
For the one-to-many (one user to many games) DB relationship, it's a bit of
SQLAlchemy er... alchemy in the model implementations and making sure the
logged in user has access to the requested Game ID in the REST endpoints.

I also came up with my own straightforward way to return the winner (if any)
with the appropriate API calls. (The document only specifies to return the
game board(s).)

For the "view game" API call the document was unclear if the sequence of
game boards should be every move - player and computer separate - or
only every pair of moves (player + computer), (player + computer), ...
I opted to return each move separately.

I put a created_at column on the database table. Initially this was intended
to return created games in order, but then I facepalmed and realized the
database will maintain row creation order so it wasn't necessary for that
purpose. I left it in place though because it's generally good practice for
every table to have this column (and modified_at) so I might as well leave it
there as an example for you to see.

## Trade-offs
Since this project involves very little and quite simple data , I opted to use only
a single database table where a row represents the entire history of a game
(represented by the sequence of moves).
This is slightly odd in since it requires encoding the list of moves into
a single column. I used JSON in this case for simplicity. I typically
avoid JSON columns but in this case the data is small and there's no need to
ever pick apart the column contents in queries or anything like that.

I also opted to write the most straightforward `_has_won()` and `_is_draw()`
algorithms. You could try to minimize the checks by taking into account the
last move (the win must be in the same column, row or diagonal as the last move)
but the way I implemented it is simple, condition-free, pure-functional and
ends up being used by both the normal play of the game and the minimax
algorithm. Plus, we're talking about a 3x3 grid, so it's comically small and
constant time anyway.

I could/should have written move unit tests, especially for key functions
like `_has_won`, `_is_draw`, `_minimax` but... had to stop somewhere.

## Special/Unique Features
Be honest, you know what it's going to be... :)
I implemented the minimax algorithm to allow the computer to play perfectly
such that it always wins or draws.
But just for fun, I started with random, so I left that in place too.
I didn't do any fancy configuration, but you can switch the `GAME_MODE`
at the top of the `game.py` file from `"perfect"` to `"random"`.

Have fun!

## Feedback on the Challenge
I'll keep it to two points:
First, it was fun! And straightforward. Similar to "real work". So: Awesome.
Second, time to implement. In my experience these coding challenges always
take longer than the "expected" time. I have two points related to that.
For one thing, place yourself in the candidate's shoes. Candidates have
little incentive to be accurate/honest about how long it took them (if it was
over the expected time) because that looks like an admission that they're
slow. And not just slow, but slower than some imagined-to-be-real folks
who _did_ complete it "in time." And on the other hand, what is the expectation
if someone can't complete it in time? Give up? Bow out? Leave it half-done?
That's sure not what I'd want in an employee. I'd want the person who
is brave enough to say "this can't be done well enough in that amount of time"
and completes the work with reasonably high quality. Time to market, especially
in the context of a startup is crucially important, but there's a balance
between "rushed" and "good enough for now" that has to be achieved.
