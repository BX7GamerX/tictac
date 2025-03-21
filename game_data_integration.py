import os
import numpy as np
import pickle
import json
from collections import defaultdict
from game_data_processor import GameDataProcessor
from move_tracker import GameMoveTracker

class GameDataIntegration:
    """Integration layer for game data processing and optimized loading
    with complete support for the new move tracker system
    """
    
    def __init__(self, use_cache=True, progress_callback=None):
        """Initialize the integration layer
        
        Args:
            use_cache (bool): Whether to use cached processed data if available
            progress_callback (callable): Optional callback for progress updates
        """
        self.processor = GameDataProcessor()
        self.data_dir = self.processor.data_dir
        self.optimized_data_file = os.path.join(self.data_dir, "optimized_game_data.pkl")
        self.use_cache = use_cache
        self.progress_callback = progress_callback
        self.json_dir = os.path.join(self.data_dir, "game_json")
        
        # Try to load optimized data if cache is enabled
        if use_cache and os.path.exists(self.optimized_data_file):
            self._report_progress("Loading cached data...", -1)
            self._load_optimized_data()
        else:
            self._initialize_data()
    
    def _initialize_data(self):
        """Initialize data by loading from JSON files and CSV, then building optimized structures"""
        # Load directly from JSON files first
        self._report_progress("Checking for JSON game files...", 0.05)
        games_loaded = self._load_from_json_files()
        
        if not games_loaded:
            # Fall back to CSV loading
            self._report_progress("No JSON games found, loading from CSV...", 0.1)
            self.processor.load_data()
        
        # Report intermediate stats
        if self.progress_callback:
            self.progress_callback("Processing game data...", 0.4, self.processor.stats)
        
        # Build optimized data structures
        self._report_progress("Building optimized data structures...", 0.6)
        self.processor.build_optimized_data_structure()
        
        # Save optimized data for future use
        self._report_progress("Saving optimized data...", 0.9)
        self._save_optimized_data()
        
        # Final report
        self._report_progress("Data loading complete", 1.0, self.processor.stats)
    
    def _load_from_json_files(self):
        """Load games directly from JSON files with move tracker data
        
        Returns:
            bool: True if games were loaded, False otherwise
        """
        try:
            if not os.path.exists(self.json_dir):
                return False
                
            json_files = [f for f in os.listdir(self.json_dir) if f.endswith('.json')]
            if not json_files:
                return False
                
            self._report_progress(f"Loading {len(json_files)} JSON games...", 0.15)
            
            # Import move tracker
            from move_tracker import GameMoveTracker
            
            # Process each JSON file
            for i, json_file in enumerate(json_files):
                game_id = json_file.split('.')[0]
                json_path = os.path.join(self.json_dir, json_file)
                
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
                        # Create game entry with move tracker data
                        self.processor.games[game_id] = {
                            'game_id': game_id,
                            'move_tracker': move_tracker,
                            'winner': game_data.get('winner'),
                            'timestamp': game_data.get('timestamp')
                        }
                        
                        # Also add legacy format moves for compatibility
                        self.processor.games[game_id]['moves'] = self._convert_to_legacy_moves(move_tracker, game_data.get('winner'))
                        self.processor.games[game_id]['move_count'] = move_tracker.all_moves.length
                        
                        # Categorize game
                        winner = game_data.get('winner')
                        if winner in [1, 2]:
                            self.processor.winning_games[winner].append(game_id)
                            self.processor.completed_games.append(game_id)
                        elif winner == 0:
                            self.processor.draws.append(game_id)
                            self.processor.completed_games.append(game_id)
                        else:
                            self.processor.incomplete_games.append(game_id)
                except Exception as e:
                    print(f"Error processing JSON game {json_file}: {e}")
                    continue
                
                # Update progress
                if i % 5 == 0:  # Update every 5 games
                    progress = 0.15 + (0.2 * (i / len(json_files)))
                    self._report_progress(f"Loading JSON game {i+1}/{len(json_files)}", progress)
            
            # Calculate statistics
            self.processor._calculate_statistics()
            
            return len(self.processor.games) > 0
            
        except Exception as e:
            print(f"Error loading from JSON: {e}")
            return False
    
    def _convert_to_legacy_moves(self, move_tracker, winner):
        """Convert move tracker data to legacy moves format
        
        Args:
            move_tracker (GameMoveTracker): Move tracker with game data
            winner (int): Game winner (1, 2, 0, or None)
            
        Returns:
            list: List of move dictionaries in legacy format
        """
        moves = []
        
        # Start at head node
        node = move_tracker.all_moves.head
        move_number = 1
        
        while node:
            move = {
                'move_number': move_number,
                'player': node.player,
                'position': (node.row, node.col),
                'board': node.board_state.copy(),
                'winner': None
            }
            
            # Only last move gets winner value
            if node.next is None:
                move['winner'] = winner
                
            moves.append(move)
            move_number += 1
            node = node.next
            
        return moves
    
    def _load_optimized_data(self):
        """Load optimized data structures from cache file"""
        try:
            self._report_progress("Loading optimized data from cache...", 0.3)
            
            with open(self.optimized_data_file, 'rb') as f:
                data = pickle.load(f)
            
            # Update processor with loaded data
            for key, value in data.items():
                setattr(self.processor, key, value)
            
            self._report_progress("Optimized data loaded successfully", 1.0, self.processor.stats)
            return True
        except Exception as e:
            print(f"Error loading optimized data: {e}")
            # Fall back to normal initialization
            self._report_progress("Cache loading failed, rebuilding data...", 0.0)
            self._initialize_data()
            return False
    
    def _save_optimized_data(self):
        """Save optimized data structures to cache file"""
        try:
            # Collect all data to save
            data = {
                'games': self.processor.games,
                'moves_by_player': self.processor.moves_by_player,
                'completed_games': self.processor.completed_games,
                'winning_games': self.processor.winning_games,
                'draws': self.processor.draws,
                'incomplete_games': self.processor.incomplete_games,
                'stats': self.processor.stats,
                'board_state_index': self.processor.board_state_index,
                'position_by_outcome': self.processor.position_by_outcome,
                'opening_moves': self.processor.opening_moves,
                'winning_sequences': self.processor.winning_sequences,
                'move_recommendations': self.processor.move_recommendations
            }
            
            # Save to pickle file
            with open(self.optimized_data_file, 'wb') as f:
                pickle.dump(data, f)
                
            print(f"Optimized data saved to {self.optimized_data_file}")
            return True
        except Exception as e:
            print(f"Error saving optimized data: {e}")
            return False
    
    def _report_progress(self, stage, progress=None, stats=None):
        """Report progress to callback if available
        
        Args:
            stage (str): Current processing stage
            progress (float): Progress value (0.0-1.0)
            stats (dict): Current statistics
        """
        if self.progress_callback:
            continue_loading = self.progress_callback(stage, progress, stats)
            if not continue_loading:
                print("Loading canceled by user")
                raise InterruptedError("Loading canceled by user")
        else:
            print(f"Status: {stage}")
    
    def refresh_data(self):
        """Refresh data by reloading from JSON and CSV and rebuilding optimized structures"""
        self._initialize_data()
        return True
    
    # Public methods for accessing data
    
    def get_all_games(self):
        """Get all games
        
        Returns:
            dict: Dictionary of all games
        """
        return self.processor.games
    
    def get_game_by_id(self, game_id):
        """Get game by ID
        
        Args:
            game_id (str): Game ID
            
        Returns:
            dict: Game data or None if not found
        """
        return self.processor.games.get(game_id)
    
    def get_games_by_outcome(self, outcome):
        """Get games by outcome
        
        Args:
            outcome: Outcome to filter by (1 or 2 for win, 0 for draw, None for incomplete)
            
        Returns:
            list: List of games matching the outcome
        """
        if outcome == 0:
            game_ids = self.processor.draws
        elif outcome in [1, 2]:
            game_ids = self.processor.winning_games.get(outcome, [])
        else:
            game_ids = self.processor.incomplete_games
            
        return [self.processor.games[gid] for gid in game_ids if gid in self.processor.games]
    
    def get_statistics(self):
        """Get overall statistics
        
        Returns:
            dict: Dictionary of statistics
        """
        return self.processor.stats
    
    def get_move_recommendation(self, board, player):
        """Get recommended move based on historical data
        
        Args:
            board (numpy.ndarray): Current board state
            player (int): Player making the move (1 or 2)
            
        Returns:
            tuple: (row, col) of recommended move, or None if no recommendation
        """
        return self.processor.get_recommended_move(board, player)
    
    def find_similar_games(self, board, limit=5):
        """Find games with similar board states
        
        Args:
            board (numpy.ndarray): Board state to find similar games for
            limit (int): Maximum number of games to return
            
        Returns:
            list: List of games matching the board state
        """
        return self.processor.find_similar_games(board, limit)
    
    def get_player_stats(self, player=None):
        """Get player statistics
        
        Args:
            player (int, optional): Player to get stats for (1 or 2). If None, get stats for both.
            
        Returns:
            dict: Dictionary of player statistics
        """
        return self.processor.analyze_player_performance(player)
    
    def get_winning_patterns(self):
        """Get common patterns in winning games
        
        Returns:
            dict: Dictionary of patterns by player
        """
        return self.processor.get_winning_patterns()
    
    def get_move_tracker_for_game(self, game_id):
        """Get the move tracker for a specific game
        
        Args:
            game_id (str): Game ID
            
        Returns:
            GameMoveTracker: Move tracker for the game or None if not available
        """
        game = self.processor.games.get(game_id)
        if game and 'move_tracker' in game:
            return game['move_tracker']
            
        # If no move tracker exists but we have legacy format, try to create one
        if game and 'moves' in game:
            try:
                # Create a new move tracker
                move_tracker = GameMoveTracker()
                
                # Add each move
                for move in game['moves']:
                    position = move.get('position')
                    player = move.get('player')
                    board = move.get('board')
                    
                    if position and player is not None and board is not None:
                        row, col = position
                        move_tracker.add_move(row, col, player, board)
                
                # Store for future use
                game['move_tracker'] = move_tracker
                return move_tracker
            except Exception as e:
                print(f"Error creating move tracker for game {game_id}: {e}")
                return None
        
        return None

# Example usage
if __name__ == "__main__":
    data_manager = GameDataIntegration()
    
    # Print statistics
    print("\n=== Game Data Integration Test ===")
    stats = data_manager.get_statistics()
    print(f"Total games: {stats['total_games']}")
    print(f"Completed games: {stats['completed_games']}")
    print(f"  - Player X wins: {stats['wins_player1']}")
    print(f"  - Player O wins: {stats['wins_player2']}")
    print(f"  - Draws: {stats['draws']}")
    
    # Test a board state for recommendations
    test_board = np.array([
        [1, 0, 0],
        [0, 2, 0],
        [0, 0, 0]
    ])
    
    rec_pos = data_manager.get_move_recommendation(test_board, 1)
    if rec_pos:
        print(f"\nRecommended move for Player X: {rec_pos}")
    
    # Get player stats
    player_stats = data_manager.get_player_stats(1)
    if player_stats and 1 in player_stats:
        p_stats = player_stats[1]
        print(f"\nPlayer X stats:")
        print(f"  - Win rate: {p_stats['win_rate']:.2f}")
        print(f"  - Games played: {p_stats['games_played']}")
        print(f"  - Wins: {p_stats['wins']}")
        
        # Show top positions
        if p_stats['most_successful_positions']:
            print("\nTop winning positions:")
            for pos, count in p_stats['most_successful_positions'][:3]:
                print(f"  - Position {pos}: {count} times")
