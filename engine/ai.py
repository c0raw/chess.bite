import random, shutil, subprocess, copy
from .movegen import legal_moves, make_move, in_check
from .board import idx_to_alg, alg_to_idx

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

def ai_easy(game_state):
    moves = legal_moves(game_state['board'], False, game_state['can_castle'], game_state['en_passant'])
    if not moves: return None
    return random.choice(moves)

def ai_naive(game_state):
    moves = legal_moves(game_state['board'], False, game_state['can_castle'], game_state['en_passant'])
    if not moves: return None
    captures = []
    for m in moves:
        (r1,c1),(r2,c2)=m
        if game_state['board'][r2][c2] != '.':
            captures.append(m)
        else:
            if game_state['board'][r1][c1].upper()=='P' and game_state['en_passant'] and (r2,c2)==game_state['en_passant']:
                captures.append(m)
    if captures:
        return random.choice(captures)
    return random.choice(moves)

def ai_normal(game_state):
    moves = legal_moves(game_state['board'], False, game_state['can_castle'], game_state['en_passant'])
    if not moves: return None
    best = None
    best_score = -10**9
    for m in moves:
        nb, ncst, nep = make_move(game_state['board'], m, game_state['can_castle'], game_state['en_passant'])
        sc = -evaluate_board(nb)
        if sc > best_score or (sc==best_score and random.random() < 0.1):
            best_score = sc; best = m
    return best

def minimax_ab(board, depth, alpha, beta, white, can_castle, en_passant):
    if depth==0:
        return evaluate_board(board), None
    moves = legal_moves(board, white, can_castle, en_passant)
    if not moves:
        if in_check(board, white):
            return (-1000000 if white else 1000000), None
        else:
            return 0, None
    best_move = None
    if white:
        value = -10**9
        for m in moves:
            nb, ncst, nep = make_move(board, m, can_castle, en_passant)
            sc, _ = minimax_ab(nb, depth-1, alpha, beta, not white, ncst, nep)
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
            sc, _ = minimax_ab(nb, depth-1, alpha, beta, not white, ncst, nep)
            if sc < value:
                value = sc; best_move = m
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move

def ai_complex(game_state, depth=3):
    board = game_state['board']
    can_castle = game_state['can_castle']
    en_passant = game_state['en_passant']
    score, move = minimax_ab(board, depth, -10**9, 10**9, False, can_castle, en_passant)
    return move

def stockfish_bestmove(game_state, think_time=0.1):
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
        rights = ''
        if can_castle.get('K', False): rights += 'K'
        if can_castle.get('Q', False): rights += 'Q'
        if can_castle.get('k', False): rights += 'k'
        if can_castle.get('q', False): rights += 'q'
        if rights=='' : rights = '-'
        if en_passant:
            ep = idx_to_alg(*en_passant)
        else:
            ep = '-'
        fen = f"{fen_board} {fen_side} {rights} {ep} 0 1"
        return fen
    sf_path = shutil.which('stockfish')
    if not sf_path:
        return None
    try:
        fen = board_to_fen(game_state['board'], True, game_state['can_castle'], game_state['en_passant'])
        proc = subprocess.Popen([sf_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        proc.stdin.write(f"position fen {fen}\n")
        proc.stdin.write(f"go movetime {int(think_time*1000)}\n")
        proc.stdin.flush()
        bestmove = None
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
        from_sq = bestmove[0:2]; to_sq = bestmove[2:4]
        return (alg_to_idx(from_sq), alg_to_idx(to_sq))
    except Exception:
        return None

def ai_impossible(game_state):
    # longer think time for best effort via Stockfish; fallback to deep minimax
    m = stockfish_bestmove(game_state, think_time=150)
    if m:
        return m
    return ai_complex(game_state, depth=4)

AI_BY_NAME = {
    'Facile': ai_easy,
    'Naïve': ai_naive,
    'Normal': ai_normal,
    'Complexe': lambda gs: ai_complex(gs, depth=3),
    'Impossible': ai_impossible
}