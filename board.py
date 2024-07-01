from typing import Iterator
from chess import *
from betza import *
import chess.pgn as pgn
import io

CustomPieceType = int

CUSTOM_PIECE_TYPES = [SERGEANT, CAPTAIN, COLONEL, COMMANDER, CORPORAL, GENERAL, LIEUTENANT,
                      ZIGZAG, STORM, HORIZONTAL_ZIGZAG, VERTICAL_ZIGZAG, HORIZONTAL_SWIPER, VERTICAL_SWIPER] = range(1, 14)
CUSTOM_PIECE_SYMBOLS = [None, None, '2', '3', '4', '5', '6', '7', '8', 'z', 's', 'h', 'v', 'h', 'v']

CUSTOM_BETZA = {}

CUSTOM_SAN_REGEX = re.compile(r"^([NBKRQSZ])?([a-h])?([1-8])?[\-x]?([a-h][1-8])(/?[SZVH])?(=?[nbrqkNBRQK])?[\+#]?\Z")

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
    piece_type: CustomPieceType = -1
    color: Color = WHITE
    betza: str = ""

    def __init__(self, type, color, moveset = ""):
        self.piece_type = type
        self.color = color
        self.betza = moveset
        self.steps: list[dict[int, int]] = from_betza(moveset).steps
        self.slider: list[dict[int, int]] = from_betza(moveset).slider
        self.slider_initial: list[int] = []
        self.hopper: list[dict[int, int]] = from_betza(moveset).hopper
        self.hopper_initial: list[int] = []
        self.crooked: list[dict[int, int]] = from_betza(moveset).crooked
        self.crooked_initial: list[int] = []

    def symbol(self):
        symbol = typing.cast(str, CUSTOM_PIECE_SYMBOLS[self.piece_type])
        return symbol.upper() if self.color == WHITE else symbol.lower()
    
    @classmethod
    def from_symbol(cls, symbol: str) -> Piece:
        return cls(CUSTOM_PIECE_SYMBOLS.index(symbol.lower()), symbol.isupper())
    
class CustomBoard(Board):
    custom_pieces: list[Bitboard] = []
    custom_piece_types: list[CustomPieceType] = []
    gated_positions: list[list[int]] = [[-1, -1], [-1, -1]]

    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        builder = []

        for square in SQUARES_180:
            if self.custom_piece_at(square):
                builder.append(self.custom_piece_at(square).symbol())
            elif self.piece_at(square):
                builder.append(self.piece_at(square).symbol())
            else:
                builder.append(".")

            if BB_SQUARES[square] & BB_FILE_H:
                if square != H1:
                    builder.append("\n")
            else:
                builder.append(" ")

        white_back_row = ['.'] * 9
        black_back_row = ['.'] * 9
        white_back_row[self.gated_positions[WHITE][0]] = 'S'
        white_back_row[self.gated_positions[WHITE][1]] = 'Z'
        black_back_row[self.gated_positions[BLACK][0]] = 's'
        black_back_row[self.gated_positions[BLACK][1]] = 'z'
        return ' '.join(black_back_row)[:15] + '\n' + "".join(builder) + '\n' + ' '.join(white_back_row)[:15]
    
    def custom_piece_type_at(self, square: Square) -> Optional[CustomPieceType]:
        mask = BB_SQUARES[square]
        if (not self.occupied & mask):
            return None
        for index in range (len(self.custom_pieces)):
            if (self.custom_pieces[index] & mask):
                return self.custom_piece_types[index]
        return None
    def custom_piece_at(self, square: Square) -> Optional[CustomPiece]:
        piece_type = self.custom_piece_type_at(square)
        if piece_type:
            mask = BB_SQUARES[square]
            color = bool(self.occupied_co[WHITE] & mask)
            return CustomPiece(piece_type, color, CUSTOM_BETZA[piece_type])
        else:
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

    def set_custom_piece_at(self, square: Square, piece: Optional[CustomPiece], promoted: bool = False):
        self.remove_custom_piece_at(square)
        if (piece == None):
            return
        mask = BB_SQUARES[square]

        for index in range (len(self.custom_pieces)):
            if (piece.piece_type == self.custom_piece_types[index]):
                self.custom_pieces[index] |= mask
        self.occupied ^= mask
        self.occupied_co[piece.color] ^= mask
        if promoted:
            self.promoted ^= mask
    
    def clear_board(self):
        super().clear_board()
        for custom_bb in self.custom_pieces:
            custom_bb = BB_EMPTY

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
            piece = self.custom_piece_at(square)
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
        return attacks

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
        non_pawn_custom = our_pieces & ~self.pawns & from_mask
        for custom in self.custom_pieces:
            non_pawn_custom &= custom
        for from_square in scan_reversed(non_pawn_custom):
            moves = self.custom_attacks_mask(from_square) & ~our_pieces & to_mask
            for to_square in scan_reversed(moves):
                yield Move(from_square, to_square)

        # Handle pawn custom
        pawns = self.pawns & self.occupied_co[self.turn] & from_mask

        pawn_type = 1
        for temp_type in range(CUSTOM_PIECE_TYPES[SERGEANT], CUSTOM_PIECE_TYPES[LIEUTENANT] + 1):
            if (self.custom_piece_types.count(temp_type) != 0 and pawn_type == 1):
                pawn_type = temp_type

        if (pawn_type == 1):
            yield from super().generate_pseudo_legal_moves(from_mask, to_mask)
            return

        # Special pawn captures
        if (pawn_type != CUSTOM_PIECE_TYPES[CORPORAL] and pawn_type != CUSTOM_PIECE_TYPES[LIEUTENANT]):
            for from_square in scan_reversed(pawns):
                targets = BB_PAWN_ATTACKS[not self.turn][from_square] & self.occupied_co[not self.turn] & to_mask

                for to_square in scan_reversed(targets):
                    yield Move(from_square, to_square)

        # Horizontal pawn moves
        if (pawn_type == CUSTOM_PIECE_TYPES[COLONEL] or pawn_type == CUSTOM_PIECE_TYPES[GENERAL] or pawn_type == CUSTOM_PIECE_TYPES[LIEUTENANT]):
            if (self.turn == WHITE):
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) == 6 or (pawn_type == CUSTOM_PIECE_TYPES[LIEUTENANT] and square_rank(from_square) == 1)):
                        if (BB_SQUARES[from_square + 1] & ~self.occupied and square_distance(from_square, from_square + 1) == 1):
                            yield Move(from_square, from_square + 1)
                        if (BB_SQUARES[from_square - 1] & ~self.occupied and square_distance(from_square, from_square - 1) == 1):
                            yield Move(from_square, from_square - 1)
            else:
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) == 1 or (pawn_type == CUSTOM_PIECE_TYPES[LIEUTENANT] and square_rank(from_square) == 6)):
                        if (BB_SQUARES[from_square + 1] & ~self.occupied and square_distance(from_square, from_square + 1) == 1):
                            yield Move(from_square, from_square + 1)
                        if (BB_SQUARES[from_square - 1] & ~self.occupied and square_distance(from_square, from_square - 1) == 1):
                            yield Move(from_square, from_square - 1)

        # Backward pawn moves
        for from_square in scan_reversed(pawns):
            if (self.turn == WHITE):
                if ((pawn_type == CUSTOM_PIECE_TYPES[SERGEANT] or pawn_type == CUSTOM_PIECE_TYPES[CAPTAIN]) and square_rank(from_square) < 4):
                    continue
                if ((pawn_type == CUSTOM_PIECE_TYPES[COLONEL] or pawn_type == CUSTOM_PIECE_TYPES[GENERAL]) and square_rank(from_square) < 3):
                    continue
                if (pawn_type == CUSTOM_PIECE_TYPES[CORPORAL] and square_rank(from_square) == 3):
                    continue
                yield Move(from_square, from_square - 8)

            else:
                if ((pawn_type == CUSTOM_PIECE_TYPES[SERGEANT] or pawn_type == CUSTOM_PIECE_TYPES[CAPTAIN]) and square_rank(from_square) > 3):
                    continue
                if ((pawn_type == CUSTOM_PIECE_TYPES[COLONEL] or pawn_type == CUSTOM_PIECE_TYPES[GENERAL]) and square_rank(from_square) > 4):
                    continue
                if (pawn_type == CUSTOM_PIECE_TYPES[CORPORAL] and square_rank(from_square) == 4):
                    continue
                yield Move(from_square, from_square + 8)

        # Knight pawn moves
        if (pawn_type == CUSTOM_PIECE_TYPES[CAPTAIN] or pawn_type == CUSTOM_PIECE_TYPES[COLONEL] or pawn_type == CUSTOM_PIECE_TYPES[COMMANDER] or pawn_type == CUSTOM_PIECE_TYPES[GENERAL]):
            if (self.turn == WHITE):
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) > 2):
                        break
                    if ((pawn_type == CUSTOM_PIECE_TYPES[CAPTAIN] or pawn_type == CUSTOM_PIECE_TYPES[COMMANDER]) and square_rank(from_square) > 1):
                        break
                    if (pawn_type != CUSTOM_PIECE_TYPES[GENERAL] and BB_SQUARES[from_square + 8] & self.occupied):
                        break
                    if (square_distance(from_square, from_square + 15) == 2 and BB_SQUARES[from_square + 15] & ~self.occupied):
                        yield Move(from_square, from_square + 15)
                    if (square_distance(from_square, from_square + 17) == 2 and BB_SQUARES[from_square + 17] & ~self.occupied):
                        yield Move(from_square, from_square + 17)

            else:
                for from_square in scan_reversed(pawns):
                    if (square_rank(from_square) < 5):
                        break
                    if ((pawn_type == CUSTOM_PIECE_TYPES[CAPTAIN] or pawn_type == CUSTOM_PIECE_TYPES[COMMANDER]) and square_rank(from_square) < 6):
                        break
                    if (pawn_type != CUSTOM_PIECE_TYPES[GENERAL] and BB_SQUARES[from_square - 8] & self.occupied):
                        break
                    if (square_distance(from_square, from_square - 15) == 2 and BB_SQUARES[from_square - 15] & ~self.occupied):
                        yield Move(from_square, from_square - 15)
                    if (square_distance(from_square, from_square - 17) == 2 and BB_SQUARES[from_square - 17] & ~self.occupied):
                        yield Move(from_square, from_square - 17)

        # Double pawn moves on 3rd rank
        if (pawn_type == CUSTOM_PIECE_TYPES[COLONEL] or pawn_type == CUSTOM_PIECE_TYPES[COMMANDER]):
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
    
    def generate_legal_moves(self, from_mask: Bitboard = BB_ALL, to_mask: Bitboard = BB_ALL):
        if self.is_variant_end():
            return

        king_mask = self.kings & self.occupied_co[self.turn]
        if king_mask:
            king = msb(king_mask)
            blockers = self._slider_blockers(king)
            checkers = self.attackers_mask(not self.turn, king)
            if checkers:
                for move in self._generate_evasions(king, checkers, from_mask, to_mask):
                    if self._is_safe(king, blockers, move):
                        yield move
            else:
                for move in self.generate_pseudo_legal_moves(from_mask, to_mask):
                    if self._is_safe(king, blockers, move):
                        yield move
        else:
            yield from self.generate_pseudo_legal_moves(from_mask, to_mask)

    def set_musketeer_board_fen(self, musketeer_fen: str) -> None:
        rows = musketeer_fen.split("/")
        fen = "/".join(rows[1:9])
        super().set_board_fen(fen)
        for ind in range (len(rows[9])):
            square = rows[9][ind]
            if (square == 'S'):
                self.gated_positions[WHITE][0] = ind
            elif (square == 'Z'):
                self.gated_positions[WHITE][1] = ind
        for ind in range (len(rows[0])):
            square = rows[0][ind]
            if (square == 's'):
                self.gated_positions[BLACK][0] = ind
            elif (square == 'z'):
                self.gated_positions[BLACK][1] = ind

    def parse_san(self, san: str) -> Move:
        # Castling.
        try:
            if (san.find("O-O-O") != -1 or san.find("0-0-0") != -1):
                return next(move for move in self.generate_castling_moves() if self.is_queenside_castling(move))
            elif (san.find("O-O") != -1 or san.find("0-0") != -1):
                return next(move for move in self.generate_castling_moves() if self.is_kingside_castling(move))
        except StopIteration:
            raise IllegalMoveError(f"illegal san: {san!r} in {self.fen()}")

        # Match normal moves.
        match = CUSTOM_SAN_REGEX.match(san)
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

        # Get the gated piece type
        g = match.group(5)
        ungated = CUSTOM_PIECE_SYMBOLS.index(g[-1].lower()) if g else None

        # Get the promotion piece type.
        p = match.group(6)
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
    
    def push(self, move: Move):
        super().push(move)

    def push_san(self, san: str):
        move = self.parse_san(san)
        self.push(move)
        if (san[-2] == '/'):
            piece = CustomPiece.from_symbol(san[-1].lower())
            piece.color = not self.turn
            self.set_custom_piece_at(move.from_square, piece)
            self.gated_positions[not self.turn][self.custom_piece_types.index(piece.piece_type)] = -1

        return move

    def push_uci(self, uci: str) -> Move:
        return super().push_uci(uci)

board = CustomBoard()
# board.push(Move(E2, E5))
# board.push(Move(E7, E7))
# board.push(Move(C2, C5))
# board.push(Move(E7, E7))
# print(board)
# for move in board.generate_pseudo_legal_moves(BB_RANK_2, BB_ALL):
#     print(move)

# board.custom_pieces.append()
# board.custom_piece_types = [PIECE_TYPES[SERGEANT]]
# board.clear_board()
# board.set_piece_at(E5, Piece(SERGEANT, WHITE))
# board.set_piece_at(D4, Piece(SERGEANT, BLACK))

board.custom_pieces.append(BB_EMPTY)
board.custom_pieces.append(BB_EMPTY)
board.custom_piece_types.append(CUSTOM_PIECE_TYPES[STORM])
board.custom_piece_types.append(CUSTOM_PIECE_TYPES[ZIGZAG])
CUSTOM_BETZA[CUSTOM_PIECE_TYPES[ZIGZAG]] = "zF7"
CUSTOM_BETZA[CUSTOM_PIECE_TYPES[STORM]] = "zW14"
temp_fen = input()
board.set_musketeer_board_fen(temp_fen)
print(board)
move = ""
while (True):
    move = input()
    if (move == "quit"):
        break
    board.push_san(move)
    print(board)
# board.set_musketeer_board_fen("**z***s*/rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR/SZ******")
# board.push_san("Nc3/Z")
# board.push_san("Nf6/Z")
# board.push_san("a4")
# board.push_san("h5")
# board.push_san("Zb3")
# print(board)
# for move in board.generate_pseudo_legal_moves(BB_E4, BB_ALL):
#     print(move)