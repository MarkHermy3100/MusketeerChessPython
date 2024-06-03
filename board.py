from typing import Iterator
from chess import *
from betza import *
import chess.pgn as pgn
import io

PIECE_TYPES = [PAWN, SERGEANT, CAPTAIN, COLONEL, COMMANDER, CORPORAL, GENERAL, LIEUTENANT,
               KNIGHT, BISHOP, ROOK, ZIGZAG, STORM, HORIZONTAL_ZIGZAG, VERTICAL_ZIGZAG,
               HORIZONTAL_SWIPER, VERTICAL_SWIPER, KING] = range(0, 18)

def print_bb(bb_int: Bitboard):
    bb = str(bin(bb_int))[2:]
    bb = '0' * (64 - len(bb)) + bb
    for r in range (8):
        for c in range (8):
            print(bb[(r << 3) + 7 - c], end = "")
        print()

def direction_in_2d(direction: int):
    dir_y = int(round(direction / 8))
    return direction - dir_y * 8, dir_y



class CustomPiece(Piece):
    def __init__(self, type, color, moveset):
        super().__init__(type, color)
        self.betza = moveset
        self.steps: list[dict[int, int]] = from_betza(moveset).steps
        self.slider: list[dict[int, int]] = from_betza(moveset).slider
        self.slider_initial: list[int] = []
        self.hopper: list[dict[int, int]] = from_betza(moveset).hopper
        self.hopper_initial: list[int] = []
        self.crooked: list[dict[int, int]] = from_betza(moveset).crooked
        self.crooked_initial: list[int] = []

    def symbol(self, symbol: str):
        return symbol.upper() if self.color == WHITE else symbol.lower()
    
class CustomBoard(Board):
    custom_pieces: list[Bitboard]
    custom_piece_types: list[CustomPiece]

    def __str__(self) -> str:
        return super().__str__()
    
    def is_slide_path(self, direction: int, start: Square, target: Square, distance: int) -> bool:
        dir_x, dir_y = direction_in_2d(direction)
        path_x = (target & 7) - (start & 7)
        path_y = (target >> 3) - (start >> 3)
        if (path_x % dir_x != 0 or path_y % dir_y != 0):
            return False
        if (path_x // dir_x != path_y // dir_y):
            return False
        if (abs(path_x // dir_x) <= distance):
            return False
        current = start
        for step in range (path_x // dir_x):
            current += direction
            if (current != target and BB_SQUARES[current] & self.occupied):
                return False
        return not BB_SQUARES[current] & self.occupied_co[self.turn]

    def is_hop_path(self, direction: int, start: Square, target: Square, distance: int) -> bool:
        return False

    def is_crooked_path(self, direction: int, start: Square, target: Square, distance: int) -> bool:
        if (target == start):
            return False
        direction_x, direction_y = direction_in_2d(direction)
        direction_perp = -direction_y + (direction_x << 3)
        path_straight = [(target & 7) - (start & 7), (target >> 3) - (start >> 3)]
        step_para = path_straight[0] * direction_x + path_straight[1] * direction_y
        step_perp = -path_straight[0] * direction_y + path_straight[1] * direction_x
        determinant = direction_x * direction_x + direction_y * direction_y
        if (step_para % determinant != 0 or step_perp % determinant != 0):
            return False
        step_para //= determinant
        step_perp //= determinant
        if (step_perp < 0):
            step_perp = -step_perp
            direction_perp = direction_y - (direction_x << 3)
        if (step_para != step_perp and step_para != step_perp + 1):
            return False
        if (step_para + step_perp > distance):
            return False
        current = start
        for step in range (1, step_para + step_perp + 1):
            current += direction if (step % 2 == 1) else direction_perp
            if (current != target and BB_SQUARES[current] & self.occupied):
                return False
        return not BB_SQUARES[target] & self.occupied_co[self.turn]

    def crooked_path(self, direction: int, start: Square, target: Square, distance: int) -> Bitboard:
        if (not self.is_crooked_path(direction, start, target, distance)):
            return BB_EMPTY
        direction_x, direction_y = direction_in_2d(direction)
        direction_perp = -direction_y + (direction_x << 3)
        path_straight = [(target & 7) - (start & 7), (target >> 3) - (start >> 3)]
        step_para = path_straight[0] * direction_x + path_straight[1] * direction_y
        step_perp = -path_straight[0] * direction_y + path_straight[1] * direction_x
        determinant = direction_x * direction_x + direction_y * direction_y
        step_para //= determinant
        step_perp //= determinant
        if (step_perp < 0):
            step_perp = -step_perp
            direction_perp = direction_y - (direction_x << 3)
        current = start
        bb_path = BB_EMPTY
        for step in range (1, step_para + step_perp + 1):
            current += direction if (step % 2 == 1) else direction_perp
            bb_path |= BB_SQUARES[current]
        return bb_path
    
    def custom_attacks_mask(self, square: Square) -> Bitboard:
        bb_square = BB_SQUARES[square]
        attacks = BB_EMPTY
        for ind in range (len(self.custom_pieces)):
            if (bb_square & self.custom_pieces[ind]):
                piece = self.custom_piece_types[ind]
                for dir in piece.steps[0].keys():
                    for to_sq in SQUARES:
                        if (self.is_slide_path(dir, square, to_sq, 1) and not BB_SQUARES[to_sq] & self.occupied):
                            attacks |= (BB_SQUARES[to_sq])
                for dir in piece.steps[1].keys():
                    for to_sq in SQUARES:
                        if (self.is_slide_path(dir, square, to_sq, 1) and BB_SQUARES[to_sq] & self.occupied):
                            attacks |= (BB_SQUARES[to_sq])

                for dir, dist in piece.slider[0].items():
                    for to_sq in SQUARES:
                        if (self.is_slide_path(dir, square, to_sq, dist) and not BB_SQUARES[to_sq] & self.occupied):
                            attacks |= (BB_SQUARES[to_sq])
                for dir, dist in piece.slider[1].items():
                    for to_sq in SQUARES:
                        if (self.is_slide_path(dir, square, to_sq, dist) and BB_SQUARES[to_sq] & self.occupied):
                            attacks |= (BB_SQUARES[to_sq])

                for dir, dist in piece.crooked[0].items():
                    for to_sq in SQUARES:
                        if (self.is_crooked_path(dir, square, to_sq, dist) and not BB_SQUARES[to_sq] & self.occupied):
                            attacks |= (BB_SQUARES[to_sq])
                for dir, dist in piece.crooked[1].items():
                    for to_sq in SQUARES:
                        if (self.is_crooked_path(dir, square, to_sq, dist) and BB_SQUARES[to_sq] & self.occupied):
                            attacks |= (BB_SQUARES[to_sq])
    # Custom moves from Betza notation
    def generate_custom_moves_from_betza(self, piece: CustomPiece, from_square: int) -> list[Square]:
        possible_moves = []
        for index, (direction, distance) in piece.steps[0]:
            for dist in range (1, max(1, distance)):
                to_square = from_square + direction * dist
                if (True):
                    possible_moves.append(to_square)
        return possible_moves

    #Pseudo-legal moves of a custom piece
    def generate_custom_pseudo_legal_moves(self, piece: CustomPiece, from_square: int, to_mask: Bitboard):
        possible_moves = self.generate_custom_moves_from_betza(piece, from_square)
        for to_square in possible_moves:
            if self.piece_at(to_square) is None or self.piece_at(to_square).color != self.turn:
                if BB_SQUARES[to_square] & to_mask:
                    yield Move(from_square, to_square)
    
    def generate_pseudo_legal_moves(self, from_mask: Bitboard = BB_ALL, to_mask: Bitboard = BB_ALL) -> Iterator[Move]:
        our_pieces = self.occupied_co[self.turn]
        
        # Handle non-pawn custom
        non_pawns = our_pieces & ~self.pawns & from_mask
        for from_square in scan_reversed(non_pawns):
            moves = self.custom_attacks_mask(from_square) & ~our_pieces & to_mask
            for to_square in scan_reversed(moves):
                yield Move(from_square, to_square)

        # Handle pawn custom
        pawns = self.pawns & self.occupied_co[self.turn] & from_mask

        # Special pawn captures
        if (self.pawns != PIECE_TYPES[CORPORAL] and self.pawns != PIECE_TYPES[LIEUTENANT]):
            for from_square in scan_reversed(pawns):
                targets = BB_PAWN_ATTACKS[not self.turn][from_square] & self.occupied_co[not self.turn] & to_mask

                for to_square in scan_reversed(targets):
                    yield Move(from_square, to_square)

        # Horizontal pawn moves
        if (self.pawns == PIECE_TYPES[COLONEL] or self.pawns == PIECE_TYPES[GENERAL] or self.pawns == PIECE_TYPES[LIEUTENANT]):
            if (self.turn == WHITE):
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) == 6 or (self.pawns == PIECE_TYPES[LIEUTENANT] and square_rank(from_square) == 1)):
                        if (BB_SQUARES[from_square + 1] & ~self.occupied and square_distance(from_square, from_square + 1) == 1):
                            yield Move(from_square, from_square + 1)
                        if (BB_SQUARES[from_square - 1] & ~self.occupied and square_distance(from_square, from_square - 1) == 1):
                            yield Move(from_square, from_square - 1)
            else:
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) == 1 or (self.pawns == PIECE_TYPES[LIEUTENANT] and square_rank(from_square) == 6)):
                        if (BB_SQUARES[from_square + 1] & ~self.occupied and square_distance(from_square, from_square + 1) == 1):
                            yield Move(from_square, from_square + 1)
                        if (BB_SQUARES[from_square - 1] & ~self.occupied and square_distance(from_square, from_square - 1) == 1):
                            yield Move(from_square, from_square - 1)

        # Backward pawn moves
        for from_square in scan_reversed(pawns):
            if (self.turn == WHITE):
                if ((self.pawns == PIECE_TYPES[SERGEANT] or self.pawns == PIECE_TYPES[CAPTAIN]) and square_rank(from_square) < 5):
                    continue
                if ((self.pawns == PIECE_TYPES[COLONEL] or self.pawns == PIECE_TYPES[GENERAL]) and square_rank(from_square) < 4):
                    continue
                if (self.pawns == PIECE_TYPES[CORPORAL] and square_rank(from_square) == 4):
                    continue

        # Knight pawn moves
        if (self.pawns == PIECE_TYPES[CAPTAIN] or self.pawns == PIECE_TYPES[COLONEL] or self.pawns == PIECE_TYPES[COMMANDER] or self.pawns == PIECE_TYPES[GENERAL]):
            
            for from_squares in scan_reversed(pawns):
                to_squares = [0, 0]
                if (square_distance(from_square, to_squares[0]) == 2):
                    yield Move(from_square, to_squares[0])
                if (square_distance(from_square, to_squares[1]) == 2):
                    yield Move(from_square, to_squares[1])

        # Double pawn moves on 3rd rank
        if (self.pawns == PIECE_TYPES[COLONEL] or self.pawns == PIECE_TYPES[COMMANDER]):
            double_moves = pawns
            if (self.turn == WHITE):
                double_moves <<= 16
                double_moves = double_moves & ~self.occupied & (BB_RANK_4 | BB_RANK_5)
            else:
                double_moves >>= 16
                double_moves = double_moves & ~self.occupied & (BB_RANK_5 | BB_RANK_4)

            double_moves &= to_mask
            for to_square in scan_reversed(double_moves):
                from_square = to_square + (16 if self.turn == BLACK else -16)
                yield Move(from_square, to_square)

        yield from super().generate_pseudo_legal_moves(from_mask, to_mask)


""" board = Board()
board.clear_board()
board.set_piece_at(E1, Piece(QUEEN, WHITE))
board.set_piece_at(E3, Piece(QUEEN, BLACK))
for move in board.generate_pseudo_legal_moves(BB_E1, BB_ALL):
    print(move)

print(board) """

# game = pgn.read_game(io.StringIO("1. He4"))
# print(game)
# board = game.board()
# for move in game.mainline_moves():
#     board.push(move)

# print(board)