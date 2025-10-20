#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jeu d'Échecs Tkinter - Menu principal + Mode IA ou 2 joueurs
Author: ChatGPT
"""

import copy
import json
import random
import tkinter as tk
from tkinter import messagebox, filedialog

# -------------------------
# Constantes
# -------------------------
BOARD_SIZE = 8
SQUARE_SIZE = 72
CANVAS_SIZE = BOARD_SIZE * SQUARE_SIZE
WHITE_COLOR = "#F0D9B5"
BLACK_COLOR = "#B58863"
HIGHLIGHT_COLOR = "#f6f669"
SELECT_BORDER = "#FF3333"
MOVE_CIRCLE_COLOR = "#4CAF50"
FILES = "abcdefgh"

UNICODE_PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    '.': ''
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

# -------------------------
# Logique du jeu (identique à avant)
# -------------------------
def on_board(r, c): return 0 <= r < 8 and 0 <= c < 8
def is_white(p): return p != '.' and p.isupper()
def is_black(p): return p != '.' and p.islower()
def same_color(p1, p2):
    return p1 != '.' and p2 != '.' and ((p1.isupper() and p2.isupper()) or (p1.islower() and p2.islower()))

def generate_moves_for_square(board, r, c):
    piece = board[r][c]
    if piece == '.': return []
    moves = []
    white = piece.isupper()
    p = piece.upper()
    if p == 'P':
        dir = -1 if white else 1
        start_row = 6 if white else 1
        if on_board(r+dir, c) and board[r+dir][c] == '.':
            moves.append((r+dir, c))
            if r == start_row and board[r+2*dir][c] == '.':
                moves.append((r+2*dir, c))
        for dc in [-1,1]:
            nr, nc = r+dir, c+dc
            if on_board(nr,nc) and board[nr][nc] != '.' and not same_color(board[r][c], board[nr][nc]):
                moves.append((nr,nc))
    elif p == 'N':
        for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r+dr, c+dc
            if on_board(nr,nc) and not same_color(board[r][c], board[nr][nc]):
                moves.append((nr,nc))
    elif p in ('B','R','Q'):
        dirs = []
        if p in ('B','Q'): dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
        if p in ('R','Q'): dirs += [(-1,0),(1,0),(0,-1),(0,1)]
        for dr,dc in dirs:
            nr, nc = r+dr, c+dc
            while on_board(nr,nc):
                if board[nr][nc] == '.':
                    moves.append((nr,nc))
                else:
                    if not same_color(board[r][c], board[nr][nc]):
                        moves.append((nr,nc))
                    break
                nr += dr; nc += dc
    elif p == 'K':
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr == 0 and dc == 0: continue
                nr, nc = r+dr, c+dc
                if on_board(nr,nc) and not same_color(board[r][c], board[nr][nc]):
                    moves.append((nr,nc))
    return moves

def make_move(board, move):
    (r1,c1),(r2,c2) = move
    b = copy.deepcopy(board)
    piece = b[r1][c1]
    b[r1][c1] = '.'
    if piece.upper() == 'P' and ((piece.isupper() and r2==0) or (piece.islower() and r2==7)):
        piece = 'Q' if piece.isupper() else 'q'
    b[r2][c2] = piece
    return b

def find_king(board, white):
    target = 'K' if white else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c] == target:
                return (r,c)
    return None

def in_check(board, white):
    kpos = find_king(board, white)
    if not kpos: return True
    kr,kc = kpos
    dirs = [
        (-1,0,'RQ'),(1,0,'RQ'),(0,-1,'RQ'),(0,1,'RQ'),
        (-1,-1,'BQ'),(-1,1,'BQ'),(1,-1,'BQ'),(1,1,'BQ')
    ]
    for dr,dc,types in dirs:
        r,c = kr+dr, kc+dc
        dist=1
        while on_board(r,c):
            p = board[r][c]
            if p != '.':
                if p.isupper()!=white:
                    if dist==1 and p.upper()=='K': return True
                    if p.upper() in types: return True
                break
            r+=dr; c+=dc; dist+=1
    for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        r,c = kr+dr, kc+dc
        if on_board(r,c):
            p = board[r][c]
            if p!='.' and p.upper()=='N' and (p.isupper()!=white): return True
    pawns = [(-1,-1),(-1,1)] if white else [(1,-1),(1,1)]
    for dr,dc in pawns:
        r,c = kr+dr,kc+dc
        if on_board(r,c):
            p=board[r][c]
            if (white and p=='p') or ((not white) and p=='P'):
                return True
    return False

def legal_moves(board, white):
    moves=[]
    for r in range(8):
        for c in range(8):
            p=board[r][c]
            if p=='.': continue
            if p.isupper()!=white: continue
            for nr,nc in generate_moves_for_square(board,r,c):
                nb=make_move(board,((r,c),(nr,nc)))
                if not in_check(nb,white):
                    moves.append(((r,c),(nr,nc)))
    return moves

def is_checkmate(board, white): return in_check(board,white) and not legal_moves(board,white)
def is_stalemate(board, white): return not in_check(board,white) and not legal_moves(board,white)

# -------------------------
# Classes
# -------------------------
class Game:
    def __init__(self, vs_ai=False):
        self.board = copy.deepcopy(START_BOARD)
        self.white_to_move = True
        self.vs_ai = vs_ai

    def ai_move(self):
        """IA simple : choisit un coup légal au hasard"""
        moves = legal_moves(self.board, False)
        if not moves: return None
        return random.choice(moves)

# -------------------------
# Interface graphique
# -------------------------
class ChessUI:
    def __init__(self, root, vs_ai=False):
        self.root=root
        self.game=Game(vs_ai)
        self.vs_ai=vs_ai
        self.selected=None
        self.legal=[]
        self.canvas=tk.Canvas(root,width=CANVAS_SIZE,height=CANVAS_SIZE)
        self.canvas.pack()
        self.status=tk.Label(root,text="",font=("Helvetica",12))
        self.status.pack(pady=6)
        self.canvas.bind("<Button-1>",self.on_click)
        self.draw_board()
        self.update_status()

    def draw_board(self):
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                x1=c*SQUARE_SIZE; y1=r*SQUARE_SIZE
                color=WHITE_COLOR if (r+c)%2==0 else BLACK_COLOR
                self.canvas.create_rectangle(x1,y1,x1+SQUARE_SIZE,y1+SQUARE_SIZE,fill=color,outline=color)
        # highlight
        if self.selected:
            r,c=self.selected
            x1=c*SQUARE_SIZE; y1=r*SQUARE_SIZE
            self.canvas.create_rectangle(x1,y1,x1+SQUARE_SIZE,y1+SQUARE_SIZE,outline=SELECT_BORDER,width=3)
        for (r,c) in self.legal:
            cx=c*SQUARE_SIZE+SQUARE_SIZE//2
            cy=r*SQUARE_SIZE+SQUARE_SIZE//2
            self.canvas.create_oval(cx-10,cy-10,cx+10,cy+10,fill=MOVE_CIRCLE_COLOR,outline="")
        # pieces
        for r in range(8):
            for c in range(8):
                p=self.game.board[r][c]
                if p!='.':
                    txt=UNICODE_PIECES[p]
                    x=c*SQUARE_SIZE+SQUARE_SIZE//2
                    y=r*SQUARE_SIZE+SQUARE_SIZE//2
                    self.canvas.create_text(x,y,text=txt,font=("DejaVu Sans",32))

    def on_click(self,e):
        c=e.x//SQUARE_SIZE; r=e.y//SQUARE_SIZE
        if not on_board(r,c): return
        p=self.game.board[r][c]
        if self.selected is None:
            if p=='.' or (p.isupper()!=self.game.white_to_move): return
            self.selected=(r,c)
            self.legal=[m[1] for m in legal_moves(self.game.board,self.game.white_to_move) if m[0]==(r,c)]
            self.draw_board()
            return
        if (r,c)==self.selected:
            self.selected=None; self.legal=[]; self.draw_board(); return
        if (r,c) in self.legal:
            move=(self.selected,(r,c))
            self.game.board=make_move(self.game.board,move)
            self.game.white_to_move=not self.game.white_to_move
            self.selected=None; self.legal=[]
            self.draw_board()
            self.check_end()
            if self.vs_ai and not self.game.white_to_move:
                self.root.after(400,self.ai_turn)
        else:
            if p!='.' and p.isupper()==self.game.white_to_move:
                self.selected=(r,c)
                self.legal=[m[1] for m in legal_moves(self.game.board,self.game.white_to_move) if m[0]==(r,c)]
                self.draw_board()
        self.update_status()

    def ai_turn(self):
        move=self.game.ai_move()
        if move:
            self.game.board=make_move(self.game.board,move)
            self.game.white_to_move=True
            self.draw_board()
            self.check_end()
            self.update_status()

    def update_status(self):
        if is_checkmate(self.game.board,self.game.white_to_move):
            msg=f"Échec et mat ! {'Blancs' if not self.game.white_to_move else 'Noirs'} gagnent."
        elif is_stalemate(self.game.board,self.game.white_to_move):
            msg="Pat ! Égalité."
        else:
            msg=f"À jouer : {'Blancs' if self.game.white_to_move else 'Noirs'}"
            if in_check(self.game.board,self.game.white_to_move):
                msg+=" — Échec !"
        self.status.config(text=msg)

    def check_end(self):
        if is_checkmate(self.game.board,self.game.white_to_move):
            messagebox.showinfo("Fin de partie","Échec et mat !")
        elif is_stalemate(self.game.board,self.game.white_to_move):
            messagebox.showinfo("Fin de partie","Pat ! Égalité.")

# -------------------------
# Menu principal
# -------------------------
class MenuPrincipal:
    def __init__(self, root):
        self.root=root
        root.title("Jeu d'Échecs - Menu Principal")
        frame=tk.Frame(root,padx=40,pady=40)
        frame.pack()
        tk.Label(frame,text="♔ Jeu d'Échecs ♚",font=("Helvetica",20,"bold")).pack(pady=20)
        tk.Button(frame,text="Joueur vs Joueur",font=("Helvetica",14),width=20,command=self.start_pvp).pack(pady=10)
        tk.Button(frame,text="Joueur vs IA",font=("Helvetica",14),width=20,command=self.start_ai).pack(pady=10)
        tk.Button(frame,text="Quitter",font=("Helvetica",12),command=root.quit).pack(pady=20)

    def start_pvp(self):
        self.open_game(vs_ai=False)

    def start_ai(self):
        self.open_game(vs_ai=True)

    def open_game(self, vs_ai):
        self.root.destroy()
        root=tk.Tk()
        ChessUI(root,vs_ai=vs_ai)
        root.title("Échecs - Partie")
        root.resizable(False,False)
        root.mainloop()

# -------------------------
# Lancement
# -------------------------
if __name__ == "__main__":
    root=tk.Tk()
    MenuPrincipal(root)
    root.resizable(False,False)
    root.mainloop()
