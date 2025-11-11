import time, copy
from .board import START_BOARD
from .movegen import make_move

class GameState:
    def __init__(self, vs_ai=False, ai_level='Facile', total_time=None):
        self.board = copy.deepcopy(START_BOARD)
        self.white_to_move = True
        self.can_castle = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant = None
        self.move_history = []
        self.start_time = time.time()
        self.move_start_time = None
        self.vs_ai = vs_ai
        self.ai_level = ai_level

        self.total_time = total_time
        if total_time and total_time > 0:
            self.remaining_time = {'W': float(total_time), 'B': float(total_time)}
        else:
            self.total_time = None
            self.remaining_time = {'W': 0.0, 'B': 0.0}

    def start_move_timer(self):
        self.move_start_time = time.time()

    def stop_move_timer(self):
        if self.move_start_time is None:
            return 0.0
        dt = time.time() - self.move_start_time
        player = 'W' if self.white_to_move else 'B'

        if not self.total_time:
            self.remaining_time[player] += dt
        else:
            self.remaining_time[player] -= dt
            if self.remaining_time[player] < 0:
                self.remaining_time[player] = 0

        self.move_start_time = None
        return dt

    def apply_move(self, move, promote_to=None):
        b, new_castle, new_ep = make_move(self.board, move, self.can_castle, self.en_passant, promote_to)
        (r1,c1),(r2,c2) = move
        self.board = b
        self.can_castle = new_castle
        self.en_passant = new_ep
        self.white_to_move = not self.white_to_move

    def to_serializable(self):
        return {
            'board': ["".join(row) for row in self.board],
            'white_to_move': self.white_to_move,
            'can_castle': self.can_castle,
            'en_passant': None if not self.en_passant else list(self.en_passant),
            'move_history': self.move_history,
            'total_time': self.total_time,
            'remaining_time': self.remaining_time
        }

    def load_serializable(self, data):
        self.board = [list(row) for row in data['board']]
        self.white_to_move = data['white_to_move']
        self.can_castle = data['can_castle']
        self.en_passant = None if not data['en_passant'] else tuple(data['en_passant'])
        self.move_history = data.get('move_history', [])
        self.total_time = data.get('total_time')
        self.remaining_time = data.get('remaining_time', {'W':0.0,'B':0.0})
        self.move_start_time = None

    def out_of_time(self):
        """Retourne 'W' ou 'B' si un joueur a épuisé son temps, sinon None"""
        if not self.total_time:
            return None
        if self.remaining_time['W'] <= 0:
            return 'W'
        if self.remaining_time['B'] <= 0:
            return 'B'
        return None