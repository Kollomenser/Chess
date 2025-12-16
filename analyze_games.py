import re
from collections import Counter
import chess
import chess.pgn

# Load the PGN data directly
with open('lichess_KempBrdy_2025-12-15.pgn', 'r') as f:
    pgn_content = f.read()

# Split into individual games - PGN games are separated by blank lines
games = []
current_game = []
for line in pgn_content.split('\n'):
    if line.strip() == '':
        if current_game:
            games.append('\n'.join(current_game))
            current_game = []
    else:
        current_game.append(line)

if current_game:
    games.append('\n'.join(current_game))

print(f"Found {len(games)} games")
print("=" * 50)

# Analyze each game
opening_moves = []
tactical_patterns = []
time_controls = []
results = []
white_wins = 0
black_wins = 0
draws = 0

for i, game_text in enumerate(games):
    if not game_text.strip():
        continue
        
    # Parse PGN headers
    headers = {}
    lines = game_text.split('\n')
    move_line = ""
    
    for line in lines:
        if line.startswith('[') and line.endswith(']'):
            # Extract header
            match = re.match(r'\[([^ ]+) "([^"]*)"\]', line)
            if match:
                headers[match.group(1)] = match.group(2)
        elif not line.startswith('['):
            move_line = line
            break
    
    # Extract game info
    white = headers.get('White', 'Unknown')
    black = headers.get('Black', 'Unknown')
    result = headers.get('Result', '*')
    time_control = headers.get('TimeControl', 'Unknown')
    eco = headers.get('ECO', 'Unknown')
    opening = headers.get('Opening', 'Unknown')
    
    # Count results when Kemp Brdy is playing
    if white == "KempBrdy":
        if result == "1-0":
            white_wins += 1
        elif result == "0-1":
            black_wins += 1
        elif result == "1/2-1/2":
            draws += 1
    elif black == "KempBrdy":
        if result == "0-1":
            white_wins += 1
        elif result == "1-0":
            black_wins += 1
        elif result == "1/2-1/2":
            draws += 1
    
    time_controls.append(time_control)
    
    # Extract opening moves (first 5 moves)
    if move_line:
        moves = move_line.split()
        first_5_moves = []
        for move in moves[:10]:  # First 5 moves for each side
            if '.' not in move and move not in ['1-0', '0-1', '1/2-1/2']:
                first_5_moves.append(move)
        
        if first_5_moves:
            opening_moves.append(' '.join(first_5_moves))
        
        # Check for tactical patterns
        move_text = ' '.join(moves)
        
        # Common tactical patterns in bullet chess
        if 'Nx' in move_text and '+' not in move_text:
            tactical_patterns.append('capture_knight')
        if 'Bx' in move_text and '+' not in move_text:
            tactical_patterns.append('capture_bishop')
        if 'Qx' in move_text and '+' not in move_text:
            tactical_patterns.append('capture_queen')
        if '+#' in move_text or '#' in move_text:
            tactical_patterns.append('checkmate')
        elif '+' in move_text:
            tactical_patterns.append('check')
        if 'O-O' in move_text or 'O-O-O' in move_text:
            tactical_patterns.append('castling')

print(f"Kemp Brdy Statistics:")
print(f"Wins: {white_wins}, Losses: {black_wins}, Draws: {draws}")
total_games = white_wins + black_wins + draws
if total_games > 0:
    print(f"Win Rate: {white_wins/total_games*100:.1f}%")
print()

# Most common openings
print("Most Common Opening Sequences:")
opening_counter = Counter(opening_moves)
for opening, count in opening_counter.most_common(5):
    print(f"  {opening}: {count} times")
print()

# Tactical patterns
print("Tactical Patterns:")
pattern_counter = Counter(tactical_patterns)
for pattern, count in pattern_counter.most_common():
    print(f"  {pattern}: {count} times")
print()

# Time controls
print("Time Controls:")
tc_counter = Counter(time_controls)
for tc, count in tc_counter.most_common():
    print(f"  {tc}: {count} games")