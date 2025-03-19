import customtkinter as ctk
import tkinter as tk
import numpy as np
import time
import random
import threading
from game import TicTacToeGame

class AITrainingWindow:
    """Window for AI model training options and progress display"""
    
    def __init__(self, parent=None, callback_on_complete=None):
        """Initialize the training window
        
        Args:
            parent: Parent window
            callback_on_complete: Function to call when training completes
        """
        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("AI Model Training")
        self.window.geometry("500x550")
        self.window.configure(fg_color="#1E1E1E")
        
        # Store callback
        self.callback_on_complete = callback_on_complete
        
        # Set up variables
        self.is_training = False
        self.training_thread = None
        self.games_completed = 0
        self.total_games = 0
        self.simulation_speed = tk.DoubleVar(value=1.0)  # Default speed multiplier
        
        # Define default training parameters
        self.training_params = {
            "num_games": 100,          # Number of games to simulate
            "random_play": True,       # Use random play for data generation
            "save_interval": 10,       # Save model every N games
            "visualize": True,         # Show game progress visually
        }
        
        # Add training state variables
        self.data_generated = False
        self.is_training_model = False
        
        # Setup UI first
        self.setup_ui()
        
        # Ensure window is created and updated before setting grab
        self.window.update_idletasks()
        
        # Schedule grab_set to execute after the window is fully drawn
        self.window.after(100, self._make_modal)
    
    def _make_modal(self):
        """Make the window modal after it's fully visible"""
        try:
            # Force multiple updates to ensure window is fully rendered
            self.window.update()
            self.window.update_idletasks()
            
            # Make the window modal
            self.window.grab_set()
            self.window.focus_force()
            
            # Explicitly bring buttons to front
            self.generate_btn.lift()
            self.train_model_btn.lift()
            self.cancel_btn.lift()
        except Exception as e:
            print(f"Could not make window modal: {e}")
    
    def setup_ui(self):
        """Set up the training window UI"""
        # Main container with padding
        self.main_frame = ctk.CTkFrame(self.window, fg_color="#252525", corner_radius=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title - Make it clickable like in the main game
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", cursor="hand2")
        title_frame.pack(pady=(15, 5))
        title_frame.bind("<Button-1>", lambda event: self.title_clicked())
        
        self.title_label = ctk.CTkLabel(
            title_frame, 
            text="AI Model Training", 
            font=ctk.CTkFont(family="Arial", size=22, weight="bold"),
            text_color="#3E92CC",
            cursor="hand2"  # Change cursor to hand when hovering
        )
        self.title_label.pack()
        self.title_label.bind("<Button-1>", lambda event: self.title_clicked())
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="Train the AI model with self-play simulation\n(Click title to start simulation)",  # Add hint text
            font=ctk.CTkFont(size=12),
            text_color="#BBBBBB",
            cursor="hand2"
        )
        subtitle.pack(pady=(0, 5))
        subtitle.bind("<Button-1>", lambda event: self.title_clicked())
        
        # Separator
        separator = ctk.CTkFrame(self.main_frame, height=2, fg_color="#3E92CC")
        separator.pack(fill=tk.X, padx=30, pady=(0, 15))
        
        # Options frame
        options_frame = ctk.CTkFrame(self.main_frame, fg_color="#2A2A2A", corner_radius=10)
        options_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Number of games option
        games_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        games_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        games_label = ctk.CTkLabel(
            games_frame,
            text="Number of Training Games:",
            font=ctk.CTkFont(size=14),
            width=180,
            anchor="w"
        )
        games_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.games_entry = ctk.CTkEntry(
            games_frame,
            width=80,
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        self.games_entry.pack(side=tk.LEFT)
        self.games_entry.insert(0, str(self.training_params["num_games"]))
        
        # Visualization option
        visual_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        visual_frame.pack(fill=tk.X, padx=15, pady=5)
        
        visual_label = ctk.CTkLabel(
            visual_frame,
            text="Show Training Visualization:",
            font=ctk.CTkFont(size=14),
            width=180,
            anchor="w"
        )
        visual_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.visual_var = tk.BooleanVar(value=self.training_params["visualize"])
        visual_switch = ctk.CTkSwitch(
            visual_frame,
            text="",
            variable=self.visual_var,
            onvalue=True,
            offvalue=False,
            button_color="#3E92CC",
            button_hover_color="#2D7DB3",
            progress_color="#4CAF50"
        )
        visual_switch.pack(side=tk.LEFT)
        
        # Simulation speed (only when visualization is on)
        speed_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        speed_frame.pack(fill=tk.X, padx=15, pady=5)
        
        speed_label = ctk.CTkLabel(
            speed_frame,
            text="Simulation Speed:",
            font=ctk.CTkFont(size=14),
            width=180,
            anchor="w"
        )
        speed_label.pack(side=tk.LEFT, padx=(0, 10))
        
        speed_slider = ctk.CTkSlider(
            speed_frame,
            from_=0.5,
            to=10.0,
            variable=self.simulation_speed,
            width=150,
            progress_color="#3E92CC",
            button_color="#2D7DB3"
        )
        speed_slider.pack(side=tk.LEFT)
        
        speed_value = ctk.CTkLabel(
            speed_frame,
            text=f"{self.simulation_speed.get()}x",
            font=ctk.CTkFont(size=12),
            width=30
        )
        speed_value.pack(side=tk.LEFT, padx=10)
        
        # Update speed value label when slider changes
        def update_speed_label(*args):
            speed_value.configure(text=f"{self.simulation_speed.get():.1f}x")
        
        self.simulation_speed.trace_add("write", update_speed_label)
        
        # Create a frame for the simulation visualization
        self.simulation_frame = ctk.CTkFrame(self.main_frame, fg_color="#2A2A2A", corner_radius=10)
        self.simulation_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Create board display
        self.board_display_frame = ctk.CTkFrame(self.simulation_frame, fg_color="transparent")
        self.board_display_frame.pack(expand=True, pady=15)
        
        self.cells = [[None for _ in range(3)] for _ in range(3)]
        
        for i in range(3):
            for j in range(3):
                cell = ctk.CTkButton(
                    self.board_display_frame, 
                    text="",
                    width=60,
                    height=60,
                    font=ctk.CTkFont(size=30, weight="bold"),
                    fg_color="#383838",
                    text_color="#FFFFFF",
                    corner_radius=5,
                    state="disabled"  # Cells are non-interactive
                )
                cell.grid(row=i, column=j, padx=3, pady=3)
                self.cells[i][j] = cell
        
        # Progress information
        progress_frame = ctk.CTkFrame(self.main_frame, fg_color="#2A2A2A", corner_radius=10)
        progress_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to generate training data",
            font=ctk.CTkFont(size=14),
            text_color="#EEEEEE"
        )
        self.status_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            orientation="horizontal",
            mode="determinate",
            progress_color="#4CAF50",
            height=15,
            corner_radius=5
        )
        self.progress_bar.pack(fill=tk.X, padx=20, pady=10)
        self.progress_bar.set(0)
        
        self.game_stats_label = ctk.CTkLabel(
            progress_frame,
            text="Games: 0/0 | X Wins: 0 | O Wins: 0 | Draws: 0",
            font=ctk.CTkFont(size=12),
            text_color="#CCCCCC"
        )
        self.game_stats_label.pack(pady=5)
        
        # Button frame with strong visual appearance
        button_frame = ctk.CTkFrame(
            self.main_frame, 
            fg_color="#3A3A3A",  # Lighter background for contrast
            corner_radius=10,
            border_width=2,     # Add border
            border_color="#4CAF50"  # Green border to highlight the section
        )
        button_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        # Clear section title to make it obvious
        section_label = ctk.CTkLabel(
            button_frame,
            text="TRAINING ACTIONS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        )
        section_label.pack(pady=(15, 10))
        
        # Create buttons directly in the button frame (no nested container)
        # Generate training data button - Large and bright
        self.generate_btn = ctk.CTkButton(
            button_frame,
            text="1. Generate Training Data",
            command=self.start_training_simulation,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#4CAF50",  # Bright green
            hover_color="#3E8E41",
            corner_radius=8,
            height=45,  # Taller
            width=300,  # Fixed width
            border_width=1,  # Add border for better visibility
            border_color="#FFFFFF"
        )
        self.generate_btn.pack(padx=20, pady=(0, 10))
        
        # Train AI Model button
        self.train_model_btn = ctk.CTkButton(
            button_frame,
            text="2. Train AI Model",
            command=self.start_model_training,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            corner_radius=8,
            height=45,  # Taller
            width=300,  # Fixed width
            border_width=1,  # Add border
            border_color="#FFFFFF",
            state="disabled"
        )
        self.train_model_btn.pack(padx=20, pady=(0, 10))
        
        # Cancel button
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel_training,
            font=ctk.CTkFont(size=14),
            fg_color="#E63946",
            hover_color="#C5313E",
            corner_radius=8,
            height=35,
            width=300,  # Fixed width
        )
        self.cancel_btn.pack(padx=20, pady=(0, 15))
        
        # Set up window close handling
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Force an update to ensure all elements are properly rendered
        self.window.update_idletasks()
    
    def title_clicked(self):
        """Handle title click to start simulation with visual feedback"""
        # Only start if we're not already training and the generate button is enabled
        if not self.is_training and not self.is_training_model and self.generate_btn.cget("state") == "normal":
            # Flash the title by changing color temporarily
            original_color = self.title_label.cget("text_color")
            self.title_label.configure(text_color="#4CAF50")  # Green flash
            
            # Start the simulation
            self.start_training_simulation()
            
            # Return title color to normal after a delay
            self.window.after(500, lambda: self.title_label.configure(text_color=original_color))
        elif self.data_generated and not self.is_training_model and self.train_model_btn.cget("state") == "normal":
            # If data is generated but model not trained, clicking the title starts the model training
            original_color = self.title_label.cget("text_color")
            self.title_label.configure(text_color="#3E92CC")  # Blue flash
            
            # Start model training
            self.start_model_training()
            
            # Return title color to normal after a delay
            self.window.after(500, lambda: self.title_label.configure(text_color=original_color))
    
    def start_training_simulation(self):
        """Start training data generation simulation"""
        # Parse input values
        try:
            num_games = int(self.games_entry.get())
            if num_games <= 0:
                raise ValueError("Number of games must be positive")
        except ValueError as e:
            self.show_error(f"Invalid input: {str(e)}")
            return
        
        # Update parameters
        self.training_params["num_games"] = num_games
        self.training_params["visualize"] = self.visual_var.get()
        
        # Reset stats
        self.games_completed = 0
        self.total_games = num_games
        self.win_stats = {"X": 0, "O": 0, "Draw": 0}
        
        # Update UI
        self.status_label.configure(text="Generating training data...")
        self.progress_bar.set(0)
        self.game_stats_label.configure(text=f"Games: 0/{num_games} | X Wins: 0 | O Wins: 0 | Draws: 0")
        
        # Disable buttons
        self.generate_btn.configure(state="disabled")
        
        # Start simulation in separate thread to keep UI responsive
        self.is_training = True
        self.training_thread = threading.Thread(target=self.run_training_simulation)
        self.training_thread.daemon = True
        self.training_thread.start()
    
    def run_training_simulation(self):
        """Run the training data generation simulation"""
        try:
            # Create a game instance for simulation
            game = TicTacToeGame()
            
            for i in range(self.total_games):
                if not self.is_training:
                    break  # Stop if training was cancelled
                
                # Reset game for new simulation
                game.reset()
                
                # Play a random game
                self.play_random_game(game)
                
                # Update stats based on game outcome
                if game.winner == 1:
                    self.win_stats["X"] += 1
                elif game.winner == 2:
                    self.win_stats["O"] += 1
                else:
                    self.win_stats["Draw"] += 1
                
                # Update progress
                self.games_completed += 1
                progress = self.games_completed / self.total_games
                
                # Update UI in main thread
                self.window.after(0, self.update_training_progress, progress)
                
                # Small delay between games if needed
                if self.training_params["visualize"] and self.games_completed < self.total_games:
                    time.sleep(0.5 / self.simulation_speed.get())  # Adjust delay based on speed
            
            # Training complete
            if self.is_training:  # Only if not cancelled
                self.window.after(0, self.finish_training, True)
        
        except Exception as e:
            print(f"Error in training simulation: {e}")
            self.window.after(0, self.finish_training, False, str(e))
    
    def play_random_game(self, game):
        """Play a random game by selecting random valid moves
        
        Args:
            game: TicTacToeGame instance
        """
        # Continue making moves until game is over
        while not game.game_over:
            # Get all valid moves
            empty_cells = game.get_empty_cells()
            
            if not empty_cells:
                break  # No valid moves left
            
            # Select a random move
            row, col = random.choice(empty_cells)
            
            # Make the move
            game.make_move(row, col)
            
            # Update visualization if enabled
            if self.training_params["visualize"]:
                # Schedule UI update in main thread
                self.window.after(0, self.update_board_display, game.board.copy())
                
                # Add delay based on simulation speed
                delay = 0.3 / self.simulation_speed.get()
                time.sleep(delay)
    
    def update_board_display(self, board):
        """Update the board visualization with current state
        
        Args:
            board: 3x3 numpy array with game state
        """
        # Player symbols and colors
        symbols = {0: "", 1: "X", 2: "O"}
        colors = {
            1: {"fg": "#4F85CC", "bg": "#2D5F8B"},  # X: Blue
            2: {"fg": "#FF5C8D", "bg": "#8B2D5F"}   # O: Pink
        }
        
        # Update each cell
        for i in range(3):
            for j in range(3):
                cell_value = board[i, j]
                
                if cell_value == 0:
                    # Empty cell
                    self.cells[i][j].configure(
                        text="",
                        fg_color="#383838",
                        text_color="#FFFFFF"
                    )
                else:
                    # Player cell
                    self.cells[i][j].configure(
                        text=symbols[cell_value],
                        fg_color=colors[cell_value]["bg"],
                        text_color=colors[cell_value]["fg"]
                    )
    
    def update_training_progress(self, progress):
        """Update the training progress display
        
        Args:
            progress: Progress value (0.0 to 1.0)
        """
        # Update progress bar
        self.progress_bar.set(progress)
        
        # Update stats label
        stats_text = (
            f"Games: {self.games_completed}/{self.total_games} | "
            f"X Wins: {self.win_stats['X']} | "
            f"O Wins: {self.win_stats['O']} | "
            f"Draws: {self.win_stats['Draw']}"
        )
        self.game_stats_label.configure(text=stats_text)
    
    def finish_training(self, success, error_msg=None):
        """Handle training completion
        
        Args:
            success: Whether training completed successfully
            error_msg: Error message if training failed
        """
        self.is_training = False
        
        if success:
            self.status_label.configure(
                text=f"Training data generation complete! {self.games_completed} games generated.",
                text_color="#4CAF50"
            )
            
            # Enable the Train AI Model button
            self.data_generated = True
            self.train_model_btn.configure(state="normal")
            
        else:
            self.status_label.configure(
                text=f"Training failed: {error_msg}",
                text_color="#E63946"
            )
        
        # Re-enable generate button
        self.generate_btn.configure(state="normal")
    
    def start_model_training(self):
        """Start training the AI model using the generated data"""
        if not self.data_generated:
            self.show_error("No training data available. Generate data first.")
            return
        
        # Update UI
        self.status_label.configure(text="Training AI model...", text_color="#FFC107")
        self.train_model_btn.configure(state="disabled")
        self.generate_btn.configure(state="disabled")
        
        # Start training in a separate thread
        self.is_training_model = True
        threading.Thread(target=self._run_model_training, daemon=True).start()
    
    def _run_model_training(self):
        """Run the actual AI model training process"""
        try:
            from ai_player import AIPlayer
            
            # Create AI player and train on generated data
            ai_player = AIPlayer()
            
            # Start with progress indication
            self.window.after(0, lambda: self.progress_bar.set(0.1))
            self.window.after(0, lambda: self.status_label.configure(text="Preparing training data..."))
            
            # Load the most recent games
            import time
            start_time = time.time()
            
            # Begin actual training
            self.window.after(0, lambda: self.status_label.configure(text="Training neural network..."))
            self.window.after(0, lambda: self.progress_bar.set(0.3))
            
            # Train the model
            success = ai_player.train_model()
            
            # Log time taken
            elapsed_time = time.time() - start_time
            print(f"Training completed in {elapsed_time:.2f} seconds")
            
            # Update progress for success or failure
            if success:
                self.window.after(0, lambda: self.progress_bar.set(1.0))
                self.window.after(0, lambda: self._complete_model_training(True))
            else:
                self.window.after(0, lambda: self.progress_bar.set(0.5))
                self.window.after(0, lambda: self._complete_model_training(False, "Failed to train model"))
                
        except Exception as e:
            print(f"Error training model: {e}")
            import traceback
            traceback.print_exc()
            self.window.after(0, lambda: self._complete_model_training(False, str(e)))
    
    def _complete_model_training(self, success, error_msg=None):
        """Handle model training completion
        
        Args:
            success: Whether model training completed successfully
            error_msg: Error message if training failed
        """
        self.is_training_model = False
        
        if success:
            self.status_label.configure(
                text="AI model trained successfully!",
                text_color="#4CAF50"
            )
            
            # Re-enable generate button in case user wants to generate more data
            self.generate_btn.configure(state="normal")
            
            # Call the callback (this should update the main app to show the AI is ready)
            if self.callback_on_complete:
                self.callback_on_complete()
                
            # Show message that we can close the window now
            self.window.after(1000, lambda: self.status_label.configure(
                text="AI model trained successfully! You can close this window.",
                text_color="#4CAF50"
            ))
            
        else:
            self.status_label.configure(
                text=f"Model training failed: {error_msg}",
                text_color="#E63946"
            )
            
            # Re-enable both buttons to allow retrying
            self.generate_btn.configure(state="normal")
            self.train_model_btn.configure(state="normal")
    
    def cancel_training(self):
        """Cancel ongoing training"""
        if self.is_training:
            self.is_training = False
            self.status_label.configure(
                text="Training cancelled",
                text_color="#FFC107"
            )
            # Re-enable buttons
            self.generate_btn.configure(state="normal")
            
        elif self.is_training_model:
            self.is_training_model = False
            self.status_label.configure(
                text="Model training cancelled",
                text_color="#FFC107"
            )
            # Re-enable buttons
            self.generate_btn.configure(state="normal")
            self.train_model_btn.configure(state="normal")
            
        else:
            self.window.destroy()
    
    def show_error(self, message):
        """Show error message
        
        Args:
            message: Error message to display
        """
        self.status_label.configure(
            text=f"Error: {message}",
            text_color="#E63946"
        )
    
    def on_closing(self):
        """Handle window closing"""
        # Cancel training if in progress
        if self.is_training or self.is_training_model:
            self.cancel_training()
        
        # Close window
        self.window.destroy()

# For testing - Improved standalone execution
if __name__ == "__main__":
    try:
        # Create root window but make it minimal
        root = ctk.CTk()
        root.title("AI Trainer Test")
        root.geometry("200x100")
        
        # Add a label and button to the root window
        label = ctk.CTkLabel(root, text="AI Trainer Test Window")
        label.pack(pady=10)
        
        # Function to open trainer window
        def open_trainer():
            # Disable the button while trainer is open
            open_btn.configure(state="disabled")
            
            # Create trainer with callback to re-enable button
            def on_trainer_close():
                open_btn.configure(state="normal")
                
            # Launch trainer window
            trainer = AITrainingWindow(root, callback_on_complete=on_trainer_close)
            
            # Handle trainer window closing
            def check_trainer_window():
                if not trainer.window.winfo_exists():
                    open_btn.configure(state="normal")
                    return
                root.after(100, check_trainer_window)
            
            # Start checking if trainer window exists
            root.after(100, check_trainer_window)
        
        # Button to open trainer
        open_btn = ctk.CTkButton(
            root, 
            text="Open AI Trainer", 
            command=open_trainer,
            fg_color="#4CAF50",
            hover_color="#3E8E41"
        )
        open_btn.pack(pady=10)
        
        # Add quit button 
        quit_btn = ctk.CTkButton(
            root,
            text="Quit",
            command=root.quit,
            fg_color="#E63946",
            hover_color="#C5313E"
        )
        quit_btn.pack(pady=5)
        
        # Start main loop with error handling
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        exit(0)
    except Exception as e:
        print(f"\nError in AI Trainer: {e}")
        exit(1)
