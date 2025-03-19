import os
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence, ImageFont, ImageDraw
import numpy as np
import customtkinter as ctk

# Asset directory path
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Create assets directory if it doesn't exist
os.makedirs(ASSETS_DIR, exist_ok=True)

# Default animation filenames
DEFAULT_ANIMATIONS = {
    "x_win": "x_win.gif",
    "o_win": "o_win.gif",
    "draw": "draw.gif",
}

class AssetManager:
    """Class for managing game assets including images and animations"""
    
    def __init__(self):
        self.cached_images = {}  # Cache for loaded images
        self.cached_gifs = {}    # Cache for loaded GIF animations
        self.icons = {}          # Cache for UI icons
        
    def get_asset_path(self, filename):
        """Get full path to an asset file"""
        return os.path.join(ASSETS_DIR, filename)
    
    def asset_exists(self, filename):
        """Check if an asset file exists"""
        if not filename:
            return False
        return os.path.exists(self.get_asset_path(filename))
    
    def load_image(self, filename, size=None):
        """Load an image with optional resizing
        
        Args:
            filename (str): Image filename in assets directory
            size (tuple): Optional (width, height) to resize image
            
        Returns:
            CTkImage: CustomTkinter compatible image
        """
        if not filename:
            return None
            
        cache_key = f"{filename}_{size[0]}x{size[1]}" if size else filename
        
        if cache_key in self.cached_images:
            return self.cached_images[cache_key]
            
        try:
            file_path = self.get_asset_path(filename)
            if not os.path.exists(file_path):
                return None
                
            # Use CTkImage instead of ImageTk.PhotoImage
            if size:
                tk_image = ctk.CTkImage(light_image=Image.open(file_path), 
                                       size=size)
            else:
                tk_image = ctk.CTkImage(light_image=Image.open(file_path))
                
            self.cached_images[cache_key] = tk_image
            return tk_image
        except Exception as e:
            print(f"Error loading image {filename}: {e}")
            return None
    
    def load_gif_frames(self, filename, size=None):
        """Load all frames from a GIF animation
        
        Args:
            filename (str): GIF filename in assets directory
            size (tuple): Optional (width, height) to resize frames
            
        Returns:
            list: List of CTkImage frames
        """
        if not filename:
            return []
            
        cache_key = f"{filename}_frames_{size[0]}x{size[1]}" if size else f"{filename}_frames"
        
        if cache_key in self.cached_gifs:
            return self.cached_gifs[cache_key]
            
        try:
            file_path = self.get_asset_path(filename)
            if not os.path.exists(file_path):
                return []
                
            gif = Image.open(file_path)
            frames = []
            
            # Extract frames from GIF
            frame_count = 0
            raw_frames = []
            for frame in ImageSequence.Iterator(gif):
                frame_copy = frame.copy().convert("RGBA") # Convert to RGBA for transparency
                if size:
                    frame_copy = frame_copy.resize(size)
                raw_frames.append(frame_copy)
                frame_count += 1
                
                # Limit to reasonable number of frames
                if frame_count >= 50:  # Avoid excessive memory use
                    break
            
            # Convert frames to CTkImage objects
            for i, frame in enumerate(raw_frames):
                # Create CTkImage for each frame
                ctk_frame = ctk.CTkImage(light_image=frame, size=size)
                frames.append(ctk_frame)
                
            self.cached_gifs[cache_key] = frames
            return frames
        except Exception as e:
            print(f"Error loading GIF {filename}: {e}")
            return []
    
    def get_animation_path(self, animation_name):
        """Get full path to an animation file
        
        Args:
            animation_name (str): Name of animation (x_win, o_win, draw)
            
        Returns:
            str: Full path to animation file or None if not found
        """
        if animation_name in DEFAULT_ANIMATIONS:
            filename = DEFAULT_ANIMATIONS[animation_name]
            full_path = self.get_asset_path(filename)
            if os.path.exists(full_path):
                return full_path
        return None

    def create_symbol_image(self, symbol, size=(80, 80), style="modern"):
        """Create a custom symbol image (X or O)"""
        try:
            # Create a blank transparent image with padding for better visibility
            padded_size = (int(size[0] * 1.1), int(size[1] * 1.1))
            image = Image.new('RGBA', padded_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Get effective dimensions for drawing
            width, height = size
            
            # Center offset to account for padding
            offset_x = (padded_size[0] - width) // 2
            offset_y = (padded_size[1] - height) // 2
            
            symbol = symbol.upper()
            
            # Vibrant colors for better visibility
            x_colors = {
                "modern": "#4361EE",
                "neon": "#00FF00",  # Bright green
                "classic": "#4F85CC"
            }
            
            o_colors = {
                "modern": "#F72585",
                "neon": "#FF0066",  # Bright pink
                "classic": "#CC4F85"
            }
            
            # Get appropriate color
            x_color = x_colors.get(style, x_colors["modern"])
            o_color = o_colors.get(style, o_colors["modern"])
            
            # Use thicker lines for better visibility
            line_width = max(int(min(width, height) * 0.08), 5)
            
            if symbol == "X":
                # Calculate parameters for X
                margin = int(width * 0.15)
                thickness = max(int(width * 0.2), 6)  # Even thicker
                
                # Draw X with thicker lines and offset for padding
                for i in range(-thickness//2, thickness//2 + 1):
                    # First diagonal (top-left to bottom-right)
                    draw.line(
                        [(offset_x + margin + i, offset_y + margin), 
                         (offset_x + width - margin + i, offset_y + height - margin)],
                        fill=x_color,
                        width=line_width
                    )
                    
                    # Second diagonal (top-right to bottom-left)
                    draw.line(
                        [(offset_x + width - margin + i, offset_y + margin), 
                         (offset_x + margin + i, offset_y + height - margin)],
                        fill=x_color,
                        width=line_width
                    )
                    
            elif symbol == "O":
                # Calculate parameters for O
                margin = int(width * 0.15)
                thickness = max(int(width * 0.15), 5)  # Thicker
                
                # Draw O as a thick circle with offset for padding
                for i in range(thickness):
                    offset = i - thickness//2
                    radius_x = (width - 2*margin) // 2
                    radius_y = (height - 2*margin) // 2
                    
                    # Calculate bounding box for ellipse with padding offset
                    x1 = offset_x + width//2 - radius_x + offset
                    y1 = offset_y + height//2 - radius_y + offset
                    x2 = offset_x + width//2 + radius_x + offset
                    y2 = offset_y + height//2 + radius_y + offset
                    
                    draw.ellipse([x1, y1, x2, y2], outline=o_color, width=line_width)
            
            # Convert to CTkImage for CustomTkinter
            ctk_image = ctk.CTkImage(
                light_image=image, 
                dark_image=image,
                size=padded_size  # Use the padded size
            )
            return ctk_image
            
        except Exception as e:
            print(f"Error creating symbol image: {e}")
            return None
    
    def create_icon(self, icon_name, size=(24, 24), color="#FFFFFF"):
        """Create a simple geometric icon for UI elements
        
        Args:
            icon_name (str): Name of icon to create
            size (tuple): Icon dimensions
            color (str): Color of the icon
            
        Returns:
            CTkImage: Icon image for CustomTkinter
        """
        cache_key = f"{icon_name}_{size[0]}x{size[1]}_{color}"
        
        if cache_key in self.icons:
            return self.icons[cache_key]
        
        try:
            # Create blank transparent image
            image = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            width, height = size
            
            if icon_name == "checkmark":
                # Draw checkmark
                points = [
                    (width * 0.2, height * 0.5),
                    (width * 0.4, height * 0.7),
                    (width * 0.8, height * 0.3)
                ]
                draw.line(points, fill=color, width=2)
                
            elif icon_name == "cross":
                # Draw X
                margin = width * 0.2
                draw.line([(margin, margin), (width - margin, height - margin)], fill=color, width=2)
                draw.line([(width - margin, margin), (margin, height - margin)], fill=color, width=2)
                
            elif icon_name == "reload":
                # Draw reload/refresh icon
                margin = width * 0.2
                # Draw circle
                draw.arc(
                    [margin, margin, width - margin, height - margin],
                    start=30, end=330, fill=color, width=2
                )
                # Draw arrow
                arrow_points = [
                    (width * 0.65, margin), 
                    (width * 0.8, margin * 1.5),
                    (width * 0.7, margin * 2)
                ]
                draw.line(arrow_points, fill=color, width=2)
            
            # Convert to CTkImage for CustomTkinter
            ctk_image = ctk.CTkImage(light_image=image, size=size)
            self.icons[cache_key] = ctk_image
            return ctk_image
            
        except Exception as e:
            print(f"Error creating icon {icon_name}: {e}")
            return None
            
    def clear_cache(self):
        """Clear all cached assets"""
        self.cached_images = {}
        self.cached_gifs = {}
        self.icons = {}
        
    def generate_placeholder_animations(self):
        """Generate placeholder animations if real ones don't exist
        
        Creates simple animations for win/draw cases that can be used
        if no GIF files are available
        """
        # X win animation
        if not self.asset_exists(DEFAULT_ANIMATIONS["x_win"]):
            self._create_placeholder_animation("x_win", "X", frames=10)
            
        # O win animation
        if not self.asset_exists(DEFAULT_ANIMATIONS["o_win"]):
            self._create_placeholder_animation("o_win", "O", frames=10)
            
        # Draw animation
        if not self.asset_exists(DEFAULT_ANIMATIONS["draw"]):
            self._create_placeholder_animation("draw", "=", frames=10)
    
    def _create_placeholder_animation(self, name, symbol, frames=10, size=(200, 150)):
        """Internal method to create a placeholder animation
        
        Args:
            name (str): Animation name
            symbol (str): Symbol to display
            frames (int): Number of frames
            size (tuple): Image size
        """
        try:
            images = []
            width, height = size
            
            # Use simple shapes instead of text to avoid font issues
            for i in range(frames):
                # Create frame
                image = Image.new('RGB', size, (30, 30, 30))
                draw = ImageDraw.Draw(image)
                
                # Animation factor (pulsating effect)
                scale = 0.5 + 0.5 * np.sin(i / frames * 2 * np.pi)
                color_val = int(155 + 100 * scale)
                
                # Symbol color
                if symbol == "X":
                    color = (color_val, 100, 255)  # Blue-ish for X
                elif symbol == "O":
                    color = (255, 100, color_val)  # Pink-ish for O
                else:
                    color = (color_val, color_val, 100)  # Yellow-ish for draw
                
                # Calculate size based on scale
                symbol_size = int(min(width, height) * 0.5 * (0.8 + 0.2 * scale))
                margin = (min(width, height) - symbol_size) // 2
                thickness = max(int(symbol_size * 0.1), 3)
                
                # Center coordinates
                center_x = width // 2
                center_y = height // 2
                
                # Draw appropriate symbol using shapes only (no text)
                if symbol == "X":
                    # Draw X as two crossing lines
                    x_margin = symbol_size // 2
                    draw.line(
                        [(center_x - x_margin, center_y - x_margin), 
                         (center_x + x_margin, center_y + x_margin)], 
                        fill=color, width=thickness
                    )
                    draw.line(
                        [(center_x + x_margin, center_y - x_margin), 
                         (center_x - x_margin, center_y + x_margin)], 
                        fill=color, width=thickness
                    )
                elif symbol == "O":
                    # Draw O as a circle
                    x1 = center_x - symbol_size // 2
                    y1 = center_y - symbol_size // 2
                    x2 = center_x + symbol_size // 2
                    y2 = center_y + symbol_size // 2
                    draw.ellipse([x1, y1, x2, y2], outline=color, width=thickness)
                else:
                    # Draw equals sign for draw
                    rect_height = symbol_size // 5
                    spacing = rect_height
                    
                    # Top bar
                    draw.rectangle(
                        [center_x - symbol_size//2, center_y - spacing - rect_height, 
                         center_x + symbol_size//2, center_y - spacing], 
                        fill=color
                    )
                    
                    # Bottom bar
                    draw.rectangle(
                        [center_x - symbol_size//2, center_y + spacing, 
                         center_x + symbol_size//2, center_y + spacing + rect_height], 
                        fill=color
                    )
                
                # Add sparkle/star effects
                if i % 2 == 0:
                    for _ in range(8):
                        # Random positions around the symbol
                        angle = np.random.uniform(0, 2 * np.pi)
                        distance = np.random.uniform(0.6, 1.0) * symbol_size
                        x = int(center_x + np.cos(angle) * distance)
                        y = int(center_y + np.sin(angle) * distance)
                        
                        # Star size varies
                        star_size = np.random.randint(2, 6)
                        
                        # Draw simple sparkle dot
                        brightness = int(200 + 55 * scale)
                        sparkle_color = (brightness, brightness, brightness)
                        draw.ellipse(
                            [x - star_size, y - star_size, 
                             x + star_size, y + star_size], 
                            fill=sparkle_color
                        )
                
                images.append(image)
            
            # Save as GIF
            filename = DEFAULT_ANIMATIONS[name]
            filepath = self.get_asset_path(filename)
            images[0].save(
                filepath,
                save_all=True,
                append_images=images[1:],
                optimize=False,
                duration=100,
                loop=0
            )
            print(f"Successfully created placeholder animation: {filename}")
            return True
            
        except Exception as e:
            print(f"Error creating placeholder animation: {e}")
            return False
