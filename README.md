# MusketeerChessPython
This user guide aims to aid and instruct the user in setting up a custom Muskeeteer chess board with arbitrary custom fairy chess pieces, the move sets of which can be defined using a built-in Betza notation interpreter.
## Overview
- `piece.py`: Module that contains definitions and classes for `betza.py` (can be cleaned up, possibly merged with `betza.py`)
- `betza.py`: Function the parses Betza notation to interpret how a custom/fairy chess piece moves.
- `board.py`: Classes and functions for a custom Musketeer chess game/next-gen pawn chess game. (which, at this point, is just half of the python-chess library *rewritten*, I kid you not)
## `betza.py`
The introduction of fairy chess variants gave birth to a very, very diverse group of "fairy" chess pieces. To compactly and systematically define how these custom pieces move, a notation system is invented by Ralph Betza in the mid 1990s, known as [Betza notation](https://www.chessvariants.com/piececlopedia.dir/betzanot.html).
Not all Betza "modifiers" are handled in betza.py, because not all modifiers are required in our Muskeeter chess variant. The modifiers used are specified in the comments in `betza.py` It is also worth noting that all the directions can be specified through capital letters. (stored in `leaper_atoms`)
This code is mostly based on [](https://github.com/fairy-stockfish/Fairy-Stockfish/blob/master/src/piece.cpp)
## `board.py`
### `class CustomPiece`
This class inherits from `class Piece` of the python-chess library, is primarily used to initialize a custom piece with an arbitrary, formally defined move set. Its basic properties include piece type, color, move directions (and respective modifiers), and symbol.
### `class CustomBoard`
Inherited from `class Board` of the python-chess library, this class consisting of ~500 lines of code holds all the core logic. Below lists the important methods that are exclusive to the `CustomBoard` class and their functionalities (or at least, what the methods are supposed to do, considering the code is rather buggy at the moment). Note that all methods of `Board` that are not specified in `CustomBoard` can also be used by a `CustomBoard` object.
1. `custom_piece_at`: Identify the type of custom piece at a square
2. `custom_piece_at`: Place a piece on a square
3. `generate_pseudo_legal_moves`: For chosen pieces, generate moves solely based on the move sets of said pieces without taking checks into accounts (which are handled by `generate_legal_moves`)
4. `set_musketeer_board_fen`: 
5. `push_san`: From the current board state, make a move (must be formatted in SAN)
6. `push_uci`: Same thing as `push_san`, but move must be formatted in UCI
