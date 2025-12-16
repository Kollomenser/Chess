import random
import time
import chess
import chess.engine
from typing import List, Tuple, Optional

class KempBrdyEngine:
    """
    Bullet AI Chess Engine based on Kemp Brdy's playing style
    Analyzed from 4,654 games with specific tactical patterns
    """
    
    def __init__(self, difficulty_level: int = 5):
        """
        Initialize the Kemp Brdy-style engine
        
        Args:
            difficulty_level: 1-10 scale for engine strength
        """
        self.difficulty = difficulty_level
        self.time_limit = 0.1  # Bullet chess - very fast decisions
        self.max_thinking_time = 0.5  # Maximum time for complex positions
        
        # Kemp Brdy's opening repertoire (from analysis)
        self.opening_repertoire = {
            'white': [
                # Most common opening: e3 e5 Bc4 Nc6 Qf3 Nf6
                ['e3', 'e5', 'Bc4', 'Nc6', 'Qf3', 'Nf6'],
                # Second most common: e4 e6 Nf3 d5 exd5 Qxd5
                ['e4', 'e6', 'Nf3', 'd5', 'exd5', 'Qxd5'],
                # Flexible setup: e3 e5 Bc4 d5 Bb3 Nf6
                ['e3', 'e5', 'Bc4', 'd5', 'Bb3', 'Nf6'],
                # Hypermodern: e3 g6 Bc4 Bg7 Qf3 e6
                ['e3', 'g6', 'Bc4', 'Bg7', 'Qf3', 'e6'],
                # Center control: e3 d5 c4 e6 cxd5 exd5
                ['e3', 'd5', 'c4', 'e6', 'cxd5', 'exd5']
            ],
            'black': [
                # French Defense responses
                ['e4', 'e6', 'Nf3', 'd5', 'exd5', 'Qxd5'],
                # Sicilian-style responses
                ['e4', 'c5', 'Nf3', 'd6', 'd4', 'cxd4'],
                # Caro-Kann style
                ['e4', 'c6', 'd4', 'd5', 'exd5', 'cxd5']
            ]
        }
        
        # Tactical preferences based on analysis
        self.tactical_weights = {
            'check': 0.8,           # High priority on giving checks
            'checkmate': 1.0,       # Maximum priority on mate
            'capture_queen': 0.9,   # High priority on queen trades
            'capture_bishop': 0.7,  # Good priority on bishop captures
            'capture_knight': 0.7,  # Good priority on knight captures
            'castling': 0.6,        # Moderate priority on castling
            'development': 0.8,     # High priority on piece development
            'center_control': 0.7,  # Good priority on center squares
            'aggression': 0.9       # Very aggressive play style
        }
    
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """
        Get the best move based on Kemp Brdy's style
        
        Args:
            board: Current chess board position
            
        Returns:
            Best chess move in Kemp Brdy's style
        """
        start_time = time.time()
        
        # Try opening book first
        opening_move = self._get_opening_move(board)
        if opening_move:
            return opening_move
        
        # Generate all legal moves
        legal_moves = list(board.legal_moves)
        
        if not legal_moves:
            return None
        
        # Score moves based on Kemp Brdy's preferences
        scored_moves = []
        for move in legal_moves:
            score = self._evaluate_move(board, move)
            scored_moves.append((score, move))
        
        # Sort by score (descending)
        scored_moves.sort(reverse=True, key=lambda x: x[0])
        
        # Add randomness based on difficulty
        if self.difficulty < 7:
            # Lower difficulty = more randomness
            scored_moves = self._add_randomness(scored_moves)
        
        # Select best move within time limit
        best_score, best_move = scored_moves[0]
        
        # Ensure we don't exceed time limits for bullet
        if time.time() - start_time > self.time_limit:
            # Fallback to any legal move if time exceeded
            return random.choice(legal_moves)
        
        return best_move
    
    def _get_opening_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get moves from Kemp Brdy's opening repertoire"""
        move_count = len(board.move_stack)
        
        if move_count > 6:  # Only use for first 6 moves
            return None
        
        # Determine if we're white or black
        is_white = board.turn == chess.WHITE
        
        # Select a random opening from repertoire
        if is_white:
            openings = self.opening_repertoire['white']
        else:
            openings = self.opening_repertoire['black']
        
        chosen_opening = random.choice(openings)
        
        if move_count < len(chosen_opening):
            try:
                expected_move_san = chosen_opening[move_count]
                return board.parse_san(expected_move_san)
            except ValueError:
                pass  # Move not legal, continue with normal evaluation
        
        return None
    
    def _evaluate_move(self, board: chess.Board, move: chess.Move) -> float:
        """
        Evaluate a move based on Kemp Brdy's playing style
        """
        score = 0.0
        
        # Make the move to analyze
        board.push(move)
        
        try:
            # Check for checkmate (highest priority)
            if board.is_checkmate():
                return 1000.0 + self.tactical_weights['checkmate'] * 100
            
            # Check for giving check
            if board.is_check():
                score += self.tactical_weights['check'] * 50
            
            # Piece capture analysis
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                capture_value = self._get_piece_value(captured_piece)
                capture_type = self._get_piece_type(captured_piece)
                
                if capture_type in self.tactical_weights:
                    score += self.tactical_weights[capture_type] * capture_value * 10
                else:
                    score += capture_value * 5
            
            # Development bonus
            if self._is_development_move(board, move):
                score += self.tactical_weights['development'] * 15
            
            # Center control bonus
            if self._controls_center(move.to_square):
                score += self.tactical_weights['center_control'] * 10
            
            # Castling bonus
            if move.from_square in [chess.E1, chess.E8] and move.to_square in [chess.G1, chess.C1, chess.G8, chess.C8]:
                score += self.tactical_weights['castling'] * 20
            
            # Aggression bonus - moves towards opponent's king
            if self._is_aggressive_move(board, move):
                score += self.tactical_weights['aggression'] * 12
            
            # Queen activity bonus (Kemp Brdy likes active queens)
            if board.piece_at(move.from_square) and board.piece_at(move.from_square).piece_type == chess.QUEEN:
                score += 8  # Bonus for queen moves
                if self._controls_center(move.to_square):
                    score += 5  # Extra bonus for queen in center
            
            # Material evaluation
            score += self._evaluate_material(board)
            
            # Position evaluation
            score += self._evaluate_position(board)
            
        finally:
            board.pop()
        
        # Add some randomness for bullet chaos
        score += random.uniform(-5, 5) * (11 - self.difficulty)
        
        return score
    
    def _get_piece_value(self, piece: chess.Piece) -> int:
        """Get numerical value of a piece"""
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        return values.get(piece.piece_type, 0)
    
    def _get_piece_type(self, piece: chess.Piece) -> str:
        """Get piece type name for tactical weights"""
        type_names = {
            chess.PAWN: 'capture_pawn',
            chess.KNIGHT: 'capture_knight',
            chess.BISHOP: 'capture_bishop',
            chess.ROOK: 'capture_rook',
            chess.QUEEN: 'capture_queen',
            chess.KING: 'capture_king'
        }
        return type_names.get(piece.piece_type, 'capture_pawn')
    
    def _is_development_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move develops a piece"""
        piece = board.piece_at(move.from_square)
        if not piece:
            return False
        
        # Knight/Bishop moves from back rank are development
        if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            if piece.color == chess.WHITE and move.from_square in [chess.B1, chess.C1, chess.F1, chess.G1]:
                return True
            elif piece.color == chess.BLACK and move.from_square in [chess.B8, chess.C8, chess.F8, chess.G8]:
                return True
        
        return False
    
    def _controls_center(self, square: chess.Square) -> bool:
        """Check if square controls center"""
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        return square in center_squares
    
    def _is_aggressive_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move is aggressive (towards opponent's territory)"""
        if board.turn == chess.WHITE:  # We just moved white
            # White moves up the board (higher rank numbers)
            return chess.square_rank(move.to_square) > chess.square_rank(move.from_square)
        else:  # We just moved black
            # Black moves down the board (lower rank numbers)
            return chess.square_rank(move.to_square) < chess.square_rank(move.from_square)
    
    def _evaluate_material(self, board: chess.Board) -> float:
        """Simple material evaluation"""
        score = 0
        for square, piece in board.piece_map().items():
            value = self._get_piece_value(piece)
            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
        return score
    
    def _evaluate_position(self, board: chess.Board) -> float:
        """Basic positional evaluation"""
        score = 0
        
        # King safety (simplified)
        if not board.is_check():
            score += 10
        
        # Mobility bonus
        legal_moves = len(list(board.legal_moves))
        score += legal_moves * 0.5
        
        return score
    
    def _add_randomness(self, scored_moves: List[Tuple[float, chess.Move]]) -> List[Tuple[float, chess.Move]]:
        """Add randomness based on difficulty level"""
        if self.difficulty >= 9:
            return scored_moves  # No randomness at high levels
        
        # Randomness factor (lower difficulty = more randomness)
        random_factor = (10 - self.difficulty) / 10
        
        # Shuffle top moves
        top_moves = scored_moves[:min(5, len(scored_moves))]
        random.shuffle(top_moves)
        
        # Combine with remaining moves
        if len(scored_moves) > 5:
            result = top_moves + scored_moves[5:]
        else:
            result = top_moves
        
        return result
    
    def get_engine_info(self) -> dict:
        """Get information about the engine"""
        return {
            'name': 'Kemp Brdy Bullet Engine',
            'author': 'Based on 4,654 games analysis',
            'style': 'Aggressive bullet chess',
            'win_rate': '49.5%',
            'primary_time_control': '60+0',
            'key_characteristics': [
                'Early queen development',
                'High tactical complexity',
                'Aggressive piece play',
                'Fast decision making',
                'Strong checkmate patterns'
            ],
            'difficulty_level': self.difficulty,
            'games_analyzed': 4654
        }


# Usage example and testing
if __name__ == "__main__":
    # Test the engine
    engine = KempBrdyEngine(difficulty_level=7)
    
    board = chess.Board()
    
    print("Kemp Brdy Bullet Engine Test")
    print("=" * 40)
    print(engine.get_engine_info())
    print()
    
    # Play a few moves
    for i in range(10):
        move = engine.get_move(board)
        if move:
            print(f"Move {i+1}: {board.san(move)}")
            board.push(move)
        else:
            break
    
    print(f"\nFinal position FEN: {board.fen()}")