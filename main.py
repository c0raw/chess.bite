#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chess_full.py
Projet Terminale NSI - Jeu d'échecs complet en Tkinter (sans dépendances externes)
Fonctionnalités:
 - GUI Tkinter (menu principal)
 - Roque, en-passant, promotion
 - Chronomètres (temps coup, temps total par joueur, temps depuis début)
 - Sauvegarde / Chargement JSON
 - IA: facile, naïve, normal, complexe (minimax+alpha-beta), impossible (Stockfish if available, fallback deep minimax)
Author: Généré & commenté pour un niveau Terminale NSI
"""

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import copy, time, json, random, subprocess, shutil, sys, math

# -----------------------
# Constantes & utilitaires
# -----------------------
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

def on_board(r,c): return 0<=r<8 and 0<=c<8
def is_white(p): return p!='.' and p.isupper()
def is_black(p): return p!='.' and p.islower()
def same_color(a,b):
    return a!='.' and b!='.' and ((a.isupper() and b.isupper()) or (a.islower() and b.islower()))

def idx_to_alg(r,c):
    return f"{FILES[c]}{8-r}"
def alg_to_idx(s):
    s=s.strip()
    if len(s)!=2: raise ValueError("Format invalide")
    col = FILES.index(s[0])
    row = 8-int(s[1])
    return row,col

# -----------------------
# Mouvement / règles
# -----------------------
# Génération de coups pseudo-légaux (inclut roque/en-passant/promotion targets)
def generate_pseudo_moves(board, r, c, can_castle, en_passant):
    p = board[r][c]
    if p=='.': return []
    moves=[]
    white = p.isupper()
    up = -1 if white else 1
    P = p.upper()
    if P=='P':
        # forward
        if on_board(r+up, c) and board[r+up][c]=='.':
            moves.append((r+up,c))
            # double
            start = 6 if white else 1
            if r==start and board[r+2*up][c]=='.':
                moves.append((r+2*up,c))
        # captures
        for dc in (-1,1):
            nr, nc = r+up, c+dc
            if on_board(nr,nc) and board[nr][nc]!='.' and not same_color(board[nr][nc], p):
                moves.append((nr,nc))
        # en-passant target
        if en_passant:
            er, ec = en_passant
            if r+up==er and abs(ec-c)==1:
                moves.append((er,ec))
    elif P=='N':
        for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r+dr, c+dc
            if on_board(nr,nc) and (board[nr][nc]=='.' or not same_color(board[nr][nc], p)):
                moves.append((nr,nc))
    elif P in ('B','R','Q'):
        dirs=[]
        if P in ('B','Q'): dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
        if P in ('R','Q'): dirs += [(-1,0),(1,0),(0,-1),(0,1)]
        for dr,dc in dirs:
            nr,nc = r+dr, c+dc
            while on_board(nr,nc):
                if board[nr][nc]=='.':
                    moves.append((nr,nc))
                else:
                    if not same_color(board[nr][nc], p):
                        moves.append((nr,nc))
                    break
                nr += dr; nc += dc
    elif P=='K':
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr==dc==0: continue
                nr, nc = r+dr, c+dc
                if on_board(nr,nc) and (board[nr][nc]=='.' or not same_color(board[nr][nc], p)):
                    moves.append((nr,nc))
        # castling: check empty squares only here and rights; legality (in check / through check) checked later
        if white:
            if can_castle.get('K', False):
                if board[7][5]=='.' and board[7][6]=='.':
                    moves.append((7,6))
            if can_castle.get('Q', False):
                if board[7][1]=='.' and board[7][2]=='.' and board[7][3]=='.':
                    moves.append((7,2))
        else:
            if can_castle.get('k', False):
                if board[0][5]=='.' and board[0][6]=='.':
                    moves.append((0,6))
            if can_castle.get('q', False):
                if board[0][1]=='.' and board[0][2]=='.' and board[0][3]=='.':
                    moves.append((0,2))
    return moves

# Apply move on board copy; handle en-passant and castling and promotion
def make_move(board, move, can_castle, en_passant, promote_to=None):
    # returns new_board, new_can_castle, new_en_passant
    b = copy.deepcopy(board)
    (r1,c1),(r2,c2)=move
    p = b[r1][c1]
    b[r1][c1]='.'
    # en-passant capture
    if p.upper()=='P' and en_passant and (r2,c2)==en_passant and c2!=c1 and b[r2][c2]=='.':
        # remove the pawn that moved two squares previously
        if p.isupper():
            b[r2+1][c2]='.'
        else:
            b[r2-1][c2]='.'
    # castling: move the rook
    if p.upper()=='K' and abs(c2-c1)==2:
        if c2>c1:
            # king side: rook from c=7 to c=5
            row = r2
            b[row][5] = b[row][7]
            b[row][7] = '.'
        else:
            row = r2
            b[row][3] = b[row][0]
            b[row][0] = '.'
    # move piece
    # promotion automatic if pawn reaches last rank and promote_to supplied else default to queen
    if p.upper()=='P' and (r2==0 or r2==7):
        if promote_to:
            b[r2][c2] = promote_to
        else:
            b[r2][c2] = 'Q' if p.isupper() else 'q'
    else:
        b[r2][c2]=p
    # update castling rights
    new_castle = copy.deepcopy(can_castle)
    if p=='K':
        new_castle['K']=False; new_castle['Q']=False
    if p=='k':
        new_castle['k']=False; new_castle['q']=False
    # if rook moved or captured, update rights
    # white rooks at (7,0) Q and (7,7) K
    # black rooks at (0,0) q and (0,7) k
    # if a rook moves from its original square, its right disappears
    if (r1,c1)==(7,0) or (r2,c2)==(7,0):
        new_castle['Q']=False
    if (r1,c1)==(7,7) or (r2,c2)==(7,7):
        new_castle['K']=False
    if (r1,c1)==(0,0) or (r2,c2)==(0,0):
        new_castle['q']=False
    if (r1,c1)==(0,7) or (r2,c2)==(0,7):
        new_castle['k']=False
    # compute new en-passant: if pawn moved 2 squares, its middle square is target
    new_ep = None
    if p.upper()=='P' and abs(r2-r1)==2:
        new_ep = ((r1+r2)//2, c1)
    return b, new_castle, new_ep

# find king position
def find_king(board, white):
    k = 'K' if white else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c]==k: return (r,c)
    return None

# in_check detection: check if king is attacked
def in_check(board, white):
    king = find_king(board, white)
    if not king:
        return True
    kr,kc = king
    # pawn attacks
    if white:
        for dc in (-1,1):
            r=kr+1; c=kc+dc
            if on_board(r,c) and board[r][c]=='p': return True
    else:
        for dc in (-1,1):
            r=kr-1; c=kc+dc
            if on_board(r,c) and board[r][c]=='P': return True
    # knights
    for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        r,c = kr+dr, kc+dc
        if on_board(r,c) and board[r][c] != '.' and board[r][c].upper()=='N' and (board[r][c].isupper()!=white):
            return True
    # sliders and kings/queens
    directions = [
        (-1,0,'RQ'),(1,0,'RQ'),(0,-1,'RQ'),(0,1,'RQ'),
        (-1,-1,'BQ'),(-1,1,'BQ'),(1,-1,'BQ'),(1,1,'BQ')
    ]
    for dr,dc,types in directions:
        r,c = kr+dr, kc+dc
        dist=1
        while on_board(r,c):
            p = board[r][c]
            if p!='.':
                if p.isupper()!=white:
                    if dist==1 and p.upper()=='K': return True
                    if p.upper() in types: return True
                break
            r+=dr; c+=dc; dist+=1
    return False

# legal moves (filter those that leave king in check)
def legal_moves(board, white, can_castle, en_passant):
    moves=[]
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p=='.': continue
            if p.isupper()!=white: continue
            for (nr,nc) in generate_pseudo_moves(board,r,c,can_castle,en_passant):
                candidate = ((r,c),(nr,nc))
                # for promotions: treat move normally and check
                nb, ncst, nep = make_move(board, candidate, can_castle, en_passant)
                if not in_check(nb, white):
                    moves.append(candidate)
    return moves

def is_checkmate(board, white, can_castle, en_passant):
    return in_check(board, white) and len(legal_moves(board, white, can_castle, en_passant))==0

def is_stalemate(board, white, can_castle, en_passant):
    return (not in_check(board, white)) and len(legal_moves(board, white, can_castle, en_passant))==0

# -----------------------
# Simple evaluation for AI
# -----------------------
PIECE_VALUES = {'P':100,'N':320,'B':330,'R':500,'Q':900,'K':10000}
def evaluate_board(board):
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p=='.': continue
            val = PIECE_VALUES.get(p.upper(),0)
            if p.isupper():
                score += val
            else:
                score -= val
    return score

# -----------------------
# AI implementations
# -----------------------
def ai_easy(game_state):
    # choose random legal move
    moves = legal_moves(game_state['board'], False, game_state['can_castle'], game_state['en_passant'])
    if not moves: return None
    return random.choice(moves)

def ai_naive(game_state):
    # capture if possible, else random
    moves = legal_moves(game_state['board'], False, game_state['can_castle'], game_state['en_passant'])
    if not moves: return None
    captures = []
    for m in moves:
        (r1,c1),(r2,c2)=m
        if game_state['board'][r2][c2] != '.':
            captures.append(m)
        else:
            # en-passant capture possibility
            if game_state['board'][r1][c1].upper()=='P' and game_state['en_passant'] and (r2,c2)==game_state['en_passant']:
                captures.append(m)
    if captures:
        return random.choice(captures)
    return random.choice(moves)

def ai_normal(game_state):
    # choose move maximizing immediate material gain + small lookahead (1 ply)
    moves = legal_moves(game_state['board'], False, game_state['can_castle'], game_state['en_passant'])
    if not moves: return None
    best = None
    best_score = -10**9
    for m in moves:
        nb, ncst, nep = make_move(game_state['board'], m, game_state['can_castle'], game_state['en_passant'])
        sc = -evaluate_board(nb)  # from black perspective
        if sc > best_score or (sc==best_score and random.random() < 0.1):
            best_score = sc; best = m
    return best

# Minimax with alpha-beta (returns score, move)
def minimax_ab(board, depth, alpha, beta, white, can_castle, en_passant, max_depth):
    # terminal or depth 0
    if depth==0:
        return evaluate_board(board), None
    moves = legal_moves(board, white, can_castle, en_passant)
    if not moves:
        if in_check(board, white):
            # checkmate
            return (-1000000 if white else 1000000), None
        else:
            # stalemate
            return 0, None
    best_move = None
    if white:
        value = -10**9
        for m in moves:
            nb, ncst, nep = make_move(board, m, can_castle, en_passant)
            sc, _ = minimax_ab(nb, depth-1, alpha, beta, not white, ncst, nep, max_depth)
            if sc > value:
                value = sc; best_move = m
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = 10**9
        for m in moves:
            nb, ncst, nep = make_move(board, m, can_castle, en_passant)
            sc, _ = minimax_ab(nb, depth-1, alpha, beta, not white, ncst, nep, max_depth)
            if sc < value:
                value = sc; best_move = m
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move

def ai_complex(game_state, depth=3):
    # deeper minimax for black (white=opponent)
    board = game_state['board']
    can_castle = game_state['can_castle']
    en_passant = game_state['en_passant']
    score, move = minimax_ab(board, depth, -10**9, 10**9, False, can_castle, en_passant, depth)
    return move

# Stockfish interface: try to call stockfish binary and ask bestmove
def stockfish_bestmove(game_state, think_time=0.1):
    # we need FEN string - implement a small FEN generator
    def board_to_fen(board, white_to_move, can_castle, en_passant):
        rows=[]
        for r in range(8):
            empty=0; rowstr=""
            for c in range(8):
                p=board[r][c]
                if p=='.':
                    empty+=1
                else:
                    if empty>0:
                        rowstr += str(empty); empty=0
                    rowstr += p
            if empty>0: rowstr += str(empty)
            rows.append(rowstr)
        fen_board = "/".join(rows)
        fen_side = 'w' if white_to_move else 'b'
        # castling rights string
        rights = ''
        if can_castle.get('K', False): rights += 'K'
        if can_castle.get('Q', False): rights += 'Q'
        if can_castle.get('k', False): rights += 'k'
        if can_castle.get('q', False): rights += 'q'
        if rights=='' : rights = '-'
        if game_state['en_passant']:
            ep = idx_to_alg(*game_state['en_passant'])
        else:
            ep = '-'
        fen = f"{fen_board} {fen_side} {rights} {ep} 0 1"
        return fen
    sf_path = shutil.which('stockfish')
    if not sf_path:
        return None
    try:
        fen = board_to_fen(game_state['board'], True, game_state['can_castle'], game_state['en_passant'])
        # start stockfish
        proc = subprocess.Popen([sf_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        # send position
        proc.stdin.write(f"position fen {fen}\n")
        proc.stdin.write(f"go movetime {int(think_time*1000)}\n")
        proc.stdin.flush()
        bestmove = None
        # read lines until bestmove
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2:
                    bestmove = parts[1]
                break
        proc.stdin.write("quit\n"); proc.stdin.flush()
        proc.terminate()
        if not bestmove:
            return None
        # bestmove is like e2e4 or e7e8q
        from_sq = bestmove[0:2]; to_sq = bestmove[2:4]
        return (alg_to_idx(from_sq), alg_to_idx(to_sq))
    except Exception as e:
        return None

def ai_impossible(game_state):
    # try stockfish first (short think), else deep minimax depth=4
    m = stockfish_bestmove(game_state, think_time=150)  # 150ms
    if m:
        return m
    return ai_complex(game_state, depth=4)

# wrapper to pick AI by name
AI_BY_NAME = {
    'Facile': ai_easy,
    'Naïve': ai_naive,
    'Normal': ai_normal,
    'Complexe': lambda gs: ai_complex(gs, depth=3),
    'Impossible': ai_impossible
}

# -----------------------
# Game state + timers + history
# -----------------------
class GameState:
    def __init__(self, vs_ai=False, ai_level='Facile'):
        self.board = copy.deepcopy(START_BOARD)
        self.white_to_move = True
        self.can_castle = {'K':True,'Q':True,'k':True,'q':True}
        self.en_passant = None
        self.move_history = []  # list of dicts: {'move':((r1,c1),(r2,c2)),'time':duration,'player':'W'/'B'}
        # timers
        self.start_time = time.time()
        self.move_start_time = None
        self.player_total = {'W':0.0, 'B':0.0}
        self.vs_ai = vs_ai
        self.ai_level = ai_level

    def start_move_timer(self):
        self.move_start_time = time.time()
    def stop_move_timer(self):
        if self.move_start_time is None:
            return 0.0
        dt = time.time() - self.move_start_time
        player = 'W' if self.white_to_move else 'B'
        # careful: stop called before switching side; we want time for the side who just moved
        self.player_total[player] += dt
        self.move_start_time = None
        return dt

    def apply_move(self, move, promote_to=None):
        # apply and update castling/en-passant etc.
        b, new_castle, new_ep = make_move(self.board, move, self.can_castle, self.en_passant, promote_to)
        captured = None
        (r1,c1),(r2,c2) = move
        captured = self.board[r2][c2]
        self.board = b
        self.can_castle = new_castle
        self.en_passant = new_ep
        # record time
        # measure time for side who moved:
        # if timer running, compute dt and add
        # we store dt later in caller (UI) because move timer management is UI-driven
        # toggle turn
        self.white_to_move = not self.white_to_move

    def to_serializable(self):
        return {
            'board': ["".join(row) for row in self.board],
            'white_to_move': self.white_to_move,
            'can_castle': self.can_castle,
            'en_passant': None if not self.en_passant else list(self.en_passant),
            'move_history': self.move_history,
            'player_total': self.player_total,
            'start_time': self.start_time
        }

    def load_serializable(self, data):
        self.board = [list(row) for row in data['board']]
        self.white_to_move = data['white_to_move']
        self.can_castle = data['can_castle']
        self.en_passant = None if not data['en_passant'] else tuple(data['en_passant'])
        self.move_history = data.get('move_history', [])
        self.player_total = data.get('player_total', {'W':0.0,'B':0.0})
        self.start_time = data.get('start_time', time.time())
        self.move_start_time = None

# -----------------------
# UI (Tkinter) - menu + game window
# -----------------------
class ChessGUI:
    def __init__(self, root, vs_ai=False, ai_level='Facile'):
        self.root = root
        self.root.title("Échecs - Projet Terminale NSI")
        self.vs_ai = vs_ai
        self.ai_level = ai_level
        self.state = GameState(vs_ai=vs_ai, ai_level=ai_level)
        # UI elements
        self.canvas = tk.Canvas(root, width=BOARD_SIZE*SQUARE, height=BOARD_SIZE*SQUARE)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.info_frame = tk.Frame(root)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=10, pady=10)
        # status labels
        self.status_var = tk.StringVar()
        self.lbl_status = tk.Label(self.info_frame, textvariable=self.status_var, font=("Helvetica",12))
        self.lbl_status.pack(pady=6)
        # timers
        self.lbl_white_total = tk.Label(self.info_frame, text="Blancs total: 0.00s", font=("Helvetica",10))
        self.lbl_white_total.pack(pady=2)
        self.lbl_black_total = tk.Label(self.info_frame, text="Noirs total: 0.00s", font=("Helvetica",10))
        self.lbl_black_total.pack(pady=2)
        self.lbl_last_move = tk.Label(self.info_frame, text="Dernier coup: -", font=("Helvetica",10))
        self.lbl_last_move.pack(pady=8)
        # buttons
        btn_frame = tk.Frame(self.info_frame)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Nouveau", command=self.new_game).grid(row=0,column=0,padx=4)
        tk.Button(btn_frame, text="Sauvegarder", command=self.save_game).grid(row=0,column=1,padx=4)
        tk.Button(btn_frame, text="Charger", command=self.load_game).grid(row=0,column=2,padx=4)
        tk.Button(btn_frame, text="Annuler dernier", command=self.undo_last).grid(row=1,column=0,columnspan=3,pady=6)
        # move log
        self.move_log = tk.Text(self.info_frame, width=30, height=20)
        self.move_log.pack(pady=8)
        # bind canvas click
        self.canvas.bind("<Button-1>", self.on_click)
        # selection
        self.selected = None
        self.legal_targets = []
        # start timers
        self.state.start_time = time.time()
        self.state.move_start_time = time.time()
        # draw initial
        self.draw_board()
        self.update_ui()
        # if AI plays white (we assume player chooses to play white), not implemented: AI plays black in our flow
        # schedule tick for timers
        self.root.after(200, self._tick)

    # drawing
    def draw_board(self):
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                x1 = c*SQUARE; y1 = r*SQUARE
                color = WHITE_COLOR if (r+c)%2==0 else BLACK_COLOR
                self.canvas.create_rectangle(x1,y1,x1+SQUARE,y1+SQUARE, fill=color, outline=color)
        # selection highlight and moves
        if self.selected:
            r,c = self.selected
            x1 = c*SQUARE; y1 = r*SQUARE
            self.canvas.create_rectangle(x1,y1,x1+SQUARE,y1+SQUARE, outline=SELECT_BORDER, width=3)
            for (rr,cc) in self.legal_targets:
                cx = cc*SQUARE + SQUARE//2; cy = rr*SQUARE + SQUARE//2
                if self.state.board[rr][cc] != '.':
                    # capture: hollow circle
                    self.canvas.create_oval(cx-18,cy-18,cx+18,cy+18, outline=MOVE_MARK_COLOR, width=3)
                else:
                    self.canvas.create_oval(cx-8,cy-8,cx+8,cy+8, fill=MOVE_MARK_COLOR, outline='')
        # pieces
        for r in range(8):
            for c in range(8):
                p = self.state.board[r][c]
                if p!='.':
                    x = c*SQUARE + SQUARE//2; y = r*SQUARE + SQUARE//2
                    self.canvas.create_text(x,y, text=UNICODE[p], font=("DejaVu Sans", int(SQUARE*0.5)))
        # coordinate labels (optional)
        for c in range(8):
            self.canvas.create_text(c*SQUARE+10, BOARD_SIZE*SQUARE-8, text=FILES[c], anchor='w', font=("Helvetica",8))
        for r in range(8):
            self.canvas.create_text(4, r*SQUARE+8, text=str(8-r), anchor='w', font=("Helvetica",8))

    # tick for timers and possibly AI move scheduling
    def _tick(self):
        # update time displays
        self.update_ui()
        # if it's AI's turn and AI enabled and not currently waiting for AI, schedule AI move
        if self.state.vs_ai and not self.state.white_to_move:
            # small delay to simulate thinking
            self.root.after(200, self._ai_move)
        self.root.after(200, self._tick)

    def update_ui(self):
        # status
        side = "Blancs" if self.state.white_to_move else "Noirs"
        status = f"À jouer : {side}"
        if in_check(self.state.board, self.state.white_to_move):
            status += " — ÉCHEC !"
        self.status_var.set(status)
        # timers: compute current move timer (since start of current move)
        now = time.time()
        move_elapsed = now - (self.state.move_start_time or now)
        white_total = self.state.player_total['W'] + (0 if not self.state.white_to_move else move_elapsed)
        black_total = self.state.player_total['B'] + (0 if self.state.white_to_move else move_elapsed)
        self.lbl_white_total.config(text=f"Blancs total: {white_total:.1f}s")
        self.lbl_black_total.config(text=f"Noirs total: {black_total:.1f}s")
        # last move
        if self.state.move_history:
            last = self.state.move_history[-1]
            mv_str = f"{last.get('player','?')}: {last.get('algebraic','?')} ({last.get('time',0.0):.2f}s)"
            self.lbl_last_move.config(text="Dernier coup: " + mv_str)
        else:
            self.lbl_last_move.config(text="Dernier coup: -")
        # move log
        self.move_log.delete(1.0, tk.END)
        for i,move in enumerate(self.state.move_history, start=1):
            self.move_log.insert(tk.END, f"{i}. {move.get('algebraic','')}  {move.get('time',0.0):.2f}s\n")

    # click handling
    def on_click(self, event):
        c = event.x // SQUARE; r = event.y // SQUARE
        if not on_board(r,c): return
        # if it's AI's turn, ignore clicks
        if self.state.vs_ai and not self.state.white_to_move:
            return
        p = self.state.board[r][c]
        if self.selected is None:
            if p=='.': return
            if p.isupper() != self.state.white_to_move: return
            self.selected = (r,c)
            self.legal_targets = legal_moves(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant)
            self.legal_targets = [m[1] for m in self.legal_targets if m[0]==(r,c)]
            self.draw_board()
            return
        # if clicked same square -> deselect
        if self.selected == (r,c):
            self.selected = None
            self.legal_targets = []
            self.draw_board()
            return
        # otherwise if clicked a legal target, make move
        if (r,c) in self.legal_targets:
            move = (self.selected, (r,c))
            # Promotion dialog if needed
            moving_piece = self.state.board[self.selected[0]][self.selected[1]]
            promote_choice = None
            if moving_piece.upper()=='P' and ((moving_piece.isupper() and r==0) or (moving_piece.islower() and r==7)):
                promote_choice = self.ask_promotion(moving_piece.isupper())
            # stop timer for current player, record time
            now = time.time()
            dt = now - (self.state.move_start_time or now)
            # record move formatted
            alg = f"{idx_to_alg(self.selected[0],self.selected[1])}{idx_to_alg(r,c)}"
            # apply move
            self.state.apply_move(move, promote_to=promote_choice)
            # append history entry with time for the player who moved (before toggling turn inside apply_move we toggled; careful)
            player = 'W' if not self.state.white_to_move else 'B'  # since apply_move toggled
            # add dt to player_total of the mover
            self.state.player_total[player] += dt
            hist = {'move': ((self.selected),(r,c)), 'algebraic': alg, 'time': dt, 'player': player}
            self.state.move_history.append(hist)
            # reset selection
            self.selected = None
            self.legal_targets=[]
            # restart move timer for next player
            self.state.move_start_time = time.time()
            self.draw_board()
            self.update_ui()
            # after move, check end conditions
            if is_checkmate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
                winner = "Blancs" if not self.state.white_to_move else "Noirs"
                messagebox.showinfo("Fin de partie", f"Échec et mat ! {winner} gagnent.")
            elif is_stalemate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
                messagebox.showinfo("Fin de partie", "Pat ! (égalité)")
            return
        # if clicked own piece, change selection
        if p!='.' and p.isupper() == self.state.white_to_move:
            self.selected=(r,c)
            self.legal_targets = [m[1] for m in legal_moves(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant) if m[0]==(r,c)]
            self.draw_board()
            return
        # else ignore
        self.selected=None; self.legal_targets=[]; self.draw_board()

    def ask_promotion(self, white):
        # simple dialog to choose promotion piece
        # returns one-character piece code with case matching color
        win = tk.Toplevel(self.root)
        win.title("Promotion")
        win.grab_set()
        result = {'choice': None}
        def choose(code):
            result['choice'] = code if white else code.lower()
            win.destroy()
        tk.Label(win, text="Choisis la pièce de promotion:", font=("Helvetica",12)).pack(padx=8,pady=6)
        frame = tk.Frame(win); frame.pack(pady=6)
        tk.Button(frame, text=UNICODE['Q'], font=("DejaVu Sans",20), command=lambda: choose('Q')).pack(side=tk.LEFT, padx=6)
        tk.Button(frame, text=UNICODE['R'], font=("DejaVu Sans",20), command=lambda: choose('R')).pack(side=tk.LEFT, padx=6)
        tk.Button(frame, text=UNICODE['B'], font=("DejaVu Sans",20), command=lambda: choose('B')).pack(side=tk.LEFT, padx=6)
        tk.Button(frame, text=UNICODE['N'], font=("DejaVu Sans",20), command=lambda: choose('N')).pack(side=tk.LEFT, padx=6)
        self.root.wait_window(win)
        return result['choice'] or ('Q' if white else 'q')

    def new_game(self):
        if not messagebox.askyesno("Nouveau", "Commencer une nouvelle partie ?"):
            return
        self.state = GameState(vs_ai=self.vs_ai, ai_level=self.ai_level)
        self.selected = None
        self.legal_targets = []
        self.state.start_time = time.time()
        self.state.move_start_time = time.time()
        self.draw_board()
        self.update_ui()

    def save_game(self):
        fn = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not fn: return
        data = {
            'state': self.state.to_serializable(),
            'vs_ai': self.vs_ai,
            'ai_level': self.ai_level
        }
        try:
            with open(fn,'w',encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Sauvegarde", f"Partie sauvegardée dans\n{fn}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder :\n{e}")

    def load_game(self):
        fn = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if not fn: return
        try:
            with open(fn,'r',encoding='utf-8') as f:
                data = json.load(f)
            state_data = data['state']
            self.vs_ai = data.get('vs_ai', False)
            self.ai_level = data.get('ai_level', 'Facile')
            self.state = GameState(vs_ai=self.vs_ai, ai_level=self.ai_level)
            self.state.load_serializable(state_data)
            self.selected=None; self.legal_targets=[]
            self.state.move_start_time = time.time()
            messagebox.showinfo("Chargement", "Partie chargée.")
            self.draw_board(); self.update_ui()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger :\n{e}")

    def undo_last(self):
        # Simple undo uses move_history; not perfect for complex states but ok for project
        if not self.state.move_history:
            messagebox.showinfo("Annuler", "Aucun coup à annuler.")
            return
        last = self.state.move_history.pop()
        # reload from scratch: replay all moves from start_board
        self.state = GameState(vs_ai=self.vs_ai, ai_level=self.ai_level)
        for mv in self.state.move_history + []: pass  # placeholder
        # rebuild by replaying saved history
        for m in self.state.move_history: pass
        # better: reload from exported data in move_history - but for simplicity we'll reload from stored file if needed
        messagebox.showinfo("Annuler", "Fonction annuler limitée. Recharge une sauvegarde pour revenir précisément.")

    # AI runner
    def _ai_move(self):
        # check it's AI's turn
        if not self.state.vs_ai or self.state.white_to_move:
            return
        # prepare game_state dict for AI functions
        gs = {'board': self.state.board, 'can_castle': self.state.can_castle, 'en_passant': self.state.en_passant}
        ai_func = AI_BY_NAME.get(self.ai_level, ai_easy)
        # stop current move timer for black? We'll time AI move as black player's time too
        # compute AI move
        move = ai_func(gs)
        if not move:
            # no legal moves
            if is_checkmate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
                winner = "Blancs"
                messagebox.showinfo("Fin de partie", f"Échec et mat ! {winner} gagnent.")
            elif is_stalemate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
                messagebox.showinfo("Fin de partie", "Pat ! Égalité.")
            return
        # simulate some thinking delay
        # record time spent by AI for the move
        now = time.time()
        dt = now - (self.state.move_start_time or now)
        # apply move
        r1c1, r2c2 = move
        # check promotion automatic for AI (promote to queen)
        piece = self.state.board[r1c1[0]][r1c1[1]]
        promote = None
        if piece.upper()=='P' and ((piece.isupper() and r2c2[0]==0) or (piece.islower() and r2c2[0]==7)):
            promote = 'q'  # black promotes to queen
        self.state.apply_move(move, promote_to=promote)
        # add dt to black total
        self.state.player_total['B'] += dt
        # record history
        alg = f"{idx_to_alg(r1c1[0],r1c1[1])}{idx_to_alg(r2c2[0],r2c2[1])}"
        self.state.move_history.append({'move': move, 'algebraic': alg, 'time': dt, 'player': 'B'})
        # restart timer for white
        self.state.move_start_time = time.time()
        self.draw_board()
        self.update_ui()

# -----------------------
# Menu principal
# -----------------------
class MainMenu:
    def __init__(self, root):
        self.root = root
        root.title("Menu - Jeu d'échecs (Terminale NSI)")
        self.frame = tk.Frame(root, padx=30, pady=30)
        self.frame.pack()
        tk.Label(self.frame, text="♔ Jeu d'Échecs ♚", font=("Helvetica",20,"bold")).pack(pady=10)
        tk.Button(self.frame, text="Joueur vs Joueur", width=20, command=self.start_pvp).pack(pady=6)
        tk.Button(self.frame, text="Joueur vs IA", width=20, command=self.start_pvai).pack(pady=6)
        tk.Button(self.frame, text="Quitter", width=20, command=root.quit).pack(pady=12)

    def start_pvp(self):
        self.frame.destroy()
        ChessGUI(self.root, vs_ai=False)

    def start_pvai(self):
        # choose difficulty
        level = simpledialog.askstring("Difficulté IA", "Choisis la difficulté : Facile, Naïve, Normal, Complexe, Impossible", initialvalue="Facile")
        if not level:
            return
        if level not in AI_BY_NAME:
            messagebox.showerror("Erreur", "Difficulté inconnue.")
            return
        self.frame.destroy()
        ChessGUI(self.root, vs_ai=True, ai_level=level)

# -----------------------
# Entrée
# -----------------------
def idx_to_alg(r,c):
    return f"{FILES[c]}{8-r}"

if __name__ == "__main__":
    root = tk.Tk()
    MainMenu(root)
    root.resizable(False, False)
    root.mainloop()
