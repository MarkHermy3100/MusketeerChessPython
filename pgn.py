import chess.pgn as pgn

game = pgn.read_game(open("./test.pgn"))    # File deleted
board = game.board()
for move in game.mainline_moves():
    board.push(move)

print(board)