import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import time, json

from engine.timecontrol import GameState
from engine.movegen import legal_moves, is_checkmate, is_stalemate, in_check
from engine.ai import AI_BY_NAME
from engine.board import UNICODE, FILES, BOARD_SIZE, SQUARE, WHITE_COLOR, BLACK_COLOR, HIGHLIGHT_COLOR, MOVE_MARK_COLOR, SELECT_BORDER
# ----- AJOUTS IMPORTANTS-----
from engine.pile_liste import Liste_chaine, Pile_LIFO
# ----------------------------

class ChessGUI:
    def __init__(self, root, vs_ai=False, ai_level='Facile', total_time=None):
        self.root = root
        self.root.title("Échecs - Projet Terminale NSI")
        self.vs_ai = vs_ai
        self.ai_level = ai_level
        self.game_over = False
        self.state = GameState(vs_ai=vs_ai, ai_level=ai_level, total_time=total_time)
        # ----- AJOUTS IMPORTANTS-----
        self.history = Pile_LIFO()
        self.positions = Liste_chaine()
        self.positions.append([row[:] for row in self.state.board])
        # ----------------------------

        self.canvas = tk.Canvas(root, width=BOARD_SIZE*SQUARE, height=BOARD_SIZE*SQUARE)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.info_frame = tk.Frame(root)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=10, pady=10)
        self.status_var = tk.StringVar()
        self.lbl_status = tk.Label(self.info_frame, textvariable=self.status_var, font=("Helvetica",12))
        self.lbl_status.pack(pady=6)
        self.lbl_white_total = tk.Label(self.info_frame, text="Blancs total: 0.00s", font=("Helvetica",10))
        self.lbl_white_total.pack(pady=2)
        self.lbl_black_total = tk.Label(self.info_frame, text="Noirs total: 0.00s", font=("Helvetica",10))
        self.lbl_black_total.pack(pady=2)
        self.lbl_last_move = tk.Label(self.info_frame, text="Dernier coup: -", font=("Helvetica",10))
        self.lbl_last_move.pack(pady=8)
        btn_frame = tk.Frame(self.info_frame)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Nouveau", command=self.new_game).grid(row=0,column=0,padx=4)
        tk.Button(btn_frame, text="Sauvegarder", command=self.save_game).grid(row=0,column=1,padx=4)
        tk.Button(btn_frame, text="Charger", command=self.load_game).grid(row=0,column=2,padx=4)
        tk.Button(btn_frame, text="Annuler dernier", command=self.undo_last).grid(row=1,column=0,columnspan=3,pady=6)
        self.move_log = tk.Text(self.info_frame, width=30, height=20)
        self.move_log.pack(pady=8)
        self.canvas.bind("<Button-1>", self.on_click)
        self.selected = None
        self.legal_targets = []
        self.state.start_time = time.time()
        self.state.move_start_time = time.time()
        self.draw_board()
        self.update_ui()
        self.root.after(200, self._tick)
        # ----- AJOUTS IMPORTANTS-----
        self.history = Pile_LIFO()
        self.positions = Liste_chaine()
        # ----------------------------

    def draw_board(self):
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                x1 = c*SQUARE; y1 = r*SQUARE
                color = WHITE_COLOR if (r+c)%2==0 else BLACK_COLOR
                self.canvas.create_rectangle(x1,y1,x1+SQUARE,y1+SQUARE, fill=color, outline=color)
        if self.selected:
            r,c = self.selected
            x1 = c*SQUARE; y1 = r*SQUARE
            self.canvas.create_rectangle(x1,y1,x1+SQUARE,y1+SQUARE, outline=SELECT_BORDER, width=3)
            for (rr,cc) in self.legal_targets:
                cx = cc*SQUARE + SQUARE//2; cy = rr*SQUARE + SQUARE//2
                if self.state.board[rr][cc] != '.':
                    self.canvas.create_oval(cx-18,cy-18,cx+18,cy+18, outline=MOVE_MARK_COLOR, width=3)
                else:
                    self.canvas.create_oval(cx-8,cy-8,cx+8,cy+8, fill=MOVE_MARK_COLOR, outline='')
        for r in range(8):
            for c in range(8):
                p = self.state.board[r][c]
                if p!='.':
                    x = c*SQUARE + SQUARE//2; y = r*SQUARE + SQUARE//2
                    self.canvas.create_text(x,y, text=UNICODE[p], font=("DejaVu Sans", int(SQUARE*0.5)))
        for c in range(8):
            self.canvas.create_text(c*SQUARE+10, BOARD_SIZE*SQUARE-8, text=FILES[c], anchor='w', font=("Helvetica",8))
        for r in range(8):
            self.canvas.create_text(4, r*SQUARE+8, text=str(8-r), anchor='w', font=("Helvetica",8))

    def _tick(self):
        self.update_ui()
        if self.state.vs_ai and not self.state.white_to_move:
            self.root.after(50, self._ai_move)
        self.root.after(200, self._tick)

    def update_ui(self):
        if self.game_over:
            return

        side = "Blancs" if self.state.white_to_move else "Noirs"
        status = f"À jouer : {side}"
        if in_check(self.state.board, self.state.white_to_move):
            status += " — ÉCHEC !"
        self.status_var.set(status)

        now = time.time()
        move_elapsed = now - (self.state.move_start_time or now)

        def fmt(seconds):
            seconds = max(0, int(seconds))
            m, s = divmod(seconds, 60)
            return f"{m:02d}:{s:02d}"

        if self.state.total_time:
            w_remain = self.state.remaining_time['W']
            b_remain = self.state.remaining_time['B']

            if self.state.white_to_move:
                w_display = fmt(w_remain - move_elapsed)
                b_display = fmt(b_remain)
            else:
                b_display = fmt(b_remain - move_elapsed)
                w_display = fmt(w_remain)

            self.lbl_white_total.config(text=f"⏱ Blancs restant : {w_display}")
            self.lbl_black_total.config(text=f"⏱ Noirs restant : {b_display}")

            if self.state.white_to_move and (w_remain - move_elapsed) <= 0:
                from tkinter import messagebox
                self.game_over = True
                messagebox.showinfo("Temps écoulé", "Temps écoulé ! Les Noirs gagnent.")
                self.root.destroy()
                return
            elif (not self.state.white_to_move) and (b_remain - move_elapsed) <= 0:
                from tkinter import messagebox
                self.game_over = True
                messagebox.showinfo("Temps écoulé", "Temps écoulé ! Les Blancs gagnent.")
                self.root.destroy()
                return

        else:
            white_total = self.state.remaining_time['W'] + (move_elapsed if self.state.white_to_move else 0)
            black_total = self.state.remaining_time['B'] + (move_elapsed if not self.state.white_to_move else 0)
            self.lbl_white_total.config(text=f"⏱ Blancs temps : {fmt(white_total)}")
            self.lbl_black_total.config(text=f"⏱ Noirs temps : {fmt(black_total)}")

        if self.state.move_history:
            last = self.state.move_history[-1]
            mv_str = f"{last.get('player','?')}: {last.get('algebraic','?')} ({last.get('time',0.0):.2f}s)"
            self.lbl_last_move.config(text="Dernier coup: " + mv_str)
        else:
            self.lbl_last_move.config(text="Dernier coup: -")

        self.move_log.delete(1.0, tk.END)
        for i, move in enumerate(self.state.move_history, start=1):
            self.move_log.insert(tk.END, f"{i}. {move.get('algebraic','')}  {move.get('time',0.0):.2f}s\n")

    def on_click(self, event):
        c = event.x // SQUARE; r = event.y // SQUARE
        if not (0 <= r < 8 and 0 <= c < 8):
            return
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
        if self.selected == (r,c):
            self.selected = None
            self.legal_targets = []
            self.draw_board()
            return
        if (r,c) in self.legal_targets:
            move = (self.selected, (r,c))
            moving_piece = self.state.board[self.selected[0]][self.selected[1]]
            promote_choice = None
            if moving_piece.upper()=='P' and ((moving_piece.isupper() and r==0) or (moving_piece.islower() and r==7)):
                promote_choice = self.ask_promotion(moving_piece.isupper())
            now = time.time()
            dt = now - (self.state.move_start_time or now)
            alg = f"{self.idx_to_alg(self.selected[0],self.selected[1])}{self.idx_to_alg(r,c)}"
            self.state.apply_move(move, promote_to=promote_choice)
            # ----- AJOUTS IMPORTANTS-----
            self.history.push(move)
            self.positions.append([row[:] for row in self.state.board])
            # ----------------------------
            player = 'W' if not self.state.white_to_move else 'B'
            if self.state.total_time:
                self.state.remaining_time[player] -= dt
                if self.state.remaining_time[player] < 0:
                    self.state.remaining_time[player] = 0
            else:
                self.state.remaining_time[player] += dt
            hist = {'move': ((self.selected),(r,c)), 'algebraic': alg, 'time': dt, 'player': player}
            self.state.move_history.append(hist)
            self.selected = None
            self.legal_targets=[]
            self.state.move_start_time = time.time()
            self.draw_board()
            self.update_ui()
            if is_checkmate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
                winner = "Blancs" if not self.state.white_to_move else "Noirs"
                self.game_over = True
                messagebox.showinfo("Fin de partie", f"Échec et mat ! {winner} gagnent.")
            elif is_stalemate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
                self.game_over = True
                messagebox.showinfo("Fin de partie", "Pat ! (égalité)")
            return
        if p!='.' and p.isupper() == self.state.white_to_move:
            self.selected=(r,c)
            self.legal_targets = [m[1] for m in legal_moves(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant) if m[0]==(r,c)]
            self.draw_board()
            return
        self.selected=None; self.legal_targets=[]; self.draw_board()

    def ask_promotion(self, white):
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
        # ----- AJOUTS IMPORTANTS-----
        if self.history.is_empty() or len(self.positions) <= 1:
            messagebox.showinfo("Annuler", "Aucun coup à annuler.")
            return

        last_move = self.history.pop()
        self.positions.pop()
        prev_node = self.positions.tail
        if not prev_node:
            initial = GameState(vs_ai=self.state.vs_ai, ai_level=self.state.ai_level)
            self.state.board = [row[:] for row in initial.board]
        else:
            self.state.board = [row[:] for row in prev_node.data]
        if self.state.move_history:
            self.state.move_history.pop()

        self.state.white_to_move = not self.state.white_to_move
        self.selected = None
        self.legal_targets = []
        self.draw_board()
        self.update_ui()
        # ----------------------------

    def _ai_move(self):
        if getattr(self, "game_over", False):
            self.ai_pending = False
            return

        gs = {'board': self.state.board, 'can_castle': self.state.can_castle, 'en_passant': self.state.en_passant}
        ai_func = AI_BY_NAME.get(self.ai_level, list(AI_BY_NAME.values())[0])
        move = ai_func(gs)

        self.ai_pending = False

        if not move:
            if is_checkmate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
                self.game_over = True
                messagebox.showinfo("Fin de partie", "Échec et mat ! Les Blancs gagnent.")
                return
            elif is_stalemate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
                self.game_over = True
                messagebox.showinfo("Fin de partie", "Pat ! Égalité.")
                return
            else:
                return

        now = time.time()
        dt = now - (self.state.move_start_time or now)
        r1c1, r2c2 = move
        piece = self.state.board[r1c1[0]][r1c1[1]]
        promote = None
        if piece.upper()=='P' and ((piece.isupper() and r2c2[0]==0) or (piece.islower() and r2c2[0]==7)):
            promote = 'q' if piece.islower() else 'Q'

        self.state.apply_move(move, promote_to=promote)

        # ----- AJOUTS IMPORTANTS-----
        self.history.push(move)
        self.positions.append([row[:] for row in self.state.board])
        # ----------------------------

        if self.state.total_time:
            self.state.remaining_time['B'] -= dt
            if self.state.remaining_time['B'] < 0:
                self.state.remaining_time['B'] = 0
        else:
            self.state.remaining_time['B'] += dt

        alg = f"{self.idx_to_alg(r1c1[0],r1c1[1])}{self.idx_to_alg(r2c2[0],r2c2[1])}"
        self.state.move_history.append({'move': move, 'algebraic': alg, 'time': dt, 'player': 'B'})
        self.state.move_start_time = time.time()
        self.draw_board()
        self.update_ui()

        if is_checkmate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
            self.game_over = True
            messagebox.showinfo("Fin de partie", "Échec et mat ! Les Noirs gagnent.")
            return
        if is_stalemate(self.state.board, self.state.white_to_move, self.state.can_castle, self.state.en_passant):
            self.game_over = True
            messagebox.showinfo("Fin de partie", "Pat ! Égalité.")
            return


    def idx_to_alg(self, r, c):
        return f"{FILES[c]}{8-r}"