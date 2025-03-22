import os
import numpy as np
import pickle
from nn_model import NeuralNetwork
from game import TicTacToeGame

class AIPlayer:
    """AI player for Tic Tac Toe using neural network model"""
    
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "ai_model.pkl")
    
    def __init__(self):
        """Initialize AI player"""
        self.model = None
        # Try to load existing model - with better error handling
        try:
            self._load_model()
        except Exception as e:
            print(f"Warning: Could not load AI model: {e}")
            # Don't raise exception to allow app to continue
    
    def _load_model(self):
        """Load trained model if it exists"""
        from debug_logger import info, warning, error, debug
        
        try:
            debug(f"Checking for AI model at: {self.MODEL_PATH}")
            if os.path.exists(self.MODEL_PATH):
                # Check if file is empty before attempting to load
                file_size = os.path.getsize(self.MODEL_PATH)
                debug(f"AI model file size: {file_size} bytes")
                
                if file_size == 0:
                    warning("AI model file is empty, will need retraining")
                    return False
                    
                with open(self.MODEL_PATH, 'rb') as f:
                    try:
                        debug("Loading AI model from file")
                        self.model = pickle.load(f)
                        info("AI model loaded successfully")
                        return True
                    except EOFError:
                        warning("AI model file is corrupted, will need retraining")
                        return False
            else:
                info("AI model file does not exist, will need training")
            return False
        except EOFError:
            warning("AI model file is empty or corrupted, will need retraining")
            return False
        except Exception as e:
            error(f"Error loading AI model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _save_model(self):
        """Save model to file"""
        try:
            with open(self.MODEL_PATH, 'wb') as f:
                pickle.dump(self.model, f)
            return True
        except Exception as e:
            print(f"Error saving AI model: {e}")
            return False
    
    def model_exists(self):
        """Check if a trained model exists
        
        Returns:
            bool: True if model exists, False otherwise
        """
        return self.model is not None
    
    def train_model(self, games=None):
        """Train a new model on game data with move tracker support
        
        Args:
            games (dict, optional): Dictionary of games to train on.
                If None, loads games from files.
                
        Returns:
            bool: True if training was successful, False otherwise
        """
        try:
            # Load games if not provided
            if games is None:
                # Try to use optimized data integration first
                try:
                    from game_data_integration import GameDataIntegration
                    data_manager = GameDataIntegration(use_cache=True)
                    games = data_manager.get_all_games()
                    print(f"Loaded {len(games)} games from data integration")
                except ImportError:
                    # Fall back to direct loading
                    games = TicTacToeGame.load_game_history_from_csv()
                    print(f"Loaded {len(games)} games from history")
            
            if not games:
                print("No games available for training")
                return False
            
            # Prepare training data
            X = []  # Board states
            y = []  # Target moves
            
            # Debug info
            valid_moves_count = 0
            skipped_moves_count = 0
            games_with_winner = 0
            games_with_draw = 0
            games_incomplete = 0
            
            # Process each game
            for game_id, game_data in games.items():
                # Check if we have a winner or draw
                winner = game_data.get('winner')
                if winner is not None:
                    if winner == 0:
                        games_with_draw += 1
                    else:
                        games_with_winner += 1
                else:
                    games_incomplete += 1
                    continue  # Skip games without clear outcome
                
                # Check if game has move tracker
                if 'move_tracker' in game_data:
                    move_tracker = game_data['move_tracker']
                    
                    # Process moves from the tracker
                    node = move_tracker.all_moves.head
                    
                    while node:
                        # Skip final move in winning games (doesn't help with learning)
                        if winner not in [None, 0] and node.next is None:
                            skipped_moves_count += 1
                            node = node.next
                            continue
                        
                        # Skip move if board is in terminal state
                        if self._is_terminal_state(node.board_state):
                            skipped_moves_count += 1
                            node = node.next
                            continue
                        
                        # Normalize and flatten board state
                        board_flat = self._preprocess_board(node.board_state)
                        
                        # Create one-hot encoded move position
                        move_pos = np.zeros(9)
                        idx = node.cell_index
                        if 0 <= idx < 9:  # Validate index
                            move_pos[idx] = 1
                            
                            # Add to training data
                            X.append(board_flat)
                            y.append(move_pos)
                            valid_moves_count += 1
                        else:
                            skipped_moves_count += 1
                        
                        node = node.next
                else:
                    # Fall back to legacy format
                    # Ensure moves exist and are properly sorted
                    if 'moves' not in game_data or not game_data['moves']:
                        continue
                        
                    # Sort moves by move number to ensure correct sequence
                    moves = sorted(game_data['moves'], key=lambda x: x.get('move_number', 0))
                    
                    # Skip games with too few moves
                    if len(moves) < 5:  # Minimum moves for a completed game
                        continue
                        
                    # Process each move in the game
                    for i, move in enumerate(moves):
                        # Skip if missing necessary data
                        if 'board' not in move or 'position' not in move:
                            skipped_moves_count += 1
                            continue
                        
                        # Skip final move in winning games (doesn't help with learning)
                        if winner not in [None, 0] and i == len(moves) - 1:
                            skipped_moves_count += 1
                            continue
                        
                        # Skip move if board is in terminal state
                        if self._is_terminal_state(move['board']):
                            skipped_moves_count += 1
                            continue
                        
                        # Normalize and flatten board state
                        board_flat = self._preprocess_board(move['board'])
                        
                        # Create one-hot encoded move position
                        move_pos = np.zeros(9)
                        position = move['position']
                        idx = position[0] * 3 + position[1]
                        if 0 <= idx < 9:  # Validate index
                            move_pos[idx] = 1
                            
                            # Add to training data
                            X.append(board_flat)
                            y.append(move_pos)
                            valid_moves_count += 1
                        else:
                            skipped_moves_count += 1
            
            # Print debug information
            print(f"Training statistics:")
            print(f"  - Games with winner: {games_with_winner}")
            print(f"  - Games with draw: {games_with_draw}")
            print(f"  - Incomplete games skipped: {games_incomplete}")
            print(f"  - Valid moves collected: {valid_moves_count}")
            print(f"  - Skipped moves: {skipped_moves_count}")
            
            # Check if we have enough training data
            if len(X) < 10:  # Need at least a few examples to train
                print("Insufficient training examples found")
                return False
            
            # Convert to numpy arrays
            X = np.array(X)
            y = np.array(y)
            
            print(f"Training on {len(X)} examples with input shape {X.shape} and output shape {y.shape}")
            
            # Create and train neural network
            nn = NeuralNetwork(learning_rate=0.01)
            nn.add_layer(9, 27, 'relu')    # Input -> Hidden
            nn.add_layer(27, 18, 'relu')   # Hidden -> Hidden
            nn.add_layer(18, 9, 'sigmoid') # Hidden -> Output
            
            # Train the model
            nn.train(X, y, epochs=200, batch_size=32, verbose=True)
            
            # Save the trained model
            self.model = nn
            success = self._save_model()
            if success:
                print("AI model trained and saved successfully")
            else:
                print("Failed to save AI model")
            return success
            
        except Exception as e:
            print(f"Error training AI model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_move(self, board):
        """Get AI's next move
        
        Args:
            board (numpy.ndarray): Current board state
            
        Returns:
            tuple: (row, col) for the next move, or (None, None) if no valid move
        """
        if not self.model_exists():
            # Clearly log that we're using a random move due to missing model
            print("AI model not available, using random move instead")
            return self._get_random_move(board)
        
        try:
            # Get empty cells
            empty_cells = []
            for i in range(3):
                for j in range(3):
                    if board[i, j] == 0:
                        empty_cells.append((i, j))
            
            if not empty_cells:
                return None, None  # No valid moves
            
            # If only one move is available, take it
            if len(empty_cells) == 1:
                return empty_cells[0]
            
            # Preprocess board for prediction
            board_flat = self._preprocess_board(board)
            
            # Get model prediction (move probabilities)
            move_probs = self.model.predict(np.array([board_flat]))[0]
            
            # Create a mask for valid moves only
            valid_moves_mask = np.zeros(9)
            for i, j in empty_cells:
                valid_moves_mask[i * 3 + j] = 1
            
            # Apply mask to set invalid move probabilities to 0
            valid_move_probs = move_probs * valid_moves_mask
            
            # If all valid moves have 0 probability, fallback to random
            if np.sum(valid_move_probs) == 0:
                return self._get_random_move(board)
            
            # Select the highest probability valid move
            best_move_idx = np.argmax(valid_move_probs)
            row = best_move_idx // 3
            col = best_move_idx % 3
            
            return row, col
            
        except Exception as e:
            print(f"Error getting AI move: {e}")
            return self._get_random_move(board)
    
    def _get_random_move(self, board):
        """Get a random valid move
        
        Args:
            board (numpy.ndarray): Current board state
            
        Returns:
            tuple: (row, col) for a random valid move, or (None, None) if no valid move
        """
        empty_cells = []
        for i in range(3):
            for j in range(3):
                if board[i, j] == 0:
                    empty_cells.append((i, j))
        
        if not empty_cells:
            return None, None
        
        return empty_cells[np.random.choice(len(empty_cells))]
    
    def _preprocess_board(self, board):
        """Preprocess board for neural network input
        
        Args:
            board (numpy.ndarray): 3x3 board state
            
        Returns:
            numpy.ndarray: Flattened and normalized board state
        """
        try:
            # Ensure board is numpy array with correct shape
            if not isinstance(board, np.ndarray):
                board = np.array(board)
            
            if board.shape != (3, 3):
                # Try to reshape if possible
                board = board.reshape(3, 3)
                
            # Flatten and normalize board (0->0, 1->1, 2->-1)
            board_flat = board.flatten().astype(float)
            
            # Validate board values
            if not np.all(np.isin(board_flat, [0, 1, 2])):
                # Clean up any invalid values
                board_flat = np.clip(board_flat, 0, 2)
            
            # Convert opponent marks (2) to -1 for better balance
            board_flat = np.where(board_flat == 2, -1, board_flat)
            return board_flat
            
        except Exception as e:
            print(f"Error preprocessing board: {e}")
            # Return a safe default (empty board)
            return np.zeros(9)
    
    def _is_terminal_state(self, board):
        """Check if board state is terminal (game over)
        
        Args:
            board (numpy.ndarray): Board state to check
            
        Returns:
            bool: True if game is over, False otherwise
        """
        # Check for win
        for player in [1, 2]:
            # Check rows and columns
            for i in range(3):
                if np.all(board[i, :] == player) or np.all(board[:, i] == player):
                    return True
            
            # Check diagonals
            if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
                return True
        
        # Check for full board (draw)
        if np.all(board != 0):
            return True
        
        return False
