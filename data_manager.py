import os
import threading
import json
import pickle
from collections import defaultdict

class GameDataManager:
    """Centralized manager for game data that can be passed between modules"""
    
    def __init__(self, preloaded_data=None):
        """Initialize the data manager
        
        Args:
            preloaded_data (dict): Optional pre-loaded data from splash screen
        """
        self.data = preloaded_data or {}
        self.data_lock = threading.RLock()  # Thread-safe access to data
        self.observers = defaultdict(list)  # Callbacks for data changes
        
        # Ensure basic structures exist
        with self.data_lock:
            if 'game_history' not in self.data:
                self.data['game_history'] = {}
            if 'game_stats' not in self.data:
                self.data['game_stats'] = {}
    
    def get(self, key, default=None):
        """Thread-safe access to get data
        
        Args:
            key (str): Data key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The requested data or default value
        """
        with self.data_lock:
            return self.data.get(key, default)
    
    def set(self, key, value, notify=True):
        """Thread-safe access to set data
        
        Args:
            key (str): Data key to set
            value: Value to store
            notify (bool): Whether to notify observers
            
        Returns:
            The stored value
        """
        with self.data_lock:
            self.data[key] = value
        
        # Notify observers if requested
        if notify:
            self._notify_observers(key, value)
        
        return value
    
    def update(self, key, update_func, notify=True):
        """Thread-safe update of data using a function
        
        Args:
            key (str): Data key to update
            update_func (callable): Function that takes current value and returns new value
            notify (bool): Whether to notify observers
            
        Returns:
            The updated value
        """
        with self.data_lock:
            current = self.data.get(key)
            updated = update_func(current)
            self.data[key] = updated
        
        # Notify observers if requested
        if notify:
            self._notify_observers(key, updated)
        
        return updated
    
    def register_observer(self, key, callback):
        """Register an observer function for data changes
        
        Args:
            key (str): Data key to observe
            callback (callable): Function to call when data changes
            
        Returns:
            None
        """
        with self.data_lock:
            self.observers[key].append(callback)
    
    def unregister_observer(self, key, callback):
        """Unregister an observer function
        
        Args:
            key (str): Data key being observed
            callback (callable): Function to remove
            
        Returns:
            bool: True if observer was removed, False otherwise
        """
        with self.data_lock:
            if key in self.observers and callback in self.observers[key]:
                self.observers[key].remove(callback)
                return True
        return False
    
    def _notify_observers(self, key, value):
        """Notify observers of data changes
        
        Args:
            key (str): Data key that changed
            value: New value
        """
        # Make a copy of observers list to avoid issues if callbacks register/unregister
        with self.data_lock:
            observers = list(self.observers.get(key, []))
        
        # Call each observer
        for callback in observers:
            try:
                callback(key, value)
            except Exception as e:
                print(f"Error in observer callback: {e}")
    
    def save_to_file(self, filename):
        """Save data to a file
        
        Args:
            filename (str): Path to save to
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Serialize data
            with self.data_lock:
                data_copy = dict(self.data)  # Make a copy to avoid lock during file write
            
            with open(filename, 'wb') as f:
                pickle.dump(data_copy, f)
            
            return True
        except Exception as e:
            print(f"Error saving data to {filename}: {e}")
            return False
    
    def load_from_file(self, filename, replace=True):
        """Load data from a file
        
        Args:
            filename (str): Path to load from
            replace (bool): Whether to replace all data or just update
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(filename):
                return False
            
            with open(filename, 'rb') as f:
                loaded_data = pickle.load(f)
            
            with self.data_lock:
                if replace:
                    self.data = loaded_data
                else:
                    self.data.update(loaded_data)
            
            return True
        except Exception as e:
            print(f"Error loading data from {filename}: {e}")
            return False
    
    def get_all(self):
        """Get a copy of all data
        
        Returns:
            dict: Copy of all data
        """
        with self.data_lock:
            return dict(self.data)
    
    def update_game_history(self, game_id, game_data, notify=True):
        """Update a specific game in the history
        
        Args:
            game_id (str): ID of the game to update
            game_data (dict): Game data to store
            notify (bool): Whether to notify observers
            
        Returns:
            dict: Updated game history
        """
        return self.update('game_history', 
                          lambda history: {**history, game_id: game_data},
                          notify)
    
    def update_game_statistics(self):
        """Recalculate game statistics from history
        
        Returns:
            dict: Updated statistics
        """
        def calculate_stats(current_stats):
            # Get game history
            history = self.get('game_history', {})
            
            # Initialize stats
            stats = {
                "total_games": len(history),
                "player_wins": {1: 0, 2: 0},
                "draws": 0,
                "incomplete": 0,
                "avg_moves": 0,
                "recent_games": []
            }
            
            # Calculate stats
            total_moves = 0
            for game_id, game in history.items():
                winner = game.get('winner')
                
                if winner in [1, 2]:
                    stats["player_wins"][winner] += 1
                elif winner == 0:
                    stats["draws"] += 1
                else:
                    stats["incomplete"] += 1
                
                # Count moves
                moves = game.get('moves', [])
                total_moves += len(moves)
            
            # Calculate average moves
            if stats["total_games"] > 0:
                stats["avg_moves"] = total_moves / stats["total_games"]
            
            # Get most recent games
            sorted_game_ids = sorted(
                history.keys(),
                key=lambda gid: history[gid].get('timestamp', gid),
                reverse=True
            )
            
            for game_id in sorted_game_ids[:5]:
                game = history[game_id]
                stats["recent_games"].append({
                    "id": game_id,
                    "winner": game.get('winner'),
                    "moves": len(game.get('moves', []))
                })
            
            return stats
        
        return self.update('game_stats', calculate_stats)
