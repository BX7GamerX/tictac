import numpy as np
import csv
import os
import datetime

class TicTacToeGame:
    # Central file for all game data
    GAME_DATA_FILE = "all_games_data.csv"
    
    def __init__(self, save_dir=None):
        # Game state: 0 = empty, 1 = X, 2 = O
        self.board = np.zeros((3, 3), dtype=int)
        self.current_player = 1  # Player 1 (X) starts
        self.game_over = False
        self.winner = None
        # Add history tracking
        self.history = []  # Will store board states after each move
        
        # Setup for CSV saving
        self.save_dir = save_dir or os.path.join(os.path.dirname(__file__), "game_data")
        os.makedirs(self.save_dir, exist_ok=True)
        self.game_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Path to central CSV file with all games
        self.csv_path = os.path.join(self.save_dir, self.GAME_DATA_FILE)
        
        # Create CSV header if file doesn't exist
        if not os.path.exists(self.csv_path):
            self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers"""
        with open(self.csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['game_id', 'move_number', 'player', 'row', 'col', 'board_state', 'timestamp', 'winner'])
    
    def make_move(self, row, col):
        """Make a move at the specified position
        
        Args:
            row (int): Row index (0-2)
            col (int): Column index (0-2)
            
        Returns:
            bool: True if the move was valid and made, False otherwise
        """
        # Check if the move is valid
        if self.board[row, col] == 0 and not self.game_over:
            # Place the current player's mark
            self.board[row, col] = self.current_player
            
            # Record the move in history
            move_data = {
                'board': self.board.copy(),  # Store a copy of the board
                'player': self.current_player,
                'position': (row, col),
                'move_number': len(self.history) + 1,
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'winner': None  # Initialize with no winner
            }
            
            # Check for win
            is_win = self.check_win()
            if is_win:
                self.game_over = True
                self.winner = self.current_player
                move_data['winner'] = self.winner  # Update winner in move data
            
            # Check for draw (board full)
            elif np.all(self.board != 0):
                self.game_over = True
                self.winner = 0  # 0 for draw
                move_data['winner'] = 0  # Update winner as draw in move data
            
            # Add to history and save
            self.history.append(move_data)
            self._save_move_to_csv(move_data)
            
            # Switch player (1->2, 2->1)
            if not self.game_over:
                self.current_player = 3 - self.current_player
            
            return True
            
        return False
    
    def _save_move_to_csv(self, move_data):
        """Save a move to the central CSV file
        
        Args:
            move_data (dict): Data about the move to save
        """
        try:
            # Flatten board to string representation
            board_flat = ''.join(str(x) for x in move_data['board'].flatten())
            
            # Create file with header if it doesn't exist
            file_exists = os.path.exists(self.csv_path)
            
            with open(self.csv_path, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header if new file
                if not file_exists:
                    writer.writerow(['game_id', 'move_number', 'player', 'row', 'col', 'board_state', 'timestamp', 'winner'])
                
                # Get winner value (None -> empty string)
                winner_value = "" if move_data.get('winner') is None else move_data.get('winner')
                
                # Write move data
                writer.writerow([
                    self.game_id,
                    move_data['move_number'],
                    move_data['player'],
                    move_data['position'][0],  # row
                    move_data['position'][1],  # col
                    board_flat,
                    move_data.get('timestamp', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    winner_value
                ])
        except Exception as e:
            print(f"Error saving move to CSV: {e}")
    
    def check_win(self):
        """Check if the current player has won
        
        Returns:
            bool: True if the current player has won, False otherwise
        """
        # Check rows and columns
        for i in range (3):
            if np.all(self.board[i, :] == self.current_player) or \
               np.all(self.board[:, i] == self.current_player):
                return True
        
        # Check diagonals
        if np.all(np.diag(self.board) == self.current_player) or \
           np.all(np.diag(np.fliplr(self.board)) == self.current_player):
                return True
        
        return False
    
    def reset(self):
        """Reset the game to initial state"""
        self.board = np.zeros((3, 3), dtype=int)
        self.current_player = 1  # Player 1 (X) starts
        self.game_over = False
        self.winner = None
        # Clear game history when resetting
        self.history = []
        
        # Generate a new game ID for the new game
        self.game_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def get_empty_cells(self):
        """Get list of empty cells on the board
        
        Returns:
            list: List of (row, col) tuples for empty cells
        """
        return [(i, j) for i in range(3) for j in range(3) if self.board[i, j] == 0]
    
    def get_game_history(self):
        """Get the complete history of the current game
        
        Returns:
            list: List of dictionaries containing board state and move info
        """
        return self.history
    
    @classmethod
    def load_game_history_from_csv(cls, game_id=None, save_dir=None):
        """Load game history from the central CSV file
        
        Args:
            game_id (str): Optional game ID to filter by. If None, returns all games.
            save_dir (str): Directory where game data is stored
            
        Returns:
            dict: Dictionary of game histories by game_id
        """
        save_dir = save_dir or os.path.join(os.path.dirname(__file__), "game_data")
        csv_path = os.path.join(save_dir, cls.GAME_DATA_FILE)
        
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return {}
        
        # Add file size check
        try:
            file_size = os.path.getsize(csv_path)
            print(f"CSV file size: {file_size} bytes")
            if file_size == 0:
                print("CSV file is empty")
                return {}
        except Exception as e:
            print(f"Error checking file size: {e}")
        
        games = {}
        
        try:
            # Debug information
            print(f"Loading game history from {csv_path}")
            
            with open(csv_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate column headers
                headers = reader.fieldnames
                print(f"CSV Headers: {headers}")
                
                required_fields = ['game_id', 'move_number', 'player', 'row', 'col', 'board_state']
                missing_fields = [field for field in required_fields if field not in headers]
                
                if missing_fields:
                    print(f"Warning: CSV missing required fields: {missing_fields}")
                
                # Group moves by game_id to detect duplicate game IDs
                game_moves = {}
                row_count = 0
                error_count = 0
                
                for row in reader:
                    row_count += 1
                    curr_game_id = row.get('game_id')
                    
                    if not curr_game_id:
                        print(f"Warning: Row {row_count} has no game_id, skipping")
                        error_count += 1
                        continue
                    
                    # Skip if we're looking for a specific game and this isn't it
                    if game_id and curr_game_id != game_id:
                        continue
                    
                    # Collect moves for each game_id
                    if curr_game_id not in game_moves:
                        game_moves[curr_game_id] = []
                        
                    # Parse move data with robust error handling
                    try:
                        # Extract and validate required fields
                        try:
                            move_number = int(row['move_number'])
                        except (ValueError, KeyError):
                            move_number = len(game_moves[curr_game_id]) + 1
                        
                        try:
                            player = int(row['player'])
                            if player not in [1, 2]:
                                print(f"Warning: Invalid player value {player} in game {curr_game_id}")
                                player = 1  # Default to player 1
                        except (ValueError, KeyError):
                            print(f"Warning: Invalid player value in game {curr_game_id}")
                            player = 1  # Default to player 1
                        
                        try:
                            row_idx = int(row['row'])
                            col_idx = int(row['col'])
                            # Validate row/col are in range 0-2
                            if not (0 <= row_idx <= 2 and 0 <= col_idx <= 2):
                                print(f"Warning: Position ({row_idx},{col_idx}) out of range in game {curr_game_id}")
                                row_idx = min(max(row_idx, 0), 2)
                                col_idx = min(max(col_idx, 0), 2)
                        except (ValueError, KeyError):
                            print(f"Warning: Invalid position in game {curr_game_id}")
                            row_idx, col_idx = 0, 0  # Default to top-left
                        
                        # Parse board state
                        try:
                            board_state = row.get('board_state', '000000000')
                            if not board_state or len(board_state) != 9:
                                print(f"Warning: Invalid board state length in game {curr_game_id}: {board_state}")
                                # Create default board
                                board_state = '000000000'
                            
                            # Validate board state contains only valid values
                            if not all(c in '012' for c in board_state):
                                print(f"Warning: Invalid characters in board state: {board_state}")
                                # Clean up invalid characters
                                board_state = ''.join(c if c in '012' else '0' for c in board_state)
                            
                            # Convert to numpy array
                            board = np.array([int(c) for c in board_state]).reshape(3, 3)
                        except Exception as e:
                            print(f"Error parsing board state in game {curr_game_id}: {e}")
                            # Create empty board
                            board = np.zeros((3, 3), dtype=int)
                        
                        # Get optional fields
                        timestamp = row.get('timestamp', 'Unknown')
                        
                        # Parse winner value (may be empty)
                        winner_value = row.get('winner', '').strip()
                        
                        try:
                            winner = int(winner_value) if winner_value else None
                            # Validate winner is a valid value (0, 1, 2 or None)
                            if winner not in [None, 0, 1, 2]:
                                print(f"Warning: Invalid winner value {winner} in game {curr_game_id}")
                                winner = None
                        except ValueError:
                            winner = None
                        
                        # Store move data
                        game_moves[curr_game_id].append({
                            'move_number': move_number,
                            'player': player,
                            'position': (row_idx, col_idx),
                            'board': board,
                            'timestamp': timestamp,
                            'winner': winner
                        })
                    except Exception as e:
                        print(f"Error parsing move for game {curr_game_id}, row {row_count}: {e}")
                        error_count += 1
                        continue
                
                # Process each game's moves
                print(f"Found {len(game_moves)} distinct game IDs, {row_count} total rows, {error_count} errors")
                
                for game_id, moves in game_moves.items():
                    # Skip empty games
                    if not moves:
                        print(f"Warning: Game {game_id} has no valid moves, skipping")
                        continue
                    
                    # Sort moves by move number
                    moves.sort(key=lambda x: x['move_number'])
                    
                    # Check for possible duplicate game IDs (games with overlapping move numbers)
                    move_numbers = [move['move_number'] for move in moves]
                    if len(set(move_numbers)) < len(move_numbers):
                        print(f"Warning: Game {game_id} has duplicate move numbers. This may be multiple games with same ID.")
                        
                        # Try to split into separate games
                        unique_game_id = game_id
                        suffix = 1
                        last_move_number = 0
                        current_game_moves = []
                        
                        for move in moves:
                            # If move number decreased or is the same, it's likely a new game
                            if move['move_number'] <= last_move_number and last_move_number > 0:
                                # Store the current game
                                if current_game_moves:
                                    games[unique_game_id] = cls._process_game_moves(current_game_moves)
                                
                                # Create a new game ID for the next segment
                                suffix += 1
                                unique_game_id = f"{game_id}_{suffix}"
                                current_game_moves = [move]
                            else:
                                current_game_moves.append(move)
                            
                            last_move_number = move['move_number']
                        
                        # Store the last segment
                        if current_game_moves:
                            games[unique_game_id] = cls._process_game_moves(current_game_moves)
                    else:
                        # Normal case - create game entry with sorted moves
                        games[game_id] = cls._process_game_moves(moves)
            
            # Debug output
            print(f"Loaded {len(games)} games")
            for game_id, game in games.items():
                winner = game.get('winner', 'None')
                move_count = len(game.get('moves', []))
                print(f"  Game {game_id}: {move_count} moves, winner: {winner}")
                
            return games
            
        except Exception as e:
            print(f"Error loading game history: {e}")
            import traceback
            traceback.print_exc()
            return {}

    @classmethod
    def _process_game_moves(cls, moves):
        """Process moves for a single game to create game data structure
        
        Args:
            moves (list): List of move dictionaries
            
        Returns:
            dict: Game data structure with moves and winner
        """
        if not moves:
            return {'moves': [], 'winner': None}
        
        # Extract winner from the final move if available
        final_winner = None
        board_states = []
        
        for move in moves:
            board_states.append(move['board'])
            if move.get('winner') is not None:
                final_winner = move['winner']
        
        # If no explicit winner recorded, determine from final board
        if final_winner is None and board_states:
            final_board = board_states[-1]
            
            # Check for a winner
            for player in [1, 2]:
                # Check rows and columns
                for i in range(3):
                    if np.all(final_board[i, :] == player) or np.all(final_board[:, i] == player):
                        final_winner = player
                        break
                
                # Check diagonals if no winner yet
                if final_winner is None:
                    if np.all(np.diag(final_board) == player) or np.all(np.diag(np.fliplr(final_board)) == player):
                        final_winner = player
                        break
            
            # If board is full and no winner, it's a draw
            if final_winner is None and np.all(final_board != 0):
                final_winner = 0
        
        # Create game data structure
        game_data = {
            'moves': moves,
            'board_states': board_states,
            'winner': final_winner,
            'timestamp': moves[0].get('timestamp', 'Unknown') if moves else 'Unknown'
        }
        
        return game_data

    @classmethod
    def get_all_game_ids(cls, save_dir=None):
        """Get all game IDs from the central CSV file
        
        Returns:
            list: List of game IDs
        """
        save_dir = save_dir or os.path.join(os.path.dirname(__file__), "game_data")
        csv_path = os.path.join(save_dir, cls.GAME_DATA_FILE)
        
        if not os.path.exists(csv_path):
            return []
            
        game_ids = set()
        
        try:
            with open(csv_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    game_ids.add(row['game_id'])
            
            return sorted(list(game_ids))
            
        except Exception as e:
            print(f"Error getting game IDs: {e}")
            return []
