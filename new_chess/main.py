import tkinter as tk
from tkinter import simpledialog, messagebox
from ui_game import ChessGUI
from engine.ai import AI_BY_NAME

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
        minutes = simpledialog.askinteger("Temps imparti", "Minutes par joueur (0 = illimité)", minvalue=0, initialvalue=10)
        total_time = minutes * 60 if minutes and minutes > 0 else None
        from ui_game import ChessGUI
        ChessGUI(self.root, vs_ai=False, total_time=total_time)

    def start_pvai(self):
        level = simpledialog.askstring("Difficulté IA", "Choisis la difficulté : Facile, Naïve, Normal, Complexe, Impossible", initialvalue="Facile")
        if not level:
            return
        if level not in AI_BY_NAME:
            messagebox.showerror("Erreur", "Difficulté inconnue.")
            return
        self.frame.destroy()
        ChessGUI(self.root, vs_ai=True, ai_level=level)

if __name__ == "__main__":
    root = tk.Tk()
    MainMenu(root)
    root.resizable(False, False)
    root.mainloop()