import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import numpy as np
import os
import datetime
import json
from game import TicTacToeGame
from move_tracker import GameMoveTracker, MoveList, MoveNode

class GameHistoryViewer:
    """Class for viewing previous game data using the move tracker system"""
    
    def __init__(self, parent=None):
        """Initialize the game history viewer
        
        Args:
            parent: Optional parent window
        """
        # Create window
        self.window = ctk.CTkToplevel(parent) if parent else ctk.CTk()
        self.window.title("Game History Viewer")
        self.window.geometry("800x600")
        self.window.configure(fg_color="#1E1E1E")
        
        # Game data
        self.games = {}
        self.selected_game_id = None
        self.selected_move = 0
        self.current_board = np.zeros((3, 3), dtype=int)
        
        # Player symbols and colors (same as main app for consistency)
        self.player_symbols = {
            1: "X",  # Player 1: X
            2: "O"   # Player 2: O
        }
        
        # Player colors
        self.player_colors = {
            1: {"fg": "#4F85CC", "bg": "#2D5F8B"},  # X: Blue
            2: {"fg": "#FF5C8D", "bg": "#8B2D5F"}   # O: Pink
        }
        
        # Add playback control variables
        self.is_playing = False
        self.playback_speed = 1.0  # seconds between moves
        self.playback_job = None
        self.previous_move_pos = None  # Track previous move position
        
        self.setup_ui()
        self.load_games()
    
    def setup_ui(self):
        """Set up the viewer UI"""
        # Main container with padding
        self.main_frame = ctk.CTkFrame(self.window, fg_color="#252525", corner_radius=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title section
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.pack(pady=(15, 5), fill=tk.X)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Game History Viewer", 
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color="#3E92CC"
        )
        title_label.pack()
        
        # Separator
        separator = ctk.CTkFrame(self.main_frame, height=2, fg_color="#3E92CC")
        separator.pack(fill=tk.X, padx=50, pady=(2, 15))
        
        # Split into two panels (games list and game details)
        content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Games list
        left_panel = ctk.CTkFrame(content_frame, fg_color="#2A2A2A", corner_radius=10, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # Games list header
        games_header = ctk.CTkLabel(
            left_panel,
            text="Games",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            text_color="#DDDDDD"
        )
        games_header.pack(pady=(10, 5))
        
        # Games list
        self.games_list_frame = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.games_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        refresh_btn = ctk.CTkButton(
            left_panel,
            text="Refresh Games List",
            command=self.load_games,
            font=ctk.CTkFont(size=14),
            fg_color="#4CAF50",
            hover_color="#3E8E41",
            corner_radius=8,
            height=32
        )
        refresh_btn.pack(pady=(5, 15), padx=10, fill=tk.X)
        
        # Right panel - Game details
        right_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Game info section
        game_info_frame = ctk.CTkFrame(right_panel, fg_color="#2A2A2A", corner_radius=10)
        game_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.game_info_label = ctk.CTkLabel(
            game_info_frame,
            text="Select a game to view details",
            font=ctk.CTkFont(size=14),
            text_color="#CCCCCC"
        )
        self.game_info_label.pack(pady=10)
        
        # Game board
        board_frame = ctk.CTkFrame(right_panel, fg_color="#2A2A2A", corner_radius=10)
        board_frame.pack(fill=tk.BOTH, expand=True)
        
        self.board_display = ctk.CTkFrame(board_frame, fg_color="transparent")
        self.board_display.pack(expand=True, pady=20, padx=20)
        
        self.cells = [[None for _ in range(3)] for _ in range(3)]
        
        for i in range(3):
            for j in range(3):
                cell = ctk.CTkButton(
                    self.board_display, 
                    text="",  # Start with empty text
                    width=80,
                    height=80,
                    font=ctk.CTkFont(size=36, weight="bold"),
                    fg_color="#383838",
                    text_color="#FFFFFF",
                    corner_radius=5,
                    state="disabled"  # All cells are disabled in viewer mode
                )
                cell.grid(row=i, column=j, padx=5, pady=5)
                self.cells[i][j] = cell
        
        # Add move info label below the board
        self.move_info_label = ctk.CTkLabel(
            board_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#EEEEEE",
            height=30
        )
        self.move_info_label.pack(pady=(5, 10))
        
        # Move navigation controls
        controls_frame = ctk.CTkFrame(right_panel, fg_color="#2A2A2A", corner_radius=10, height=60)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        nav_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        nav_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # First move button
        self.first_move_btn = ctk.CTkButton(
            nav_frame,
            text="⏮",  # First move icon
            command=self.show_first_move,
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            width=40
        )
        self.first_move_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Previous move button
        self.prev_move_btn = ctk.CTkButton(
            nav_frame,
            text="◀",
            command=self.show_previous_move,
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            width=40
        )
        self.prev_move_btn.pack(side=tk.LEFT, padx=5)
        
        # Play/Pause button
        self.play_btn = ctk.CTkButton(
            nav_frame,
            text="▶",  # Play icon
            command=self.toggle_playback,
            font=ctk.CTkFont(size=14),
            fg_color="#4CAF50",
            hover_color="#3E8E41",
            width=40
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        # Next move button
        self.next_move_btn = ctk.CTkButton(
            nav_frame,
            text="▶",
            command=self.show_next_move,
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            width=40
        )
        self.next_move_btn.pack(side=tk.LEFT, padx=5)
        
        # Last move button
        self.last_move_btn = ctk.CTkButton(
            nav_frame,
            text="⏭",  # Last move icon
            command=self.show_last_move,
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            width=40
        )
        self.last_move_btn.pack(side=tk.LEFT, padx=5)
        
        self.move_label = ctk.CTkLabel(
            nav_frame,
            text="Move: 0/0",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100
        )
        self.move_label.pack(side=tk.LEFT, padx=10)
        
        # Playback speed control
        speed_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        speed_frame.pack(pady=(0, 10), padx=20, fill=tk.X)
        
        speed_label = ctk.CTkLabel(
            speed_frame,
            text="Playback Speed:",
            font=ctk.CTkFont(size=12),
            width=100
        )
        speed_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.speed_var = tk.DoubleVar(value=1.0)
        
        speed_slider = ctk.CTkSlider(
            speed_frame,
            from_=0.5,
            to=3.0,
            variable=self.speed_var,
            width=150
        )
        speed_slider.pack(side=tk.LEFT, padx=5)
        
        self.speed_label = ctk.CTkLabel(
            speed_frame,
            text="1.0x",
            font=ctk.CTkFont(size=12),
            width=40
        )
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        # Update speed label when slider changes
        self.speed_var.trace_add("write", self.update_speed_label)
        
        # Initial update of UI state
        self.update_ui_state()
    
    def load_games(self):
        """Load game history from the central CSV file or JSON files"""
        # Clear the games list
        for widget in self.games_list_frame.winfo_children():
            widget.destroy()
        
        # Create enhanced loading screen
        loading_frame = ctk.CTkFrame(
            self.games_list_frame,
            fg_color="#333333",
            corner_radius=10
        )
        loading_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        loading_title = ctk.CTkLabel(
            loading_frame,
            text="Loading Game History",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#3E92CC"
        )
        loading_title.pack(pady=(20, 10))
        
        # Add a more descriptive status message
        self.loading_status = ctk.CTkLabel(
            loading_frame,
            text="Initializing data loader...",
            font=ctk.CTkFont(size=14),
            text_color="#CCCCCC"
        )
        self.loading_status.pack(pady=5)
        
        # Add a progress bar
        self.loading_progress = ctk.CTkProgressBar(
            loading_frame,
            width=300,
            height=15,
            corner_radius=5,
            mode="indeterminate"
        )
        self.loading_progress.pack(pady=15)
        self.loading_progress.start()
        
        # Add stats display that will update during loading
        self.loading_stats = ctk.CTkLabel(
            loading_frame,
            text="Games: 0 | X Wins: 0 | O Wins: 0 | Draws: 0",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA"
        )
        self.loading_stats.pack(pady=5)
        
        # Add cancel button for long-running operations
        cancel_btn = ctk.CTkButton(
            loading_frame,
            text="Cancel",
            command=self.cancel_loading,
            font=ctk.CTkFont(size=13),
            fg_color="#E63946",
            hover_color="#C5313E",
            width=120,
            height=32
        )
        cancel_btn.pack(pady=15)
        
        # Force UI update to show loading screen
        self.window.update_idletasks()
        
        # Initialize loading state
        self.is_loading = True
        self.cancel_loading_requested = False
        
        # Start loading in a separate thread to keep UI responsive
        import threading
        self.loading_thread = threading.Thread(target=self._load_games_async)
        self.loading_thread.daemon = True
        self.loading_thread.start()
        
        # Start checking for completion
        self.window.after(100, self._check_loading_complete)

    def _load_games_async(self):
        """Load game data in background thread with move tracker integration"""
        try:
            # Update status via the main thread
            self.window.after(0, lambda: self.loading_status.configure(text="Looking for JSON game files..."))
            
            # Try to use optimized data loading with move tracker support
            try:
                from game_data_integration import GameDataIntegration
                
                # Create data manager with progress callback
                self.window.after(0, lambda: self.loading_status.configure(text="Initializing data processor..."))
                
                # Progress update function that safely updates UI from background thread
                def update_progress(stage, progress=None, stats=None):
                    if self.cancel_loading_requested:
                        return False  # Signal to stop loading
                    
                    # Update UI in main thread
                    self.window.after(0, lambda: self.loading_status.configure(text=stage))
                    
                    # Update progress bar if value provided
                    if progress is not None:
                        if progress < 0:  # Indeterminate
                            self.window.after(0, self.loading_progress.start)
                        else:
                            self.window.after(0, lambda: self.loading_progress.stop())
                            self.window.after(0, lambda: self.loading_progress.set(progress))
                    
                    # Update stats if provided
                    if stats:
                        stats_text = f"Games: {stats.get('total_games', 0)} | "
                        stats_text += f"X Wins: {stats.get('wins_player1', 0)} | "
                        stats_text += f"O Wins: {stats.get('wins_player2', 0)} | "
                        stats_text += f"Draws: {stats.get('draws', 0)}"
                        self.window.after(0, lambda: self.loading_stats.configure(text=stats_text))
                    
                    return True  # Continue loading
                
                # Create data integration with progress reporting
                data_manager = GameDataIntegration(use_cache=True, progress_callback=update_progress)
                
                # Set loading progress to determinate mode once structure is loaded
                self.window.after(0, lambda: self.loading_progress.stop())
                self.window.after(0, lambda: self.loading_progress.configure(mode="determinate"))
                self.window.after(0, lambda: self.loading_progress.set(0.25))
                
                # Get games dictionary
                self.games = data_manager.get_all_games()
                self.window.after(0, lambda: self.loading_progress.set(0.75))
                
                # Store data manager for potential further use
                self.data_manager = data_manager
                
                # Update final stats
                stats = data_manager.get_statistics()
                update_progress("Data processing complete", 1.0, stats)
                
            except ImportError:
                # Fall back to direct JSON and CSV loading with move tracker support
                self.window.after(0, lambda: self.loading_status.configure(
                    text="Loading games directly from JSON and CSV..."
                ))
                self.games = self.load_games_with_move_tracker()
                
            # Loading complete
            self.is_loading = False
            
        except Exception as e:
            print(f"Error in background loading: {e}")
            import traceback
            traceback.print_exc()
            
            # Update UI with error
            self.window.after(0, lambda: self.loading_status.configure(
                text=f"Error loading data: {str(e)}",
                text_color="#E63946"
            ))
            
            # Stop progress animation
            self.window.after(0, self.loading_progress.stop)
            
            # Flag as no longer loading
            self.is_loading = False

    def load_games_with_move_tracker(self):
        """Load games using move tracker from JSON files first, then CSV if needed"""
        games = {}
        
        try:
            # First try to load from JSON files which should have move tracker data
            json_dir = os.path.join(os.path.dirname(__file__), "game_data", TicTacToeGame.GAME_JSON_DIR)
            
            if os.path.exists(json_dir):
                json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
                print(f"Found {len(json_files)} JSON game files")
                
                # Update UI
                self.window.after(0, lambda: self.loading_status.configure(
                    text=f"Loading {len(json_files)} games from JSON..."
                ))
                self.window.after(0, lambda: self.loading_progress.set(0.2))
                
                for i, json_file in enumerate(json_files):
                    if self.cancel_loading_requested:
                        break
                        
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
                            # Create game entry with move tracker data
                            games[game_id] = {
                                'move_tracker': move_tracker,
                                'winner': game_data.get('winner'),
                                'timestamp': game_data.get('timestamp'),
                                'moves': []  # Legacy format for compatibility
                            }
                            
                            # Also convert to legacy format for backwards compatibility
                            all_moves = moves_data.get('all_moves', [])
                            for move in all_moves:
                                if move.get('board_state'):
                                    row = move.get('row')
                                    col = move.get('col')
                                    player = move.get('player')
                                    board = np.array(move.get('board_state'))
                                    move_number = move.get('move_number')
                                    
                                    games[game_id]['moves'].append({
                                        'position': (row, col),
                                        'player': player,
                                        'board': board,
                                        'move_number': move_number,
                                        'winner': game_data.get('winner') if len(games[game_id]['moves']) == len(all_moves) - 1 else None
                                    })
                    except Exception as e:
                        print(f"Error loading game from JSON {json_file}: {e}")
                        continue
                    
                    # Update progress
                    if i % 5 == 0:  # Update every 5 games to avoid too many UI updates
                        progress = 0.2 + (0.6 * (i / len(json_files)))
                        self.window.after(0, lambda p=progress: self.loading_progress.set(p))
                
                # If we loaded games from JSON, we can return now
                if games and not self.cancel_loading_requested:
                    # Update UI for success
                    self.window.after(0, lambda: self.loading_progress.set(1.0))
                    self.window.after(0, lambda: self.loading_status.configure(
                        text=f"Successfully loaded {len(games)} games from JSON"
                    ))
                    
                    return games
            
            # If no JSON games were loaded, try CSV as fallback
            self.window.after(0, lambda: self.loading_status.configure(
                text="No JSON games found, falling back to CSV..."
            ))
            self.window.after(0, lambda: self.loading_progress.set(0.4))
            
            # Load from CSV and convert to move tracker format
            csv_games = TicTacToeGame.load_game_history_from_csv()
            
            if not self.cancel_loading_requested and csv_games:
                # Convert each CSV game to include move tracker
                self.window.after(0, lambda: self.loading_status.configure(
                    text=f"Converting {len(csv_games)} CSV games to move tracker format..."
                ))
                
                for i, (game_id, game) in enumerate(csv_games.items()):
                    if self.cancel_loading_requested:
                        break
                        
                    # Create a new move tracker for this game
                    move_tracker = GameMoveTracker()
                    
                    # Add each move to the tracker
                    for move in game.get('moves', []):
                        position = move.get('position')
                        player = move.get('player')
                        board = move.get('board')
                        
                        if position and player is not None and board is not None:
                            row, col = position
                            move_tracker.add_move(row, col, player, board)
                    
                    # Add game with move tracker
                    games[game_id] = {
                        'move_tracker': move_tracker,
                        'winner': game.get('winner'),
                        'timestamp': game.get('timestamp'),
                        'moves': game.get('moves', [])  # Keep legacy format for compatibility
                    }
                    
                    # Update progress
                    if i % 5 == 0:  # Update every 5 games
                        progress = 0.4 + (0.6 * (i / len(csv_games)))
                        self.window.after(0, lambda p=progress: self.loading_progress.set(p))
            
            # Final update
            self.window.after(0, lambda: self.loading_progress.set(1.0))
            self.window.after(0, lambda: self.loading_status.configure(
                text=f"Successfully loaded {len(games)} games"
            ))
            
            return games
            
        except Exception as e:
            print(f"Error in move tracker game loading: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _check_loading_complete(self):
        """Check if background loading is complete and update UI if so"""
        if not self.is_loading:
            # Loading complete, update UI
            if self.cancel_loading_requested:
                # Don't update UI if loading was canceled
                self.cancel_loading_requested = False
                return
            
            # Stop progress bar
            self.loading_progress.stop()
            
            # Clear loading screen
            for widget in self.games_list_frame.winfo_children():
                widget.destroy()
            
            # Finalize UI setup with loaded data
            if not self.games:
                no_games_label = ctk.CTkLabel(
                    self.games_list_frame,
                    text="No games found in history",
                    font=ctk.CTkFont(size=14),
                    text_color="#CCCCCC"
                )
                no_games_label.pack(pady=10)
                return
            
            # Sort game IDs chronologically
            game_ids = sorted(
                self.games.keys(), 
                key=lambda gid: self.games[gid].get('timestamp', gid),
                reverse=True
            )
            
            # Add filter UI
            self.add_filter_controls()
            
            # Populate with filtered list (using pagination)
            self.current_page = 0
            self.page_size = 20  # Number of games per page
            self.populate_games_list(game_ids, True)
            
        else:
            # Still loading, check again after a delay
            self.window.after(100, self._check_loading_complete)

    def cancel_loading(self):
        """Cancel the current loading operation"""
        if self.is_loading:
            self.cancel_loading_requested = True
            self.loading_status.configure(text="Canceling...")
            
            # Stop and reset any UI elements
            self.is_loading = False
            
            # Clear loading UI after a short delay
            self.window.after(500, lambda: self._reset_after_cancel())

    def _reset_after_cancel(self):
        """Reset UI after canceling load operation"""
        for widget in self.games_list_frame.winfo_children():
            widget.destroy()
        
        # Show message
        canceled_msg = ctk.CTkLabel(
            self.games_list_frame,
            text="Loading canceled",
            font=ctk.CTkFont(size=14),
            text_color="#FFC107"
        )
        canceled_msg.pack(pady=10)
        
        # Add reload button
        reload_btn = ctk.CTkButton(
            self.games_list_frame,
            text="Reload Games",
            command=self.load_games,
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            corner_radius=8,
            height=35
        )
        reload_btn.pack(pady=15)

    def load_games_standard(self):
        """Legacy fallback loading method without optimization"""
        try:
            self.window.after(0, lambda: self.loading_status.configure(text="Loading game history from CSV..."))
            return TicTacToeGame.load_game_history_from_csv()
        except Exception as e:
            print(f"Error in standard loading: {e}")
            return {}

    def select_game(self, game_id):
        """Select a game to view using move tracker
        
        Args:
            game_id (str): ID of the game to view
        """
        self.selected_game_id = game_id
        self.selected_move = 0
        
        # Reset board view
        self.current_board = np.zeros((3, 3), dtype=int)
        self.update_board_display()
        
        # Update game info
        if game_id in self.games:
            game = self.games[game_id]
            
            # Format date from game_id
            try:
                date_str = f"{game_id[:4]}-{game_id[4:6]}-{game_id[6:8]}"
                time_str = f"{game_id[9:11]}:{game_id[11:13]}:{game_id[13:15]}"
                date_display = f"{date_str} {time_str}"
            except:
                date_display = game_id
            
            # Get winner info using move tracker if available
            if 'move_tracker' in game:
                move_tracker = game['move_tracker']
                winner = game.get('winner')
                move_count = move_tracker.all_moves.length
                
                # Reset move tracker to start position for navigation
                if move_tracker.all_moves.head:
                    move_tracker.all_moves.goto_start()
            else:
                # Fall back to legacy format
                winner = game.get('winner')
                move_count = len(game.get('moves', []))
            
            if winner:
                winner_text = f"Winner: Player {winner} ({self.player_symbols[winner]})"
            else:
                winner_text = "Draw" if move_count == 9 else "Incomplete"
            
            # Add debug button below game info
            if not hasattr(self, 'debug_btn'):
                self.debug_btn = ctk.CTkButton(
                    self.game_info_label.master,
                    text="Debug Info",
                    command=self.show_debug_info,
                    font=ctk.CTkFont(size=12),
                    fg_color="#555555",
                    hover_color="#666666",
                    corner_radius=4,
                    height=25,
                    width=100
                )
                self.debug_btn.pack(pady=(0, 5))
            else:
                self.debug_btn.pack(pady=(0, 5))
            
            # Update game info text
            self.game_info_label.configure(
                text=f"Game: {date_display}\n{winner_text}\nMoves: {move_count}"
            )
            
            # Update move label
            self.move_label.configure(text=f"Move: 0/{move_count}")
        
        # Update UI state
        self.update_ui_state()

    def show_debug_info(self):
        """Show a popup with detailed move data for debugging"""
        if not self.selected_game_id or self.selected_game_id not in self.games:
            return
        
        game = self.games[self.selected_game_id]
        
        # Create popup window
        debug_window = ctk.CTkToplevel(self.window)
        debug_window.title(f"Debug Info - Game {self.selected_game_id}")
        debug_window.geometry("700x500")
        debug_window.configure(fg_color="#252525")
        
        # Disable initially to prevent interaction with window during setup
        debug_window.withdraw()
        
        # Main frame
        main_frame = ctk.CTkFrame(debug_window, fg_color="#2A2A2A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Game ID and winner info
        header_frame = ctk.CTkFrame(main_frame, fg_color="#333333", corner_radius=5)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add file path info for debugging
        csv_path = os.path.join(os.path.dirname(__file__), "game_data", TicTacToeGame.GAME_DATA_FILE)
        csv_info = ctk.CTkLabel(
            header_frame,
            text=f"CSV Path: {csv_path}",
            font=ctk.CTkFont(size=10),
            text_color="#AAAAAA"
        )
        csv_info.pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        # Rest of the header
        header_label = ctk.CTkLabel(
            header_frame,
            text=f"Game ID: {self.selected_game_id}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#EEEEEE"
        )
        header_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # Move count
        move_count = len(game.get('moves', []))
        move_count_label = ctk.CTkLabel(
            header_frame,
            text=f"Total Moves: {move_count}",
            font=ctk.CTkFont(size=12),
            text_color="#DDDDDD"
        )
        move_count_label.pack(anchor=tk.W, padx=10, pady=(0, 5))
        
        winner = game.get('winner')
        winner_text = f"Winner: Player {winner} ({self.player_symbols[winner]})" if winner in [1, 2] else (
                      "Result: Draw" if winner == 0 else "Result: Incomplete")
        
        winner_color = self.player_colors[winner]["fg"] if winner in [1, 2] else (
                       "#FFC107" if winner == 0 else "#CCCCCC")
        
        result_label = ctk.CTkLabel(
            header_frame,
            text=winner_text,
            font=ctk.CTkFont(size=14),
            text_color=winner_color
        )
        result_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # Fix bug in empty games
        moves = game.get('moves', [])
        if not moves:
            empty_msg = ctk.CTkLabel(
                main_frame,
                text="No moves found for this game. The data may be corrupted.",
                font=ctk.CTkFont(size=16),
                text_color="#E63946"
            )
            empty_msg.pack(pady=50)
            
            # Skip the rest of the move display for empty games
            close_btn = ctk.CTkButton(
                main_frame,
                text="Close",
                command=debug_window.destroy,
                font=ctk.CTkFont(size=14),
                fg_color="#E63946",
                hover_color="#C5313E",
                height=35
            )
            close_btn.pack(pady=15)
            
            # Function to make window modal safely after it's visible
            def make_modal():
                try:
                    debug_window.deiconify()
                    debug_window.focus_force()
                    debug_window.update()
                    try:
                        debug_window.grab_set()
                    except Exception:
                        pass
                except Exception as e:
                    print(f"Error making debug window modal: {e}")
            
            debug_window.after(100, make_modal)
            debug_window.transient(self.window)
            return

        # Continue with move data display for non-empty games
        # Move data table
        moves_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        moves_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Table header
        header_bg = "#333333"
        header_row = ctk.CTkFrame(moves_frame, fg_color=header_bg, height=30)
        header_row.pack(fill=tk.X, pady=(0, 5))
        header_row.pack_propagate(False)
        
        cols = ["Move #", "Player", "Position", "Board State", "Winner"]
        col_widths = [60, 80, 100, 300, 80]
        
        for i, (col, width) in enumerate(zip(cols, col_widths)):
            label = ctk.CTkLabel(
                header_row, 
                text=col,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width,
                anchor="w"
            )
            label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # Move data - ensure we properly sort moves by move number
        moves = sorted(game.get('moves', []), key=lambda m: m.get('move_number', 0) 
                                                        if isinstance(m.get('move_number', 0), int) 
                                                        else 0)
        
        # Debug info before populating moves
        print(f"Game ID: {self.selected_game_id}")
        print(f"Total moves: {len(moves)}")
        
        for i, move in enumerate(moves):
            # Add debug print for move data
            print(f"Move {i+1}: {move.get('position')}, Player: {move.get('player')}")
            
            row_bg = "#2D2D2D" if i % 2 == 0 else "#353535"
            move_row = ctk.CTkFrame(moves_frame, fg_color=row_bg, height=40)
            move_row.pack(fill=tk.X, pady=1)
            move_row.pack_propagate(False)
            
            # Move number
            move_number = move.get('move_number', i+1)
            if not isinstance(move_number, int):
                move_number = i+1
                
            move_num_label = ctk.CTkLabel(
                move_row,
                text=str(move_number),
                font=ctk.CTkFont(size=12),
                width=col_widths[0],
                anchor="w"
            )
            move_num_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
            
            # Player
            player = move.get('player', '?')
            player_label = ctk.CTkLabel(
                move_row,
                text=f"Player {player} ({self.player_symbols.get(player, '?')})",
                font=ctk.CTkFont(size=12),
                width=col_widths[1],
                anchor="w",
                text_color=self.player_colors.get(player, {}).get("fg", "#FFFFFF")
            )
            player_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            # Position
            position = move.get('position', (None, None))
            position_text = f"({position[0]}, {position[1]})" if position and position[0] is not None else "Unknown"
            position_label = ctk.CTkLabel(
                move_row,
                text=position_text,
                font=ctk.CTkFont(size=12),
                width=col_widths[2],
                anchor="w"
            )
            position_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
            
            # Board state - format as a 3x3 grid
            board = move.get('board')
            if board is not None and hasattr(board, 'shape') and board.shape == (3, 3):
                board_str = ""
                for r in range(3):
                    for c in range(3):
                        cell_val = board[r, c]
                        symbol = " " if cell_val == 0 else self.player_symbols.get(cell_val, str(cell_val))
                        board_str += f"{symbol} "
                    board_str += " | "
                board_label = ctk.CTkLabel(
                    move_row,
                    text=board_str,
                    font=ctk.CTkFont(family="Courier", size=12),
                    width=col_widths[3],
                    anchor="w"
                )
            else:
                board_label = ctk.CTkLabel(
                    move_row,
                    text="Invalid board data",
                    font=ctk.CTkFont(size=12),
                    width=col_widths[3],
                    anchor="w"
                )
            board_label.grid(row=0, column=3, padx=5, pady=5, sticky="w")
            
            # Winner info
            move_winner = move.get('winner')
            if move_winner in [1, 2]:
                winner_text = f"Player {move_winner}"
                winner_color = self.player_colors[move_winner]["fg"]
            elif move_winner == 0:
                winner_text = "Draw"
                winner_color = "#FFC107"  # Yellow
            else:
                winner_text = "None"
                winner_color = "#CCCCCC"  # Gray
                
            winner_label = ctk.CTkLabel(
                move_row,
                text=winner_text,
                font=ctk.CTkFont(size=12),
                width=col_widths[4],
                anchor="w",
                text_color=winner_color
            )
            winner_label.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        # Raw data button for advanced debugging
        raw_data_btn = ctk.CTkButton(
            main_frame,
            text="View Raw Data Structure",
            command=lambda: self.show_raw_data_popup(game),
            font=ctk.CTkFont(size=12),
            fg_color="#555555",
            hover_color="#666666",
            height=30
        )
        raw_data_btn.pack(pady=(10, 0))
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=debug_window.destroy,
            font=ctk.CTkFont(size=14),
            fg_color="#E63946",
            hover_color="#C5313E",
            height=35
        )
        close_btn.pack(pady=15)
        
        # Function to make window modal safely after it's visible
        def make_modal():
            try:
                # Show the window now that it's ready
                debug_window.deiconify()
                debug_window.focus_force()
                
                # Attempt to make it modal, with error handling
                debug_window.update()
                try:
                    debug_window.grab_set()
                    print("Debug window grab successful")
                except tk.TclError as e:
                    print(f"Could not set grab: {e}")
                    # Try again after a delay
                    debug_window.after(200, try_grab_again)
            except Exception as e:
                print(f"Error making debug window modal: {e}")
        
        # Retry grabbing the window
        def try_grab_again():
            try:
                if debug_window.winfo_exists():
                    debug_window.grab_set()
                    print("Debug window grab successful (retry)")
            except Exception as e:
                print(f"Could not set grab on retry: {e}")
        
        # Schedule making it modal
        debug_window.after(100, make_modal)
        
        # Make sure other windows won't interfere
        debug_window.transient(self.window)

    def show_raw_data_popup(self, game_data):
        """Show raw game data structure for advanced debugging
        
        Args:
            game_data (dict): Game data dictionary
        """
        # Create popup window
        raw_window = ctk.CTkToplevel(self.window)
        raw_window.title("Raw Game Data")
        raw_window.geometry("600x400")
        raw_window.configure(fg_color="#252525")
        
        # Temporarily hide window while building UI
        raw_window.withdraw()
        
        # Create text area with scrollbar
        frame = ctk.CTkFrame(raw_window, fg_color="#2A2A2A")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        text_area = ctk.CTkTextbox(frame, fg_color="#333333", text_color="#EEEEEE")
        text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 10))
        
        # Format game data
        text = "GAME DATA STRUCTURE:\n\n"
        # Add game info
        text += f"Game ID: {self.selected_game_id}\n"
        text += f"Winner: {game_data.get('winner')}\n"
        text += f"Total Moves: {len(game_data.get('moves', []))}\n\n"
        
        # Add move data
        text += "MOVES:\n"
        for i, move in enumerate(game_data.get('moves', [])):
            text += f"\nMove {i+1}:\n"
            for key, value in move.items():
                if key == 'board':
                    text += f"  {key}: "
                    if isinstance(value, np.ndarray):
                        text += "\n"
                        for row in value:
                            text += f"    {row}\n"
                    else:
                        text += f"{value}\n"
                else:
                    text += f"  {key}: {value}\n"
        
        # Insert text
        text_area.insert("1.0", text)
        text_area.configure(state="disabled")  # Make read-only
        
        # Close button
        close_btn = ctk.CTkButton(
            frame,
            text="Close",
            command=raw_window.destroy,
            font=ctk.CTkFont(size=14),
            fg_color="#E63946",
            hover_color="#C5313E",
            height=35
        )
        close_btn.pack(pady=(0, 5))
        
        # Function to make window modal safely
        def make_modal():
            try:
                # Show the window
                raw_window.deiconify()
                raw_window.focus_force()
                
                # Attempt to make it modal
                raw_window.update()
                try:
                    raw_window.grab_set()
                except tk.TclError:
                    # Try again after a delay
                    raw_window.after(200, try_grab_again)
            except Exception as e:
                print(f"Error making raw data window modal: {e}")
        
        # Retry grabbing the window
        def try_grab_again():
            try:
                if raw_window.winfo_exists():
                    raw_window.grab_set()
            except Exception:
                pass
        
        # Schedule making it modal
        raw_window.after(100, make_modal)
        
        # Make sure it stays above parent
        raw_window.transient(self.window)

    def show_previous_move(self):
        """Show the previous move in the selected game using move tracker linked list"""
        if not self.selected_game_id:
            return
            
        game = self.games.get(self.selected_game_id)
        if not game:
            return
            
        # Use move tracker if available
        if 'move_tracker' in game and self.selected_move > 0:
            move_tracker = game['move_tracker']
            
            # If we're not at the beginning, go back one node
            if self.selected_move == 1:
                # Going to the start (empty board)
                self.selected_move = 0
                self.current_board = np.zeros((3, 3), dtype=int)
                self.previous_move_pos = None
            else:
                # Navigate through linked list
                current_node = move_tracker.all_moves.current
                if current_node and current_node.prev:
                    # Move to previous node
                    prev_node = move_tracker.all_moves.previous_move()
                    self.selected_move -= 1
                    
                    # Get board state from the node
                    self.current_board = prev_node.board_state.copy()
                    self.previous_move_pos = (prev_node.row, prev_node.col)
            
            # Update display
            self.update_board_display()
            self.update_move_info(self.selected_move)
        else:
            # Fall back to legacy approach if move tracker not available
            if self.selected_move > 0:
                self.selected_move -= 1
                self.update_game_display()
    
    def show_next_move(self):
        """Show the next move in the selected game using move tracker linked list"""
        if not self.selected_game_id:
            return
            
        game = self.games.get(self.selected_game_id)
        if not game:
            return
        
        # Use move tracker if available
        if 'move_tracker' in game:
            move_tracker = game['move_tracker']
            total_moves = move_tracker.all_moves.length
            
            if self.selected_move < total_moves:
                # If at beginning, set current to head
                if self.selected_move == 0:
                    move_tracker.all_moves.goto_start()
                    node = move_tracker.all_moves.current
                else:
                    # Otherwise advance to next
                    node = move_tracker.all_moves.next_move()
                
                if node:
                    self.selected_move += 1
                    self.current_board = node.board_state.copy()
                    self.previous_move_pos = (node.row, node.col)
                    
                    # Update display
                    self.update_board_display()
                    self.update_move_info(self.selected_move)
        else:
            # Fall back to legacy approach
            if self.selected_move < len(game.get('moves', [])):
                self.selected_move += 1
                self.update_game_display()
    
    def update_game_display(self):
        """Update the display for the current move in the selected game"""
        if not self.selected_game_id:
            return
            
        game = self.games.get(self.selected_game_id)
        if not game:
            return
        
        # Reset board if at move 0
        if self.selected_move == 0:
            self.current_board = np.zeros((3, 3), dtype=int)
        else:
            # Get board state at selected move
            self.current_board = game['moves'][self.selected_move - 1]['board']
        
        # Update board display
        self.update_board_display()
        
        # Update move label
        total_moves = len(game['moves'])
        self.move_label.configure(text=f"Move: {self.selected_move}/{total_moves}")
        
        # Get move details for highlighting if applicable
        if self.selected_move > 0:
            move_data = game['moves'][self.selected_move - 1]
            self.previous_move_pos = move_data['position']
            
            # Update move info with player and position
            player = move_data['player']
            player_symbol = self.player_symbols[player]
            row, col = self.previous_move_pos
            
            # Add a move info display showing details of current move
            move_info = (
                f"Move {self.selected_move}: Player {player_symbol} at "
                f"position ({row+1},{col+1})"
            )
            
            if hasattr(self, 'move_info_label'):
                self.move_info_label.configure(text=move_info)
        else:
            self.previous_move_pos = None
            if hasattr(self, 'move_info_label'):
                self.move_info_label.configure(text="")
        
        # Update UI state
        self.update_ui_state()
    
    def update_board_display(self):
        """Update the board display with the current board state"""
        for i in range(3):
            for j in range(3):
                cell_value = self.current_board[i, j]
                
                # Determine if this cell is the most recent move
                is_recent_move = self.previous_move_pos and (i, j) == self.previous_move_pos
                
                if cell_value == 0:
                    # Empty cell - don't set border_color to avoid the error
                    self.cells[i][j].configure(
                        text="",
                        fg_color="#383838",
                        text_color="#FFFFFF",
                        border_width=0
                        # Don't include border_color here
                    )
                else:
                    # Player cell
                    player_symbol = self.player_symbols[cell_value]
                    player_colors = self.player_colors[cell_value]
                    
                    # Config for player cell
                    cell_config = {
                        "text": player_symbol,
                        "fg_color": player_colors["bg"],
                        "text_color": player_colors["fg"]
                    }
                    
                    # Add border only if this is the recent move
                    if is_recent_move:
                        cell_config["border_width"] = 2
                        cell_config["border_color"] = "#FFFFFF"
                    else:
                        cell_config["border_width"] = 0
                        # Don't include border_color to avoid the error
                    
                    # Apply configuration
                    self.cells[i][j].configure(**cell_config)
    
    def update_ui_state(self):
        """Update UI elements based on current state"""
        if not self.selected_game_id or self.selected_game_id not in self.games:
            # No game selected
            self.prev_move_btn.configure(state="disabled")
            self.next_move_btn.configure(state="disabled")
            return
            
        game = self.games[self.selected_game_id]
        
        # Enable/disable prev move button
        if self.selected_move > 0:
            self.prev_move_btn.configure(state="normal")
        else:
            self.prev_move_btn.configure(state="disabled")
        
        # Enable/disable next move button
        if self.selected_move < len(game['moves']):
            self.next_move_btn.configure(state="normal")
        else:
            self.next_move_btn.configure(state="disabled")
    
    def update_speed_label(self, *args):
        """Update the speed label when the slider value changes"""
        speed = self.speed_var.get()
        self.speed_label.configure(text=f"{speed:.1f}x")
        self.playback_speed = 1.0 / speed  # Convert to seconds
    
    def toggle_playback(self):
        """Toggle automatic playback of moves"""
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """Start automatic playback of moves"""
        if not self.selected_game_id:
            return
        
        game = self.games.get(self.selected_game_id)
        if not game:
            return
        
        # If at the end, start from beginning
        if self.selected_move >= len(game['moves']):
            self.selected_move = 0
            self.current_board = np.zeros((3, 3), dtype=int)
            self.update_board_display()
        
        # Update play button to show pause icon
        self.play_btn.configure(text="⏸")
        
        # Start playback
        self.is_playing = True
        self.advance_playback()
    
    def advance_playback(self):
        """Advance to the next move during playback"""
        if not self.is_playing or not self.selected_game_id:
            return
        
        game = self.games.get(self.selected_game_id)
        if not game:
            return
        
        # If not at the end, show next move
        if self.selected_move < len(game['moves']):
            self.show_next_move()
            
            # Schedule next move if not at the end
            if self.selected_move < len(game['moves']):
                delay_ms = int(self.playback_speed * 1000)
                self.playback_job = self.window.after(delay_ms, self.advance_playback)
            else:
                # End of game, stop playback
                self.stop_playback()
        else:
            # End of game, stop playback
            self.stop_playback()
    
    def stop_playback(self):
        """Stop automatic playback"""
        if self.playback_job:
            self.window.after_cancel(self.playback_job)
            self.playback_job = None
        
        self.is_playing = False
        self.play_btn.configure(text="▶")
    
    def show_first_move(self):
        """Show the first move (empty board) using move tracker linked list"""
        if not self.selected_game_id:
            return
        
        # Stop any ongoing playback
        self.stop_playback()
        
        game = self.games.get(self.selected_game_id)
        if not game:
            return
        
        # Reset to empty board
        self.selected_move = 0
        self.current_board = np.zeros((3, 3), dtype=int)
        self.previous_move_pos = None
        
        # For move tracker, reset the current position to start
        if 'move_tracker' in game:
            move_tracker = game['move_tracker']
            move_tracker.all_moves.goto_start()
        
        # Update display
        self.update_board_display()
        self.update_move_info(0)
    
    def show_last_move(self):
        """Show the last move of the game using move tracker linked list"""
        if not self.selected_game_id:
            return
        
        # Stop any ongoing playback
        self.stop_playback()
        
        game = self.games.get(self.selected_game_id)
        if not game:
            return
        
        # Use move tracker if available
        if 'move_tracker' in game:
            move_tracker = game['move_tracker']
            
            # Go to the end of the linked list
            move_tracker.all_moves.goto_end()
            node = move_tracker.all_moves.current
            
            if node:
                self.selected_move = move_tracker.all_moves.length
                self.current_board = node.board_state.copy()
                self.previous_move_pos = (node.row, node.col)
                
                # Update display
                self.update_board_display()
                self.update_move_info(self.selected_move)
        else:
            # Fall back to legacy approach
            moves = game.get('moves', [])
            if not moves:
                return
            
            # Set to last move
            self.selected_move = len(moves)
            
            # Update board to final state
            self.current_board = moves[-1]['board'].copy()
            self.previous_move_pos = moves[-1]['position']
            
            # Update display
            self.update_board_display()
            self.update_move_info(self.selected_move)

    def on_closing(self):
        """Handle window closing event"""
        # Stop any ongoing playback
        self.stop_playback()
        self.window.destroy()
    
    def run(self):
        """Run the viewer as a standalone application"""
        self.window.mainloop()

    def populate_games_list(self, game_ids, filter_completed=True):
        """Populate the games list with the given game IDs using pagination
        
        Args:
            game_ids (list): List of game IDs to display
            filter_completed (bool): Whether to filter out incomplete games
        """
        # Clear current list except filter controls
        for widget in self.games_list_frame.winfo_children():
            if not isinstance(widget, ctk.CTkFrame) or "filter" not in str(widget):
                if not isinstance(widget, ctk.CTkFrame) or "pagination" not in str(widget):
                    widget.destroy()
        
        # Apply filter
        if filter_completed:
            filtered_ids = [gid for gid in game_ids if self.games[gid].get('winner') is not None]
        else:
            filtered_ids = list(game_ids)
        
        self.filtered_game_ids = filtered_ids  # Store for pagination
        total_games = len(filtered_ids)
        
        # Calculate pagination
        total_pages = (total_games + self.page_size - 1) // self.page_size
        self.total_pages = max(1, total_pages)
        self.current_page = min(self.current_page, self.total_pages - 1)
        
        # Get slice of game IDs for current page
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_games)
        current_game_ids = filtered_ids[start_idx:end_idx]
        
        # Show stats
        stats_text = f"Showing {start_idx+1}-{end_idx} of {total_games} games"
        if filter_completed and len(game_ids) > total_games:
            stats_text += f" ({len(game_ids) - total_games} incomplete games filtered)"
        
        stats_label = ctk.CTkLabel(
            self.games_list_frame,
            text=stats_text,
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA"
        )
        stats_label.pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        # Display games for current page
        displayed_count = 0
        for game_id in current_game_ids:
            game = self.games[game_id]
            
            # Skip games with no moves
            if not game.get('moves'):
                continue
                
            # Format date from game_id or timestamp
            try:
                if game.get('timestamp') and isinstance(game['timestamp'], str):
                    # Try to parse a standardized timestamp format
                    date_parts = game['timestamp'].split()
                    if len(date_parts) >= 2:
                        date_display = f"{date_parts[0]} {date_parts[1]}"
                    else:
                        date_display = game['timestamp']
                else:
                    # Fall back to parsing from game_id
                    date_str = f"{game_id[:4]}-{game_id[4:6]}-{game_id[6:8]}"
                    time_str = f"{game_id[9:11]}:{game_id[11:13]}:{game_id[13:15]}"
                    date_display = f"{date_str} {time_str}"
            except Exception as e:
                print(f"Error formatting date for game {game_id}: {e}")
                date_display = game_id
            
            # Get winner info and move count
            winner = game.get('winner')
            moves_count = len(game.get('moves', []))
            
            if winner in [1, 2]:
                winner_text = f"Winner: Player {winner} ({self.player_symbols[winner]})"
                text_color = self.player_colors[winner]["fg"]
            elif winner == 0:
                winner_text = "Draw"
                text_color = "#FFC107"  # Yellow for draw
            else:
                winner_text = "Incomplete" if moves_count > 0 else "Invalid Game"
                text_color = "#CCCCCC"  # Gray for incomplete
            
            # Create game entry with optimized rendering
            game_frame = ctk.CTkFrame(
                self.games_list_frame, 
                fg_color="#383838",
                corner_radius=5,
                height=70
            )
            game_frame.pack(fill=tk.X, pady=5, padx=5)
            game_frame.pack_propagate(False)  # Maintain height
            
            # Game ID label with formatted date
            id_label = ctk.CTkLabel(
                game_frame,
                text=f"{date_display} ({moves_count} moves)",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#AAAAAA"
            )
            id_label.pack(anchor=tk.W, padx=10, pady=(10, 0))
            
            # Winner label with appropriate color
            winner_label = ctk.CTkLabel(
                game_frame,
                text=winner_text,
                font=ctk.CTkFont(size=14),
                text_color=text_color
            )
            winner_label.pack(anchor=tk.W, padx=10, pady=(0, 5))
            
            # Make the entire frame clickable
            game_frame.bind("<Button-1>", lambda e, gid=game_id: self.select_game(gid))
            id_label.bind("<Button-1>", lambda e, gid=game_id: self.select_game(gid))
            winner_label.bind("<Button-1>", lambda e, gid=game_id: self.select_game(gid))
            
            displayed_count += 1
        
        # Show message if no games were displayed
        if displayed_count == 0:
            no_games_label = ctk.CTkLabel(
                self.games_list_frame,
                text="No games found matching filter criteria",
                font=ctk.CTkFont(size=14),
                text_color="#CCCCCC"
            )
            no_games_label.pack(pady=10)
        
        # Add pagination controls
        self._add_pagination_controls()
        
        # Display count in the status area
        print(f"Displayed {displayed_count} games (page {self.current_page + 1} of {self.total_pages})")

    def _add_pagination_controls(self):
        """Add pagination controls to the games list"""
        # Create pagination frame
        pagination_frame = ctk.CTkFrame(
            self.games_list_frame,
            fg_color="#333333",
            corner_radius=8,
            height=40
        )
        pagination_frame.pack(fill=tk.X, pady=10, padx=5)
        pagination_frame.pack_propagate(False)
        
        # First page button
        first_page_btn = ctk.CTkButton(
            pagination_frame,
            text="⏮",
            command=lambda: self._change_page(0),
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            width=30,
            height=25,
            state="normal" if self.current_page > 0 else "disabled"
        )
        first_page_btn.pack(side=tk.LEFT, padx=(10, 2))
        
        # Previous page button
        prev_page_btn = ctk.CTkButton(
            pagination_frame,
            text="◀",
            command=lambda: self._change_page(self.current_page - 1),
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            width=30,
            height=25,
            state="normal" if self.current_page > 0 else "disabled"
        )
        prev_page_btn.pack(side=tk.LEFT, padx=2)
        
        # Page indicator
        page_label = ctk.CTkLabel(
            pagination_frame,
            text=f"Page {self.current_page + 1} of {self.total_pages}",
            font=ctk.CTkFont(size=12),
            width=100
        )
        page_label.pack(side=tk.LEFT, padx=10)
        
        # Next page button
        next_page_btn = ctk.CTkButton(
            pagination_frame,
            text="▶",
            command=lambda: self._change_page(self.current_page + 1),
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            width=30,
            height=25,
            state="normal" if self.current_page < self.total_pages - 1 else "disabled"
        )
        next_page_btn.pack(side=tk.LEFT, padx=2)
        
        # Last page button
        last_page_btn = ctk.CTkButton(
            pagination_frame,
            text="⏭",
            command=lambda: self._change_page(self.total_pages - 1),
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            width=30,
            height=25,
            state="normal" if self.current_page < self.total_pages - 1 else "disabled"
        )
        last_page_btn.pack(side=tk.LEFT, padx=(2, 10))

    def _change_page(self, page_num):
        """Change to a different page of results
        
        Args:
            page_num (int): Page number (0-based)
        """
        if 0 <= page_num < self.total_pages:
            self.current_page = page_num
            self.populate_games_list(self.filtered_game_ids, filter_completed=False)  # Already filtered

    def apply_filter(self):
        """Apply the completed games filter"""
        filter_completed = self.filter_var.get()
        
        # Get all game IDs in proper order
        game_ids = sorted(
            self.games.keys(), 
            key=lambda gid: self.games[gid].get('timestamp', gid),
            reverse=True
        )
        
        # Reset to first page when filter changes
        self.current_page = 0
        
        # Repopulate with filter applied
        self.populate_games_list(game_ids, filter_completed)

    def add_filter_controls(self):
        """Add filter controls to the games list"""
        filter_frame = ctk.CTkFrame(
            self.games_list_frame,
            fg_color="#333333",
            corner_radius=8
        )
        filter_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        self.filter_var = tk.BooleanVar(value=True)
        
        filter_label = ctk.CTkLabel(
            filter_frame,
            text="Filter:",
            font=ctk.CTkFont(size=12),
            width=40,
            anchor="w"
        )
        filter_label.pack(side=tk.LEFT, padx=5)
        
        filter_check = ctk.CTkCheckBox(
            filter_frame,
            text="Completed Games Only",
            variable=self.filter_var,
            command=self.apply_filter,
            font=ctk.CTkFont(size=12),
            checkbox_width=18,
            checkbox_height=18
        )
        filter_check.pack(side=tk.LEFT, padx=5, pady=5)

# Allow running this module directly
if __name__ == "__main__":
    viewer = GameHistoryViewer()
    viewer.run()
