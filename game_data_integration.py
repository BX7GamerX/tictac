import os
import numpy as np
import pickle
from game_data_processor import GameDataProcessor

class GameDataIntegration:
    """Integration layer for game data processing and optimized loading
    
    This class provides a simplified interface to access game data with
    optimized loading and analysis features. It acts as a facade for
    the more complex GameDataProcessor.
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
        
        # Try to load optimized data if cache is enabled
        if use_cache and os.path.exists(self.optimized_data_file):
            self._report_progress("Loading cached data...", -1)
            self._load_optimized_data()
        else:
            self._initialize_data()
    
    def _initialize_data(self):
        """Initialize data by loading from CSV and building optimized structures"""
        # Load raw data from CSV
        self._report_progress("Loading game data from CSV...", 0.1)
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
        """Refresh data by reloading from CSV and rebuilding optimized structures"""
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
