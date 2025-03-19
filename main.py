import customtkinter as ctk
import os
import tkinter as tk
from app import TicTacToeApp
from assets_manager import AssetManager, ASSETS_DIR

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
    if not os.path.exists(os.path.join(ASSETS_DIR, "x_win.gif")):
        print("No animations found, generating placeholders...")
        assets.generate_placeholder_animations()
        print("Animation generation complete.")
    
    # Set window icon if available
    icon_path = os.path.join(ASSETS_DIR, "icon.png")
    if os.path.exists(icon_path):
        try:
            # Different method for different platforms
            if hasattr(root, 'iconphoto'):
                icon = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon)
        except Exception as e:
            print(f"Could not load icon: {e}")
    
    print("Starting application...")
    # Initialize app with the asset manager
    app = TicTacToeApp(root, assets)
    
    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()
