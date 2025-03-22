import customtkinter as ctk
import sys
import os
import pickle
import threading
import time
import traceback

# Import debug logger for enhanced logging
from debug_logger import info, warning, error, success, transition, debug

# Apply CustomTkinter patches for thread safety (do this before any UI creation)
info("Applying CustomTkinter patches for thread safety")
try:
    from customtkinter_patch import apply_customtkinter_patches
    apply_customtkinter_patches()
except Exception as e:
    error(f"Failed to apply CustomTkinter patches: {e}")

debug("Checking if we can continue starting up")

# Add more diagnostics to find where it's hanging
info("About to import SplashScreen")
from splash_screen import SplashScreen
info("About to import MainMenu")
from main_menu import MainMenu
info("About to import GameDataManager") 
from data_manager import GameDataManager

# Define the watchdog function here, before it's used
def add_main_menu_watchdog(menu_window):
    """Add a watchdog timer to monitor main menu responsiveness"""
    from debug_logger import warning, error, info, debug
    from utils import update_app_heartbeat
    
    def watchdog_check():
        info("Main menu watchdog check running")
        try:
            # Verify window is still responding
            if hasattr(menu_window, 'winfo_exists') and menu_window.winfo_exists():
                # Update the global heartbeat
                beat_count = update_app_heartbeat()
                info(f"Main menu is responsive, watchdog rescheduled (heartbeat #{beat_count})")
                
                # Schedule another check
                menu_window.after(5000, watchdog_check)
            else:
                warning("Main menu window no longer exists, watchdog stopped")
        except Exception as e:
            error(f"Main menu watchdog check failed: {e}")
            # If the check fails, it means the window is not responding
            try:
                # Try to restart the main menu
                error("Attempting to restart main menu due to unresponsiveness")
                # Create a new menu from scratch
                from main_menu import MainMenu
                from data_manager import GameDataManager
                data_manager = GameDataManager.get_instance()
                if data_manager:
                    new_menu = MainMenu(data_manager.get_all())
                    # Add watchdog to new menu too
                    add_main_menu_watchdog(new_menu.window)
                    new_menu.run()
                    
                    # Return True to indicate success
                    return True
            except Exception as e2:
                error(f"Failed to restart main menu: {e2}")
                return False
    
    # Start the watchdog
    try:
        menu_window.after(5000, watchdog_check)
        info("Main menu watchdog started")
        return True
    except Exception as e:
        warning(f"Could not start main menu watchdog: {e}")
        return False

def main():
    info("Starting Tic Tac Toe application")
    
    # Set theme and appearance
    info("Setting appearance mode to dark")
    ctk.set_appearance_mode("dark")
    info("Setting default color theme to blue")
    ctk.set_default_color_theme("blue")
    debug("Set CustomTkinter appearance mode and color theme")
    
    # Configure CTk to disable the HighDPI auto-scaling to avoid blurry images
    info("Disabling automatic DPI awareness")
    try:
        ctk.deactivate_automatic_dpi_awareness()
        debug("Disabled automatic DPI awareness")
    except Exception as e:
        warning(f"Could not deactivate DPI awareness: {e}")
    
    # Cleanup any stray Tkinter after commands
    info("Cleaning up stray after commands")
    try:
        from utils import cleanup_after_commands
        cleanup_after_commands()
        debug("Cleaned up stray after commands")
    except Exception as e:
        warning(f"Error cleaning up after commands: {e}")
    
    # Create singleton data manager that will be passed between components
    info("Initializing data manager")
    try:
        data_manager = GameDataManager.get_instance()
        debug("Data manager initialized successfully")
    except Exception as e:
        error(f"Failed to initialize data manager: {e}")
        data_manager = None
    
    # Initialize task manager for background threading - with additional error handling
    info("Initializing task manager")
    try:
        from threaded_task_manager import task_manager
        debug("Task manager initialized successfully")
    except Exception as e:
        error(f"Failed to initialize task manager: {e}")
    
    # Try to load cached data if it exists
    info("Checking for cached data")
    try:
        cache_file = os.path.join(os.path.dirname(__file__), "game_data", "cached_data.pkl")
        debug(f"Checking for cached data at: {cache_file}")
        
        # Make sure data manager was initialized
        if data_manager:
            data_loaded = data_manager.load_from_file(cache_file, replace=False)
            if data_loaded:
                success("Loaded cached game data")
            else:
                info("No cached data found or failed to load")
        else:
            warning("Skipping cached data load - data manager not initialized")
            data_loaded = False
    except Exception as e:
        error(f"Error loading cached data: {e}")
        data_loaded = False
    
    # Define the callback for when loading completes - with additional logging
    def on_loading_complete(loaded_data):
        from debug_logger import info, success, error, warning, debug, transition
        
        transition("Loading complete callback triggered, launching main menu")
        
        # Add additional detailed logging to track where we might be getting stuck
        debug(f"Starting main menu launch procedure - data keys: {list(loaded_data.keys() if loaded_data else [])}")
        
        # Add safeguard for empty data
        if not loaded_data:
            warning("Loaded data is empty in callback - using empty initialization")
            loaded_data = {}
        
        # Update data manager with loaded data - this is the ONE-TIME loading
        if data_manager:
            for key, value in loaded_data.items():
                # Skip the preloaded menu as it's not data to store
                if key != 'preloaded_menu':
                    debug(f"Setting data manager key: {key}")
                    data_manager.set(key, value, notify=False)
                    debug(f"Added {key} to data manager")
        else:
            warning("Data manager is not initialized, skipping data update")
        
        # Save cached data for faster startup next time - do this in background
        def save_cache_data():
            try:
                # Get pickle-safe data
                if hasattr(data_manager, 'get_pickle_safe_data'):
                    save_data = data_manager.get_pickle_safe_data()
                    debug(f"Preparing to save cache data with pickle-safe method")
                else:
                    # Fall back to filtering manually
                    save_data = {
                        k: v for k, v in data_manager.get_all().items() 
                        if k in ['game_history', 'game_stats'] or not isinstance(v, object)
                    }
                    debug(f"Preparing to save cache data with manual filtering: {list(save_data.keys())}")
                    
                cache_file = os.path.join(os.path.dirname(__file__), "game_data", "cached_data.pkl")
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                
                with open(cache_file, 'wb') as f:
                    pickle.dump(save_data, f)
                    
                success("Saved cache data successfully")
                return True
            except Exception as e:
                error(f"Error saving cached data: {e}")
                import traceback
                traceback.print_exc()
                return False
            
        from threaded_task_manager import run_in_background
        debug("Starting background task to save cached data")
        run_in_background(save_cache_data)
        
        # Check if we have a preloaded menu - with better thread safety and logging
        preloaded_menu = loaded_data.get('preloaded_menu')
        debug(f"Preloaded menu available: {preloaded_menu is not None}")
        
        # Launch main menu with additional crash prevention
        try:
            # Thread-safe check for window existence
            from utils import thread_safe_window_check
            
            has_valid_window = False
            if preloaded_menu:
                try:
                    debug("Checking if preloaded menu window exists")
                    has_valid_window = thread_safe_window_check(preloaded_menu.window)
                    debug(f"Preloaded menu window valid: {has_valid_window}")
                except Exception as e:
                    warning(f"Error checking preloaded menu window: {e}")
                    has_valid_window = False
            
            if has_valid_window:
                # Show the preloaded menu
                transition("Using preloaded menu for smoother transition")
                try:
                    debug("About to show preloaded menu")
                    # Make sure it's visible
                    preloaded_menu.show()
                    success("Preloaded menu shown successfully")
                    
                    # Allow a moment for window appearance
                    debug("Pausing briefly to let window appear")
                    time.sleep(0.1)
                    
                    # Add watchdog for menu
                    add_main_menu_watchdog(preloaded_menu.window)
                    
                    # Then run it
                    debug("Starting preloaded menu mainloop")
                    preloaded_menu.run()
                except Exception as e:
                    error(f"Error showing preloaded menu: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Try creating a new menu as fallback
                    warning("Fallback: Creating new menu instance due to preloaded menu failure")
                    from main_menu import MainMenu
                    menu = MainMenu(data_manager.get_all())
                    add_main_menu_watchdog(menu.window)
                    menu.run()
            else:
                # Create a new menu if preloaded one isn't available
                transition("Creating new main menu instance")
                from main_menu import MainMenu
                debug("Initializing new MainMenu with data from data_manager")
                menu = MainMenu(data_manager.get_all())
                success("Main menu created successfully")
                
                # Add watchdog
                add_main_menu_watchdog(menu.window)
                
                debug("Starting main menu mainloop")
                menu.run()
        except Exception as e:
            error(f"Critical error launching main menu: {e}")
            import traceback
            traceback.print_exc()
            
            # Absolute last resort - try basic initialization
            try:
                error("LAST RESORT: Attempting basic UI initialization")
                root = ctk.CTk()
                root.title("Tic Tac Toe - Emergency Mode")
                root.geometry("500x300")
                
                error_label = ctk.CTkLabel(
                    root, 
                    text="Error during startup - emergency mode activated",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="#E63946"
                )
                error_label.pack(pady=20)
                
                message = ctk.CTkLabel(
                    root,
                    text="The application experienced an error during startup.\nYou can quit and restart, or continue in limited mode.",
                    font=ctk.CTkFont(size=14),
                    wraplength=400
                )
                message.pack(pady=10)
                
                quit_btn = ctk.CTkButton(
                    root,
                    text="Quit Application",
                    command=root.quit,
                    font=ctk.CTkFont(size=14),
                    fg_color="#E63946",
                    hover_color="#C5313E",
                    width=200,
                    height=40
                )
                quit_btn.pack(pady=20)
                
                root.mainloop()
            except Exception as e2:
                error(f"Emergency UI also failed: {e2}")
                
            sys.exit(1)
    
    # Initialize and show splash screen
    info("Showing splash screen") 
    
    # Try/except to ensure clean shutdown even if splash screen errors
    try:
        debug("Starting splash screen")
        # Create splash screen with loading callback
        splash = SplashScreen(on_complete_callback=on_loading_complete)
        
        # Mark that a main UI is active
        from utils import mark_main_ui_active
        mark_main_ui_active(True)
        
        # Add a hard safety timeout to prevent UI thread hangs
        def watchdog_timer():
            from debug_logger import error, warning, info
            error("WATCHDOG: UI thread may be blocked in splash screen start")
            warning("WATCHDOG: Attempting recovery...")
            
            # Try to directly trigger loaded callback as emergency measure
            try:
                if hasattr(splash, 'loaded_data'):
                    info("WATCHDOG: Executing emergency callback with available data")
                    on_loading_complete(splash.loaded_data)
                else:
                    warning("WATCHDOG: No loaded data available, using empty init")
                    on_loading_complete({})
            except Exception as e:
                error(f"WATCHDOG: Emergency callback also failed: {e}")
                # Last resort - try to exit cleanly
                sys.exit(1)
        
        # Schedule the watchdog to run after 5 seconds
        watchdog_id = None
        try:
            info("Setting up UI thread watchdog timer")
            watchdog_id = splash.window.after(5000, watchdog_timer)
        except Exception as e:
            warning(f"Could not setup watchdog timer: {e}")
            
        # Now start the splash screen
        info("About to call splash.start()")
        try:
            splash.start()
            # If we get here, cancel the watchdog
            if watchdog_id:
                try:
                    splash.window.after_cancel(watchdog_id)
                except:
                    pass
            info("Splash screen started successfully")
        except Exception as e:
            error(f"Exception in splash.start(): {e}")
            import traceback
            traceback.print_exc()
            
            # Try to cancel the watchdog to prevent double-callback
            if watchdog_id:
                try:
                    splash.window.after_cancel(watchdog_id)
                except:
                    pass
                    
            # Direct callback with emergency recovery
            warning("Directly executing callback due to splash screen failure")
            on_loading_complete(splash.loaded_data if hasattr(splash, 'loaded_data') else {})
            
    except Exception as e:
        error(f"Error in splash screen initialization: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to launch main menu even if splash screen failed
        warning("Splash screen failed, trying to launch main menu directly")
        
        # Create a simple UI showing progress
        try:
            root = ctk.CTk()
            root.title("Tic Tac Toe - Emergency Recovery")
            root.geometry("500x300")
            
            ctk.CTkLabel(
                root, 
                text="Recovering from initialization error",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#E63946"
            ).pack(pady=20)
            
            # Create a progress bar 
            progress = ctk.CTkProgressBar(root, width=400)
            progress.pack(pady=20)
            progress.set(0.2)
            
            def update_progress():
                current = progress.get()
                if current < 0.9:
                    progress.set(current + 0.1)
                    root.after(200, update_progress)
                else:
                    # Start main initialization
                    root.after(500, lambda: on_loading_complete({}))
            
            # Start progress animation
            root.after(100, update_progress)
            
            # Add quit button
            ctk.CTkButton(
                root,
                text="Quit Application",
                command=root.quit,
                font=ctk.CTkFont(size=14),
                fg_color="#E63946",
                hover_color="#C5313E"
            ).pack(pady=20)
            
            # Start UI
            root.mainloop()
            
        except Exception as e2:
            error(f"Emergency interface also failed: {e2}")
            # Last resort - try direct initialization
            on_loading_complete({})
    
    # Wrap the final task manager shutdown in a try-except
    try:
        # Perform clean shutdown of task manager when application exits
        info("Shutting down task manager")
        task_manager.shutdown()
        
        # Final cleanup of any stray after commands
        debug("Final cleanup of stray after commands")
        cleanup_after_commands()
    except Exception as e:
        error(f"Error during shutdown: {e}")

# Import tkinter for global exception handling
import _tkinter

# Define emergency fallback function
def emergency_fallback():
    """Provide a minimal emergency fallback if normal startup fails"""
    from debug_logger import error, warning, info
    from utils import is_any_ui_active, mark_emergency_active, mark_main_ui_active
    
    # Check if another UI is already running
    if is_any_ui_active():
        info("Emergency fallback called but a UI is already running - skipping")
        return
    
    # Mark that we're starting emergency mode
    mark_emergency_active(True)
    
    error("EMERGENCY FALLBACK: Starting minimal emergency application")
    
    try:
        import customtkinter as ctk
        import tkinter as tk
        
        # Attempt to clean up existing Tkinter instances
        try:
            # Try to get existing root and destroy it
            import tkinter
            if hasattr(tkinter, '_default_root') and tkinter._default_root:
                try:
                    info("Closing existing Tkinter root before emergency start")
                    tkinter._default_root.destroy()
                except:
                    pass
        except:
            pass
        
        # Create a minimal emergency window
        root = ctk.CTk()
        root.title("Tic Tac Toe - Emergency Mode")
        root.geometry("600x400")
        root.configure(fg_color="#1E1E1E")
        
        # Function to run when window closes
        def on_closing():
            mark_emergency_active(False)
            root.destroy()
            info("Emergency application closed")
        
        # Set proper close handler
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Add some basic UI
        header = ctk.CTkLabel(
            root,
            text="Tic Tac Toe - Emergency Mode",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#E63946"
        )
        header.pack(pady=30)
        
        message = ctk.CTkLabel(
            root,
            text="The application couldn't start normally.\nThis is a fallback mode with basic functionality.",
            font=ctk.CTkFont(size=16),
            text_color="#EEEEEE",
            justify="center"
        )
        message.pack(pady=20)
        
        # Frame for game buttons
        button_frame = ctk.CTkFrame(root, fg_color="#252525", corner_radius=10)
        button_frame.pack(pady=20, fill="x", padx=40)
        
        # Add a simple version of the game
        game_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        game_frame.pack(pady=20, padx=20)
        
        # Current player indicator
        player_var = tk.StringVar(value="X")
        
        # Game state
        current_board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        game_over = False
        
        def check_winner():
            nonlocal current_board, game_over
            
            # Check rows
            for row in current_board:
                if row[0] != 0 and row[0] == row[1] == row[2]:
                    game_over = True
                    return row[0]
            
            # Check columns
            for col in range(3):
                if current_board[0][col] != 0 and current_board[0][col] == current_board[1][col] == current_board[2][col]:
                    game_over = True
                    return current_board[0][col]
            
            # Check diagonals
            if current_board[0][0] != 0 and current_board[0][0] == current_board[1][1] == current_board[2][2]:
                game_over = True
                return current_board[0][0]
                
            if current_board[0][2] != 0 and current_board[0][2] == current_board[1][1] == current_board[2][0]:
                game_over = True
                return current_board[0][2]
            
            # Check for draw
            if all(current_board[r][c] != 0 for r in range(3) for c in range(3)):
                game_over = True
                return "Draw"
            
            return None
        
        def cell_click(row, col):
            nonlocal current_board, game_over
            
            if game_over:
                return
                
            # If cell is already taken, ignore
            if current_board[row][col] != 0:
                return
                
            # Update board
            current_player = 1 if player_var.get() == "X" else 2
            current_board[row][col] = current_player
            
            # Update button text
            buttons[row][col].configure(
                text="X" if current_player == 1 else "O",
                text_color="#4F85CC" if current_player == 1 else "#FF5C8D"
            )
            
            # Check for winner
            result = check_winner()
            if result:
                if result == "Draw":
                    status_label.configure(text="Game ended in a draw!")
                else:
                    winner = "X" if result == 1 else "O"
                    status_label.configure(text=f"Player {winner} wins!")
                    
                # Enable restart button
                restart_btn.configure(state="normal")
            else:
                # Switch player
                player_var.set("O" if player_var.get() == "X" else "X")
                status_label.configure(text=f"Current player: {player_var.get()}")
        
        def restart_game():
            nonlocal current_board, game_over
            current_board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            game_over = False
            player_var.set("X")
            
            # Reset buttons
            for row in range(3):
                for col in range(3):
                    buttons[row][col].configure(text="", fg_color="#333333")
            
            # Reset status
            status_label.configure(text="Current player: X")
            restart_btn.configure(state="disabled")
        
        # Create the grid of buttons
        buttons = []
        for row in range(3):
            button_row = []
            for col in range(3):
                btn = ctk.CTkButton(
                    game_frame,
                    text="",
                    width=80,
                    height=80,
                    corner_radius=0,
                    font=ctk.CTkFont(size=24, weight="bold"),
                    fg_color="#333333",
                    hover_color="#444444",
                    command=lambda r=row, c=col: cell_click(r, c)
                )
                btn.grid(row=row, column=col, padx=2, pady=2)
                button_row.append(btn)
            buttons.append(button_row)
        
        # Game status
        status_label = ctk.CTkLabel(
            button_frame,
            text="Current player: X",
            font=ctk.CTkFont(size=16),
            text_color="#EEEEEE"
        )
        status_label.pack(pady=10)
        
        # Restart button
        restart_btn = ctk.CTkButton(
            button_frame,
            text="Restart Game",
            command=restart_game,
            font=ctk.CTkFont(size=14),
            fg_color="#3E92CC",
            hover_color="#2D7DB3",
            state="disabled"
        )
        restart_btn.pack(pady=10)
        
        # Add quit button
        quit_btn = ctk.CTkButton(
            root,
            text="Quit Application",
            command=root.quit,
            font=ctk.CTkFont(size=14),
            fg_color="#E63946",
            hover_color="#C5313E",
            width=180
        )
        quit_btn.pack(pady=20)
        
        info("Emergency fallback interface setup complete")
        
        # Start the mainloop
        root.mainloop()
        info("Emergency application closed normally")
        
    except Exception as e:
        error(f"Emergency fallback failed: {e}")
        mark_emergency_active(False)  # Reset the flag
        import traceback
        traceback.print_exc()

# Add a early timeout for slow operations
from utils import force_early_timeout
try:
    force_early_timeout(emergency_callback=emergency_fallback)
except Exception as e:
    print(f"Error setting up early timeout: {e}")

if __name__ == "__main__":
    # Set up deadlock detection and force exit as safety measure
    from utils import force_exit_if_stuck
    force_exit_if_stuck(timeout=60)  # Force exit after 60 seconds of inactivity
    
    try:
        main()
    except KeyboardInterrupt:
        info("\nApplication terminated by user.")
        # Cleanup any stray after commands before exit
        from utils import cleanup_after_commands
        cleanup_after_commands()
        sys.exit(0)
    except _tkinter.TclError as e:
        if "application has been destroyed" in str(e):
            info("\nApplication closed.")
        else:
            error(f"\nTkinter error: {e}")
        # Cleanup any stray after commands before exit
        from utils import cleanup_after_commands
        cleanup_after_commands()
        sys.exit(0)
    except Exception as e:
        error(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup any stray after commands before exit
        from utils import cleanup_after_commands
        cleanup_after_commands()
        sys.exit(1)
