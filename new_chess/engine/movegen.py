from .board import *
import copy

def generate_pseudo_moves(board, r, c, can_castle, en_passant):
    p = board[r][c]
    if p=='.': return []
    moves=[]
    white = p.isupper()
    up = -1 if white else 1
    P = p.upper()
    if P=='P':
        if on_board(r+up, c) and board[r+up][c]=='.':
            moves.append((r+up,c))
            start = 6 if white else 1
            if r==start and board[r+2*up][c]=='.':
                moves.append((r+2*up,c))
        for dc in (-1,1):
            nr, nc = r+up, c+dc
            if on_board(nr,nc) and board[nr][nc]!='.' and not same_color(board[nr][nc], p):
                moves.append((nr,nc))
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
        # castle squares (we check emptiness only here; legality wrt check is handled later)
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

def make_move(board, move, can_castle, en_passant, promote_to=None):
    b = copy.deepcopy(board)
    (r1,c1),(r2,c2)=move
    p = b[r1][c1]
    b[r1][c1]='.'
    # en-passant capture removal
    if p.upper()=='P' and en_passant and (r2,c2)==en_passant and c2!=c1 and b[r2][c2]=='.':
        if p.isupper():
            b[r2+1][c2]='.'
        else:
            b[r2-1][c2]='.'
    # castling rook movement
    if p.upper()=='K' and abs(c2-c1)==2:
        if c2>c1:
            row = r2
            b[row][5] = b[row][7]
            b[row][7] = '.'
        else:
            row = r2
            b[row][3] = b[row][0]
            b[row][0] = '.'
    # promotion
    if p.upper()=='P' and (r2==0 or r2==7):
        if promote_to:
            b[r2][c2] = promote_to
        else:
            b[r2][c2] = 'Q' if p.isupper() else 'q'
    else:
        b[r2][c2]=p
    new_castle = copy.deepcopy(can_castle)
    # update castling rights
    if p=='K':
        new_castle['K']=False; new_castle['Q']=False
    if p=='k':
        new_castle['k']=False; new_castle['q']=False
    if (r1,c1)==(7,0) or (r2,c2)==(7,0):
        new_castle['Q']=False
    if (r1,c1)==(7,7) or (r2,c2)==(7,7):
        new_castle['K']=False
    if (r1,c1)==(0,0) or (r2,c2)==(0,0):
        new_castle['q']=False
    if (r1,c1)==(0,7) or (r2,c2)==(0,7):
        new_castle['k']=False
    new_ep = None
    if p.upper()=='P' and abs(r2-r1)==2:
        new_ep = ((r1+r2)//2, c1)
    return b, new_castle, new_ep

def find_king(board, white):
    k = 'K' if white else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c]==k: return (r,c)
    return None

def in_check(board, white):
    king = find_king(board, white)
    if not king:
        return True
    kr,kc = king
    # pawns
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
    # sliders
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

def legal_moves(board, white, can_castle, en_passant):
    moves=[]
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p=='.': continue
            if p.isupper()!=white: continue
            for (nr,nc) in generate_pseudo_moves(board,r,c,can_castle,en_passant):
                candidate = ((r,c),(nr,nc))
                nb, ncst, nep = make_move(board, candidate, can_castle, en_passant)
                if not in_check(nb, white):
                    moves.append(candidate)
    return moves

def is_checkmate(board, white, can_castle, en_passant):
    return in_check(board, white) and len(legal_moves(board, white, can_castle, en_passant))==0

def is_stalemate(board, white, can_castle, en_passant):
    return (not in_check(board, white)) and len(legal_moves(board, white, can_castle, en_passant))==0