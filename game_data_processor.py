import os
import csv
import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime
import pickle

class GameDataProcessor:
    """Class for processing and analyzing game data
    
    This class provides utilities for loading, validating, processing, and
    analyzing game data from CSV files. It organizes the data in a way that
    facilitates easy access to winning/losing patterns, player statistics,
    and other game analytics.
    """
    
    def __init__(self, data_dir=None, filename=None):
        """Initialize the game data processor
        
        Args:
            data_dir (str, optional): Directory containing game data files
            filename (str, optional): Name of the CSV file containing game data
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "game_data")
        self.filename = filename or "all_games_data.csv"
        self.csv_path = os.path.join(self.data_dir, self.filename)
        
        # Data structures
        self.games = {}  # All games by game_id
        self.moves_by_player = {1: [], 2: []}  # Moves by player
        self.completed_games = []  # Games with a valid outcome
        self.winning_games = {1: [], 2: []}  # Games won by each player
        self.draws = []  # Games that ended in a draw
        self.incomplete_games = []  # Games without a valid outcome
        
        # Game statistics
        self.stats = {
            'total_games': 0,
            'completed_games': 0,
            'incomplete_games': 0,
            'wins_player1': 0,
            'wins_player2': 0,
            'draws': 0,
            'avg_moves_per_game': 0,
            'validation': {
                'invalid_moves': 0,
                'invalid_boards': 0,
                'duplicate_moves': 0,
                'conflicting_winners': 0
            }
        }
        
        # Load data if file exists
        if os.path.exists(self.csv_path):
            self.load_data()
    
    def load_data(self, validate=True):
        """Load game data from CSV file and JSON files with move tracker support
        
        Args:
            validate (bool): Whether to validate the loaded data
            
        Returns:
            dict: Dictionary of processed game data
        """
        print(f"Loading game data from {self.csv_path}...")
        
        # Reset data structures
        self._reset_data_structures()
        
        try:
            # First try loading JSON files which contain move tracker data
            json_dir = os.path.join(self.data_dir, "game_json")
            if os.path.exists(json_dir):
                print(f"Found JSON directory at {json_dir}")
                json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
                print(f"Found {len(json_files)} JSON game files")
                
                if json_files:
                    # Import move tracker if not already imported
                    if not hasattr(self, 'move_tracker_imported'):
                        try:
                            from move_tracker import GameMoveTracker
                            self.move_tracker_imported = True
                        except ImportError:
                            print("Move tracker module not found, skipping JSON loading")
                            self.move_tracker_imported = False
                    
                    if hasattr(self, 'move_tracker_imported') and self.move_tracker_imported:
                        # Process each JSON file
                        for json_file in json_files:
                            game_id = json_file.split('.')[0]
                            json_path = os.path.join(json_dir, json_file)
                            
                            try:
                                # Load game data from JSON
                                with open(json_path, 'r') as f:
                                    game_data = json.load(f)
                                
                                # Extract moves data - this will contain move tracker info
                                moves_data = game_data.get('moves', {})
                                
                                # Create a move tracker to restore the data
                                move_tracker = GameMoveTracker()
                                restored = move_tracker.restore_from_moves_data(moves_data)
                                
                                if restored:
                                    # Get the final state for winner detection
                                    final_board = move_tracker.current_board
                                    
                                    # Get the winner from JSON data
                                    winner = game_data.get('winner')
                                    
                                    # If winner is not specified in JSON, determine from final board
                                    if winner is None and final_board is not None:
                                        winner = self._determine_winner(final_board)
                                    
                                    # Extract all moves for legacy compatibility
                                    moves = []
                                    all_move_data = moves_data.get('all_moves', [])
                                    
                                    for move_data in all_move_data:
                                        board_state = move_data.get('board_state')
                                        if board_state:
                                            row = move_data.get('row')
                                            col = move_data.get('col')
                                            player = move_data.get('player')
                                            move_number = move_data.get('move_number')
                                            
                                            # Convert board to numpy array
                                            board = np.array(board_state)
                                            
                                            moves.append({
                                                'move_number': move_number,
                                                'player': player,
                                                'position': (row, col),
                                                'board': board,
                                                'winner': winner if move_number == len(all_move_data) else None
                                            })
                                    
                                    # Create game entry
                                    self.games[game_id] = {
                                        'game_id': game_id,
                                        'moves': moves,
                                        'winner': winner,
                                        'move_count': len(moves),
                                        'timestamp': game_data.get('timestamp'),
                                        'move_tracker': move_tracker  # Store the move tracker for advanced operations
                                    }
                                    
                                    # Categorize the game
                                    self._categorize_game(game_id, self.games[game_id])
                                    
                                    # Store moves by player
                                    self._store_player_moves(game_id, moves)
                            except Exception as e:
                                print(f"Error processing JSON game {game_id}: {e}")
                                continue
            
            # Check if we need to also load from CSV
            if len(self.games) == 0 or not os.path.exists(json_dir):
                print("No games loaded from JSON, trying CSV...")
                # Fall back to CSV loading using pandas
                # Using pandas for more robust CSV handling
                df = pd.read_csv(self.csv_path)
                
                # Check for required columns
                required_columns = ['game_id', 'move_number', 'player', 'row', 'col', 'board_state']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    print(f"CSV file missing required columns: {missing_columns}")
                    return self.games
                
                # Group data by game_id
                game_groups = df.groupby('game_id')
                
                # Process each game
                for game_id, game_df in game_groups:
                    try:
                        # Sort moves by move_number
                        game_df = game_df.sort_values('move_number')
                        
                        # Check for valid number of moves
                        if len(game_df) < 1 or len(game_df) > 9:
                            print(f"Warning: Game {game_id} has {len(game_df)} moves, expected 1-9")
                        
                        # Process moves
                        moves = []
                        for _, row in game_df.iterrows():
                            try:
                                # Convert data types
                                move_number = int(row['move_number'])
                                player = int(row['player'])
                                row_idx = int(row['row'])
                                col_idx = int(row['col'])
                                
                                # Skip invalid values
                                if player not in [1, 2] or not (0 <= row_idx <= 2) or not (0 <= col_idx <= 2):
                                    print(f"Warning: Game {game_id}, move {move_number} has invalid values")
                                    self.stats['validation']['invalid_moves'] += 1
                                    continue
                                
                                # Parse board state
                                board_state = str(row['board_state'])
                                if len(board_state) != 9 or not all(c in '012' for c in board_state):
                                    print(f"Warning: Game {game_id}, move {move_number} has invalid board state")
                                    self.stats['validation']['invalid_boards'] += 1
                                    continue
                                    
                                # Convert to numpy array
                                board = np.array([int(c) for c in board_state]).reshape(3, 3)
                                
                                # Parse winner (may be empty)
                                winner = None
                                if 'winner' in row and row['winner'] and pd.notna(row['winner']):
                                    try:
                                        winner = int(row['winner'])
                                        if winner not in [0, 1, 2]:
                                            winner = None
                                    except (ValueError, TypeError):
                                        winner = None
                                
                                # Get timestamp if available
                                timestamp = row.get('timestamp', None)
                                if timestamp and pd.isna(timestamp):
                                    timestamp = None
                                
                                # Create move object
                                move = {
                                    'move_number': move_number,
                                    'player': player,
                                    'position': (row_idx, col_idx),
                                    'board': board,
                                    'timestamp': timestamp,
                                    'winner': winner
                                }
                                
                                moves.append(move)
                                
                            except Exception as e:
                                print(f"Error processing move in game {game_id}: {e}")
                                continue
                        
                        # Skip if no valid moves
                        if not moves:
                            print(f"Game {game_id} has no valid moves, skipping")
                            continue
                        
                        # Create game object
                        game = self._process_game_data(game_id, moves)
                        
                        # Store game
                        self.games[game_id] = game
                        
                        # Categorize game
                        self._categorize_game(game_id, game)
                        
                        # Store moves by player
                        self._store_player_moves(game_id, moves)
                        
                    except Exception as e:
                        print(f"Error processing game {game_id}: {e}")
                        continue
        
            # Calculate statistics
            self._calculate_statistics()
            
            # Additional validation if requested
            if validate:
                self._validate_data()
            
            print(f"Loaded {len(self.games)} games successfully")
            return self.games
            
        except Exception as e:
            print(f"Error loading game data: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _reset_data_structures(self):
        """Reset all data structures"""
        self.games = {}
        self.moves_by_player = {1: [], 2: []}
        self.completed_games = []
        self.winning_games = {1: [], 2: []}
        self.draws = []
        self.incomplete_games = []
        
        # Reset statistics
        for key in self.stats:
            if isinstance(self.stats[key], dict):
                for subkey in self.stats[key]:
                    self.stats[key][subkey] = 0
            else:
                self.stats[key] = 0
    
    def _process_game_data(self, game_id, moves):
        """Process game data to determine outcome and create game object
        
        Args:
            game_id (str): ID of the game
            moves (list): List of move objects
            
        Returns:
            dict: Processed game object
        """
        # Sort moves by move number to ensure correct order
        moves = sorted(moves, key=lambda x: x['move_number'])
        
        # Extract final winner if available
        final_winner = None
        board_states = []
        
        for move in moves:
            board_states.append(move['board'])
            
            # If move has winner field, use the latest non-None value
            if move.get('winner') is not None:
                final_winner = move['winner']
        
        # If no winner specified, determine from final board state
        if final_winner is None and board_states:
            final_board = board_states[-1]
            final_winner = self._determine_winner(final_board)
        
        # Create game object
        return {
            'game_id': game_id,
            'moves': moves,
            'board_states': board_states,
            'winner': final_winner,
            'move_count': len(moves),
            'timestamp': moves[0].get('timestamp') if moves else None
        }
    
    def _determine_winner(self, board):
        """Determine winner from board state
        
        Args:
            board (numpy.ndarray): 3x3 board state
            
        Returns:
            int: Winner (1 or 2), 0 for draw, None if game incomplete
        """
        # Check for winner
        for player in [1, 2]:
            # Check rows and columns
            for i in range(3):
                if np.all(board[i, :] == player) or np.all(board[:, i] == player):
                    return player
            
            # Check diagonals
            if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
                return player
        
        # Check for draw (board full)
        if np.all(board != 0):
            return 0
        
        # Game still in progress
        return None
    
    def _categorize_game(self, game_id, game):
        """Categorize game based on outcome
        
        Args:
            game_id (str): ID of the game
            game (dict): Game object
        """
        winner = game['winner']
        
        if winner is None:
            # Game incomplete
            self.incomplete_games.append(game_id)
        elif winner == 0:
            # Game is a draw
            self.draws.append(game_id)
            self.completed_games.append(game_id)
        elif winner in [1, 2]:
            # Game has a winner
            self.winning_games[winner].append(game_id)
            self.completed_games.append(game_id)
    
    def _store_player_moves(self, game_id, moves):
        """Store moves by player for analysis
        
        Args:
            game_id (str): ID of the game
            moves (list): List of move objects
        """
        for move in moves:
            player = move['player']
            if player in [1, 2]:
                self.moves_by_player[player].append({
                    'game_id': game_id,
                    'move': move
                })
    
    def _calculate_statistics(self):
        """Calculate overall statistics from loaded data"""
        self.stats['total_games'] = len(self.games)
        self.stats['completed_games'] = len(self.completed_games)
        self.stats['incomplete_games'] = len(self.incomplete_games)
        self.stats['wins_player1'] = len(self.winning_games[1])
        self.stats['wins_player2'] = len(self.winning_games[2])
        self.stats['draws'] = len(self.draws)
        
        # Calculate average moves per game
        total_moves = sum(game['move_count'] for game in self.games.values())
        if self.stats['total_games'] > 0:
            self.stats['avg_moves_per_game'] = total_moves / self.stats['total_games']
    
    def _validate_data(self):
        """Perform additional validation on loaded data"""
        for game_id, game in self.games.items():
            moves = game['moves']
            
            # Check for duplicate moves (same position multiple times)
            positions = set()
            for move in moves:
                pos = move['position']
                if pos in positions:
                    self.stats['validation']['duplicate_moves'] += 1
                positions.add(pos)
            
            # Check for conflicting winners
            winners = set()
            for move in moves:
                if move.get('winner') is not None:
                    winners.add(move['winner'])
            
            if len(winners) > 1:
                self.stats['validation']['conflicting_winners'] += 1
    
    def get_winning_moves(self, player=None, count=10):
        """Get moves from winning games
        
        Args:
            player (int, optional): Player to filter by (1 or 2)
            count (int, optional): Maximum number of moves to return
            
        Returns:
            list: List of move objects from winning games
        """
        winning_moves = []
        
        # Determine which games to look at
        if player in [1, 2]:
            game_ids = self.winning_games[player]
        else:
            # Both players
            game_ids = self.winning_games[1] + self.winning_games[2]
        
        # Collect winning moves
        for game_id in game_ids:
            game = self.games[game_id]
            winner = game['winner']
            
            # Skip if not matching requested player
            if player is not None and winner != player:
                continue
                
            # Add all moves by the winner
            for move in game['moves']:
                if move['player'] == winner:
                    winning_moves.append({
                        'game_id': game_id,
                        'move': move
                    })
                    
                    # Break if we have enough moves
                    if len(winning_moves) >= count:
                        break
            
            # Break if we have enough moves
            if len(winning_moves) >= count:
                break
        
        return winning_moves
    
    def get_moves_in_context(self, context_board=None, player=None, outcome=None):
        """Get moves made in a specific board context
        
        This allows finding how players responded to specific board states.
        
        Args:
            context_board (numpy.ndarray, optional): Board state to match
            player (int, optional): Player to filter by (1 or 2)
            outcome (int, optional): Filter by outcome (1/2 for win, 0 for draw)
            
        Returns:
            list: List of moves matching the criteria
        """
        matching_moves = []
        
        # If no context board provided, return empty list
        if context_board is None:
            return matching_moves
        
        # Determine which games to consider based on outcome
        game_ids = []
        if outcome in [1, 2]:
            game_ids = self.winning_games[outcome]
        elif outcome == 0:
            game_ids = self.draws
        else:
            game_ids = list(self.games.keys())
        
        # Look for matching board states
        for game_id in game_ids:
            game = self.games[game_id]
            
            # Skip games without the right number of moves
            if len(game['moves']) < 2:
                continue
            
            # Check each move except the last (which has no response)
            for i in range(len(game['moves']) - 1):
                current_move = game['moves'][i]
                next_move = game['moves'][i + 1]
                
                # Skip if player filter doesn't match
                if player is not None and next_move['player'] != player:
                    continue
                
                # Check if board matches the context board
                if np.array_equal(current_move['board'], context_board):
                    matching_moves.append({
                        'game_id': game_id,
                        'context_move': current_move,
                        'response_move': next_move,
                        'game_outcome': game['winner']
                    })
        
        return matching_moves
    
    def get_winning_patterns(self):
        """Get common patterns in winning games
        
        Returns:
            dict: Dictionary of patterns by player
        """
        patterns = {1: {}, 2: {}}
        
        # Process winning games for each player
        for player in [1, 2]:
            move_patterns = defaultdict(int)
            openings = defaultdict(int)
            
            # Only look at games won by this player
            for game_id in self.winning_games[player]:
                game = self.games[game_id]
                
                # Track winning player's moves as patterns
                for move in game['moves']:
                    if move['player'] == player:
                        # Track position frequency
                        pos = move['position']
                        move_patterns[pos] += 1
                        
                        # Track opening moves (first move by player)
                        if move['move_number'] <= 2:  # First move by each player
                            openings[pos] += 1
            
            # Store patterns
            patterns[player]['move_frequency'] = dict(move_patterns)
            patterns[player]['openings'] = dict(openings)
            
            # Calculate position effectiveness (percent of wins with this position)
            total_wins = len(self.winning_games[player])
            if total_wins > 0:
                patterns[player]['position_effectiveness'] = {
                    pos: count / total_wins for pos, count in move_patterns.items()
                }
        
        return patterns
    
    def save_processed_data(self, filename=None):
        """Save processed data for faster loading
        
        Args:
            filename (str, optional): Filename to save to
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Default filename
            if filename is None:
                filename = "processed_game_data.pkl"
            
            filepath = os.path.join(self.data_dir, filename)
            
            # Data to save
            data = {
                'games': self.games,
                'moves_by_player': self.moves_by_player,
                'completed_games': self.completed_games,
                'winning_games': self.winning_games,
                'draws': self.draws,
                'incomplete_games': self.incomplete_games,
                'stats': self.stats,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to pickle file
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"Processed data saved to {filepath}")
            return True
            
        except Exception as e:
            print(f"Error saving processed data: {e}")
            return False
    
    def load_processed_data(self, filename=None):
        """Load previously processed data
        
        Args:
            filename (str, optional): Filename to load from
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            # Default filename
            if filename is None:
                filename = "processed_game_data.pkl"
            
            filepath = os.path.join(self.data_dir, filename)
            
            # Check if file exists
            if not os.path.exists(filepath):
                print(f"Processed data file not found: {filepath}")
                return False
            
            # Load from pickle file
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            # Update instance data
            self.games = data['games']
            self.moves_by_player = data['moves_by_player']
            self.completed_games = data['completed_games']
            self.winning_games = data['winning_games']
            self.draws = data['draws']
            self.incomplete_games = data['incomplete_games']
            self.stats = data['stats']
            
            print(f"Processed data loaded from {filepath}")
            return True
            
        except Exception as e:
            print(f"Error loading processed data: {e}")
            return False
    
    def print_summary(self):
        """Print a summary of the loaded data"""
        print("\n=== Game Data Summary ===")
        print(f"Total games: {self.stats['total_games']}")
        print(f"Completed games: {self.stats['completed_games']}")
        print(f"  - Player 1 wins: {self.stats['wins_player1']}")
        print(f"  - Player 2 wins: {self.stats['wins_player2']}")
        print(f"  - Draws: {self.stats['draws']}")
        print(f"Incomplete games: {self.stats['incomplete_games']}")
        print(f"Average moves per game: {self.stats['avg_moves_per_game']:.2f}")
        print("\nValidation issues:")
        print(f"  - Invalid moves: {self.stats['validation']['invalid_moves']}")
        print(f"  - Invalid boards: {self.stats['validation']['invalid_boards']}")
        print(f"  - Duplicate moves: {self.stats['validation']['duplicate_moves']}")
        print(f"  - Conflicting winners: {self.stats['validation']['conflicting_winners']}")
        print("========================\n")

    def build_optimized_data_structure(self):
        """Build optimized data structures for fast access to game patterns
        with support for move tracker data
        """
        try:
            print("Building optimized data structures...")
            
            # Index board states for quick pattern matching
            self.board_state_index = {}
            
            # Position frequency by outcome
            self.position_by_outcome = {
                'win_1': defaultdict(int),   # Positions that led to player 1 wins
                'win_2': defaultdict(int),   # Positions that led to player 2 wins
                'draw': defaultdict(int),    # Positions that led to draws
                'all': defaultdict(int)      # All positions regardless of outcome
            }
            
            # Opening move frequencies
            self.opening_moves = {
                1: defaultdict(int),  # First player opening moves
                2: defaultdict(int)   # Second player opening moves
            }
            
            # Move sequences that lead to wins
            self.winning_sequences = {
                1: [],  # Winning sequences for player 1
                2: []   # Winning sequences for player 2
            }
            
            # Process all games to build these structures
            for game_id, game in self.games.items():
                winner = game.get('winner')
                
                # Check if game has move tracker
                if 'move_tracker' in game:
                    move_tracker = game['move_tracker']
                    move_list = move_tracker.all_moves
                    
                    # Get list of all moves
                    moves = []
                    current_node = move_list.head
                    move_index = 0
                    
                    while current_node:
                        position = (current_node.row, current_node.col)
                        player = current_node.player
                        board = current_node.board_state
                        
                        moves.append({
                            'position': position,
                            'player': player,
                            'board': board,
                            'move_index': move_index
                        })
                        
                        move_index += 1
                        current_node = current_node.next
                else:
                    # Use legacy move format
                    moves = []
                    for i, move in enumerate(game.get('moves', [])):
                        position = move.get('position')
                        player = move.get('player')
                        board = move.get('board')
                        
                        if position and player is not None and board is not None:
                            moves.append({
                                'position': position,
                                'player': player,
                                'board': board,
                                'move_index': i
                            })
                
                # Skip if no moves
                if not moves:
                    continue
                    
                # Track position frequencies by outcome
                outcome_key = f'win_{winner}' if winner in [1, 2] else 'draw' if winner == 0 else None
                    
                # Process each move in the game
                for i, move in enumerate(moves):
                    position = move.get('position')
                    player = move.get('player')
                    board = move.get('board')
                    
                    if position and player and board is not None:
                        # Global position counts
                        self.position_by_outcome['all'][position] += 1
                        
                        # Position counts by outcome
                        if outcome_key:
                            self.position_by_outcome[outcome_key][position] += 1
                        
                        # Track opening moves (first move by each player)
                        if i < 2:  # First two moves in the game
                            self.opening_moves[player][position] += 1
                        
                        # Index board states for pattern matching
                        board_key = self._board_to_key(board)
                        if board_key not in self.board_state_index:
                            self.board_state_index[board_key] = []
                        
                        self.board_state_index[board_key].append({
                            'game_id': game_id,
                            'move': move,
                            'move_index': i,
                            'outcome': winner
                        })
                
                # Track winning sequences
                if winner in [1, 2]:
                    # Filter moves by winning player
                    winner_moves = [m for m in moves if m.get('player') == winner]
                    if winner_moves:
                        # Record sequence of positions
                        sequence = [m.get('position') for m in winner_moves]
                        self.winning_sequences[winner].append({
                            'game_id': game_id,
                            'sequence': sequence
                        })
            
            # Create frequency-based move recommendations
            self._build_move_recommendations()
            
            print("Optimized data structures built successfully")
            return True
            
        except Exception as e:
            print(f"Error building optimized data structures: {e}")
            return False

    def _board_to_key(self, board):
        """Convert board state to a string key for indexing
        
        Args:
            board (numpy.ndarray): 3x3 board state
            
        Returns:
            str: String key that uniquely identifies the board state
        """
        if hasattr(board, 'flatten'):
            return ''.join(str(int(x)) for x in board.flatten())
        return str(board)

    def _build_move_recommendations(self):
        """Build move recommendation lookup tables based on historical data"""
        # Create recommendations based on board state
        self.move_recommendations = {}
        
        # Process all indexed board states
        for board_key, occurrences in self.board_state_index.items():
            # Group by next move's position
            next_moves = {}
            for item in occurrences:
                game_id = item['game_id']
                move_index = item['move_index']
                outcome = item['outcome']
                
                # Find the next move in this game (if not the last move)
                if game_id in self.games and 'moves' in self.games[game_id]:
                    moves = self.games[game_id]['moves']
                    if move_index + 1 < len(moves):
                        next_move = moves[move_index + 1]
                        next_position = next_move.get('position')
                        if next_position:
                            if next_position not in next_moves:
                                next_moves[next_position] = {'count': 0, 'wins': 0, 'draws': 0, 'losses': 0}
                            
                            next_moves[next_position]['count'] += 1
                            
                            # Track outcome after this move
                            next_player = next_move.get('player')
                            if next_player and outcome in [1, 2]:
                                if outcome == next_player:
                                    next_moves[next_position]['wins'] += 1
                                else:
                                    next_moves[next_position]['losses'] += 1
                            elif outcome == 0:
                                next_moves[next_position]['draws'] += 1
            
            # If we found next moves for this board state, calculate scores and store recommendations
            if next_moves:
                # Calculate success rate for each move (weighted by wins/draws)
                scored_moves = []
                for pos, data in next_moves.items():
                    if data['count'] > 0:
                        # Calculate score: (wins + 0.5*draws) / count
                        success_weight = (data['wins'] + 0.5 * data['draws']) / data['count']
                        scored_moves.append({
                            'position': pos,
                            'count': data['count'],
                            'success_rate': success_weight,
                            'stats': data
                        })
                
                # Sort by success rate and then by count
                sorted_moves = sorted(
                    scored_moves, 
                    key=lambda x: (x['success_rate'], x['count']),
                    reverse=True
                )
                
                # Store the recommendations for this board state
                self.move_recommendations[board_key] = sorted_moves

    def get_recommended_move(self, board, player):
        """Get recommended move based on historical data
        
        Args:
            board (numpy.ndarray): Current board state
            player (int): Player making the move (1 or 2)
            
        Returns:
            tuple: (row, col) of recommended move, or None if no recommendation
        """
        board_key = self._board_to_key(board)
        
        # Check if we have recommendations for this board state
        if board_key in self.move_recommendations:
            recommendations = self.move_recommendations[board_key]
            
            # Filter out positions that are already taken
            valid_recommendations = []
            for rec in recommendations:
                pos = rec['position']
                row, col = pos
                if 0 <= row < 3 and 0 <= col < 3 and board[row, col] == 0:
                    valid_recommendations.append(rec)
            
            # Return the highest-rated valid recommendation
            if valid_recommendations:
                return valid_recommendations[0]['position']
        
        # Fallback: get most successful position for this player
        empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i, j] == 0]
        if not empty_cells:
            return None
            
        # Check player's winning positions
        outcome_key = f'win_{player}'
        positions = self.position_by_outcome.get(outcome_key, {})
        
        # Filter to only empty positions
        valid_positions = [(pos, count) for pos, count in positions.items() if pos in empty_cells]
        
        # Sort by frequency and return the most common one
        if valid_positions:
            valid_positions.sort(key=lambda x: x[1], reverse=True)
            return valid_positions[0][0]
        
        # Last resort: random empty cell
        import random
        return random.choice(empty_cells)

    def find_similar_games(self, board, limit=5):
        """Find games with similar board states
        
        Args:
            board (numpy.ndarray): Board state to find similar games for
            limit (int): Maximum number of games to return
            
        Returns:
            list: List of games matching the board state
        """
        board_key = self._board_to_key(board)
        similar_games = []
        
        # Direct match
        if board_key in self.board_state_index:
            matches = self.board_state_index[board_key]
            
            # Get unique game IDs
            game_ids = set()
            for match in matches:
                game_ids.add(match['game_id'])
            
            # Add matched games
            for game_id in list(game_ids)[:limit]:
                if game_id in self.games:
                    similar_games.append(self.games[game_id])
                    
            return similar_games
        
        # Fuzzy matching (count matching cells)
        board_array = np.array([int(c) for c in board_key]).reshape(3, 3)
        
        # Score each game by similarity
        scored_games = []
        processed_games = set()
        
        for key, matches in self.board_state_index.items():
            for match in matches:
                game_id = match['game_id']
                
                # Skip if we already processed this game
                if game_id in processed_games:
                    continue
                    
                processed_games.add(game_id)
                
                # Get the board state
                move_board = match['move']['board']
                
                # Calculate similarity score (count matching cells)
                similarity = np.sum(board_array == move_board)
                
                # Add to scored games
                scored_games.append((game_id, similarity))
        
        # Sort by similarity (descending)
        scored_games.sort(key=lambda x: x[1], reverse=True)
        
        # Add top matches
        for game_id, _ in scored_games[:limit]:
            if game_id in self.games:
                similar_games.append(self.games[game_id])
        
        return similar_games

    def analyze_player_performance(self, player=None):
        """Analyze performance stats for a player
        
        Args:
            player (int, optional): Player to analyze (1 or 2). If None, analyze both.
            
        Returns:
            dict: Dictionary of performance statistics
        """
        stats = {}
        
        # Determine which players to analyze
        players = [player] if player in [1, 2] else [1, 2]
        
        for p in players:
            player_stats = {
                'games_played': 0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'win_rate': 0,
                'most_common_moves': [],
                'most_successful_positions': [],
                'opening_preferences': []
            }
            
            # Count games where this player participated
            player_games = []
            for game_id, game in self.games.items():
                moves = game.get('moves', [])
                
                # Check if player is in this game
                player_in_game = any(move.get('player') == p for move in moves)
                
                if player_in_game:
                    player_games.append(game_id)
                    player_stats['games_played'] += 1
                    
                    # Track outcome
                    winner = game.get('winner')
                    if winner == p:
                        player_stats['wins'] += 1
                    elif winner in [1, 2] and winner != p:
                        player_stats['losses'] += 1
                    elif winner == 0:
                        player_stats['draws'] += 1
            
            # Calculate win rate
            if player_stats['games_played'] > 0:
                player_stats['win_rate'] = player_stats['wins'] / player_stats['games_played']
            
            # Get most common moves
            moves_count = defaultdict(int)
            for item in self.moves_by_player.get(p, []):
                pos = item['move'].get('position')
                if pos:
                    moves_count[pos] += 1
            
            # Sort and add to stats
            sorted_moves = sorted(moves_count.items(), key=lambda x: x[1], reverse=True)
            player_stats['most_common_moves'] = sorted_moves[:5]  # Top 5
            
            # Most successful positions (those that led to wins)
            win_key = f'win_{p}'
            if win_key in self.position_by_outcome:
                win_positions = self.position_by_outcome[win_key]
                sorted_win_pos = sorted(win_positions.items(), key=lambda x: x[1], reverse=True)
                player_stats['most_successful_positions'] = sorted_win_pos[:5]  # Top 5
            
            # Opening move preferences
            if p in self.opening_moves:
                opening_prefs = self.opening_moves[p]
                sorted_openings = sorted(opening_prefs.items(), key=lambda x: x[1], reverse=True)
                player_stats['opening_preferences'] = sorted_openings
            
            stats[p] = player_stats
        
        return stats

# Add a main function to run a test analysis
if __name__ == "__main__":
    # Create processor
    processor = GameDataProcessor()
    
    # Load data
    processor.load_data()
    
    # Print summary
    processor.print_summary()
    
    # Get winning patterns
    patterns = processor.get_winning_patterns()
    print("\nWinning patterns for Player X:")
    if patterns[1]['move_frequency']:
        print("  Most common moves:")
        sorted_moves = sorted(patterns[1]['move_frequency'].items(), key=lambda x: x[1], reverse=True)
        for pos, count in sorted_moves[:3]:
            print(f"    Position {pos}: {count} times")
    
    print("\nWinning patterns for Player O:")
    if patterns[2]['move_frequency']:
        print("  Most common moves:")
        sorted_moves = sorted(patterns[2]['move_frequency'].items(), key=lambda x: x[1], reverse=True)
        for pos, count in sorted_moves[:3]:
            print(f"    Position {pos}: {count} times")
