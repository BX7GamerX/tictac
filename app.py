import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageSequence
import os
from game import TicTacToeGame
from ai_player import AIPlayer
from assets_manager import AssetManager, ASSETS_DIR
from game_history import GameHistoryViewer
from ai_trainer import AITrainingWindow

class TicTacToeApp:
    def __init__(self, root, assets_manager=None):
        self.root = root
        self.root.title("Tic Tac Toe")
        self.root.geometry("600x700")
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
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame with padding
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#252525", corner_radius=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Title with better styling (made more compact) - now clickable
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", cursor="hand2")
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
        separator = ctk.CTkFrame(self.main_frame, height=2, fg_color="#3E92CC")
        separator.pack(fill=tk.X, padx=50, pady=(2, 10))
        
        # Mode selection with improved styling (more compact)
        mode_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
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
        ai_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
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
        self.board_frame = ctk.CTkFrame(self.main_frame, fg_color="#2A2A2A", corner_radius=10)
        self.board_frame.pack(pady=(20, 10), padx=20)
        
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        
        for i in range(3):
            for j in range(3):
                button = ctk.CTkButton(
                    self.board_frame, 
                    text="",  # Start with empty text
                    width=95,  # Slightly larger
                    height=95, # Slightly larger
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
        self.animation_container = ctk.CTkFrame(self.main_frame, fg_color="#2D2D2D", corner_radius=10, height=120)
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
        status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        status_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="Player X's turn", 
            font=ctk.CTkFont(family="Arial", size=18, weight="bold"),
            text_color="#EEEEEE"
        )
        self.status_label.pack()
        
        # Make the button container frame more visible with a subtle background
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="#2A2A2A", corner_radius=10)
        button_frame.pack(fill=tk.X, pady=15, padx=20)
        
        # Add a centered container for buttons
        button_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_container.pack(pady=15)
        
        # Make New Game button larger and more visible
        self.reset_btn = ctk.CTkButton(
            button_container, 
            text="New Game", 
            command=self.reset_game,
            font=ctk.CTkFont(size=18, weight="bold"),  # Larger, bolder font
            fg_color="#4CAF50",  # Bright green - more visible
            hover_color="#3E8E41",  # Darker green on hover
            width=150,  # Larger width
            height=50,  # Larger height
            corner_radius=10,
            border_width=2,  # Add border for extra visibility
            border_color="#AAAAAA"  # Light gray border
        )
        self.reset_btn.pack(side=tk.LEFT, padx=15)
        
        # Make Quit button match the style of New Game button
        quit_btn = ctk.CTkButton(
            button_container, 
            text="Quit", 
            command=self.root.quit,
            font=ctk.CTkFont(size=18, weight="bold"),  # Match New Game button
            fg_color="#E63946",  # Keep red for quit
            hover_color="#C5313E",
            width=150,  # Same size as New Game
            height=50,
            corner_radius=10,
            border_width=2,
            border_color="#AAAAAA"
        )
        quit_btn.pack(side=tk.LEFT, padx=15)
        
        # Add a title to the button section for better clarity
        button_title = ctk.CTkLabel(
            button_frame,
            text="Game Controls",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color="#888888"
        )
        button_title.pack(pady=(10, 0))  # Place at top of frame
        
        # Add "Game History" button next to the other buttons
        history_btn = ctk.CTkButton(
            button_container, 
            text="Game History", 
            command=self.show_game_history,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#3E92CC",  # Blue
            hover_color="#2D7DB3",
            width=150,
            height=50,
            corner_radius=10,
            border_width=2,
            border_color="#AAAAAA"
        )
        history_btn.pack(side=tk.LEFT, padx=15)
        
        # Ensure the button frame is above the button container
        button_title.lift()
    
    # Add a method to show game history
    def show_game_history(self):
        """Show the game history viewer"""
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
