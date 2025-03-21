import customtkinter as ctk
from app import TicTacToeApp
from assets_manager import AssetManager, ASSETS_DIR
import os
import sys

def main():
    # Set theme and appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create root window
    root = ctk.CTk()
    root.title("Tic Tac Toe Game")
    
    # Initialize asset manager
    print("Initializing asset manager...")
    assets = AssetManager()
    
    # Generate placeholder animations if needed
    assets.generate_placeholder_animations()
    
    # Create app
    print("Initializing game...")
    app = TicTacToeApp(root, assets_manager=assets)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Check for --train-ai argument
        if sys.argv[1] == "--train-ai":
            print("Auto-starting AI training...")
            app.train_ai_model()
        # Check for --view-history argument
        elif sys.argv[1] == "--view-history":
            print("Auto-opening history viewer...")
            app.root.after(500, app.show_game_history)
    
    # Run the application
    print("Starting game...")
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
