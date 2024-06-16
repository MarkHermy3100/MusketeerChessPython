from typing import Iterator
from chess import *
from chess import STARTING_FEN, Piece, Square
from betza import *
import chess.pgn as pgn
import io

CustomPieceType = int

CUSTOM_PIECE_TYPES = [SERGEANT, CAPTAIN, COLONEL, COMMANDER, CORPORAL, GENERAL, LIEUTENANT,
                      ZIGZAG, STORM, HORIZONTAL_ZIGZAG, VERTICAL_ZIGZAG, HORIZONTAL_SWIPER, VERTICAL_SWIPER] = range(len(PIECE_TYPES), len(PIECE_TYPES) + 13)

CUSTOM_SAN_REGEX = re.compile(r"^([NBKRQV])?([a-h])?([1-8])?[\-x]?([a-h][1-8])(=?[nbrqkNBRQK])?[\+#]?\Z")

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
    def __init__(self):
        super().__init__()
        self.custom_pieces: list[Bitboard]
        self.custom_piece_types: list[int]
        self.gated_positions: list[list[int]]

    def __str__(self) -> str:
        return super().__str__()
    
    def custom_piece_type_at(self, square: Square) -> Optional[CustomPieceType]:
        mask = BB_SQUARES[square]
        if (not self.occupied & mask):
            return None
        for index in range (len(self.custom_pieces)):
            if (self.custom_pieces[index] & mask):
                return self.custom_piece_types[index]
        return None
    
    def remove_custom_piece_at(self, square: Square) -> Optional[CustomPieceType]:
        piece_type = self.custom_piece_type_at(square)
        if (piece_type == None):
            return None
        mask = BB_SQUARES[square]

        for index in range (len(self.custom_pieces)):
            if (piece_type == self.custom_piece_types[index]):
                self.custom_pieces[index] ^= mask

        self.occupied ^= mask
        self.occupied_co[WHITE] &= ~mask
        self.occupied_co[BLACK] &= ~mask

        self.promoted &= ~mask

        return piece_type

    def set_custom_piece_at(self, square: Square, piece_type: Optional[CustomPieceType], color: Color, promoted: bool = False):
        self.remove_custom_piece_at(square)
        if (piece_type == None):
            return
        mask = BB_SQUARES[square]

        for index in range (len(self.custom_pieces)):
            if (piece_type == self.custom_piece_types[index]):
                self.custom_pieces[index] |= mask
        self.occupied ^= mask
        self.occupied_co[color] ^= mask
        if promoted:
            self.promoted ^= mask
    
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

        pawn_type = PIECE_TYPES[PAWN]
        for temp_type in range(PIECE_TYPES[SERGEANT], PIECE_TYPES[LIEUTENANT] + 1):
            if (self.custom_piece_types.count(temp_type) != 0 and pawn_type == PIECE_TYPES[PAWN]):
                pawn_type = temp_type

        # Special pawn captures
        if (pawn_type != PIECE_TYPES[CORPORAL] and pawn_type != PIECE_TYPES[LIEUTENANT]):
            for from_square in scan_reversed(pawns):
                targets = BB_PAWN_ATTACKS[not self.turn][from_square] & self.occupied_co[not self.turn] & to_mask

                for to_square in scan_reversed(targets):
                    yield Move(from_square, to_square)

        # Horizontal pawn moves
        if (pawn_type == PIECE_TYPES[COLONEL] or pawn_type == PIECE_TYPES[GENERAL] or pawn_type == PIECE_TYPES[LIEUTENANT]):
            if (self.turn == WHITE):
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) == 6 or (pawn_type == PIECE_TYPES[LIEUTENANT] and square_rank(from_square) == 1)):
                        if (BB_SQUARES[from_square + 1] & ~self.occupied and square_distance(from_square, from_square + 1) == 1):
                            yield Move(from_square, from_square + 1)
                        if (BB_SQUARES[from_square - 1] & ~self.occupied and square_distance(from_square, from_square - 1) == 1):
                            yield Move(from_square, from_square - 1)
            else:
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) == 1 or (pawn_type == PIECE_TYPES[LIEUTENANT] and square_rank(from_square) == 6)):
                        if (BB_SQUARES[from_square + 1] & ~self.occupied and square_distance(from_square, from_square + 1) == 1):
                            yield Move(from_square, from_square + 1)
                        if (BB_SQUARES[from_square - 1] & ~self.occupied and square_distance(from_square, from_square - 1) == 1):
                            yield Move(from_square, from_square - 1)

        # Backward pawn moves
        for from_square in scan_reversed(pawns):
            if (self.turn == WHITE):
                if ((pawn_type == PIECE_TYPES[SERGEANT] or pawn_type == PIECE_TYPES[CAPTAIN]) and square_rank(from_square) < 4):
                    continue
                if ((pawn_type == PIECE_TYPES[COLONEL] or pawn_type == PIECE_TYPES[GENERAL]) and square_rank(from_square) < 3):
                    continue
                if (pawn_type == PIECE_TYPES[CORPORAL] and square_rank(from_square) == 3):
                    continue
                yield Move(from_square, from_square - 8)

            else:
                if ((pawn_type == PIECE_TYPES[SERGEANT] or pawn_type == PIECE_TYPES[CAPTAIN]) and square_rank(from_square) > 3):
                    continue
                if ((pawn_type == PIECE_TYPES[COLONEL] or pawn_type == PIECE_TYPES[GENERAL]) and square_rank(from_square) > 4):
                    continue
                if (pawn_type == PIECE_TYPES[CORPORAL] and square_rank(from_square) == 4):
                    continue
                yield Move(from_square, from_square + 8)

        # Knight pawn moves
        if (pawn_type == PIECE_TYPES[CAPTAIN] or pawn_type == PIECE_TYPES[COLONEL] or pawn_type == PIECE_TYPES[COMMANDER] or pawn_type == PIECE_TYPES[GENERAL]):
            if (self.turn == WHITE):
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) > 2):
                        break
                    if ((pawn_type == PIECE_TYPES[CAPTAIN] or pawn_type == PIECE_TYPES[COMMANDER]) and square_rank(from_square) > 1):
                        break
                    if (pawn_type != PIECE_TYPES[GENERAL] and BB_SQUARES[from_square + 8] & self.occupied):
                        break
                    if (square_distance(from_square, from_square + 15) == 2 and BB_SQUARES[from_square + 15] & ~self.occupied):
                        yield Move(from_square, from_square + 15)
                    if (square_distance(from_square, from_square + 17) == 2 and BB_SQUARES[from_square + 17] & ~self.occupied):
                        yield Move(from_square, from_square + 17)

            else:
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) < 5):
                        break
                    if ((pawn_type == PIECE_TYPES[CAPTAIN] or pawn_type == PIECE_TYPES[COMMANDER]) and square_rank(from_square) < 6):
                        break
                    if (pawn_type != PIECE_TYPES[GENERAL] and BB_SQUARES[from_square - 8] & self.occupied):
                        break
                    if (square_distance(from_square, from_square - 15) == 2 and BB_SQUARES[from_square - 15] & ~self.occupied):
                        yield Move(from_square, from_square - 15)
                    if (square_distance(from_square, from_square - 17) == 2 and BB_SQUARES[from_square - 17] & ~self.occupied):
                        yield Move(from_square, from_square - 17)

        # Double pawn moves on 3rd rank
        if (pawn_type == PIECE_TYPES[COLONEL] or pawn_type == PIECE_TYPES[COMMANDER]):
            double_moves = pawns
            if (self.turn == WHITE):
                double_moves = (double_moves << 8) & ~self.occupied
                double_moves = double_moves << 8 & ~self.occupied & (BB_RANK_4 | BB_RANK_5)
            else:
                double_moves = (double_moves >> 8) & ~self.occupied
                double_moves = double_moves >> 8 & ~self.occupied & (BB_RANK_5 | BB_RANK_4)

            double_moves &= to_mask
            for to_square in scan_reversed(double_moves):
                from_square = to_square + (16 if self.turn == BLACK else -16)
                yield Move(from_square, to_square)

        yield from super().generate_pseudo_legal_moves(from_mask, to_mask)
    

    def set_musketeer_board_fen(self, musketeer_fen: str) -> None:
        rows = musketeer_fen.split("/")
        print(rows)
        fen = "/".join(rows[1:9])
        super().set_board_fen(fen)


    def parse_san(self, san: str) -> Move:
        # Castling.
        try:
            if san in ["O-O", "O-O+", "O-O#", "0-0", "0-0+", "0-0#"]:
                return next(move for move in self.generate_castling_moves() if self.is_kingside_castling(move))
            elif san in ["O-O-O", "O-O-O+", "O-O-O#", "0-0-0", "0-0-0+", "0-0-0#"]:
                return next(move for move in self.generate_castling_moves() if self.is_queenside_castling(move))
        except StopIteration:
            raise IllegalMoveError(f"illegal san: {san!r} in {self.fen()}")

        # Match normal moves.
        match = SAN_REGEX.match(san)
        if not match:
            # Null moves.
            if san in ["--", "Z0", "0000", "@@@@"]:
                return Move.null()
            elif "," in san:
                raise InvalidMoveError(f"unsupported multi-leg move: {san!r}")
            else:
                raise InvalidMoveError(f"invalid san: {san!r}")

        # Get target square. Mask our own pieces to exclude castling moves.
        to_square = SQUARE_NAMES.index(match.group(4))
        to_mask = BB_SQUARES[to_square] & ~self.occupied_co[self.turn]

        # Get the promotion piece type.
        p = match.group(5)
        promotion = PIECE_SYMBOLS.index(p[-1].lower()) if p else None

        # Filter by original square.
        from_mask = BB_ALL
        if match.group(2):
            from_file = FILE_NAMES.index(match.group(2))
            from_mask &= BB_FILES[from_file]
        if match.group(3):
            from_rank = int(match.group(3)) - 1
            from_mask &= BB_RANKS[from_rank]

        # Filter by piece type.
        if match.group(1):
            piece_type = PIECE_SYMBOLS.index(match.group(1).lower())
            from_mask &= self.pieces_mask(piece_type, self.turn)
        elif match.group(2) and match.group(3):
            # Allow fully specified moves, even if they are not pawn moves,
            # including castling moves.
            move = self.find_move(square(from_file, from_rank), to_square, promotion)
            if move.promotion == promotion:
                return move
            else:
                raise IllegalMoveError(f"missing promotion piece type: {san!r} in {self.fen()}")
        else:
            from_mask &= self.pawns

            # Do not allow pawn captures if file is not specified.
            if not match.group(2):
                from_mask &= BB_FILES[square_file(to_square)]

        # Match legal moves.
        matched_move = None
        for move in self.generate_legal_moves(from_mask, to_mask):
            if move.promotion != promotion:
                continue

            if matched_move:
                raise AmbiguousMoveError(f"ambiguous san: {san!r} in {self.fen()}")

            matched_move = move

        if not matched_move:
            raise IllegalMoveError(f"illegal san: {san!r} in {self.fen()}")

        return matched_move


board = CustomBoard()
# board.custom_pieces.append()
# board.custom_piece_types = [PIECE_TYPES[SERGEANT]]
# board.clear_board()
# board.set_piece_at(E5, Piece(SERGEANT, WHITE))
# board.set_piece_at(D4, Piece(SERGEANT, BLACK))

board.set_musketeer_board_fen("**v***u*/4kbnr/pppppppp/8/8/8/8/PPPPPPPP/4KBNR/**U*V***")
print(board)