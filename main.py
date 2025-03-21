import customtkinter as ctk
import sys
import os
from splash_screen import SplashScreen
from main_menu import MainMenu
from data_manager import GameDataManager

def main():
    # Set theme and appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Configure CTk to disable the HighDPI auto-scaling to avoid blurry images
    ctk.deactivate_automatic_dpi_awareness()
    
    # Cleanup any stray Tkinter after commands
    from utils import cleanup_after_commands
    cleanup_after_commands()
    
    # Create data manager that will be passed to all components
    data_manager = GameDataManager()
    
    # Initialize task manager for background threading
    from threaded_task_manager import task_manager
    
    # Import tkinter for exception handling
    import _tkinter
    
    # Try to load cached data if it exists
    cache_file = os.path.join(os.path.dirname(__file__), "game_data", "cached_data.pkl")
    data_loaded = data_manager.load_from_file(cache_file, replace=False)
    
    if data_loaded:
        print("Loaded cached game data")
    
    # Define the callback for when loading completes
    def on_loading_complete(loaded_data):
        print("Loading complete, launching main menu...")
        
        # Update data manager with loaded data
        for key, value in loaded_data.items():
            data_manager.set(key, value, notify=False)
        
        # Save cached data for faster startup next time - do this in background
        def save_cache_data():
            data_manager.save_to_file(cache_file)
            return True
            
        from threaded_task_manager import run_in_background
        run_in_background(save_cache_data)
        
        # Launch main menu with the data manager
        # Use try/except to catch any startup errors
        try:
            menu = MainMenu(data_manager.get_all())
            menu.run()
        except Exception as e:
            print(f"Error launching main menu: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Initialize and show splash screen
    print("Showing splash screen...")
    splash = SplashScreen(on_complete_callback=on_loading_complete)
    
    # Try/except to ensure clean shutdown even if splash screen errors
    try:
        splash.start()
    except Exception as e:
        print(f"Error in splash screen: {e}")
        # Try to launch main menu even if splash screen failed
        on_loading_complete(splash.loaded_data if hasattr(splash, 'loaded_data') else {})
    
    # Wrap the final task manager shutdown in a try-except
    try:
        # Perform clean shutdown of task manager when application exits
        task_manager.shutdown()
        
        # Final cleanup of any stray after commands
        cleanup_after_commands()
    except:
        pass

# Import tkinter for global exception handling
import _tkinter

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        # Cleanup any stray after commands before exit
        from utils import cleanup_after_commands
        cleanup_after_commands()
        sys.exit(0)
    except _tkinter.TclError as e:
        if "application has been destroyed" in str(e):
            print("\nApplication closed.")
        else:
            print(f"\nTkinter error: {e}")
        # Cleanup any stray after commands before exit
        from utils import cleanup_after_commands
        cleanup_after_commands()
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup any stray after commands before exit
        from utils import cleanup_after_commands
        cleanup_after_commands()
        sys.exit(1)
