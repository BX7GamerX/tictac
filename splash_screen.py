import customtkinter as ctk
import tkinter as tk
import threading
import time
import os
from PIL import Image, ImageTk, ImageSequence
from assets_manager import AssetManager, ASSETS_DIR
from utils import convert_to_ctk_image, load_gif_frames_as_ctk, safe_after, cancel_after_safely

class SplashScreen:
    """Splash screen with loading animation and progress updates"""
    
    def __init__(self, on_complete_callback=None):
        """Initialize the splash screen
        
        Args:
            on_complete_callback: Function to call when loading completes. 
                                 Will be passed the loaded data as an argument.
        """
        self.on_complete_callback = on_complete_callback
        self.is_loading = True
        self.loading_thread = None
        self.loaded_data = {}
        self.after_ids = []  # Track scheduled callbacks
        
        # Create window
        self.window = ctk.CTk()
        self.window.title("Loading")
        self.window.geometry("500x350")
        self.window.configure(fg_color="#1E1E1E")
        self.window.overrideredirect(True)  # Frameless window
        
        # Center window on screen
        self.center_window()
        
        # Setup UI
        self.setup_ui()
        
        # Initialize animation variables
        self.animation_frames = []
        self.current_frame = 0
        self.animation_label = None
        
        # Set proper handler for when window is destroyed
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Start loading data in background
        self.loading_thread = threading.Thread(target=self._load_data)
        self.loading_thread.daemon = True
    
    def center_window(self):
        """Center the window on the screen"""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        x = (screen_width - 500) // 2
        y = (screen_height - 350) // 2
        
        self.window.geometry(f"500x350+{x}+{y}")
    
    def setup_ui(self):
        """Set up the UI elements"""
        # Main container
        main_frame = ctk.CTkFrame(self.window, fg_color="#252525", corner_radius=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Tic Tac Toe",
            font=ctk.CTkFont(family="Arial", size=32, weight="bold"),
            text_color="#3E92CC"
        )
        title_label.pack(pady=(25, 5))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Loading game resources...",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color="#AAAAAA"
        )
        subtitle_label.pack(pady=(0, 15))
        
        # Animation area
        self.animation_frame = ctk.CTkFrame(main_frame, fg_color="#2A2A2A", corner_radius=10, height=120)
        self.animation_frame.pack(fill=tk.X, padx=20)
        
        # Progress status
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Initializing...",
            font=ctk.CTkFont(family="Arial", size=12),
            text_color="#DDDDDD"
        )
        self.status_label.pack(pady=(20, 5))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            orientation="horizontal",
            mode="indeterminate",
            height=15,
            corner_radius=10,
            progress_color="#4CAF50"
        )
        self.progress_bar.pack(fill=tk.X, padx=40, pady=(5, 20))
        
        # Version info
        version_label = ctk.CTkLabel(
            main_frame,
            text="Version 1.0",
            font=ctk.CTkFont(family="Arial", size=10),
            text_color="#666666"
        )
        version_label.pack(side=tk.BOTTOM, pady=10)
    
    def load_animation(self):
        """Load and start the loading animation"""
        try:
            # Create assets directory if it doesn't exist
            os.makedirs(ASSETS_DIR, exist_ok=True)
            
            # Look for loading animation
            animation_path = os.path.join(ASSETS_DIR, "loading.gif")
            
            # If animation doesn't exist, create a basic one
            if not os.path.exists(animation_path):
                self._generate_placeholder_animation()
                # Try again with the placeholder
                if not os.path.exists(animation_path):
                    # If still doesn't exist, show static message
                    loading_label = ctk.CTkLabel(
                        self.animation_frame,
                        text="Loading...",
                        font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
                        text_color="#3E92CC"
                    )
                    loading_label.pack(expand=True, pady=40)
                    return
            
            # Load GIF frames as CTkImage objects to prevent warnings
            self.animation_frames = load_gif_frames_as_ctk(animation_path, size=(100, 100))
            
            if not self.animation_frames:
                # If no frames were loaded, show static message
                loading_label = ctk.CTkLabel(
                    self.animation_frame,
                    text="Loading...",
                    font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
                    text_color="#3E92CC"
                )
                loading_label.pack(expand=True, pady=40)
                return
                
            # Create animation label
            self.animation_label = ctk.CTkLabel(
                self.animation_frame,
                text="",
                image=self.animation_frames[0] if self.animation_frames else None
            )
            self.animation_label.pack(expand=True, pady=10)
            
            # Start animation
            self.current_frame = 0
            self.animate_loading()
            
        except Exception as e:
            print(f"Error loading animation: {e}")
            # Show static message as fallback
            loading_label = ctk.CTkLabel(
                self.animation_frame,
                text="Loading...",
                font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
                text_color="#3E92CC"
            )
            loading_label.pack(expand=True, pady=40)
    
    def animate_loading(self):
        """Update the animation frame"""
        if not self.is_loading or not hasattr(self, 'window') or not self.window.winfo_exists():
            return
            
        if self.animation_label and self.animation_frames:
            try:
                # Update to next frame
                self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
                self.animation_label.configure(image=self.animation_frames[self.current_frame])
                
                # Continue animation if still loading
                if self.is_loading:
                    self.schedule_after(100, self.animate_loading)
            except Exception as e:
                print(f"Error in loading animation: {e}")
    
    def _generate_placeholder_animation(self):
        """Generate a simple loading animation"""
        try:
            from PIL import Image, ImageDraw
            
            # Create a series of frames with a moving dot
            frames = []
            size = (200, 100)
            color = "#3E92CC"
            
            for i in range(10):
                frame = Image.new("RGBA", size, (42, 42, 42, 255))
                draw = ImageDraw.Draw(frame)
                
                # Draw the dots
                radius = 8
                spacing = 30
                center_y = size[1] // 2
                start_x = (size[0] - spacing * 4) // 2
                
                for j in range(5):
                    # Calculate alpha - highest for current position
                    alpha = 255 if j == i % 5 else max(50, 255 - abs(j - i % 5) * 70)
                    
                    # Draw the dot
                    x = start_x + j * spacing
                    dot_color = color[:-2] + hex(alpha)[2:].zfill(2)
                    draw.ellipse(
                        (x - radius, center_y - radius, x + radius, center_y + radius),
                        fill=dot_color
                    )
                
                frames.append(frame)
            
            # Save as GIF
            animation_path = os.path.join(ASSETS_DIR, "loading.gif")
            frames[0].save(
                animation_path,
                save_all=True,
                append_images=frames[1:],
                duration=100,
                loop=0
            )
            
            print(f"Generated placeholder animation at {animation_path}")
            return True
            
        except Exception as e:
            print(f"Error generating placeholder animation: {e}")
            return False
    
    def _load_data(self):
        """Load all game data and assets in background thread"""
        try:
            total_steps = 7  # Increased number of steps for more detailed loading
            current_step = 0
            
            # Step 1: Initialize assets manager and check directories
            self.window.after(0, lambda: self._update_progress("Initializing asset manager...", current_step/total_steps))
            current_step += 1
            
            # Create assets directory if it doesn't exist
            os.makedirs(ASSETS_DIR, exist_ok=True)
            
            # Game data directory
            game_data_dir = os.path.join(os.path.dirname(__file__), "game_data")
            os.makedirs(game_data_dir, exist_ok=True)
            
            # Initialize asset manager
            assets_manager = AssetManager()
            self.loaded_data['assets_manager'] = assets_manager
            
            # Step 2: Load animations and visual assets
            self.window.after(0, lambda: self._update_progress("Loading animations and visual assets...", current_step/total_steps))
            current_step += 1
            
            # Ensure core animations exist
            assets_manager.generate_placeholder_animations()
            
            # Check for background animation and generate if needed
            bg_path = os.path.join(ASSETS_DIR, "background.gif")
            if not os.path.exists(bg_path):
                self._generate_background_animation(assets_manager)
            
            # Step 3: Initialize move tracker system
            self.window.after(0, lambda: self._update_progress("Initializing move tracking system...", current_step/total_steps))
            current_step += 1
            
            try:
                from move_tracker import GameMoveTracker
                self.loaded_data['move_tracker_system'] = GameMoveTracker
            except ImportError:
                print("Warning: Move tracker module not available")
                self.loaded_data['move_tracker_system'] = None
            
            # Step 4: Load game history data with optimized integration
            self.window.after(0, lambda: self._update_progress("Loading game history data...", current_step/total_steps))
            current_step += 1
            
            game_history = self._load_game_history()
            self.loaded_data['game_history'] = game_history
            
            # Step 5: Load AI model
            self.window.after(0, lambda: self._update_progress("Checking AI model...", current_step/total_steps))
            current_step += 1
            
            from ai_player import AIPlayer
            ai_player = AIPlayer()
            self.loaded_data['ai_player'] = ai_player
            
            # Step 6: Initialize game engine
            self.window.after(0, lambda: self._update_progress("Initializing game engine...", current_step/total_steps))
            current_step += 1
            
            from game import TicTacToeGame
            game = TicTacToeGame()
            self.loaded_data['game'] = game
            
            # Step 7: Final preparations
            self.window.after(0, lambda: self._update_progress("Finalizing and caching data...", current_step/total_steps))
            current_step += 1
            
            # Calculate and cache some basic game statistics for quick access
            if game_history:
                stats = self._calculate_basic_statistics(game_history)
                self.loaded_data['game_stats'] = stats
            
            # Give a moment to see 100% progress
            time.sleep(0.5)
            
            # Signal loading complete in main thread
            self.window.after(0, self._loading_complete)
            
        except Exception as e:
            print(f"Error during data loading: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error and allow continuing
            self.window.after(0, lambda: self._update_progress(f"Error: {str(e)}", 1.0, error=True))
            self.window.after(2000, self._loading_complete)
    
    def _generate_background_animation(self, assets_manager=None):
        """Generate a more sophisticated background animation for the main menu"""
        try:
            from PIL import Image, ImageDraw
            
            # Create a series of frames with Tic Tac Toe themed animation
            frames = []
            size = (800, 600)
            
            # Colors
            bg_color = (30, 30, 30, 255)  # Dark background
            grid_color = (80, 80, 80, 128)  # Grid lines
            x_color = (79, 133, 204, 180)  # X color
            o_color = (255, 92, 141, 180)  # O color
            
            # Generate 24 frames (smoother animation)
            num_frames = 24
            for i in range(num_frames):
                # Create a new frame
                frame = Image.new("RGBA", size, bg_color)
                draw = ImageDraw.Draw(frame)
                
                # Draw a large Tic Tac Toe grid in the background
                grid_size = 450
                grid_x = (size[0] - grid_size) // 2
                grid_y = (size[1] - grid_size) // 2
                
                # Vertical grid lines
                for j in range(1, 3):
                    x = grid_x + j * (grid_size // 3)
                    draw.line([(x, grid_y), (x, grid_y + grid_size)], fill=grid_color, width=3)
                
                # Horizontal grid lines
                for j in range(1, 3):
                    y = grid_y + j * (grid_size // 3)
                    draw.line([(grid_x, y), (grid_x + grid_size, y)], fill=grid_color, width=3)
                
                # Draw animated X's and O's that fade in and out at different positions
                cell_size = grid_size // 3
                positions = [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)]
                
                for p, (row, col) in enumerate(positions):
                    # Alternate X and O
                    is_x = (p % 2 == 0)
                    
                    # Calculate animation phase (0-1) with offset for each position
                    phase = (i + p * (num_frames // len(positions))) % num_frames / num_frames
                    
                    # Only draw if in active phase (first half of animation)
                    if phase < 0.5:
                        # Calculate alpha (opacity) - fade in, then fade out
                        alpha = 255 * (1 - abs(phase - 0.25) * 4)
                        
                        # Calculate position
                        x1 = grid_x + col * cell_size
                        y1 = grid_y + row * cell_size
                        x2 = x1 + cell_size
                        y2 = y1 + cell_size
                        
                        # Add padding
                        padding = cell_size // 6
                        x1 += padding
                        y1 += padding
                        x2 -= padding
                        y2 -= padding
                        
                        if is_x:
                            # Draw X
                            draw.line([(x1, y1), (x2, y2)], fill=x_color[:3] + (int(alpha),), width=5)
                            draw.line([(x2, y1), (x1, y2)], fill=x_color[:3] + (int(alpha),), width=5)
                        else:
                            # Draw O
                            draw.ellipse([(x1, y1), (x2, y2)], outline=o_color[:3] + (int(alpha),), width=5)
                
                # Add floating particles in the background
                for j in range(30):
                    # Calculate position with movement based on frame
                    angle = (i * 5 + j * 37) % 360
                    import math
                    distance = 250 + 50 * math.sin(math.radians(i * 10 + j * 20))
                    px = size[0] // 2 + int(math.cos(math.radians(angle)) * distance * 0.8)
                    py = size[1] // 2 + int(math.sin(math.radians(angle)) * distance)
                    
                    # Size varies with frame
                    particle_size = 2 + int(2 * math.sin(math.radians(i * 15 + j * 30)))
                    
                    # Color alternates between X and O colors with reduced opacity
                    particle_color = x_color if j % 2 == 0 else o_color
                    opacity = 40 + int(20 * math.sin(math.radians(i * 8 + j * 15)))
                    
                    # Draw the particle
                    draw.ellipse(
                        [(px - particle_size, py - particle_size), 
                         (px + particle_size, py + particle_size)],
                        fill=particle_color[:3] + (opacity,)
                    )
                
                frames.append(frame)
            
            # Save as GIF
            animation_path = os.path.join(ASSETS_DIR, "background.gif")
            frames[0].save(
                animation_path,
                save_all=True,
                append_images=frames[1:],
                duration=50,  # Faster animation
                loop=0
            )
            
            print(f"Generated enhanced background animation at {animation_path}")
            return True
            
        except Exception as e:
            print(f"Error generating background animation: {e}")
            return False
    
    def _load_game_history(self):
        """Load game history data
        
        Returns:
            dict: Game history data
        """
        try:
            # Try to use data integration if available
            try:
                from game_data_integration import GameDataIntegration
                data_manager = GameDataIntegration(use_cache=True)
                history = data_manager.get_all_games()
                print(f"Loaded {len(history)} games from data integration")
                return history
            except ImportError:
                # Fall back to direct loading
                from game import TicTacToeGame
                history = TicTacToeGame.load_game_history_from_csv()
                print(f"Loaded {len(history)} games from CSV")
                return history
        except Exception as e:
            print(f"Error loading game history: {e}")
            return {}
    
    def _update_progress(self, status, progress, error=False):
        """Update the progress display
        
        Args:
            status (str): Status message
            progress (float): Progress value (0.0 to 1.0)
            error (bool): Whether this is an error message
        """
        # Update status
        self.status_label.configure(
            text=status,
            text_color="#E63946" if error else "#DDDDDD"
        )
        
        # Update progress bar
        if progress < 0:
            # Indeterminate mode
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
        else:
            # Determinate mode
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.stop()
            self.progress_bar.set(progress)
    
    def _loading_complete(self):
        """Handle completion of loading"""
        self.is_loading = False
        
        # Stop progress animation
        self.progress_bar.stop()
        self.progress_bar.set(1.0)
        
        # Update status
        self.status_label.configure(text="Loading complete!", text_color="#4CAF50")
        
        # Terminate splash screen immediately without delay
        self._close_and_open_main()

    def _close_and_open_main(self):
        """Close splash screen and open main menu"""
        # First stop all animations and threads to prevent UI updates after window destruction
        self.is_loading = False
        
        # Clean up any stray after commands
        from utils import cleanup_after_commands
        cleanup_after_commands()
        
        # Make a local copy of callback and data
        callback_func = self.on_complete_callback
        if callback_func:
            callback_data = dict(self.loaded_data)
        else:
            callback_data = None
        
        # Clean up resources before closing
        self._cleanup_resources()
        
        # Force destroy window immediately
        try:
            window_exists = hasattr(self, 'window') and self.window.winfo_exists()
            if window_exists:
                # Cancel all remaining after callbacks
                for after_id in list(self.after_ids):
                    self.cancel_after(after_id)
                    
                self.window.withdraw()  # Hide window first
                self.window.quit()      # Stop the mainloop
                self.window.destroy()   # Force destroy window
            
            # Clean up any stray after commands again after window destruction
            cleanup_after_commands()
            
            # Clear references to UI elements to help garbage collection
            self.animation_label = None
            self.animation_frames = []
            self.status_label = None
            self.progress_bar = None
            self.after_ids = []
            
            # Now that window is destroyed, call the callback if it exists
            if callback_data is not None and callback_func is not None:
                callback_func(callback_data)
                
        except Exception as e:
            print(f"Error closing splash screen: {e}")
            # Still try to call the callback even if there was an error
            if callback_data is not None and callback_func is not None:
                try:
                    callback_func(callback_data)
                except Exception as e2:
                    print(f"Error in callback after splash screen close: {e2}")

    def _cleanup_resources(self):
        """Clean up resources before closing"""
        # Stop any ongoing animations
        self.is_loading = False
        
        # Clear animation references to help garbage collection
        self.animation_frames = []
        
        # Stop progress bar if running
        if hasattr(self, 'progress_bar'):
            try:
                self.progress_bar.stop()
            except:
                pass
        
        # Make sure loading thread is terminated if still running
        if self.loading_thread and self.loading_thread.is_alive():
            # Cannot forcibly terminate a thread in Python, but we can set a flag
            # that the thread should check and exit gracefully
            self.is_loading = False

    def _calculate_basic_statistics(self, game_history):
        """Calculate basic game statistics from history data
        
        Args:
            game_history (dict): Dictionary of game history data
            
        Returns:
            dict: Statistics dictionary
        """
        stats = {
            "total_games": len(game_history),
            "player_wins": {1: 0, 2: 0},
            "draws": 0,
            "incomplete": 0,
            "avg_moves": 0,
            "recent_games": []
        }
        
        total_moves = 0
        move_counts = []
        
        # Process each game
        for game_id, game in game_history.items():
            winner = game.get('winner')
            
            if winner in [1, 2]:
                stats["player_wins"][winner] += 1
            elif winner == 0:
                stats["draws"] += 1
            else:
                stats["incomplete"] += 1
            
            # Count moves
            moves = game.get('moves', [])
            move_count = len(moves)
            total_moves += move_count
            
            if move_count > 0:
                move_counts.append((game_id, move_count))
        
        # Calculate average moves
        if stats["total_games"] > 0:
            stats["avg_moves"] = total_moves / stats["total_games"]
        
        # Get most recent games (up to 5)
        sorted_game_ids = sorted(
            game_history.keys(),
            key=lambda gid: game_history[gid].get('timestamp', gid),
            reverse=True
        )
        
        for game_id in sorted_game_ids[:5]:
            game = game_history[game_id]
            stats["recent_games"].append({
                "id": game_id,
                "winner": game.get('winner'),
                "moves": len(game.get('moves', []))
            })
        
        return stats
    
    def start(self):
        """Start the splash screen and loading process"""
        # Start the progress bar
        self.progress_bar.start()
        
        # Start loading animation
        self.load_animation()
        
        # Start loading data
        self.loading_thread.start()
        
        # Catch exceptions during mainloop to ensure clean shutdown
        try:
            # Start the mainloop
            self.window.mainloop()
        except Exception as e:
            print(f"Error in splash screen mainloop: {e}")
            # Force close window if exception occurs
            try:
                self._on_closing()
            except:
                pass
            # Call callback if not already called
            if self.on_complete_callback and self.loaded_data:
                self.on_complete_callback(dict(self.loaded_data))

    def _on_closing(self):
        """Handle window closing properly"""
        # Set flag to stop animations and loading
        self.is_loading = False
        
        # Cancel all scheduled callbacks
        for after_id in self.after_ids:
            try:
                self.window.after_cancel(after_id)
            except Exception:
                pass
        
        # Clear references to allow garbage collection
        self.animation_frames = []
        self.animation_label = None
        
        # Call cleanup
        self._cleanup_resources()
        
        # Destroy window
        self.window.destroy()

    def schedule_after(self, delay, callback):
        """Schedule an after callback and track its ID
        
        Args:
            delay: Delay in milliseconds
            callback: Function to call
            
        Returns:
            The after ID
        """
        if not hasattr(self, 'window') or not self.window.winfo_exists():
            return None
            
        after_id = self.window.after(delay, callback)
        self.after_ids.append(after_id)
        return after_id

    def cancel_after(self, after_id):
        """Cancel an after callback
        
        Args:
            after_id: ID of callback to cancel
        """
        if after_id in self.after_ids:
            try:
                self.window.after_cancel(after_id)
                self.after_ids.remove(after_id)
            except Exception:
                pass


# For testing - run this file directly
if __name__ == "__main__":
    def on_loading_complete(data):
        print("Loading complete!")
        print(f"Loaded data: {list(data.keys())}")
    
    splash = SplashScreen(on_complete_callback=on_loading_complete)
    splash.start()
