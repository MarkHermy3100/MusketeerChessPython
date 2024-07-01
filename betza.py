from piece import *

leaper_atoms: dict[str, list[tuple]] = {
    'W': [(1, 0)],
    'F': [(1, 1)],
    'D': [(2, 0)],
    'N': [(2, 1)],
    'A': [(2, 2)],
    'H': [(3, 0)],
    'L': [(3, 1)],
    'C': [(3, 1)],
    'J': [(3, 2)],
    'Z': [(3, 2)],
    'G': [(3, 3)]
}
rider_atoms: dict[str, list[tuple]] = {
    'R': [(1, 0)],
    'B': [(1, 1)],
    'Q': [(1, 0), (1, 1)]
}
verticals = "fbvh"
horizontals = "rlsh"

def crooked_path(base: int, start: int, target: int, distance: int) -> list[int]:
    if (target == start):
        return []
    base_y = int(round(base / 8))
    base_x = base - base_y * 8
    base_perp = -base_y + (base_x << 3)
    path_straight = [(target & 7) - (start & 7), (target >> 3) - (start >> 3)]
    step_para = path_straight[0] * base_x + path_straight[1] * base_y
    step_perp = -path_straight[0] * base_y + path_straight[1] * base_x
    determinant = base_x * base_x + base_y * base_y
    if (step_para % determinant != 0 or step_perp % determinant != 0):
        return []
    step_para //= determinant
    step_perp //= determinant
    if (step_perp < 0):
        step_perp = -step_perp
        base_perp = base_y - (base_x << 3)
    if (step_para != step_perp and step_para != step_perp + 1):
        return []
    if (step_para + step_perp > distance):
        return []
    path = [start]
    for steps in range (1, step_para + step_perp + 1):
        path.append(path[-1] + base if (steps % 2 == 1) else path[-1] + base_perp)
    return path

def from_betza(betza) -> PieceInfo:
    new_piece = PieceInfo()
    move_modalities = []
    hopper: bool = False
    rider: bool = False
    lame: bool = False
    crooked: bool = False
    distance: int = 0
    prelim_directions: list[str] = []
    
    if (crooked): return

    for i in range (len(betza)):
        character: str = betza[i]
        char_next: str = betza[i + 1] if i + 1 < len(betza) else ''
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
        elif (character == 'z'):
            crooked = True
        elif (verticals.find(character) != -1 or horizontals.find(character) != -1):
            if (i + 1 < len(betza)):
                if (char_next == character
                    or (verticals.find(character) != -1 and horizontals.find(char_next) != -1)
                    or (horizontals.find(character) != -1 and verticals.find(char_next) != -1)):
                    prelim_directions.append(character + char_next)
                    i += 1
                    continue
            prelim_directions.append(character * 2)
        elif (leaper_atoms.get(character) != None or rider_atoms.get(character) != None):
            atoms: list[tuple] = leaper_atoms.get(character) if rider_atoms.get(character) == None else rider_atoms.get(character)
            if (rider_atoms.get(character) != None):
                rider = True
            if (i + 1 < len(betza) and (char_next.isdigit() or char_next == character)):
                rider = True
                if (char_next.isdigit()):
                    distance = ord(char_next) - ord('0')
                i += 1
            if (not rider and lame):
                distance = -1
            if (len(move_modalities) == 0):
                move_modalities.append(MoveModality.MODALITY_QUIET)
                move_modalities.append(MoveModality.MODALITY_CAPTURE)
            for atom in atoms:
                directions: list[str] = []
                for dir in prelim_directions:
                    if (len(atoms) == 1 and atom[1] == 0 and dir[0] != dir[1]):
                        directions.append(dir[0] * 2)
                        directions.append(dir[1] * 2)
                    else:
                        directions.append(dir)
                for modality in move_modalities:
                    move = new_piece.steps[modality]
                    if (hopper): 
                        move = new_piece.hopper[modality]
                    elif (rider):
                        move = new_piece.slider[modality]
                    if (crooked):
                        move = new_piece.crooked[modality]
                    has_dir = lambda s: directions.count(s) != 0
                    if (len(directions) == 0 or has_dir("ff") or has_dir("vv") or has_dir("rf") or has_dir("rv") or has_dir("fh") or has_dir("rh") or has_dir("hr")):
                        move[atom[0] * FILE_NB + atom[1]] = distance
                    if (len(directions) == 0 or has_dir("bb") or has_dir("vv") or has_dir("lb") or has_dir("lv") or has_dir("bh") or has_dir("lh") or has_dir("hr")):
                        move[-atom[0] * FILE_NB - atom[1]] = distance
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
            crooked = False
            distance = 0            
    return new_piece



# Testing


musketeer = PieceMap()
musketeer.add(PieceType.PAWN, from_betza("fmWfcF"))     # Pawn
musketeer.add(PieceType.KNIGHT, from_betza("N"))           # Knight
musketeer.add(PieceType.BISHOP, from_betza("nF7"))          # Bishop
musketeer.add(PieceType.ROOK, from_betza("nW7"))          # Rook
musketeer.add(PieceType.QUEEN, from_betza("nF7W7"))        # Queen

musketeer.add(PieceType.GENERAL, from_betza("fBfsWbB2bR"))

# for index, (piece, p_inf) in enumerate(musketeer.pieces.items()):
#     if (piece == PieceType.GENERAL):
#         print(p_inf.steps, p_inf.slider)
# Print values here to test piece range