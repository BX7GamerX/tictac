import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import os
import time
import threading
from data_manager import GameDataManager
from utils import update_app_heartbeat

class GameHistoryViewer:
    """Viewer for past game history with filtering and replay capabilities"""
    
    def __init__(self):
        """Initialize the game history viewer"""
        self.window = None
        self.history_loaded = False
        self.game_history = {}
        self.filtered_games = []
        self.current_game_id = None
        self.current_move_index = 0
        self.animation_running = False
        self.loading_cancelled = False
        
        # Create window
        self.setup_ui()
        
        # Set up initial heartbeat
        update_app_heartbeat()
        
        # Load history in a background thread
        self.load_thread = threading.Thread(target=self._load_history_data, daemon=True)
        self.load_thread.start()
    
    def setup_ui(self):
        """Set up the UI elements"""
        # Create window
        self.window = ctk.CTk()
        self.window.title("Game History")
        self.window.geometry("1000x700")
        self.window.configure(fg_color="#1E1E1E")
        
        # Main frame with two columns
        main_frame = ctk.CTkFrame(self.window, fg_color="#252525", corner_radius=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left column - Game list
        left_frame = ctk.CTkFrame(main_frame, fg_color="#2A2A2A", corner_radius=10, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left_frame.pack_propagate(False)  # Maintain width
        
        # Fix the width of the left frame
        left_frame.configure(width=300)
        
        # Search and filter options at top of left frame
        filter_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        filter_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Filter label
        ctk.CTkLabel(
            filter_frame,
            text="Filter Games:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        # Winner filter
        winner_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        winner_frame.pack(fill=tk.X, pady=5)
        
        ctk.CTkLabel(
            winner_frame,
            text="Winner:",
            font=ctk.CTkFont(size=12)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Winner options
        self.winner_var = tk.StringVar(value="All")
        winner_dropdown = ctk.CTkOptionMenu(
            winner_frame,
            values=["All", "Player X", "Player O", "Draw", "Incomplete"],
            variable=self.winner_var,
            command=self._apply_filters,
            width=120
        )
        winner_dropdown.pack(side=tk.RIGHT)
        
        # Moves filter with slider
        moves_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        moves_frame.pack(fill=tk.X, pady=5)
        
        ctk.CTkLabel(
            moves_frame,
            text="Max Moves:",
            font=ctk.CTkFont(size=12)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.moves_var = tk.IntVar(value=9)
        moves_slider = ctk.CTkSlider(
            moves_frame,
            from_=1,
            to=9,
            number_of_steps=8,
            variable=self.moves_var,
            command=self._apply_filters_delayed
        )
        moves_slider.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        
        # Display current value of slider
        self.moves_label = ctk.CTkLabel(
            moves_frame,
            text="9",
            font=ctk.CTkFont(size=12),
            width=20
        )
        self.moves_label.pack(side=tk.RIGHT)
        
        # Sort order
        sort_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        sort_frame.pack(fill=tk.X, pady=5)
        
        ctk.CTkLabel(
            sort_frame,
            text="Sort By:",
            font=ctk.CTkFont(size=12)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_var = tk.StringVar(value="Newest First")
        sort_dropdown = ctk.CTkOptionMenu(
            sort_frame,
            values=["Newest First", "Oldest First", "Most Moves", "Fewest Moves"],
            variable=self.sort_var,
            command=self._apply_filters,
            width=120
        )
        sort_dropdown.pack(side=tk.RIGHT)
        
        # Search button
        search_btn = ctk.CTkButton(
            filter_frame,
            text="Apply Filters",
            command=self._apply_filters,
            font=ctk.CTkFont(size=13),
            fg_color="#3E92CC",
            hover_color="#2D7DB3"
        )
        search_btn.pack(fill=tk.X, pady=10)
        
        # Game list with scrollbar
        games_frame = ctk.CTkFrame(left_frame, fg_color="#252525", corner_radius=5)
        games_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create placeholder for games list
        self.games_container = ctk.CTkScrollableFrame(
            games_frame,
            fg_color="#252525",
            corner_radius=5,
            label_text="Game History",
            label_fg_color="#3E3E3E"
        )
        self.games_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.games_container,
            text="Loading game history...",
            font=ctk.CTkFont(size=14),
            text_color="#AAAAAA"
        )
        self.loading_label.pack(pady=20)
        
        # Right column - Game details and replay
        right_frame = ctk.CTkFrame(main_frame, fg_color="#2A2A2A", corner_radius=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Game details at top
        self.details_frame = ctk.CTkFrame(right_frame, fg_color="#252525", corner_radius=5, height=100)
        self.details_frame.pack(fill=tk.X, padx=10, pady=10)
        self.details_frame.pack_propagate(False)  # Fix height
        
        # Game ID and result
        self.game_title = ctk.CTkLabel(
            self.details_frame,
            text="Select a game to view details",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        )
        self.game_title.pack(pady=(15, 5))
        
        self.game_result = ctk.CTkLabel(
            self.details_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#AAAAAA"
        )
        self.game_result.pack(pady=(0, 5))
        
        # Board display in center
        self.board_frame = ctk.CTkFrame(right_frame, fg_color="#252525", corner_radius=5)
        self.board_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create board grid
        self.board_container = ctk.CTkFrame(self.board_frame, fg_color="transparent")
        self.board_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Create the 3x3 grid of cells
        self.cells = []
        for row in range(3):
            cell_row = []
            for col in range(3):
                cell = ctk.CTkButton(
                    self.board_container,
                    text="",
                    width=80,
                    height=80,
                    corner_radius=0,
                    font=ctk.CTkFont(size=24, weight="bold"),
                    fg_color="#333333",
                    hover_color="#333333",
                    border_width=1,
                    border_color="#555555",
                    state="disabled"
                )
                cell.grid(row=row, column=col, padx=2, pady=2)
                cell_row.append(cell)
            self.cells.append(cell_row)
        
        # Replay controls at bottom
        controls_frame = ctk.CTkFrame(right_frame, fg_color="#252525", corner_radius=5, height=80)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        controls_frame.pack_propagate(False)  # Fix height
        
        # Replay controls container
        replay_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        replay_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Move counter
        self.move_counter = ctk.CTkLabel(
            replay_frame,
            text="Move: 0/0",
            font=ctk.CTkFont(size=14),
            width=100
        )
        self.move_counter.pack(side=tk.LEFT, padx=20)
        
        # Replay buttons
        button_frame = ctk.CTkFrame(replay_frame, fg_color="transparent")
        button_frame.pack(side=tk.LEFT)
        
        # Create control buttons
        controls = [
            ("⏮", self._first_move, "#3E92CC"),  # First move
            ("⏪", self._prev_move, "#3E92CC"),   # Previous move
            ("▶", self._play_pause, "#4CAF50"),  # Play/Pause
            ("⏩", self._next_move, "#3E92CC"),   # Next move
            ("⏭", self._last_move, "#3E92CC")    # Last move
        ]
        
        for text, command, color in controls:
            btn = ctk.CTkButton(
                button_frame,
                text=text,
                command=command,
                font=ctk.CTkFont(size=16),
                width=40,
                height=40,
                fg_color=color,
                hover_color="#555555"
            )
            btn.pack(side=tk.LEFT, padx=5)
        
        # Speed control
        speed_frame = ctk.CTkFrame(replay_frame, fg_color="transparent")
        speed_frame.pack(side=tk.LEFT, padx=20)
        
        ctk.CTkLabel(
            speed_frame,
            text="Speed:",
            font=ctk.CTkFont(size=14)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.speed_var = tk.StringVar(value="1.0x")
        speed_options = ["0.5x", "1.0x", "2.0x", "3.0x"]
        speed_dropdown = ctk.CTkOptionMenu(
            speed_frame,
            values=speed_options,
            variable=self.speed_var,
            width=70
        )
        speed_dropdown.pack(side=tk.LEFT)
        speed_dropdown.set("1.0x")
        
        # Exit button at bottom
        exit_btn = ctk.CTkButton(
            self.window,
            text="Close",
            command=self.on_closing,
            font=ctk.CTkFont(size=14),
            fg_color="#E63946",
            hover_color="#C5313E",
            width=120
        )
        exit_btn.pack(pady=10)
        
        # Set up proper window close handling
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set up heartbeat updates to prevent force exit
        self._setup_heartbeat_checks()
    
    def _setup_heartbeat_checks(self):
        """Set up periodic heartbeat checks"""
        def update_heartbeat():
            if not hasattr(self, 'window') or not self.window.winfo_exists():
                return
            
            # Update application heartbeat
            update_app_heartbeat()
            
            # Schedule next update
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.after(5000, update_heartbeat)
        
        # Start heartbeat updates
        if hasattr(self, 'window') and self.window.winfo_exists():
            self.window.after(5000, update_heartbeat)
    
    def _load_history_data(self):
        """Load game history data from data manager"""
        try:
            # Update heartbeat immediately
            update_app_heartbeat()
            
            # Get game history from data manager
            data_manager = GameDataManager.get_instance()
            
            if data_manager:
                chunk_size = 50  # Process games in chunks to avoid UI freezes
                all_games = data_manager.get('game_history', {})
                
                # Update UI with total count
                total_games = len(all_games)
                if hasattr(self, 'window') and self.window.winfo_exists():
                    self.window.after(0, lambda: self._update_loading_status(f"Loading {total_games} games..."))
                
                # Process in chunks
                self.game_history = {}
                game_items = list(all_games.items())
                
                for i in range(0, len(game_items), chunk_size):
                    # Check if loading was cancelled
                    if self.loading_cancelled:
                        return
                        
                    # Process a chunk
                    chunk = dict(game_items[i:i+chunk_size])
                    self.game_history.update(chunk)
                    
                    # Update progress
                    progress = min(100, int((i + len(chunk)) / len(game_items) * 100))
                    if hasattr(self, 'window') and self.window.winfo_exists():
                        self.window.after(0, lambda p=progress: self._update_loading_status(f"Loading games... {p}%"))
                    
                    # Short sleep to allow UI to update
                    time.sleep(0.1)
                    
                    # Update heartbeat
                    update_app_heartbeat()
            else:
                self.game_history = {}
            
            # Update UI on main thread
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.after(0, self._update_games_list)
                
        except Exception as e:
            print(f"Error loading game history: {e}")
            # Show error on main thread
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.after(0, lambda: self._show_error(f"Error loading history: {e}"))
    
    def _update_loading_status(self, message):
        """Update the loading status message
        
        Args:
            message (str): Loading status message to display
        """
        if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
            self.loading_label.configure(text=message)
    
    def _update_games_list(self):
        """Update the games list with loaded history"""
        try:
            # Remove loading indicator
            if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
                self.loading_label.destroy()
            
            # Check if we have any games
            if not self.game_history:
                no_games_label = ctk.CTkLabel(
                    self.games_container,
                    text="No games found",
                    font=ctk.CTkFont(size=14),
                    text_color="#AAAAAA"
                )
                no_games_label.pack(pady=20)
                return
            
            # Apply initial filters to get games list
            self._apply_filters()
            
            # Mark history as loaded
            self.history_loaded = True
            
        except Exception as e:
            print(f"Error updating games list: {e}")
            self._show_error(f"Error updating games list: {e}")
    
    def _apply_filters_delayed(self, _=None):
        """Apply filters with a slight delay to prevent excessive updates"""
        try:
            # Update the moves label immediately
            self.moves_label.configure(text=str(int(self.moves_var.get())))
            
            # Cancel any existing delayed update
            if hasattr(self, '_filter_after_id'):
                try:
                    self.window.after_cancel(self._filter_after_id)
                except Exception:
                    pass
            
            # Schedule a new update
            if hasattr(self, 'window') and self.window.winfo_exists():
                self._filter_after_id = self.window.after(500, self._apply_filters)
                
        except Exception as e:
            print(f"Error in delayed filter: {e}")
            # Update heartbeat to prevent force exit
            update_app_heartbeat()
    
    def _apply_filters(self, _=None):
        """Apply filters to the game history"""
        try:
            # Update heartbeat
            update_app_heartbeat()
            
            if not self.game_history:
                return
            
            # Clear existing games list
            for widget in self.games_container.winfo_children():
                try:
                    widget.destroy()
                except Exception:
                    pass
            
            # Get filter values
            winner_filter = self.winner_var.get()
            max_moves = int(self.moves_var.get())
            sort_order = self.sort_var.get()
            
            # Apply winner filter - process in chunks for responsiveness
            filtered_games = []
            
            # Convert filter text to winner values
            winner_map = {
                "All": None,  # All games
                "Player X": 1,
                "Player O": 2,
                "Draw": 0,
                "Incomplete": -1  # Special case for None
            }
            
            target_winner = winner_map.get(winner_filter)
            
            # Create processing function that can be split across multiple UI events
            def process_games_chunk():
                nonlocal filtered_games
                
                # Process up to 100 games at a time
                items = list(self.game_history.items())
                chunk_size = 100
                processed = 0
                
                for game_id, game in items:
                    # Check if processing should be cancelled
                    if not hasattr(self, 'window') or not self.window.winfo_exists():
                        return
                    
                    winner = game.get('winner')
                    moves = game.get('moves', [])
                    
                    # Skip if more moves than allowed
                    if len(moves) > max_moves:
                        continue
                    
                    # Apply winner filter
                    if winner_filter == "All" or \
                       (winner_filter == "Player X" and winner == 1) or \
                       (winner_filter == "Player O" and winner == 2) or \
                       (winner_filter == "Draw" and winner == 0) or \
                       (winner_filter == "Incomplete" and winner is None):
                        filtered_games.append((game_id, game))
                    
                    processed += 1
                    if processed >= chunk_size:
                        # Schedule next chunk
                        if hasattr(self, 'window') and self.window.winfo_exists():
                            self.window.after(1, process_games_chunk)
                        return
                
                # All games processed, continue with sorting and display
                finish_filtering()
            
            # Function to sort and display games after filtering
            def finish_filtering():
                nonlocal filtered_games
                
                # Apply sorting
                try:
                    if sort_order == "Newest First":
                        filtered_games.sort(key=lambda g: g[1].get('timestamp', g[0]), reverse=True)
                    elif sort_order == "Oldest First":
                        filtered_games.sort(key=lambda g: g[1].get('timestamp', g[0]))
                    elif sort_order == "Most Moves":
                        filtered_games.sort(key=lambda g: len(g[1].get('moves', [])), reverse=True)
                    elif sort_order == "Fewest Moves":
                        filtered_games.sort(key=lambda g: len(g[1].get('moves', [])))
                except Exception as e:
                    print(f"Error sorting games: {e}")
                
                # Store filtered games
                self.filtered_games = filtered_games
                
                # Display games in batches
                display_games_batch(0, 50)  # Start with first 50
            
            # Function to display games in batches
            def display_games_batch(start_idx, batch_size):
                if not hasattr(self, 'window') or not self.window.winfo_exists():
                    return
                
                if not self.filtered_games:
                    no_games_label = ctk.CTkLabel(
                        self.games_container,
                        text="No games match the filters",
                        font=ctk.CTkFont(size=14),
                        text_color="#AAAAAA"
                    )
                    no_games_label.pack(pady=20)
                    return
                
                # Display a batch of games
                end_idx = min(start_idx + batch_size, len(self.filtered_games))
                
                for i in range(start_idx, end_idx):
                    game_id, game = self.filtered_games[i]
                    create_game_item(game_id, game, i)
                
                # If more games to display, schedule next batch
                if end_idx < len(self.filtered_games):
                    if hasattr(self, 'window') and self.window.winfo_exists():
                        self.window.after(10, lambda: display_games_batch(end_idx, batch_size))
                else:
                    # Update heartbeat when done
                    update_app_heartbeat()
            
            # Function to create a game item in the list
            def create_game_item(game_id, game, index):
                if not hasattr(self, 'games_container') or not self.games_container.winfo_exists():
                    return
                
                # Get game details
                winner = game.get('winner')
                moves = game.get('moves', [])
                
                # Format winner text
                if winner == 1:
                    winner_text = "X Wins"
                    winner_color = "#4F85CC"  # Blue for X
                elif winner == 2:
                    winner_text = "O Wins"
                    winner_color = "#FF5C8D"  # Pink for O
                elif winner == 0:
                    winner_text = "Draw"
                    winner_color = "#DDDDDD"  # White for draw
                else:
                    winner_text = "Incomplete"
                    winner_color = "#AAAAAA"  # Gray for incomplete
                
                # Create game item
                game_frame = ctk.CTkFrame(
                    self.games_container,
                    fg_color="#333333",
                    corner_radius=5,
                    height=60
                )
                game_frame.pack(fill=tk.X, padx=5, pady=5)
                game_frame.pack_propagate(False)  # Fix height
                
                # Create clickable area for selection
                game_btn = ctk.CTkButton(
                    game_frame,
                    text="",
                    fg_color="transparent",
                    hover_color="#444444",
                    corner_radius=5,
                    command=lambda gid=game_id: self._select_game(gid)
                )
                game_btn.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Game ID label
                date_part = game_id.split('_')[0] if '_' in game_id else game_id
                time_part = game_id.split('_')[1] if '_' in game_id and len(game_id.split('_')) > 1 else ""
                
                # Format date/time if possible
                try:
                    formatted_date = f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    formatted_time = f"{time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}" if len(time_part) >= 6 else time_part
                    id_text = f"{formatted_date} {formatted_time}"
                except Exception:
                    id_text = game_id
                
                id_label = ctk.CTkLabel(
                    game_frame,
                    text=id_text,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w"
                )
                id_label.place(x=10, y=10)
                
                # Winner and moves
                result_text = f"{winner_text} • {len(moves)} moves"
                result_label = ctk.CTkLabel(
                    game_frame,
                    text=result_text,
                    text_color=winner_color,
                    font=ctk.CTkFont(size=12),
                    anchor="w"
                )
                result_label.place(x=10, y=35)
            
            # Start the chunked processing
            process_games_chunk()
            
        except Exception as e:
            print(f"Error applying filters: {e}")
            self._show_error(f"Error filtering games: {e}")
            # Update heartbeat to prevent force exit
            update_app_heartbeat()
    
    def _select_game(self, game_id):
        """Select a game to view"""
        try:
            # Store current game
            self.current_game_id = game_id
            self.current_move_index = 0
            
            # Stop any running animation
            self.animation_running = False
            
            # Get game data
            game = self.game_history.get(game_id, {})
            winner = game.get('winner')
            moves = game.get('moves', [])
            
            # Update game title
            date_part = game_id.split('_')[0] if '_' in game_id else game_id
            time_part = game_id.split('_')[1] if '_' in game_id and len(game_id.split('_')) > 1 else ""
            
            # Format date/time if possible
            try:
                formatted_date = f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"
                formatted_time = f"{time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}" if len(time_part) >= 6 else time_part
                id_text = f"Game: {formatted_date} {formatted_time}"
            except Exception:
                id_text = f"Game: {game_id}"
            
            self.game_title.configure(text=id_text)
            
            # Format winner text
            if winner == 1:
                result_text = "Result: Player X Wins"
            elif winner == 2:
                result_text = "Result: Player O Wins"
            elif winner == 0:
                result_text = "Result: Draw"
            else:
                result_text = "Result: Game Incomplete"
            
            self.game_result.configure(text=result_text)
            
            # Update move counter
            self.move_counter.configure(text=f"Move: 0/{len(moves)}")
            
            # Clear board
            self._clear_board()
            
            # If there are moves, highlight the first game in the list
            if self.filtered_games:
                # Find index of current game in filtered list
                selected_index = -1
                for i, (fgid, _) in enumerate(self.filtered_games):
                    if fgid == game_id:
                        selected_index = i
                        break
                
                # Highlight the selected game
                try:
                    for i, child in enumerate(self.games_container.winfo_children()):
                        if i == selected_index:
                            child.configure(fg_color="#3E92CC")
                        else:
                            child.configure(fg_color="#333333")
                except Exception as e:
                    print(f"Error highlighting game: {e}")
            
            # Update heartbeat
            update_app_heartbeat()
            
        except Exception as e:
            print(f"Error selecting game: {e}")
            # Update heartbeat to prevent force exit
            update_app_heartbeat()
    
    def _clear_board(self):
        """Clear the game board"""
        try:
            for row in range(3):
                for col in range(3):
                    if hasattr(self, 'cells') and len(self.cells) > row and len(self.cells[row]) > col:
                        self.cells[row][col].configure(
                            text="",
                            fg_color="#333333"
                        )
        except Exception as e:
            print(f"Error clearing board: {e}")
    
    def _update_board_display(self):
        """Update the board display for current move index"""
        try:
            if not self.current_game_id:
                return
            
            # Get game data
            game = self.game_history.get(self.current_game_id, {})
            moves = game.get('moves', [])
            
            # Clear the board first
            self._clear_board()
            
            # Show moves up to current index
            for i in range(self.current_move_index):
                if i < len(moves):
                    move = moves[i]
                    row = move.get('row', 0)
                    col = move.get('col', 0)
                    player = move.get('player', 1)
                    
                    # Update cell if it exists
                    if hasattr(self, 'cells') and len(self.cells) > row and len(self.cells[row]) > col:
                        self.cells[row][col].configure(
                            text="X" if player == 1 else "O",
                            text_color="#4F85CC" if player == 1 else "#FF5C8D"
                        )
            
            # Update move counter
            if hasattr(self, 'move_counter'):
                self.move_counter.configure(text=f"Move: {self.current_move_index}/{len(moves)}")
                
            # Update heartbeat
            update_app_heartbeat()
            
        except Exception as e:
            print(f"Error updating board: {e}")
            # Update heartbeat to prevent force exit
            update_app_heartbeat()
    
    def _first_move(self):
        """Go to first move"""
        self.animation_running = False
        self.current_move_index = 0
        self._update_board_display()
    
    def _last_move(self):
        """Go to last move"""
        if not self.current_game_id:
            return
        
        self.animation_running = False
        game = self.game_history.get(self.current_game_id, {})
        moves = game.get('moves', [])
        self.current_move_index = len(moves)
        self._update_board_display()
    
    def _prev_move(self):
        """Go to previous move"""
        self.animation_running = False
        if self.current_move_index > 0:
            self.current_move_index -= 1
            self._update_board_display()
    
    def _next_move(self):
        """Go to next move"""
        if not self.current_game_id:
            return
        
        self.animation_running = False
        game = self.game_history.get(self.current_game_id, {})
        moves = game.get('moves', [])
        
        if self.current_move_index < len(moves):
            self.current_move_index += 1
            self._update_board_display()
    
    def _play_pause(self):
        """Play or pause the animation"""
        if not self.current_game_id:
            return
        
        # Toggle animation state
        self.animation_running = not self.animation_running
        
        if self.animation_running:
            self._animate_replay()
    
    def _animate_replay(self):
        """Animate the game replay"""
        try:
            if not self.animation_running or not self.current_game_id:
                return
            
            # Get game data
            game = self.game_history.get(self.current_game_id, {})
            moves = game.get('moves', [])
            
            # If at end, go back to start
            if self.current_move_index >= len(moves):
                self.current_move_index = 0
                self._update_board_display()
            
            # Go to next move
            if self.current_move_index < len(moves):
                self.current_move_index += 1
                self._update_board_display()
            
            # Schedule next animation step if still running
            if self.animation_running and hasattr(self, 'window') and self.window.winfo_exists():
                # Calculate delay based on speed
                try:
                    speed_str = self.speed_var.get()
                    speed = float(speed_str.replace('x', ''))
                except Exception:
                    speed = 1.0
                
                delay = int(1000 / speed)  # Faster speed = shorter delay
                self.window.after(delay, self._animate_replay)
                
        except Exception as e:
            print(f"Error animating replay: {e}")
            self.animation_running = False
            # Update heartbeat to prevent force exit
            update_app_heartbeat()
    
    def _show_error(self, message):
        """Show an error message
        
        Args:
            message (str): Error message to display
        """
        try:
            # Clear games container
            if hasattr(self, 'games_container') and self.games_container.winfo_exists():
                for widget in self.games_container.winfo_children():
                    try:
                        widget.destroy()
                    except Exception:
                        pass
            
            # Show error message
            if hasattr(self, 'games_container') and self.games_container.winfo_exists():
                error_label = ctk.CTkLabel(
                    self.games_container,
                    text=message,
                    font=ctk.CTkFont(size=14),
                    text_color="#E63946"
                )
                error_label.pack(pady=20)
                
            # Update heartbeat
            update_app_heartbeat()
            
        except Exception as e:
            print(f"Error showing error message: {e}")
    
    def on_closing(self):
        """Handle window closing event"""
        try:
            # Stop any running animation
            self.animation_running = False
            
            # Cancel loading if still in progress
            self.loading_cancelled = True
            
            # Clear references to help with garbage collection
            self.game_history = {}
            self.filtered_games = []
            
            # Update heartbeat before closing
            update_app_heartbeat()
            
            # Destroy window
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.destroy()
                
        except Exception as e:
            print(f"Error during closing: {e}")
            # Force destroy window even on error
            try:
                if hasattr(self, 'window') and self.window.winfo_exists():
                    self.window.destroy()
            except Exception:
                pass
    
    def run(self):
        """Run the game history viewer"""
        try:
            # Set up initial heartbeat
            update_app_heartbeat()
            
            if hasattr(self, 'window') and self.window.winfo_exists():
                try:
                    # Use a safer mainloop approach
                    self._safe_mainloop()
                except Exception as e:
                    print(f"Error in mainloop: {e}")
        except Exception as e:
            print(f"Error running history viewer: {e}")
    
    def _safe_mainloop(self):
        """A safer version of mainloop with periodic heartbeats"""
        def ensure_heartbeat():
            if not hasattr(self, 'window') or not self.window.winfo_exists():
                return
                
            # Update heartbeat
            update_app_heartbeat()
            
            # Process events explicitly to prevent freezing
            try:
                self.window.update()
            except Exception:
                pass
                
            # Schedule next heartbeat
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.after(500, ensure_heartbeat)
        
        # Start regular heartbeats
        if hasattr(self, 'window') and self.window.winfo_exists():
            self.window.after(500, ensure_heartbeat)
            
            # Enter the mainloop
            self.window.mainloop()

# Testing function
if __name__ == "__main__":
    viewer = GameHistoryViewer()
    viewer.run()
