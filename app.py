import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageSequence
import os
import numpy as np
from game import TicTacToeGame
from ai_player import AIPlayer
from assets_manager import AssetManager, ASSETS_DIR
from game_history import GameHistoryViewer
from ai_trainer import AITrainingWindow

class TicTacToeApp:
    def __init__(self, root, assets_manager=None):
        self.root = root
        self.root.title("Tic Tac Toe")
        self.root.geometry("900x700")  # Wider to accommodate history panel
        self.root.configure(fg_color="#1E1E1E")  # Dark background
        
        # Setup asset manager
        self.assets = assets_manager if assets_manager else AssetManager()
        
        # Ensure we have placeholder animations if needed
        self.assets.generate_placeholder_animations()
        
        # Initialize game components
        self.game = TicTacToeGame()
        self.ai = AIPlayer()
        
        # UI state variables
        self.mode = tk.StringVar(value="human_vs_human")
        self.animation_running = False
        self.animation_label = None
        self.animation_frames = []
        self.current_frame = 0
        
        # Player symbols - use static text instead of images for reliability
        self.player_symbols = {
            1: "X",  # Player 1: X
            2: "O"   # Player 2: O
        }
        
        # Player colors
        self.player_colors = {
            1: {"fg": "#4F85CC", "bg": "#2D5F8B"},  # X: Blue
            2: {"fg": "#FF5C8D", "bg": "#8B2D5F"}   # O: Pink
        }
        
        # Store references to prevent garbage collection
        self._image_refs = []
        
        # Set up history tracking
        self.history_games = {}
        self.selected_history_game = None
        
        self.setup_ui()
        
        # Load game history after UI setup
        self.load_history()
    
    def setup_ui(self):
        # Create a main container with two panels (game and history)
        self.main_container = ctk.CTkFrame(self.root, fg_color="#1E1E1E")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for the game
        self.game_panel = ctk.CTkFrame(self.main_container, fg_color="#252525", corner_radius=15)
        self.game_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=10)
        
        # Right panel for history
        self.history_panel = ctk.CTkFrame(self.main_container, fg_color="#252525", corner_radius=15, width=250)
        self.history_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 10), pady=10)
        
        # Set up the game UI in the left panel
        self.setup_game_ui()
        
        # Set up the history UI in the right panel
        self.setup_history_ui()
    
    def setup_game_ui(self):
        # Title with better styling (made more compact) - now clickable
        title_frame = ctk.CTkFrame(self.game_panel, fg_color="transparent", cursor="hand2")
        title_frame.pack(pady=(15, 5))
        title_frame.bind("<Button-1>", lambda event: self.title_clicked())
        
        # Title label - also clickable
        self.title_label = ctk.CTkLabel(
            title_frame, 
            text="Tic Tac Toe", 
            font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
            text_color="#3E92CC",
            cursor="hand2"  # Change cursor to hand when hovering
        )
        self.title_label.pack()
        self.title_label.bind("<Button-1>", lambda event: self.title_clicked())
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="The Classic Game\n(Click title for New Game)",  # Add hint text
            font=ctk.CTkFont(family="Arial", size=12),
            text_color="#8B8B8B",
            cursor="hand2"
        )
        subtitle.pack()
        subtitle.bind("<Button-1>", lambda event: self.title_clicked())
        
        # Separator
        separator = ctk.CTkFrame(self.game_panel, height=2, fg_color="#3E92CC")
        separator.pack(fill=tk.X, padx=50, pady=(2, 10))
        
        # Mode selection with improved styling (more compact)
        mode_frame = ctk.CTkFrame(self.game_panel, fg_color="transparent")
        mode_frame.pack(pady=8)
        
        mode_label = ctk.CTkLabel(
            mode_frame, 
            text="Game Mode:", 
            font=ctk.CTkFont(size=14),
            text_color="#DDDDDD"
        )
        mode_label.pack(side=tk.LEFT, padx=10)
        
        human_vs_human = ctk.CTkRadioButton(
            mode_frame, 
            text="Human vs Human", 
            variable=self.mode, 
            value="human_vs_human",
            font=ctk.CTkFont(size=13),
            border_width_checked=6,
            fg_color="#3E92CC",
            hover_color="#2D7DB3"
        )
        human_vs_human.pack(side=tk.LEFT, padx=10)
        
        human_vs_ai = ctk.CTkRadioButton(
            mode_frame, 
            text="Human vs AI", 
            variable=self.mode, 
            value="human_vs_ai",
            command=self.check_ai_model,
            font=ctk.CTkFont(size=13),
            border_width_checked=6,
            fg_color="#3E92CC",
            hover_color="#2D7DB3"
        )
        human_vs_ai.pack(side=tk.LEFT, padx=10)
        
        # AI model check with improved styling (more compact)
        ai_frame = ctk.CTkFrame(self.game_panel, fg_color="transparent")
        ai_frame.pack(pady=5)
        
        self.ai_status_label = ctk.CTkLabel(
            ai_frame, 
            text="AI Model: Not Checked", 
            font=ctk.CTkFont(size=13),
            text_color="#CCCCCC"
        )
        self.ai_status_label.pack(side=tk.LEFT, padx=10)
        
        self.train_ai_btn = ctk.CTkButton(
            ai_frame, 
            text="Train AI Model", 
            command=self.train_ai_model,
            font=ctk.CTkFont(size=13),
            fg_color="#E76F51",
            hover_color="#D65F41",
            corner_radius=8,
            height=32
        )
        self.train_ai_btn.pack(side=tk.LEFT, padx=10)
        self.train_ai_btn.configure(state="disabled")
        
        # Game board section with better button configuration
        self.board_frame = ctk.CTkFrame(self.game_panel, fg_color="#2A2A2A", corner_radius=10)
        self.board_frame.pack(pady=(20, 10), padx=20)
        
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        
        for i in range(3):
            for j in range(3):
                button = ctk.CTkButton(
                    self.board_frame, 
                    text="",  # Start with empty text
                    width=85,  # Slightly smaller to fit in the narrower panel
                    height=85, # Slightly smaller to fit in the narrower panel
                    command=lambda row=i, col=j: self.make_move(row, col),
                    font=ctk.CTkFont(size=42, weight="bold"),  # Larger font for better visibility
                    fg_color="#383838",
                    hover_color="#444444",
                    text_color="#FFFFFF",  # Default text color
                    text_color_disabled="#FFFFFF",  # Keep text visible when disabled
                    corner_radius=5,
                    border_width=0
                )
                button.grid(row=i, column=j, padx=5, pady=5)
                self.buttons[i][j] = button
        
        # Animation area moved below the board
        self.animation_container = ctk.CTkFrame(self.game_panel, fg_color="#2D2D2D", corner_radius=10, height=120)
        self.animation_container.pack(fill=tk.X, padx=20, pady=(5, 10))
        self.animation_container.pack_propagate(False)  # Prevent resizing based on content
        
        # Animation label heading
        animation_title = ctk.CTkLabel(
            self.animation_container,
            text="Game Results",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            text_color="#8B8B8B"
        )
        animation_title.pack(pady=(5, 0))
        
        # Animation frame inside the container
        self.animation_frame = ctk.CTkFrame(self.animation_container, fg_color="transparent")
        self.animation_frame.pack(expand=True, fill=tk.BOTH)
        
        # Status area with improved styling
        status_frame = ctk.CTkFrame(self.game_panel, fg_color="transparent")
        status_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="Player X's turn", 
            font=ctk.CTkFont(family="Arial", size=18, weight="bold"),
            text_color="#EEEEEE"
        )
        self.status_label.pack()
        
        # Make the button container frame more visible with a subtle background
        button_frame = ctk.CTkFrame(self.game_panel, fg_color="#2A2A2A", corner_radius=10)
        button_frame.pack(fill=tk.X, pady=15, padx=20)
        
        # Add a centered container for buttons
        button_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_container.pack(pady=15)
        
        # Make New Game button larger and more visible
        self.reset_btn = ctk.CTkButton(
            button_container, 
            text="New Game", 
            command=self.reset_game,
            font=ctk.CTkFont(size=16, weight="bold"),  # Slightly smaller
            fg_color="#4CAF50",  # Bright green - more visible
            hover_color="#3E8E41",  # Darker green on hover
            width=120,  # Smaller width to fit in narrower panel
            height=45,  # Smaller height
            corner_radius=10,
            border_width=2,  # Add border for extra visibility
            border_color="#AAAAAA"  # Light gray border
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Make Quit button match the style of New Game button
        quit_btn = ctk.CTkButton(
            button_container, 
            text="Quit", 
            command=self.root.quit,
            font=ctk.CTkFont(size=16, weight="bold"),  # Match New Game button
            fg_color="#E63946",  # Keep red for quit
            hover_color="#C5313E",
            width=120,  # Same size as New Game
            height=45,
            corner_radius=10,
            border_width=2,
            border_color="#AAAAAA"
        )
        quit_btn.pack(side=tk.LEFT, padx=5)
        
        # Add a title to the button section for better clarity
        button_title = ctk.CTkLabel(
            button_frame,
            text="Game Controls",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color="#888888"
        )
        button_title.pack(pady=(10, 0))  # Place at top of frame
        
        # Add "View History" button next to the other buttons
        history_btn = ctk.CTkButton(
            button_container, 
            text="Full History", 
            command=self.show_game_history,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#3E92CC",  # Blue
            hover_color="#2D7DB3",
            width=120,
            height=45,
            corner_radius=10,
            border_width=2,
            border_color="#AAAAAA"
        )
        history_btn.pack(side=tk.LEFT, padx=5)
        
        # Ensure the button frame is above the button container
        button_title.lift()
    
    def setup_history_ui(self):
        """Set up the history panel UI"""
        # History panel title
        history_title = ctk.CTkLabel(
            self.history_panel,
            text="Game History",
            font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
            text_color="#3E92CC"
        )
        history_title.pack(pady=(15, 5))
        
        # Separator under title
        history_sep = ctk.CTkFrame(self.history_panel, height=2, fg_color="#3E92CC")
        history_sep.pack(fill=tk.X, padx=30, pady=(0, 10))
        
        # History statistics section
        stats_frame = ctk.CTkFrame(self.history_panel, fg_color="#2A2A2A", corner_radius=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Stats title
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="Statistics",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#EEEEEE"
        )
        stats_title.pack(pady=(5, 0))
        
        # Stats container with grid layout for stats
        self.stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_container.pack(pady=5, padx=5, fill=tk.X)
        
        # Labels for stats
        self.total_games_label = ctk.CTkLabel(
            self.stats_container,
            text="Total Games: 0",
            font=ctk.CTkFont(size=12),
            text_color="#CCCCCC"
        )
        self.total_games_label.pack(anchor=tk.W, padx=10, pady=2)
        
        self.x_wins_label = ctk.CTkLabel(
            self.stats_container,
            text="X Wins: 0 (0%)",
            font=ctk.CTkFont(size=12),
            text_color=self.player_colors[1]["fg"]
        )
        self.x_wins_label.pack(anchor=tk.W, padx=10, pady=2)
        
        self.o_wins_label = ctk.CTkLabel(
            self.stats_container,
            text="O Wins: 0 (0%)",
            font=ctk.CTkFont(size=12),
            text_color=self.player_colors[2]["fg"]
        )
        self.o_wins_label.pack(anchor=tk.W, padx=10, pady=2)
        
        self.draws_label = ctk.CTkLabel(
            self.stats_container,
            text="Draws: 0 (0%)",
            font=ctk.CTkFont(size=12),
            text_color="#FFC107"  # Yellow for draws
        )
        self.draws_label.pack(anchor=tk.W, padx=10, pady=2)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            stats_frame,
            text="Refresh History",
            command=self.load_history,
            font=ctk.CTkFont(size=12),
            fg_color="#4CAF50",
            hover_color="#3E8E41",
            corner_radius=6,
            height=25
        )
        refresh_btn.pack(pady=5)
        
        # Recent games list
        recent_games_frame = ctk.CTkFrame(self.history_panel, fg_color="#2A2A2A", corner_radius=10)
        recent_games_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Recent games title
        recent_games_title = ctk.CTkLabel(
            recent_games_frame,
            text="Recent Games",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#EEEEEE"
        )
        recent_games_title.pack(pady=(5, 0))
        
        # Scrollable frame for the game list
        self.games_list_frame = ctk.CTkScrollableFrame(
            recent_games_frame,
            fg_color="#333333",
            corner_radius=5
        )
        self.games_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add placeholder text
        self.placeholder_label = ctk.CTkLabel(
            self.games_list_frame,
            text="Loading game history...",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA"
        )
        self.placeholder_label.pack(pady=20)
        
        # Mini board preview for selected game
        self.preview_frame = ctk.CTkFrame(self.history_panel, fg_color="#2A2A2A", corner_radius=10, height=150)
        self.preview_frame.pack(fill=tk.X, padx=10, pady=10)
        self.preview_frame.pack_propagate(False)  # Maintain fixed height
        
        # Preview title
        self.preview_title = ctk.CTkLabel(
            self.preview_frame,
            text="Game Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#EEEEEE"
        )
        self.preview_title.pack(pady=(5, 0))
        
        # Mini board container
        self.mini_board_frame = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        self.mini_board_frame.pack(expand=True, pady=5)
        
        # Create mini board cells
        self.mini_cells = [[None for _ in range(3)] for _ in range(3)]
        
        for i in range(3):
            for j in range(3):
                cell = ctk.CTkButton(
                    self.mini_board_frame, 
                    text="",
                    width=30,
                    height=30,
                    font=ctk.CTkFont(size=16, weight="bold"),
                    fg_color="#383838",
                    text_color="#FFFFFF",
                    corner_radius=3,
                    state="disabled"  # Cells are non-interactive
                )
                cell.grid(row=i, column=j, padx=2, pady=2)
                self.mini_cells[i][j] = cell
    
    def load_history(self):
        """Load game history data and update the history panel"""
        # Clear the games list
        for widget in self.games_list_frame.winfo_children():
            widget.destroy()
        
        # Show loading message
        loading_label = ctk.CTkLabel(
            self.games_list_frame,
            text="Loading game history...",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA"
        )
        loading_label.pack(pady=20)
        
        # Force UI update to show loading screen
        self.root.update_idletasks()
        
        # Load game history in a separate thread
        import threading
        self.loading_thread = threading.Thread(target=self._load_history_async)
        self.loading_thread.daemon = True
        self.loading_thread.start()
        
        # Check for completion
        self.root.after(100, self._check_history_loading_complete)
    
    def _load_history_async(self):
        """Load game history data asynchronously"""
        try:
            # Try to use data integration if available
            try:
                from game_data_integration import GameDataIntegration
                data_manager = GameDataIntegration(use_cache=True)
                self.history_games = data_manager.get_all_games()
            except ImportError:
                # Fall back to direct loading
                self.history_games = TicTacToeGame.load_game_history_from_csv()
            
            # Sort games by timestamp (most recent first)
            self.sorted_game_ids = sorted(
                self.history_games.keys(),
                key=lambda gid: self.history_games[gid].get('timestamp', gid),
                reverse=True
            )
        except Exception as e:
            print(f"Error loading history data: {e}")
            import traceback
            traceback.print_exc()
            self.history_games = {}
            self.sorted_game_ids = []
    
    def _check_history_loading_complete(self):
        """Check if history loading is complete and update UI if so"""
        # Check if loading thread is still running
        if self.loading_thread.is_alive():
            # Still loading, check again later
            self.root.after(100, self._check_history_loading_complete)
            return
        
        # Loading complete, update UI
        self._update_history_ui()
    
    def _update_history_ui(self):
        """Update the history UI with loaded data"""
        # Clear the games list
        for widget in self.games_list_frame.winfo_children():
            widget.destroy()
        
        # Update statistics
        self._update_statistics()
        
        # Show message if no games found
        if not self.history_games:
            no_games_label = ctk.CTkLabel(
                self.games_list_frame,
                text="No games found in history",
                font=ctk.CTkFont(size=12),
                text_color="#AAAAAA"
            )
            no_games_label.pack(pady=20)
            return
        
        # Display recent games (limited to 20 most recent)
        max_games = min(20, len(self.sorted_game_ids))
        for i in range(max_games):
            game_id = self.sorted_game_ids[i]
            game = self.history_games[game_id]
            
            # Format date from game_id
            try:
                date_str = f"{game_id[:4]}-{game_id[4:6]}-{game_id[6:8]}"
                time_str = f"{game_id[9:11]}:{game_id[11:13]}"
                date_display = f"{date_str} {time_str}"
            except:
                date_display = game_id[:15] + "..."
            
            # Get winner and move count
            winner = game.get('winner')
            moves = game.get('moves', [])
            move_count = len(moves)
            
            if winner in [1, 2]:
                winner_symbol = "X" if winner == 1 else "O"
                winner_color = self.player_colors[winner]["fg"]
                winner_text = f"Winner: {winner_symbol}"
            elif winner == 0:
                winner_text = "Draw"
                winner_color = "#FFC107"  # Yellow for draws
            else:
                winner_text = "Incomplete"
                winner_color = "#AAAAAA"  # Gray for incomplete
            
            # Create game entry
            game_frame = ctk.CTkFrame(
                self.games_list_frame,
                fg_color="#383838",
                corner_radius=5,
                height=60
            )
            game_frame.pack(fill=tk.X, pady=3, padx=5)
            game_frame.pack_propagate(False)  # Maintain fixed height
            
            # Date label
            date_label = ctk.CTkLabel(
                game_frame,
                text=date_display,
                font=ctk.CTkFont(size=11),
                text_color="#AAAAAA"
            )
            date_label.pack(anchor=tk.W, padx=10, pady=(8, 0))
            
            # Result label
            result_label = ctk.CTkLabel(
                game_frame,
                text=f"{winner_text} · {move_count} moves",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=winner_color
            )
            result_label.pack(anchor=tk.W, padx=10, pady=(0, 8))
            
            # Make the frame clickable
            game_frame.bind("<Button-1>", lambda e, gid=game_id: self._show_game_preview(gid))
            date_label.bind("<Button-1>", lambda e, gid=game_id: self._show_game_preview(gid))
            result_label.bind("<Button-1>", lambda e, gid=game_id: self._show_game_preview(gid))
        
        # Select the first game for preview
        if self.sorted_game_ids:
            self._show_game_preview(self.sorted_game_ids[0])
    
    def _update_statistics(self):
        """Update the statistics display"""
        total_games = len(self.history_games)
        x_wins = sum(1 for game in self.history_games.values() if game.get('winner') == 1)
        o_wins = sum(1 for game in self.history_games.values() if game.get('winner') == 2)
        draws = sum(1 for game in self.history_games.values() if game.get('winner') == 0)
        
        # Calculate percentages
        x_pct = (x_wins / total_games * 100) if total_games > 0 else 0
        o_pct = (o_wins / total_games * 100) if total_games > 0 else 0
        draws_pct = (draws / total_games * 100) if total_games > 0 else 0
        
        # Update labels
        self.total_games_label.configure(text=f"Total Games: {total_games}")
        self.x_wins_label.configure(text=f"X Wins: {x_wins} ({x_pct:.1f}%)")
        self.o_wins_label.configure(text=f"O Wins: {o_wins} ({o_pct:.1f}%)")
        self.draws_label.configure(text=f"Draws: {draws} ({draws_pct:.1f}%)")
    
    def _show_game_preview(self, game_id):
        """Show a preview of the selected game
        
        Args:
            game_id (str): ID of the game to preview
        """
        if game_id not in self.history_games:
            return
        
        self.selected_history_game = game_id
        game = self.history_games[game_id]
        
        # Format date from game_id
        try:
            date_str = f"{game_id[:4]}-{game_id[4:6]}-{game_id[6:8]}"
            time_str = f"{game_id[9:11]}:{game_id[11:13]}:{game_id[13:15]}"
            date_display = f"{date_str} {time_str}"
        except:
            date_display = game_id
        
        # Get the final board state
        final_board = None
        moves = game.get('moves', [])
        
        if moves:
            final_board = moves[-1].get('board')
        
        # Check if game has move tracker instead
        if 'move_tracker' in game:
            move_tracker = game['move_tracker']
            final_board = move_tracker.current_board
        
        # Update preview title
        winner = game.get('winner')
        if winner in [1, 2]:
            winner_symbol = "X" if winner == 1 else "O"
            winner_color = self.player_colors[winner]["fg"]
            self.preview_title.configure(
                text=f"Game: {date_display[:10]}\nWinner: {winner_symbol}",
                text_color=winner_color
            )
        elif winner == 0:
            self.preview_title.configure(
                text=f"Game: {date_display[:10]}\nResult: Draw",
                text_color="#FFC107"  # Yellow for draws
            )
        else:
            self.preview_title.configure(
                text=f"Game: {date_display[:10]}\nIncomplete",
                text_color="#AAAAAA"
            )
        
        # Update mini board
        if final_board is not None:
            for i in range(3):
                for j in range(3):
                    cell_value = final_board[i, j]
                    
                    if cell_value == 0:
                        # Empty cell
                        self.mini_cells[i][j].configure(
                            text="",
                            fg_color="#383838",
                            text_color="#FFFFFF"
                        )
                    else:
                        # Player cell
                        player_symbol = self.player_symbols[cell_value]
                        player_colors = self.player_colors[cell_value]
                        
                        self.mini_cells[i][j].configure(
                            text=player_symbol,
                            fg_color=player_colors["bg"],
                            text_color=player_colors["fg"]
                        )
        else:
            # Clear the board if no final state
            for i in range(3):
                for j in range(3):
                    self.mini_cells[i][j].configure(
                        text="",
                        fg_color="#383838",
                        text_color="#FFFFFF"
                    )
    
    # Add a method to show game history
    def show_game_history(self):
        """Show the full game history viewer"""
        # Pass the currently selected game ID to the viewer if available
        selected_game = self.selected_history_game if hasattr(self, 'selected_history_game') else None
        GameHistoryViewer(self.root)
    
    def check_ai_model(self):
        if self.mode.get() == "human_vs_ai":
            if self.ai.model_exists():
                self.ai_status_label.configure(text="AI Model: Available ✓", text_color="#4CAF50")
                self.train_ai_btn.configure(state="disabled")
            else:
                self.ai_status_label.configure(text="AI Model: Not Available ✗", text_color="#E63946")
                self.train_ai_btn.configure(state="normal")
        else:
            self.ai_status_label.configure(text="AI Model: Not Needed", text_color="#CCCCCC")
            self.train_ai_btn.configure(state="disabled")
    
    def train_ai_model(self):
        """Open AI training window"""
        self.ai_status_label.configure(text="AI Model: Preparing Training...", text_color="#FFC107")
        
        # Define callback function for when training completes
        def on_training_complete():
            if self.ai.model_exists():
                self.ai_status_label.configure(text="AI Model: Available ✓", text_color="#4CAF50")
                self.train_ai_btn.configure(state="disabled")
            else:
                self.ai_status_label.configure(text="AI Model: Training Failed ✗", text_color="#E63946")
        
        # Launch training window
        training_window = AITrainingWindow(self.root, callback_on_complete=on_training_complete)
    
    def make_move(self, row, col):
        """Handle a player's move at the given row and column"""
        if self.animation_running:
            return  # Don't allow moves during animations
            
        # Get the current player before making the move
        current_player = self.game.current_player
            
        if self.game.make_move(row, col):
            # Get player symbol and colors
            player_number = current_player
            player_symbol = self.player_symbols[player_number]
            player_colors = self.player_colors[player_number]
            
            # Update button with player symbol and colors - using TEXT instead of images
            self.buttons[row][col].configure(
                text=player_symbol,  # Use text symbol (X or O)
                state="disabled",
                fg_color=player_colors["bg"],
                text_color=player_colors["fg"]  # Use contrasting text color
            )
            
            # Force update to ensure rendering
            self.root.update_idletasks()
            
            # Check game state
            if self.game.game_over:
                if self.game.winner:
                    # We have a winner
                    winner_symbol = "X" if self.game.winner == 1 else "O"
                    winner_color = "#2D5F8B" if self.game.winner == 1 else "#8B2D5F"
                    self.status_label.configure(
                        text=f"Player {winner_symbol} wins!",
                        text_color=winner_color
                    )
                    self.show_win_animation(winner_symbol)
                else:
                    # It's a draw
                    self.status_label.configure(text="It's a draw!", text_color="#FFC107")
                    self.show_win_animation("draw")
            else:
                # Game continues - update for next player
                next_player = self.game.current_player
                next_symbol = "X" if next_player == 1 else "O"
                next_color = "#2D5F8B" if next_player == 1 else "#8B2D5F"
                self.status_label.configure(
                    text=f"Player {next_symbol}'s turn",
                    text_color=next_color
                )
                
                # If playing against AI and it's AI's turn
                if self.mode.get() == "human_vs_ai" and self.game.current_player == 2:  # O is AI
                    self.root.after(800, self.ai_move)
        
        # After the game is over, refresh the history panel
        if self.game.game_over:
            # Allow a little time for game to be saved
            self.root.after(1000, self.load_history)
    
    def show_win_animation(self, winner):
        """Show animation for win or draw result"""
        animation_name = f"{winner.lower()}_win" if winner in ["X", "O"] else "draw"
        
        # Get animation path using asset manager
        animation_path = self.assets.get_animation_path(animation_name)
        
        if (animation_path and os.path.exists(animation_path)):
            self.play_animation(animation_path)
        else:
            # Try to generate a placeholder animation
            print(f"Animation {animation_name} not found. Generating placeholder...")
            self.assets.generate_placeholder_animations()
            
            # Try again with the placeholder
            animation_path = self.assets.get_animation_path(animation_name)
            if (animation_path and os.path.exists(animation_path)):
                self.play_animation(animation_path)
            else:
                # Fallback to showing a win message directly in the results area
                self._show_win_message(winner)
    
    def _show_win_message(self, winner):
        """Display a win message directly in the animation area"""
        # Clear any existing content
        for widget in self.animation_frame.winfo_children():
            widget.destroy()
            
        winner_text = "X Wins!" if winner == "X" else ("O Wins!" if winner == "O" else "It's a Draw!")
        winner_color = "#2D5F8B" if winner == "X" else "#8B2D5F" if winner == "O" else "#FFC107"
        
        # Create fancy result display
        result_frame = ctk.CTkFrame(self.animation_frame, fg_color="#333333", corner_radius=10)
        result_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        result_label = ctk.CTkLabel(
            result_frame,
            text=winner_text,
            font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
            text_color=winner_color
        )
        result_label.pack(expand=True)
    
    def play_animation(self, animation_path):
        """Play animation from the given path"""
        try:
            # Clear any existing animation
            for widget in self.animation_frame.winfo_children():
                widget.destroy()
            
            # Get the base filename
            base_filename = os.path.basename(animation_path)
            
            # Use asset manager to load frames
            self.animation_frames = self.assets.load_gif_frames(
                base_filename, 
                size=(160, 100)
            )
            
            if not self.animation_frames:
                print(f"No animation frames loaded for {base_filename}")
                # Fallback to static image
                winner_text = "X Wins!" if "x_win" in base_filename else (
                             "O Wins!" if "o_win" in base_filename else "Draw!")
                
                result_frame = ctk.CTkFrame(self.animation_frame, fg_color="#333333")
                result_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
                
                result_label = ctk.CTkLabel(
                    result_frame,
                    text=winner_text,
                    font=ctk.CTkFont(size=28, weight="bold"),
                    text_color="#FFFFFF"
                )
                result_label.pack(expand=True)
                return
            
            # Create animation label
            self.animation_label = ctk.CTkLabel(
                self.animation_frame, 
                text="",
                image=self.animation_frames[0]  # Start with first frame
            )
            self.animation_label.pack(expand=True)
            
            # Start animation
            self.current_frame = 0
            self.animation_running = True
            self.update_animation_frame()
            
        except Exception as e:
            print(f"Error playing animation: {e}")
    
    def update_animation_frame(self):
        """Update the current animation frame"""
        if not self.animation_running or not self.animation_frames:
            return
        
        try:
            # Update the label with the current frame
            if 0 <= self.current_frame < len(self.animation_frames):
                # Update to current frame
                self.animation_label.configure(image=self.animation_frames[self.current_frame])
                
                # Move to next frame
                self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
                
                # Schedule the next frame
                self.root.after(100, self.update_animation_frame)
            else:
                # End of animation
                self.animation_running = False
        except Exception as e:
            print(f"Error updating animation frame: {e}")
            self.animation_running = False
    
    def ai_move(self):
        if not self.game.game_over and not self.animation_running and self.ai.model_exists():
            ai_row, ai_col = self.ai.get_move(self.game.board)
            if ai_row is not None and ai_col is not None:
                self.make_move(ai_row, ai_col)
    
    def title_clicked(self):
        """Handle title click to start a new game with visual feedback"""
        # Flash the title by changing color temporarily
        original_color = self.title_label.cget("text_color")
        self.title_label.configure(text_color="#4CAF50")  # Green flash
        
        # Reset game
        self.reset_game()
        
        # Return title color to normal after a delay
        self.root.after(500, lambda: self.title_label.configure(text_color=original_color))
    
    def reset_game(self):
        """Reset the game to its initial state"""
        # Flash the reset button to provide feedback
        orig_color = self.reset_btn.cget("fg_color")
        self.reset_btn.configure(fg_color="#FFC107")  # Highlight with yellow
        self.root.after(200, lambda: self.reset_btn.configure(fg_color=orig_color))
        
        self.game.reset()
        self.animation_running = False
        
        # Clear animation area
        for widget in self.animation_frame.winfo_children():
            widget.destroy()
        
        # Reset all buttons - use text approach
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].configure(
                    text="",  # Clear text
                    state="normal",
                    fg_color="#383838",
                    text_color="#FFFFFF"  # Reset text color
                )
        
        # Update status with a more prominent message
        self.status_label.configure(
            text="Game Reset - Player X's Turn",
            text_color="#4CAF50"  # Green to indicate successful reset
        )
        
        # After a delay, change back to normal status color
        self.root.after(1500, lambda: self.status_label.configure(
            text="Player X's turn",
            text_color=self.player_colors[1]["fg"]
        ))
        
        # If against AI and AI goes first (which it doesn't in our setup)
        if self.mode.get() == "human_vs_ai" and self.game.current_player == 2:
            self.root.after(800, self.ai_move)
