BOARD_SIZE = 8
SQUARE = 70

WHITE_COLOR = "#F0D9B5"
BLACK_COLOR = "#B58863"
HIGHLIGHT_COLOR = "#F6F669"
MOVE_MARK_COLOR = "#4CAF50"
SELECT_BORDER = "#FF3333"

FILES = "abcdefgh"

UNICODE = {
    'K':'♔','Q':'♕','R':'♖','B':'♗','N':'♘','P':'♙',
    'k':'♚','q':'♛','r':'♜','b':'♝','n':'♞','p':'♟',
    '.':''
}

START_BOARD = [
    list("rnbqkbnr"),
    list("pppppppp"),
    list("........"),
    list("........"),
    list("........"),
    list("........"),
    list("PPPPPPPP"),
    list("RNBQKBNR")
]

def on_board(r, c): return 0 <= r < 8 and 0 <= c < 8
def is_white(p): return p != '.' and p.isupper()
def is_black(p): return p != '.' and p.islower()
def same_color(a, b): return a != '.' and b != '.' and ((a.isupper() and b.isupper()) or (a.islower() and b.islower()))

def idx_to_alg(r, c):
    return f"{FILES[c]}{8-r}"

def alg_to_idx(s):
    s = s.strip()
    if len(s) != 2:
        raise ValueError("Format invalide")
    col = FILES.index(s[0])
    row = 8 - int(s[1])
    return row, col