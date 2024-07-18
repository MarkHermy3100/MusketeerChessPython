from flask import Flask, request, render_template, jsonify
from board import *

app = Flask(__name__)

chess_board = CustomBoard()
chess_board.clear_board()
LAST_CLICKED_SQUARE = None
starting_square: Square = -1


def invert_index(index):
    return (7 - index // 8) * 8 + index % 8


@app.route('/')
def home():
    return render_template('index.html', board=chess_board)


@app.route('/legal_moves/<int:index>')
def legal_moves(index):
    global LAST_CLICKED_SQUARE

    LAST_CLICKED_SQUARE = (index := invert_index(index))
    moves = [
        move.to_square for move in chess_board.legal_moves
        if move.from_square == index
    ]

    return jsonify(moves)


@app.route('/make_move/<int:index>', methods=['POST'])
def make_move(index):
    # noinspection PyTypeChecker
    chess_board.push(Move(LAST_CLICKED_SQUARE, invert_index(index)))
    return jsonify(chess_board.fen())


# @app.route('/', methods = ['POST'])
# def set_starting_position(index):
#     global starting_square
#     starting_square = invert_index(index)


@app.route('/get_betza/<string:betza>')
def get_betza(betza):
    chess_board.custom_pieces.append(BB_EMPTY)
    chess_board.custom_piece_types.append(CUSTOM_PIECE_TYPES[STORM])
    CUSTOM_BETZA[CUSTOM_PIECE_TYPES[STORM]] = betza
    new_piece = CustomPiece(CUSTOM_PIECE_TYPES[STORM], WHITE, betza)
    chess_board.set_custom_piece_at(E4, new_piece)
    return jsonify([move.to_square for move in chess_board.generate_pseudo_legal_moves(BB_E4, BB_ALL)])


# @app.route('/', methods = ['GET'])
# def get_starting_position():
#     return starting_square


if __name__ == '__main__':
    app.run(debug=True)