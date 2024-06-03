import enum

FILE_NB = 8

class PieceMap:
    def __init__(self):
        self.name = ""
        self.pieces = {}

    def add(self, piece_type, piece_info):
        self.pieces[piece_type] = piece_info
    
    def clear_all():
        return 0

class PieceInfo:
    def __init__(self):
        self.name = ""
        self.betza = ""
        self.steps = [{}, {}]
        self.slider = [{}, {}]
        self.hopper = [{}, {}]
        self.crooked = [{}, {}]

class MoveModality(enum.IntEnum):
    MODALITY_QUIET = 0
    MODALITY_CAPTURE = 1
    MOVE_MODALITY_NB = 2

class Direction(enum.IntEnum):
    NORTH = 8
    EAST = 1
    SOUTH = -NORTH
    WEST = -EAST

    NORTH_EAST = NORTH + EAST
    SOUTH_EAST = SOUTH + EAST
    SOUTH_WEST = SOUTH + WEST
    NORTH_WEST = NORTH + WEST

class PieceType(enum.IntEnum):
    PAWN = 1
    SERGEANT = 2
    CAPTAIN = 3
    COLONEL = 4
    COMMANDER = 5
    CORPORAL = 6
    GENERAL = 7
    LIEUTENANT = 8
    KNIGHT = 10
    BISHOP = 11
    ROOK = 12
    QUEEN = 13

    KING = 100