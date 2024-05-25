from enum import Enum

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
        self.steps = {}
        self.slider = {}
        self.hopper = {}


class MoveModality(Enum):
    MODALITY_QUIET: 0
    MODALITY_CAPTURE: 0
    MOVE_MODALITY_NB: 0

class Direction(Enum):
    NORTH = 8
    EAST = 1
    SOUTH = -NORTH
    WEST = -EAST

    NORTH_EAST = NORTH + EAST
    SOUTH_EAST = SOUTH + EAST
    SOUTH_WEST = SOUTH + WEST
    NORTH_WEST = NORTH + WEST