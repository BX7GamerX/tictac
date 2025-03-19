import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import numpy as np
import os
import datetime
from game import TicTacToeGame

class GameHistoryViewer:
    """Class for viewing previous game data"""
    
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
        """Load game history from the central CSV file"""
        # Clear the games list
        for widget in self.games_list_frame.winfo_children():
            widget.destroy()
        
        # Load game data
        self.games = TicTacToeGame.load_game_history_from_csv()
        
        if not self.games:
            no_games_label = ctk.CTkLabel(
                self.games_list_frame,
                text="No games found",
                font=ctk.CTkFont(size=14),
                text_color="#CCCCCC"
            )
            no_games_label.pack(pady=10)
            return
        
        # Sort game IDs by timestamp (assuming game_id format is datetime-based)
        game_ids = sorted(self.games.keys(), reverse=True)
        
        for game_id in game_ids:
            game = self.games[game_id]
            
            # Format date from game_id
            try:
                date_str = f"{game_id[:4]}-{game_id[4:6]}-{game_id[6:8]}"
                time_str = f"{game_id[9:11]}:{game_id[11:13]}:{game_id[13:15]}"
                date_display = f"{date_str} {time_str}"
            except:
                date_display = game_id
            
            # Get winner info
            winner = game.get('winner')
            if winner:
                winner_text = f"Winner: Player {winner} ({self.player_symbols[winner]})"
            else:
                winner_text = "Draw" if game['moves'] else "Incomplete"
            
            # Create game entry
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
                text=date_display,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#AAAAAA"
            )
            id_label.pack(anchor=tk.W, padx=10, pady=(10, 0))
            
            # Winner label with different color based on winner
            if winner:
                text_color = self.player_colors[winner]["fg"]
            elif winner_text == "Draw":
                text_color = "#FFC107"  # Yellow for draw
            else:
                text_color = "#CCCCCC"  # Gray for incomplete
            
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
    
    def select_game(self, game_id):
        """Select a game to view
        
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
            
            # Get winner info
            winner = game.get('winner')
            if winner:
                winner_text = f"Winner: Player {winner} ({self.player_symbols[winner]})"
            else:
                winner_text = "Draw" if len(game['moves']) == 9 else "Incomplete"
            
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
                text=f"Game: {date_display}\n{winner_text}\nMoves: {len(game['moves'])}"
            )
            
            # Update move label
            total_moves = len(game['moves'])
            self.move_label.configure(text=f"Move: 0/{total_moves}")
        
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
        
        header_label = ctk.CTkLabel(
            header_frame,
            text=f"Game ID: {self.selected_game_id}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#EEEEEE"
        )
        header_label.pack(anchor=tk.W, padx=10, pady=5)
        
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
        """Show the previous move in the selected game"""
        if self.selected_game_id and self.selected_move > 0:
            self.selected_move -= 1
            self.update_game_display()
    
    def show_next_move(self):
        """Show the next move in the selected game"""
        if not self.selected_game_id:
            return
            
        game = self.games.get(self.selected_game_id)
        if not game:
            return
            
        if self.selected_move < len(game['moves']):
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
        """Show the first move (empty board)"""
        if not self.selected_game_id:
            return
        
        # Stop any ongoing playback
        self.stop_playback()
        
        # Reset to empty board
        self.selected_move = 0
        self.current_board = np.zeros((3, 3), dtype=int)
        self.update_board_display()
        
        # Update move counter
        game = self.games.get(self.selected_game_id)
        if game:
            self.move_label.configure(text=f"Move: 0/{len(game['moves'])}")
        
        # Update UI state
        self.update_ui_state()
    
    def show_last_move(self):
        """Show the last move of the game"""
        if not self.selected_game_id:
            return
        
        # Stop any ongoing playback
        self.stop_playback()
        
        game = self.games.get(self.selected_game_id)
        if not game or not game['moves']:
            return
        
        # Set to last move
        self.selected_move = len(game['moves'])
        
        # Update board to final state
        self.current_board = game['moves'][-1]['board'].copy()
        self.update_board_display()
        
        # Update move counter
        self.move_label.configure(text=f"Move: {self.selected_move}/{len(game['moves'])}")
        
        # Update UI state
        self.update_ui_state()
    
    def on_closing(self):
        """Handle window closing event"""
        # Stop any ongoing playback
        self.stop_playback()
        self.window.destroy()
    
    def run(self):
        """Run the viewer as a standalone application"""
        self.window.mainloop()

# Allow running this module directly
if __name__ == "__main__":
    viewer = GameHistoryViewer()
    viewer.run()
