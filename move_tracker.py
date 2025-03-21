import numpy as np

class MoveNode:
    """Represents a single move in the game history
    
    This is a node in a doubly linked list of moves, allowing
    efficient traversal of game history in both directions.
    """
    
    def __init__(self, cell_index, player, board_state, move_number=None):
        """Initialize a move node
        
        Args:
            cell_index (int): Index of cell (0-8)
            player (int): Player who made the move (1 or 2)
            board_state (numpy.ndarray): Board state after this move
            move_number (int, optional): Move number in the game sequence
        """
        self.cell_index = cell_index  # 0-8 index (flattened)
        self.row = cell_index // 3    # 0-2 row
        self.col = cell_index % 3     # 0-2 column
        self.player = player          # 1 or 2
        self.board_state = board_state.copy() if board_state is not None else None
        self.move_number = move_number
        
        # Linked list pointers
        self.next = None
        self.prev = None
    
    def get_position(self):
        """Get the position as (row, col) tuple
        
        Returns:
            tuple: (row, col) position
        """
        return (self.row, self.col)
    
    def to_dict(self):
        """Convert to dictionary for serialization
        
        Returns:
            dict: Dictionary representation of the move
        """
        return {
            'cell_index': self.cell_index,
            'row': self.row,
            'col': self.col,
            'player': self.player,
            'board_state': self.board_state.tolist() if self.board_state is not None else None,
            'move_number': self.move_number
        }


class MoveList:
    """A doubly linked list of moves for tracking game history"""
    
    def __init__(self):
        """Initialize an empty move list"""
        self.head = None  # First move
        self.tail = None  # Last move
        self.current = None  # Current position for playback
        self.length = 0
    
    def add_move(self, cell_index, player, board_state):
        """Add a new move to the end of the list
        
        Args:
            cell_index (int): Index of cell (0-8)
            player (int): Player who made the move (1 or 2)
            board_state (numpy.ndarray): Board state after this move
            
        Returns:
            MoveNode: The newly added node
        """
        # Create new node
        new_node = MoveNode(
            cell_index=cell_index,
            player=player,
            board_state=board_state,
            move_number=self.length + 1
        )
        
        # If list is empty, set head
        if self.head is None:
            self.head = new_node
            self.tail = new_node
            self.current = new_node
        else:
            # Add to end of list
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
            self.current = new_node
        
        self.length += 1
        return new_node
    
    def goto_start(self):
        """Go to the start of the move list
        
        Returns:
            MoveNode: The first node or None if list is empty
        """
        self.current = self.head
        return self.current
    
    def goto_end(self):
        """Go to the end of the move list
        
        Returns:
            MoveNode: The last node or None if list is empty
        """
        self.current = self.tail
        return self.current
    
    def next_move(self):
        """Move to the next move in the list
        
        Returns:
            MoveNode: The next node or None if at end
        """
        if self.current and self.current.next:
            self.current = self.current.next
            return self.current
        return None
    
    def previous_move(self):
        """Move to the previous move in the list
        
        Returns:
            MoveNode: The previous node or None if at start
        """
        if self.current and self.current.prev:
            self.current = self.current.prev
            return self.current
        return None
    
    def get_current_board(self):
        """Get the board state at current position
        
        Returns:
            numpy.ndarray: Current board state or empty board if at start
        """
        if self.current:
            return self.current.board_state.copy()
        return np.zeros((3, 3), dtype=int)
    
    def get_initial_board(self):
        """Get empty board (before any moves)
        
        Returns:
            numpy.ndarray: Empty board
        """
        return np.zeros((3, 3), dtype=int)
    
    def to_list(self):
        """Convert move list to regular list
        
        Returns:
            list: List of move dictionaries
        """
        moves = []
        node = self.head
        while node:
            moves.append(node.to_dict())
            node = node.next
        return moves
    
    def get_player_moves(self, player):
        """Get moves made by a specific player
        
        Args:
            player (int): Player number (1 or 2)
            
        Returns:
            list: List of move nodes by this player
        """
        player_moves = []
        node = self.head
        while node:
            if node.player == player:
                player_moves.append(node)
            node = node.next
        return player_moves
    
    def clear(self):
        """Clear the move list"""
        self.head = None
        self.tail = None
        self.current = None
        self.length = 0


class GameMoveTracker:
    """Tracks moves for a Tic Tac Toe game using linked lists"""
    
    def __init__(self):
        """Initialize the move tracker"""
        self.all_moves = MoveList()          # All moves in order
        self.player_moves = {1: MoveList(), 2: MoveList()}  # Moves by player
        
        # Latest board state
        self.current_board = np.zeros((3, 3), dtype=int)
    
    def add_move(self, row, col, player, board_state):
        """Add a move to the tracking system
        
        Args:
            row (int): Row (0-2)
            col (int): Column (0-2)
            player (int): Player (1 or 2)
            board_state (numpy.ndarray): Board state after move
            
        Returns:
            MoveNode: The newly added node
        """
        # Calculate cell index (0-8)
        cell_index = row * 3 + col
        
        # Add to all moves list
        move_node = self.all_moves.add_move(cell_index, player, board_state)
        
        # Add to player's moves list
        self.player_moves[player].add_move(cell_index, player, board_state)
        
        # Update current board
        self.current_board = board_state.copy()
        
        return move_node
    
    def clear(self):
        """Reset the move tracker"""
        self.all_moves.clear()
        self.player_moves[1].clear()
        self.player_moves[2].clear()
        self.current_board = np.zeros((3, 3), dtype=int)
    
    def get_moves_data(self):
        """Get all move data for saving
        
        Returns:
            dict: Dictionary with move data
        """
        return {
            'all_moves': self.all_moves.to_list(),
            'player1_moves': self.player_moves[1].to_list(),
            'player2_moves': self.player_moves[2].to_list(),
            'final_board': self.current_board.tolist() if self.current_board is not None else None
        }
    
    def restore_from_moves_data(self, moves_data):
        """Restore move tracker state from saved data
        
        Args:
            moves_data (dict): Dictionary with move data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clear current state
            self.clear()
            
            # Reconstruct all moves
            all_moves = moves_data.get('all_moves', [])
            for move in all_moves:
                # Convert board state back to numpy array
                board_state = np.array(move['board_state']) if move['board_state'] else None
                
                # Add move
                self.all_moves.add_move(
                    move['cell_index'],
                    move['player'],
                    board_state
                )
            
            # Reconstruct player moves (optional, could rebuild from all_moves)
            for player in [1, 2]:
                player_key = f'player{player}_moves'
                if player_key in moves_data:
                    for move in moves_data[player_key]:
                        board_state = np.array(move['board_state']) if move['board_state'] else None
                        self.player_moves[player].add_move(
                            move['cell_index'],
                            move['player'],
                            board_state
                        )
            
            # Set current board
            if 'final_board' in moves_data and moves_data['final_board']:
                self.current_board = np.array(moves_data['final_board'])
            elif self.all_moves.tail and self.all_moves.tail.board_state is not None:
                self.current_board = self.all_moves.tail.board_state.copy()
            
            return True
        except Exception as e:
            print(f"Error restoring move data: {e}")
            return False
