# Two-Flags Game
This is a chess-like game, called Flags Game. The goal of the game is to capture all of the opponent's flags.

## Getting Started
To start the game, you will need to run the main driver file named FlagsMain.py

<pre><code>python3 FlagsMain.py</code></pre>


## Game Rules
* The game is played on an 8x8 board.
* The game starts with a standard chess setup, with the exception of the pawns.
* The pawns move as they do in standard chess.
* The game ends when one player captures all of the opponent's flags.
* The player can also win by no valid moves for the opponent.
* The player can also win by making the opponent run out of time.

## File Structure
* `FlagsEngine.py`: This file contains the logic for the game, including the board representation, move validation, and game over conditions.
* `smartMoveFinder.py`: This file contains an AI agent that can play the game.
* `Zobrist.py`: This file contains code for Zobrist Hashing, it is used for transposition table in the minimax algorithm.
* `FlagsMain.py`: This file is the main driver for the game. It handles user input and updates the graphics.
* `application.py`: This file contains the GUI of the game using Pygame library.
* `client.py`: This file contains the logic for running the game as a client, connecting to the server and sending/receiving moves.
* `images`: this folder contain the images that will be used in the game
