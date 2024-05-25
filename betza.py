import chess
from piece import *

leaper_atoms = {
    'W': (1, 0),
    'F': (1, 1),
    'D': (2, 0),
    'N': (2, 1),
    'A': (2, 2),
    'H': (3, 0),
    'L': (3, 1),
    'C': (3, 1),
    'J': (3, 2),
    'Z': (3, 2),
    'G': (3, 3)
}
rider_atoms = {
    'R': [(1, 0)],
    'B': [(1, 1)],
    'Q': [(1, 0), (1, 1)]
}
verticals = "fbvh"
horizontals = "rlsh"

def from_betza(betza) -> PieceInfo:
    new_piece = PieceInfo()
    move_modalities = []
    hopper = False
    rider = False
    lame = False
    distance = 0
    prelim_directions = []

    if (hopper or rider or lame or distance == 1):
        return

    for i in range (len(betza)):
        character = betza[i]
        if (character == 'm' or character == 'c'):
            if (character == 'c'):
                move_modalities.append(MoveModality.MODALITY_CAPTURE)
            else:
                move_modalities.append(MoveModality.MODALITY_QUIET)
        elif (character == 'p' or character == 'g' or character == 'j'):
            hopper = True
            if (character == 'g' or character == 'j'):
                distance = 1
        elif (character == 'n'):
            lame = True
        elif (verticals.find(character) != -1 or horizontals.find(character) != -1):
            if (i + 1 < len(betza)):
                char2 = betza[i + 1]
                if (char2 == character
                    or (verticals.find(character) != -1 and horizontals.find(char2) != -1)
                    or (horizontals.find(character) != -1 and verticals.find(char2) != -1)):
                    prelim_directions.append(character + char2)
                    i += 1
                    continue
            prelim_directions.append(character * 2)
        elif (leaper_atoms.get(character) != None or rider_atoms.get(character) != None):
            atoms = leaper_atoms.get(character)[0] if rider_atoms.get(character) == None else rider_atoms.get(character)[0]
            if (rider_atoms.get(character) != None):
                rider = True
            if (i + 1 < len(betza) and (str(betza[i + 1]).isdigit() or betza[i + 1] == character)):
                rider = True
                if (str(betza[i + 1]).isdigit()):
                    distance = ord(betza[i + 1]) - ord('0')
                i += 1
            if (not rider and lame):
                distance = -1
            if (len(move_modalities) == 0):
                move_modalities.append(MoveModality.MODALITY_QUIET)
                move_modalities.append(MoveModality.MODALITY_CAPTURE)
            for atom in atoms:
                directions = []
                for dir in prelim_directions:
                    if (len(atoms) == 1 and atom[1] == 0 and dir[0] != dir[1]):
                        directions.append(dir[0] * 2)
                        directions.append(dir[1] * 2)
                    else:
                        directions.append(dir)
                for modality in move_modalities:
                    move = new_piece.steps[0][modality]
                    if (hopper): 
                        move = new_piece.hopper[0][modality]
                    elif (rider):
                        move = new_piece.slider[0][modality]
                    has_dir = lambda s: directions.count(s) != 0
                    if (len(directions) == 0 or has_dir("ff") or has_dir("vv") or has_dir("rf") or has_dir("rv") or has_dir("fh") or has_dir("rh") or has_dir("hr")):
                        move[Direction(atom[0] * FILE_NB + atom[1])] = distance
                    if (len(directions) == 0 or has_dir("bb") or has_dir("vv") or has_dir("lb") or has_dir("lv") or has_dir("bh") or has_dir("lh") or has_dir("hr")):
                        move[Direction(-atom[0] * FILE_NB - atom[1])] = distance
                    if (len(directions) == 0 or has_dir("rr") or has_dir("ss") or has_dir("br") or has_dir("bs") or has_dir("bh") or has_dir("rh") or has_dir("hr")):
                        move[-atom[1] * FILE_NB + atom[0]] = distance
                    if (len(directions) == 0 or has_dir("ll") or has_dir("ss") or has_dir("fl") or has_dir("fs") or has_dir("fh") or has_dir("lh") or has_dir("hr")):
                        move[atom[1] * FILE_NB - atom[0]] = distance
                    if (len(directions) == 0 or has_dir("rr") or has_dir("ss") or has_dir("fr") or has_dir("fs") or has_dir("fh") or has_dir("rh") or has_dir("hl")):
                        move[atom[1] * FILE_NB + atom[0]] = distance
                    if (len(directions) == 0 or has_dir("ll") or has_dir("ss") or has_dir("bl") or has_dir("bs") or has_dir("bh") or has_dir("lh") or has_dir("hl")):
                        move[-atom[1] * FILE_NB - atom[0]] = distance
                    if (len(directions) == 0 or has_dir("bb") or has_dir("vv") or has_dir("rb") or has_dir("rv") or has_dir("bh") or has_dir("rh") or has_dir("hl")):
                        move[-atom[0] * FILE_NB + atom[1]] = distance
                    if (len(directions) == 0 or has_dir("ff") or has_dir("vv") or has_dir("lf") or has_dir("lv") or has_dir("fh") or has_dir("lh") or has_dir("hl")):
                        move[atom[0] * FILE_NB - atom[1]] = distance
            move_modalities.clear()
            prelim_directions.clear()
            hopper = False
            rider = False
            lame = False
            distance = 0
    
    return new_piece



# Testing

"""
musketeer = PieceMap()
musketeer.add(1, from_betza("fmWfceF"))     # Pawn
musketeer.add(2, from_betza("N"))           # Knight
musketeer.add(3, from_betza("F7"))          # Bishop
musketeer.add(4, from_betza("W7"))          # Rook
musketeer.add(5, from_betza("F7W7"))        # Queen

# Print values here to test piece range
"""