import customtkinter as ctk
import tkinter as tk
import threading
import os
import time
from PIL import Image, ImageTk, ImageSequence
from assets_manager import AssetManager, ASSETS_DIR
from game import TicTacToeGame
from app import TicTacToeApp
from game_history import GameHistoryViewer
from ai_trainer import AITrainingWindow

class MainMenu:
    """Main menu with animated background and navigation buttons"""
    
    def __init__(self, loaded_data=None, preload_only=False):
        """Initialize the main menu
        
        Args:
            loaded_data (dict): Pre-loaded data from splash screen
            preload_only (bool): If True, only set up widgets without showing window
        """
        self.loaded_data = loaded_data or {}
        self.preload_only = preload_only
        self.is_visible = False
        
        # Set UI state tracking
        from utils import mark_main_ui_active
        mark_main_ui_active(True)
        
        # Add heartbeat tracking for deadlock detection
        self.last_heartbeat = time.time()
        self.heartbeat_counter = 0
        
        # Extract pre-loaded components
        self.assets_manager = self.loaded_data.get('assets_manager', AssetManager())
        self.game_history = self.loaded_data.get('game_history', {})
        self.ai_player = self.loaded_data.get('ai_player')
        self.game = self.loaded_data.get('game')
        
        # Get pre-calculated statistics if available
        self.game_stats = self.loaded_data.get('game_stats', {})
        
        # Create window
        self.window = ctk.CTk()
        self.window.title("Tic Tac Toe - Main Menu")
        self.window.geometry("800x600")
        self.window.configure(fg_color="#1E1E1E")
        
        # If preloading, withdraw the window immediately
        if preload_only:
            self.window.withdraw()
        
        # Set up animation variables
        self.animation_frames = []
        self.current_frame = 0
        self.animation_running = False
        
        # Store after callbacks for cleanup
        self.after_ids = []
        
        # Track loading status of components
        self.components_loaded = {
            'background': False,
            'statistics': False
        }
        
        # Setup UI first (with empty containers)
        self.setup_ui()
        
        # Set up proper window close handling
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Then load resource-intensive components in background threads
        self.start_background_loading()
    
    def on_closing(self):
        """Handle window closing event - cleanup resources"""
        # Update UI state tracking
        from utils import mark_main_ui_active
        mark_main_ui_active(False)
        
        # Stop animation
        self.animation_running = False
        
        # Cancel all scheduled after callbacks
        for after_id in self.after_ids:
            try:
                self.window.after_cancel(after_id)
            except Exception:
                pass
        
        # Clear references to images to help garbage collection
        self.animation_frames = []
        if hasattr(self, '_frames_reference'):
            self._frames_reference = []
        if hasattr(self, '_current_image'):
            self._current_image = None
        
        # Now destroy the window
        self.window.destroy()
    
    def schedule_after(self, delay, callback):
        """Schedule a callback and track its ID for cleanup
        
        Args:
            delay: Delay in milliseconds
            callback: Function to call
            
        Returns:
            The after ID
        """
        try:
            if hasattr(self, 'window') and self.window.winfo_exists():
                after_id = self.window.after(delay, callback)
                self.after_ids.append(after_id)
                return after_id
            return None
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                print("Warning: Attempted to schedule callback from non-main thread")
                return None
            else:
                raise
    
    def remove_after_id(self, after_id):
        """Remove an after ID from tracking list
        
        Args:
            after_id: ID to remove
        """
        if after_id in self.after_ids:
            self.after_ids.remove(after_id)
    
    def start_background_loading(self):
        """Start loading resource-intensive components in background threads"""
        # Thread for loading and processing the background animation
        bg_thread = threading.Thread(target=self._load_background_animation)
        bg_thread.daemon = True
        bg_thread.start()
        
        # Thread for processing game statistics if not pre-calculated
        if not self.game_stats and self.game_history:
            stats_thread = threading.Thread(target=self._process_game_statistics)
            stats_thread.daemon = True
            stats_thread.start()
        else:
            # If pre-calculated, update the UI directly
            self.components_loaded['statistics'] = True
            self.window.after(100, self._update_statistics_display)
    
    def _load_background_animation(self):
        """Load the background animation in a separate thread - optimized version"""
        try:
            # First check if we have preloaded animation frames
            if self.loaded_data and 'background_animation' in self.loaded_data:
                preloaded_frames = self.loaded_data['background_animation']
                if preloaded_frames:
                    print("Using preloaded background animation")
                    # Thread-safe way to update UI on main thread
                    try:
                        # Don't try to access winfo_exists from a background thread
                        from utils import schedule_on_main_thread
                        schedule_on_main_thread(self.window, self._set_animation_frames, preloaded_frames)
                        return
                    except RuntimeError as e:
                        if "main thread is not in main loop" in str(e):
                            print("Warning: Can't update UI from background thread, will try alternative approach")
                        else:
                            raise
            
            # Look for background animation
            animation_path = os.path.join(ASSETS_DIR, "background.gif")
            
            if not os.path.exists(animation_path):
                # Try to create a basic one if assets manager is available
                if self.assets_manager:
                    try:
                        # Set temporary status
                        self.window.after(0, lambda: self._update_status_display("Generating background animation..."))
                        self._generate_background_animation()
                    except Exception as e:
                        print(f"Error generating background: {e}")
            
            # Set status message
            self.window.after(0, lambda: self._update_status_display("Loading background animation..."))
            
            # Load GIF frames
            with Image.open(animation_path) as img:
                # Get original dimensions
                orig_width, orig_height = img.size
                
                # Calculate new dimensions to fit window while maintaining aspect ratio
                target_height = 600
                target_width = int(orig_width * (target_height / orig_height))
                
                # Load and resize each frame
                frames = []
                for frame in ImageSequence.Iterator(img):
                    # Resize frame
                    frame = frame.convert("RGBA")
                    frame = frame.resize((target_width, target_height), Image.LANCZOS)
                    
                    # Convert to PhotoImage
                    photoframe = ImageTk.PhotoImage(frame)
                    frames.append(photoframe)
                
                # Make sure window still exists before updating UI
                if hasattr(self, 'window') and self.window.winfo_exists():
                    # Keep reference to frames in the instance
                    self._frames_reference = frames  # Keep a strong reference to prevent garbage collection
                    # Update animation frames in main thread
                    self.schedule_after(0, lambda: self._set_animation_frames(frames))
        
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                print("Warning: Threading issue in background animation loading. Will retry on main thread.")
                # Queue this operation to be run on the main thread next time it's idle
                from utils import schedule_on_main_thread
                schedule_on_main_thread(self.window, self.load_background_animation)
            else:
                print(f"Error loading background animation: {e}")
        except Exception as e:
            print(f"Error loading background animation: {e}")
            from utils import schedule_on_main_thread
            schedule_on_main_thread(self.window, self._update_status_display, "Error loading background")
    
    def _set_animation_frames(self, frames):
        """Update animation frames and start animation (called in main thread)"""
        try:
            self.animation_frames = frames
            
            if self.animation_frames and len(self.animation_frames) > 0:
                # Keep a strong reference to prevent garbage collection
                self._current_image = self.animation_frames[0]
                self.bg_animation_label.configure(image=self._current_image)
                self.animation_running = True
                self.animate_background()
            
            # Mark as loaded
            self.components_loaded['background'] = True
            self._update_status_display("Background loaded successfully")
            
            # Hide status after a delay if all components are loaded
            if all(self.components_loaded.values()):
                self.schedule_after(1000, self._hide_status_display)
        except Exception as e:
            print(f"Error setting animation frames: {e}")
    
    def animate_background(self):
        """Update the background animation frame"""
        try:
            if not hasattr(self, 'window') or not self.window.winfo_exists() or not self.animation_running:
                self.animation_running = False
                return
                
            # Update heartbeat to show UI thread is responsive
            self.last_heartbeat = time.time()
            self.heartbeat_counter += 1
                
            if self.animation_frames and len(self.animation_frames) > 0:
                # Update to next frame
                self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
                # Store current image to prevent garbage collection
                self._current_image = self.animation_frames[self.current_frame]
                self.bg_animation_label.configure(image=self._current_image)
                
                # Continue animation
                if self.animation_running:
                    after_id = self.schedule_after(100, self.animate_background)
                    
                    # Every 10 frames, check if UI has been responsive
                    if self.heartbeat_counter % 10 == 0:
                        self._check_ui_responsiveness()
        except Exception as e:
            print(f"Error in animation: {e}")
            self.animation_running = False
    
    def _check_ui_responsiveness(self):
        """Check if the UI is responding properly"""
        from debug_logger import warning, info
        from utils import update_app_heartbeat
        
        # Calculate time since last heartbeat
        time_since_heartbeat = time.time() - self.last_heartbeat
        
        # If more than 2 seconds since last heartbeat, UI might be stuck
        if time_since_heartbeat > 2.0:
            warning(f"UI thread may be stuck - {time_since_heartbeat:.1f}s since last heartbeat")
            
            # Try to process pending events to unstick the UI
            try:
                self.window.update()
                info("Processed pending events to unstick UI")
                # Reset heartbeat
                self.last_heartbeat = time.time()
                # Also update the application-wide heartbeat
                update_app_heartbeat()
            except Exception as e:
                warning(f"Could not process events: {e}")
        else:
            # Update application heartbeat on regular checks too
            update_app_heartbeat()
        
        # Schedule to run this check again periodically
        self.schedule_after(2000, self._check_ui_responsiveness)
        return True
    
    def _process_game_statistics(self):
        """Process game statistics in background thread - optimized version"""
        try:
            # First check if we have preloaded statistics
            if self.game_stats:
                # Already have stats from preloaded data, just update UI
                self.window.after(0, self._update_statistics_display)
                return
                
            # Update status in main thread
            self.window.after(0, lambda: self._update_status_display("Processing game statistics..."))
            
            # Try to get from data manager first
            try:
                from data_manager import GameDataManager
                data_manager = GameDataManager.get_instance()
                if data_manager and data_manager.has('game_stats'):
                    # Use precomputed stats
                    self.game_stats = data_manager.get('game_stats', {})
                    print("Using preloaded game statistics")
                    self.window.after(0, self._update_statistics_display)
                    return
            except Exception as e:
                print(f"Error getting stats from data manager: {e}")
            
            # Calculate statistics
            stats = {
                "total_games": len(self.game_history),
                "player_wins": {1: 0, 2: 0},
                "draws": 0,
                "incomplete": 0,
                "avg_moves": 0,
                "recent_games": []
            }
            
            total_moves = 0
            
            # Process each game
            for game_id, game in self.game_history.items():
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
            
            # Get most recent games (up to 5)
            sorted_game_ids = sorted(
                self.game_history.keys(),
                key=lambda gid: self.game_history[gid].get('timestamp', gid),
                reverse=True
            )
            
            for game_id in sorted_game_ids[:5]:
                game = self.game_history[game_id]
                stats["recent_games"].append({
                    "id": game_id,
                    "winner": game.get('winner'),
                    "moves": len(game.get('moves', []))
                })
            
            # Store the calculated statistics
            self.game_stats = stats
            
            # Store in data manager for future use
            try:
                from data_manager import GameDataManager
                data_manager = GameDataManager.get_instance()
                if data_manager:
                    data_manager.set('game_stats', stats, notify=False)
            except Exception:
                pass
                
            # Update UI in main thread
            self.window.after(0, self._update_statistics_display)
            
        except Exception as e:
            print(f"Error processing game statistics: {e}")
            self.window.after(0, lambda: self._update_status_display("Error processing game stats"))
    
    def _update_statistics_display(self):
        """Update the statistics display with calculated stats"""
        if not hasattr(self, 'stats_label') or not self.game_stats:
            return
        
        total_games = self.game_stats.get("total_games", 0)
        x_wins = self.game_stats.get("player_wins", {}).get(1, 0)
        o_wins = self.game_stats.get("player_wins", {}).get(2, 0)
        draws = self.game_stats.get("draws", 0)
        
        # Format statistics text
        stats_text = f"Total Games: {total_games} | X Wins: {x_wins} | O Wins: {o_wins} | Draws: {draws}"
        
        # Add average moves if available
        avg_moves = self.game_stats.get("avg_moves", 0)
        if avg_moves > 0:
            stats_text += f" | Avg Moves: {avg_moves:.1f}"
        
        # Update the stats label
        self.stats_label.configure(text=stats_text)
        
        # Mark as loaded
        self.components_loaded['statistics'] = True
        
        # Hide status after a delay if all components are loaded
        if all(self.components_loaded.values()):
            self.schedule_after(1000, self._hide_status_display)
    
    def _update_status_display(self, message):
        """Update the status display with a message"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
            self.status_label.pack(side=tk.TOP, pady=5)  # Ensure it's visible
    
    def _hide_status_display(self):
        """Hide the status display"""
        if hasattr(self, 'status_label'):
            self.status_label.pack_forget()
    
    def setup_ui(self):
        """Set up the UI elements"""
        # Create a background frame for animation
        self.bg_frame = ctk.CTkFrame(self.window, fg_color="#1E1E1E", corner_radius=0)
        self.bg_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Create background animation label
        self.bg_animation_label = ctk.CTkLabel(
            self.bg_frame,
            text="",
            fg_color="transparent"
        )
        self.bg_animation_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Create overlay for better text readability with dark glass effect
        overlay = ctk.CTkFrame(
            self.window, 
            fg_color=("#EEEEEE", "#121212"),  # Light/dark colors without alpha
            corner_radius=0
        )
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Add a subtle grid pattern for depth
        for i in range(0, 800, 40):
            line_h = ctk.CTkFrame(overlay, fg_color=("#CCCCCC", "#333333"), height=1, width=800)
            line_h.place(x=0, y=i)
            
            line_v = ctk.CTkFrame(overlay, fg_color=("#CCCCCC", "#333333"), width=1, height=600)
            line_v.place(x=i, y=0)
        
        # Create a modern card-like main content container
        main_frame = ctk.CTkFrame(
            self.window,
            fg_color=("#F0F0F0", "#1E1E2E"),
            corner_radius=20,
            border_width=2,
            border_color=("#CCCCCC", "#3E92CC")
        )
        main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.85, relheight=0.85)
        
        # Add a status label for loading messages
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Loading components...",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA",
            bg_color="#333333",
            corner_radius=5
        )
        self.status_label.pack(side=tk.TOP, pady=5)
        
        # App icon/logo at the top
        logo_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        logo_frame.pack(pady=(25, 0))
        
        # X and O logo elements side by side
        x_label = ctk.CTkLabel(
            logo_frame,
            text="TIC",
            font=ctk.CTkFont(family="Arial", size=38, weight="bold"),
            text_color="#4F85CC"  # X color
        )
        x_label.pack(side=tk.LEFT, padx=5)
        
        tac_label = ctk.CTkLabel(
            logo_frame,
            text="TAC",
            font=ctk.CTkFont(family="Arial", size=38, weight="bold"),
            text_color="#FF5C8D"  # O color
        )
        tac_label.pack(side=tk.LEFT, padx=5)
        
        toe_label = ctk.CTkLabel(
            logo_frame,
            text="TOE",
            font=ctk.CTkFont(family="Arial", size=38, weight="bold"),
            text_color="#4CAF50"  # Green
        )
        toe_label.pack(side=tk.LEFT, padx=5)
        
        # Subtitle with glowing effect
        subtitle_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=30)
        subtitle_frame.pack(pady=(5, 30))
        
        subtitle_label = ctk.CTkLabel(
            subtitle_frame,
            text="THE CLASSIC GAME",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color="#AAAAAA"
        )
        subtitle_label.pack()
        
        # Create a glowing separator
        separator = ctk.CTkFrame(main_frame, height=2, fg_color="#3E92CC", width=300)
        separator.pack(pady=(0, 30))
        
        # Button styling - more modern, colorful buttons
        button_width = 250
        button_height = 50
        button_font = ctk.CTkFont(family="Arial", size=16, weight="bold")
        button_corner_radius = 10
        button_spacing = 15
        
        # Use a scrollable frame for buttons to accommodate different screen sizes
        buttons_container = ctk.CTkScrollableFrame(
            main_frame, 
            fg_color="transparent",
            scrollbar_button_color="#3E92CC",
            scrollbar_button_hover_color="#2D7DB3",
            width=button_width + 20,
            height=350  # Fixed height
        )
        buttons_container.pack(pady=10)
        
        # Button styles with icons (using emoji as simple icons)
        button_configs = [
            {
                "text": "👥  Play Human vs Human",
                "command": self.play_human_vs_human,
                "fg_color": "#4CAF50",
                "hover_color": "#3E8E41"
            },
            {
                "text": "🤖  Play vs AI",
                "command": self.play_vs_ai,
                "fg_color": "#3E92CC",
                "hover_color": "#2D7DB3"
            },
            {
                "text": "📊  View Game History",
                "command": self.view_game_history,
                "fg_color": "#9B59B6",
                "hover_color": "#8E44AD"
            },
            {
                "text": "⚙️  Train AI Model",
                "command": self.train_ai,
                "fg_color": "#E67E22",
                "hover_color": "#D35400"
            },
            {
                "text": "🚪  Quit Game",
                "command": self.on_closing,
                "fg_color": "#E63946",
                "hover_color": "#C5313E"
            }
        ]
        
        # Create buttons with hover effect
        for config in button_configs:
            button = ctk.CTkButton(
                buttons_container,
                text=config["text"],
                command=config["command"],
                font=button_font,
                fg_color=config["fg_color"],
                hover_color=config["hover_color"],
                width=button_width,
                height=button_height,
                corner_radius=button_corner_radius,
                border_width=2,
                border_color="#333333"  # Changed from "#FFFFFF20" to solid color
            )
            button.pack(pady=button_spacing)
        
        # Game stats display at bottom
        stats_frame = ctk.CTkFrame(
            main_frame, 
            fg_color=("#E5E5E5", "#23233A"),
            corner_radius=10,
            height=60
        )
        stats_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=30, pady=20)
        stats_frame.pack_propagate(False)
        
        # Display stats
        stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_container.pack(expand=True)
        
        stats_title = ctk.CTkLabel(
            stats_container,
            text="Game Statistics",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF"
        )
        stats_title.pack()
        
        self.stats_label = ctk.CTkLabel(
            stats_container,
            text="Loading statistics...",
            font=ctk.CTkFont(size=12),
            text_color="#DDDDDD"
        )
        self.stats_label.pack()
        
        # Version info
        version_label = ctk.CTkLabel(
            main_frame,
            text="Version 1.1",
            font=ctk.CTkFont(family="Arial", size=10),
            text_color="#666666"
        )
        version_label.pack(side=tk.BOTTOM, pady=5)
        
        # Initial statistics update if data available
        if self.game_stats:
            self._update_statistics_display()
    
    def load_background_animation(self):
        """Load the background animation"""
        try:
            # Look for background animation
            animation_path = os.path.join(ASSETS_DIR, "background.gif")
            
            # If animation doesn't exist, try to create a basic one
            if not os.path.exists(animation_path):
                self._generate_background_animation()
                # Try again with the generated animation
                if not os.path.exists(animation_path):
                    print("Unable to create background animation")
                    return
            
            # Load GIF frames
            with Image.open(animation_path) as img:
                # Get original dimensions
                orig_width, orig_height = img.size
                
                # Calculate new dimensions to fit window while maintaining aspect ratio
                target_height = 600
                target_width = int(orig_width * (target_height / orig_height))
                
                # Load and resize each frame
                for frame in ImageSequence.Iterator(img):
                    # Resize frame
                    frame = frame.convert("RGBA")
                    frame = frame.resize((target_width, target_height), Image.LANCZOS)
                    
                    # Convert to PhotoImage
                    photoframe = ImageTk.PhotoImage(frame)
                    self.animation_frames.append(photoframe)
                
            # Start animation if frames were loaded
            if self.animation_frames:
                self.bg_animation_label.configure(image=self.animation_frames[0])
                self.animation_running = True
                self.animate_background()
        
        except Exception as e:
            print(f"Error loading background animation: {e}")
    
    def animate_background(self):
        """Update the background animation frame"""
        try:
            if not hasattr(self, 'window') or not self.window.winfo_exists():
                self.animation_running = False
                return
                
            if self.animation_running and self.animation_frames and len(self.animation_frames) > 0:
                # Update to next frame
                self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
                # Store current image to prevent garbage collection
                self._current_image = self.animation_frames[self.current_frame]
                self.bg_animation_label.configure(image=self._current_image)
                
                # Continue animation
                self.window.after(100, self.animate_background)
        except Exception as e:
            print(f"Error in animation: {e}")
            self.animation_running = False
    
    def _generate_background_animation(self):
        """Generate a simple background animation"""
        try:
            from PIL import Image, ImageDraw
            import math
            
            # Create a series of frames with moving patterns
            frames = []
            size = (800, 600)
            
            # Colors
            bg_color = (30, 30, 30, 255)  # Dark background
            pattern_color = (62, 146, 204, 40)  # Light blue with transparency
            
            # Generate frames
            num_frames = 20
            for i in range(num_frames):
                # Create a new frame
                frame = Image.new("RGBA", size, bg_color)
                draw = ImageDraw.Draw(frame)
                
                # Draw some animated elements
                # 1. Moving circles
                for j in range(10):
                    # Position based on frame number
                    angle = (i + j * 36) * 3.6  # Degrees, 36° spacing, moving
                    x = size[0] // 2 + int(math.cos(math.radians(angle)) * 200)
                    y = size[1] // 2 + int(math.sin(math.radians(angle)) * 150)
                    
                    # Size pulsating with frame number
                    radius = 30 + int(10 * math.sin(math.radians(i * 18 + j * 36)))
                    
                    # Draw circle
                    draw.ellipse(
                        (x - radius, y - radius, x + radius, y + radius),
                        fill=pattern_color
                    )
                
                # 2. Grid lines
                spacing = 50
                offset = i * 2  # Moving offset
                
                # Horizontal lines
                for y in range(-offset % spacing, size[1], spacing):
                    draw.line([(0, y), (size[0], y)], fill=(255, 255, 255, 10), width=1)
                
                # Vertical lines
                for x in range(-offset % spacing, size[0], spacing):
                    draw.line([(x, 0), (x, size[1])], fill=(255, 255, 255, 10), width=1)
                
                frames.append(frame)
            
            # Save as GIF
            animation_path = os.path.join(ASSETS_DIR, "background.gif")
            frames[0].save(
                animation_path,
                save_all=True,
                append_images=frames[1:],
                duration=100,
                loop=0
            )
            
            print(f"Generated background animation at {animation_path}")
            return True
        
        except Exception as e:
            print(f"Error generating background animation: {e}")
            return False
    
    def play_human_vs_human(self):
        """Launch the game in human vs human mode"""
        self.window.withdraw()  # Hide main menu
        
        # Create game window
        game_window = ctk.CTk()
        
        # Initialize game with loaded data
        app = TicTacToeApp(game_window, assets_manager=self.assets_manager)
        
        # Set the game mode to human vs human
        app.mode.set("human_vs_human")
        
        # Handle game window closing
        def on_game_close():
            game_window.destroy()
            self.window.deiconify()  # Show main menu again
        
        game_window.protocol("WM_DELETE_WINDOW", on_game_close)
        
        # Start the game
        game_window.mainloop()
    
    def play_vs_ai(self):
        """Launch the game in human vs AI mode"""
        # Check if AI model is available
        ai_available = self.ai_player and self.ai_player.model_exists()
        if not ai_available:
            # Show warning and offer to train
            result = self.show_confirm_dialog(
                "AI model not found",
                "The AI model is not available. Would you like to train it now?",
                ["Train AI", "Play Anyway", "Cancel"]
            )
            
            if result == "Train AI":
                self.train_ai()
                return
            elif result == "Cancel":
                return
        
        # Hide main menu
        self.window.withdraw()
        
        # Create game window
        game_window = ctk.CTk()
        
        # Initialize game with loaded data
        app = TicTacToeApp(game_window, assets_manager=self.assets_manager)
        
        # Set the game mode to human vs AI
        app.mode.set("human_vs_ai")
        app.check_ai_model()  # Update AI status display
        
        # Handle game window closing
        def on_game_close():
            game_window.destroy()
            self.window.deiconify()  # Show main menu again
        
        game_window.protocol("WM_DELETE_WINDOW", on_game_close)
        
        # Start the game
        game_window.mainloop()
    
    def view_game_history(self):
        """Open the game history viewer"""
        # Hide main menu temporarily
        self.window.withdraw()
        
        # Initialize history viewer
        viewer = GameHistoryViewer()
        
        # When viewer closes, show main menu again
        def check_viewer():
            try:
                # First check if our own window still exists
                if not hasattr(self, 'window') or not self.window.winfo_exists():
                    return  # Our window is gone, stop checking
                    
                # Then check if viewer window still exists
                if viewer.window is None or not viewer.window.winfo_exists():
                    self.window.deiconify()  # Show main menu again
                    return
                
                # Continue checking
                after_id = self.schedule_after(100, check_viewer)
            except Exception as e:
                print(f"Error checking viewer window: {e}")
                # Try to restore main window if there was an error
                try:
                    if hasattr(self, 'window') and self.window.winfo_exists():
                        self.window.deiconify()
                except:
                    pass
        
        # Start checking for viewer window
        self.schedule_after(100, check_viewer)
        
        # Run the viewer
        viewer.run()
    
    def train_ai(self):
        """Open the AI training window"""
        # Initialize training window
        training_window = AITrainingWindow(self.window)
        
        # No need to hide main menu as AITrainingWindow is modal
    
    def show_confirm_dialog(self, title, message, options):
        """Show a confirmation dialog with custom options
        
        Args:
            title (str): Dialog title
            message (str): Dialog message
            options (list): List of button texts
        
        Returns:
            str: The selected option or None if canceled
        """
        try:
            # Make sure parent window is viewable before creating dialog
            if not self.window.winfo_viewable():
                self.window.deiconify()
                self.window.update()
            
            # Create dialog window
            dialog = ctk.CTkToplevel(self.window)
            dialog.title(title)
            dialog.geometry("400x200")
            dialog.configure(fg_color="#252525")
            
            # Allow dialog to initialize before setting transient/grab
            dialog.update_idletasks()
            
            # Make dialog modal
            dialog.transient(self.window)
            
            # Try to set grab safely, with fallback
            try:
                # First check if dialog is viewable
                dialog.update()
                if dialog.winfo_viewable():
                    dialog.grab_set()
                else:
                    # Wait a bit and try again
                    self.window.after(100, lambda: safe_grab_set(dialog))
            except Exception as e:
                print(f"Could not set grab on dialog: {e}")
            
            # Center on parent
            center_dialog_on_parent(dialog, self.window)
            
            # Track result
            result = [None]
            
            # Set result and close
            def set_result(option):
                result[0] = option
                dialog.destroy()
            
            # Message
            message_label = ctk.CTkLabel(
                dialog,
                text=message,
                font=ctk.CTkFont(size=14),
                wraplength=350
            )
            message_label.pack(pady=(20, 30))
            
            # Buttons
            buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            buttons_frame.pack(pady=10)
            
            # Create buttons for options
            for option in options:
                button = ctk.CTkButton(
                    buttons_frame,
                    text=option,
                    command=lambda opt=option: set_result(opt),
                    font=ctk.CTkFont(size=13),
                    width=100,
                    height=30
                )
                button.pack(side=tk.LEFT, padx=10)
            
            # Helper function for safe grab_set
            def safe_grab_set(widget):
                try:
                    if widget.winfo_exists() and widget.winfo_viewable():
                        widget.grab_set()
                except Exception:
                    pass
            
            # Helper function to center dialog
            def center_dialog_on_parent(dialog, parent):
                dialog.update_idletasks()
                parent_x = parent.winfo_x()
                parent_y = parent.winfo_y()
                parent_width = parent.winfo_width()
                parent_height = parent.winfo_height()
                
                dialog_width = dialog.winfo_width()
                dialog_height = dialog.winfo_height()
                x = parent_x + (parent_width - dialog_width) // 2
                y = parent_y + (parent_height - dialog_height) // 2
                dialog.geometry(f"+{x}+{y}")
            
            # Wait for the dialog to close
            dialog.wait_window()
            
            return result[0]
        except Exception as e:
            print(f"Error showing dialog: {e}")
            return None
    
    def show(self):
        """Show the preloaded window"""
        from debug_logger import transition, error, success, debug, warning, info
        
        transition("MainMenu.show() called - showing preloaded window")
        info("Showing main menu window - this is where transitions often hang")
        
        if not self.is_visible:
            try:
                # Make sure window is fully prepared
                if hasattr(self, 'window') and self.window.winfo_exists():
                    debug("Window exists, preparing to show it")
                    self.window.update_idletasks()
                    
                    # Center window on screen
                    self._center_window()
                    debug("Window centered on screen")
                    
                    # MODIFIED: Set alpha to 1.0 directly - skipping fade-in for reliability
                    debug("Setting window to full opacity immediately for reliability")
                    try:
                        self.window.attributes("-alpha", 1.0)
                    except Exception as e:
                        warning(f"Could not set window alpha: {e}")
                    
                    # Show window directly with multiple approaches for reliability
                    try:
                        debug("Trying to deiconify window")
                        self.window.deiconify()
                        debug("Window deiconified successfully")
                    except Exception as e:
                        warning(f"Error deiconifying window: {e}")
                        # Try alternative approach immediately
                        try:
                            debug("Trying wm_deiconify as alternative approach")
                            self.window.wm_deiconify()
                            debug("Used wm_deiconify successfully")
                        except Exception as e2:
                            error(f"Both deiconify methods failed: {e2}")
                            try:
                                # Final desperate approach
                                debug("Trying state('normal') approach")
                                self.window.state('normal')
                                debug("State normal set successfully")
                            except Exception as e3:
                                error(f"All window show methods failed: {e3}")
                    
                    # Force update to ensure window is displayed
                    try:
                        debug("Forcing window update")
                        self.window.update()
                        debug("Window update completed")
                    except Exception as e:
                        warning(f"Cannot force window update: {e}")
                    
                    # Force focus after a tiny delay
                    self.schedule_after(50, lambda: self._force_window_focus())
                    
                    # Mark visible immediately, don't wait for fade-in
                    self.is_visible = True
                    success("Main menu window marked as visible")
                    
                    # Monitor window visibility
                    self.schedule_after(500, self._check_window_visibility)
                    
                else:
                    error("Window does not exist or has been destroyed")
                    # Report window state for debugging
                    if hasattr(self, 'window'):
                        debug(f"Window object exists but winfo_exists() is False")
                    else:
                        debug(f"Window object does not exist on MainMenu instance")
            except Exception as e:
                error(f"Error showing main menu: {e}")
                import traceback
                traceback.print_exc()
                
                # Last chance direct approach
                try:
                    error("Attempting last-chance direct window show")
                    if hasattr(self, 'window'):
                        self.window.withdraw()
                        time.sleep(0.05)
                        self.window.deiconify()
                        self.is_visible = True
                        success("Window shown with last-chance method")
                except Exception as e2:
                    error(f"Last-chance window show failed: {e2}")

    def _force_window_focus(self):
        """Force window to take focus with multiple approaches"""
        from debug_logger import debug, warning
        
        try:
            # Multiple approaches for different platforms
            debug("Forcing window focus")
            self.window.focus_force()
            self.window.lift()
            
            # Try additional methods for stubborn platforms
            try:
                self.window.attributes('-topmost', True)
                self.window.update()
                self.window.attributes('-topmost', False)
                debug("Used topmost attribute method")
            except Exception as e:
                warning(f"Topmost method failed: {e}")
            
            # Attempt to grab focus
            try:
                self.window.grab_set()
                self.window.grab_release()
                debug("Used grab_set/release method")
            except Exception as e:
                warning(f"Grab method failed: {e}")
                
        except Exception as e:
            warning(f"Focus forcing failed: {e}")

    def _check_window_visibility(self):
        """Monitor window visibility and fix if needed"""
        from debug_logger import debug, warning, error
        
        if not hasattr(self, 'window') or not self.window.winfo_exists():
            error("Window no longer exists during visibility check")
            return
            
        try:
            is_mapped = bool(self.window.winfo_ismapped())
            debug(f"Window mapped state: {is_mapped}")
            
            if not is_mapped and self.is_visible:
                warning("Window should be visible but isn't mapped - forcing show")
                self.window.deiconify()
                self.window.focus_force()
                
                # Try resetting geometry
                try:
                    self._center_window()
                    debug("Reset window geometry")
                except Exception as e:
                    warning(f"Could not reset geometry: {e}")
                    
            # Try updating again
            try:
                self.window.update_idletasks()
            except Exception as e:
                warning(f"Could not update idletasks: {e}")
                
            # Schedule another check - less frequent after first few checks
            if hasattr(self, '_visibility_check_count'):
                self._visibility_check_count += 1
            else:
                self._visibility_check_count = 1
                
            # Decay check frequency over time
            if self._visibility_check_count < 5:
                next_check = 1000  # 1 second for first 5 checks
            elif self._visibility_check_count < 10:
                next_check = 5000  # 5 seconds for next 5 checks
            else:
                next_check = 30000  # 30 seconds after that
                
            self.schedule_after(next_check, self._check_window_visibility)
            
        except Exception as e:
            error(f"Error checking window visibility: {e}")
            # Keep checking anyway
            self.schedule_after(5000, self._check_window_visibility)

    def run(self):
        """Run the main menu"""
        from debug_logger import transition, success, error, debug, info
        
        transition("MainMenu.run() called")
        
        # If was preloaded and not yet visible, show it first
        if self.preload_only and not self.is_visible:
            debug("Menu was preloaded but not visible, showing it first")
            self.show()
        
        # Reset heartbeat before entering mainloop
        self.last_heartbeat = time.time()
        
        # Start regular UI responsiveness checks
        self.schedule_after(2000, self._check_ui_responsiveness)
        
        # Start mainloop if not already running
        if hasattr(self, 'window') and self.window.winfo_exists():
            try:
                debug("Starting main menu mainloop")
                
                # Use safer mainloop approach that allows periodic event processing
                self._safer_mainloop()
                
                success("Main menu mainloop completed")
            except Exception as e:
                error(f"Error in main menu mainloop: {e}")
        else:
            error("Cannot start mainloop - window does not exist or was destroyed")

    def _safer_mainloop(self):
        """A safer version of mainloop that ensures regular event processing"""
        from debug_logger import debug, warning, error
        
        # First try the standard mainloop, but with a timeout
        try:
            # Set a regular update timer to ensure UI refreshes
            def ensure_update():
                try:
                    if hasattr(self, 'window') and self.window.winfo_exists():
                        # Process events explicitly
                        self.window.update()
                        # Reset heartbeat
                        self.last_heartbeat = time.time()
                        # Schedule next update
                        self.window.after(200, ensure_update)
                except Exception as e:
                    warning(f"UI update failed: {e}")
            
            # Start the regular updates
            self.window.after(200, ensure_update)
            
            # Now start mainloop with error handling
            debug("Starting standard mainloop with safety checks")
            self.window.mainloop()
            debug("Standard mainloop completed")
            
        except Exception as e:
            error(f"Standard mainloop failed: {e}")
            # Fall back to manual event loop
            self._manual_event_loop()

    def _manual_event_loop(self):
        """Fallback manual event loop to replace mainloop if it fails"""
        from debug_logger import warning, debug
        
        warning("Using manual event loop as fallback")
        
        try:
            running = True
            
            def process_events():
                nonlocal running
                try:
                    if hasattr(self, 'window') and self.window.winfo_exists():
                        # Update the root window to process events
                        self.window.update()
                        # Reset heartbeat
                        self.last_heartbeat = time.time()
                        # Schedule next event processing
                        self.window.after(10, process_events)
                    else:
                        running = False
                except Exception as e:
                    warning(f"Manual event processing failed: {e}")
                    running = False
            
            # Start event processing
            process_events()
            
            # Wait until window is closed
            import time
            while running:
                time.sleep(0.1)
                
            debug("Manual event loop completed")
            
        except Exception as e:
            warning(f"Manual event loop failed: {e}")

# For testing - run this file directly
if __name__ == "__main__":
    menu = MainMenu()
    menu.run()
