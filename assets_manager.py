import os
import time
from PIL import Image, ImageDraw, ImageTk, ImageSequence
import customtkinter as ctk
from utils import convert_to_ctk_image

# Define assets directory
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

class AssetManager:
    """Manager for game assets like images and animations"""
    
    def __init__(self):
        """Initialize the asset manager"""
        # Ensure assets directory exists
        os.makedirs(ASSETS_DIR, exist_ok=True)
        
        # Cache for loaded assets to prevent duplicated loading
        self.image_cache = {}
        self.animation_cache = {}
        self.ctk_image_cache = {}
        
        # Known assets that can be generated if missing
        self.known_assets = {
            'x_symbol.png': self._generate_x_symbol,
            'o_symbol.png': self._generate_o_symbol,
            'game_over.png': self._generate_game_over,
            'x_win.gif': self._generate_win_animation,
            'o_win.gif': self._generate_win_animation,
            'draw.gif': self._generate_draw_animation
        }
    
    def load_image(self, filename, size=None, fallback_generate=False):
        """Load an image file
        
        Args:
            filename (str): Image filename
            size (tuple): Optional size to resize to (width, height)
            fallback_generate (bool): Whether to generate placeholder if missing
            
        Returns:
            PIL.Image: Loaded image or None if not found
        """
        # Check cache first
        cache_key = f"{filename}_{size}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        # Load the image
        filepath = os.path.join(ASSETS_DIR, filename)
        
        # Generate if missing and generation is supported
        if not os.path.exists(filepath) and fallback_generate and filename in self.known_assets:
            generate_func = self.known_assets[filename]
            success = generate_func(filename)
            if not success:
                return None
        
        try:
            if os.path.exists(filepath):
                # Load and resize if needed
                image = Image.open(filepath)
                if size:
                    image = image.resize(size, Image.LANCZOS)
                
                # Cache it
                self.image_cache[cache_key] = image
                return image
        except Exception as e:
            print(f"Error loading image {filename}: {e}")
        
        return None
    
    def get_ctk_image(self, filename, size=None, fallback_generate=False):
        """Get a CTkImage for use with CustomTkinter
        
        Args:
            filename (str): Image filename
            size (tuple): Optional size to resize to (width, height)
            fallback_generate (bool): Whether to generate placeholder if missing
            
        Returns:
            CTkImage: CustomTkinter image or None if not found
        """
        # Check cache first
        cache_key = f"ctk_{filename}_{size}"
        if cache_key in self.ctk_image_cache:
            return self.ctk_image_cache[cache_key]
        
        # Load the PIL image
        pil_image = self.load_image(filename, size, fallback_generate)
        if not pil_image:
            return None
        
        # Convert to CTkImage
        try:
            ctk_image = convert_to_ctk_image(pil_image, size)
            
            # Cache it
            self.ctk_image_cache[cache_key] = ctk_image
            return ctk_image
        except Exception as e:
            print(f"Error converting to CTkImage: {e}")
            return None
    
    def get_animation_path(self, name):
        """Get path to an animation file
        
        Args:
            name (str): Animation name (e.g., 'x_win', 'draw')
            
        Returns:
            str: Path to animation file or None if not found
        """
        # Try different extensions
        extensions = ['.gif']
        
        for ext in extensions:
            path = os.path.join(ASSETS_DIR, f"{name}{ext}")
            if os.path.exists(path):
                return path
        
        return None
    
    def preload_animation(self, filename, size=None):
        """Preload animation frames for future use
        
        Args:
            filename (str): Animation filename
            size (tuple): Optional size to resize frames to
            
        Returns:
            list: List of animation frames as CTkImage objects
        """
        # Check cache first
        cache_key = f"{filename}_{size}"
        if cache_key in self.animation_cache:
            return self.animation_cache[cache_key]
        
        # Load animation
        filepath = os.path.join(ASSETS_DIR, filename)
        
        try:
            if os.path.exists(filepath):
                from utils import load_gif_frames_as_ctk
                frames = load_gif_frames_as_ctk(filepath, size)
                
                # Cache it
                self.animation_cache[cache_key] = frames
                return frames
        except Exception as e:
            print(f"Error preloading animation {filename}: {e}")
        
        return []
    
    def load_gif_frames(self, filename, size=None):
        """Load frames from a GIF animation
        
        Args:
            filename (str): GIF filename
            size (tuple): Optional size to resize frames to (width, height)
            
        Returns:
            list: List of PhotoImage frames
        """
        # For backward compatibility
        return self.preload_animation(filename, size)
    
    def generate_placeholder_animations(self):
        """Generate placeholder animations for standard game events"""
        # Generate each animation if it doesn't exist
        for name in ['x_win.gif', 'o_win.gif', 'draw.gif']:
            self.get_animation_path(name.split('.')[0])  # Just get the name part
            
            # Generate if missing
            filepath = os.path.join(ASSETS_DIR, name)
            if not os.path.exists(filepath):
                if name in self.known_assets:
                    generate_func = self.known_assets[name]
                    generate_func(name)
        
        return True
    
    def _generate_x_symbol(self, filename):
        """Generate a placeholder X symbol image
        
        Args:
            filename (str): Target filename
            
        Returns:
            bool: True if generated successfully, False otherwise
        """
        try:
            # Create X symbol
            size = (200, 200)
            image = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # X color
            x_color = (79, 133, 204, 255)  # Blue X
            
            # Draw X
            line_width = 20
            padding = 20
            draw.line([(padding, padding), (size[0] - padding, size[1] - padding)], fill=x_color, width=line_width)
            draw.line([(size[0] - padding, padding), (padding, size[1] - padding)], fill=x_color, width=line_width)
            
            # Save
            filepath = os.path.join(ASSETS_DIR, filename)
            image.save(filepath)
            
            print(f"Generated X symbol at {filepath}")
            return True
        except Exception as e:
            print(f"Error generating X symbol: {e}")
            return False
    
    def _generate_o_symbol(self, filename):
        """Generate a placeholder O symbol image
        
        Args:
            filename (str): Target filename
            
        Returns:
            bool: True if generated successfully, False otherwise
        """
        try:
            # Create O symbol
            size = (200, 200)
            image = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # O color
            o_color = (255, 92, 141, 255)  # Pink O
            
            # Draw circle
            padding = 20
            line_width = 20
            draw.ellipse(
                [(padding, padding), (size[0] - padding, size[1] - padding)],
                outline=o_color,
                width=line_width
            )
            
            # Save
            filepath = os.path.join(ASSETS_DIR, filename)
            image.save(filepath)
            
            print(f"Generated O symbol at {filepath}")
            return True
        except Exception as e:
            print(f"Error generating O symbol: {e}")
            return False
    
    def _generate_game_over(self, filename):
        """Generate a placeholder game over image
        
        Args:
            filename (str): Target filename
            
        Returns:
            bool: True if generated successfully, False otherwise
        """
        try:
            # Create game over image
            size = (400, 100)
            image = Image.new("RGBA", size, (0, 0, 0, 128))
            draw = ImageDraw.Draw(image)
            
            # Draw text
            text = "GAME OVER"
            
            # Calculate text position (center)
            try:
                # Use ImageFont if available
                from PIL import ImageFont
                font = ImageFont.truetype("arial.ttf", 36)
                text_size = draw.textlength(text, font=font)
                x = (size[0] - text_size) // 2
                
                # Draw with font
                draw.text((x, 30), text, fill=(255, 255, 255, 255), font=font)
            except Exception:
                # Fallback if font not available
                x = size[0] // 4
                draw.text((x, 30), text, fill=(255, 255, 255, 255))
            
            # Save
            filepath = os.path.join(ASSETS_DIR, filename)
            image.save(filepath)
            
            print(f"Generated game over image at {filepath}")
            return True
        except Exception as e:
            print(f"Error generating game over image: {e}")
            return False
    
    def _generate_win_animation(self, filename):
        """Generate a win animation
        
        Args:
            filename (str): Target filename
            
        Returns:
            bool: True if generated successfully, False otherwise
        """
        try:
            # Figure out which player this is for
            player = 1 if 'x_win' in filename.lower() else 2
            
            # Create a series of frames with win animation
            frames = []
            size = (200, 150)
            bg_color = (42, 42, 42, 200)
            
            # Player colors
            colors = {
                1: (79, 133, 204, 255),  # X: Blue
                2: (255, 92, 141, 255)   # O: Pink
            }
            color = colors[player]
            
            # Player symbols
            symbols = {1: "X", 2: "O"}
            symbol = symbols[player]
            
            # Generate frames
            num_frames = 15
            for i in range(num_frames):
                # Create a new frame
                frame = Image.new("RGBA", size, bg_color)
                draw = ImageDraw.Draw(frame)
                
                # Animation phase - growing and shrinking
                scale = 1.0 + 0.3 * abs(i - num_frames // 2) / (num_frames // 2)
                
                # Draw text with growing/shrinking effect
                text = f"{symbol} WINS!"
                
                # Calculate text position and size
                try:
                    # Use ImageFont if available
                    from PIL import ImageFont
                    font_size = int(36 * scale)
                    font = ImageFont.truetype("arial.ttf", font_size)
                    text_size = draw.textlength(text, font=font)
                    x = (size[0] - text_size) // 2
                    
                    # Draw with scaling
                    draw.text((x, 50), text, fill=color, font=font)
                except Exception:
                    # Fallback if font not available
                    x = size[0] // 4
                    draw.text((x, 50), text, fill=color)
                
                frames.append(frame)
            
            # Save as GIF
            filepath = os.path.join(ASSETS_DIR, filename)
            frames[0].save(
                filepath,
                save_all=True,
                append_images=frames[1:],
                duration=100,
                loop=0
            )
            
            print(f"Generated win animation at {filepath}")
            return True
        except Exception as e:
            print(f"Error generating win animation: {e}")
            return False
    
    def _generate_draw_animation(self, filename):
        """Generate a draw animation
        
        Args:
            filename (str): Target filename
            
        Returns:
            bool: True if generated successfully, False otherwise
        """
        try:
            # Create a series of frames with draw animation
            frames = []
            size = (200, 150)
            bg_color = (42, 42, 42, 200)
            
            # Generate frames
            num_frames = 15
            for i in range(num_frames):
                # Create a new frame
                frame = Image.new("RGBA", size, bg_color)
                draw = ImageDraw.Draw(frame)
                
                # Animation phase - color changing
                phase = i / num_frames
                r = int(255 * (0.5 + 0.5 * abs(phase - 0.5) * 2))
                g = int(200 * phase)
                b = int(100 * (1 - phase))
                color = (r, g, b, 255)
                
                # Draw text with color change
                text = "DRAW!"
                
                # Calculate text position and size
                try:
                    # Use ImageFont if available
                    from PIL import ImageFont
                    font_size = 36
                    font = ImageFont.truetype("arial.ttf", font_size)
                    text_size = draw.textlength(text, font=font)
                    x = (size[0] - text_size) // 2
                    
                    # Draw with color change
                    draw.text((x, 50), text, fill=color, font=font)
                except Exception:
                    # Fallback if font not available
                    x = size[0] // 4
                    draw.text((x, 50), text, fill=color)
                
                frames.append(frame)
            
            # Save as GIF
            filepath = os.path.join(ASSETS_DIR, filename)
            frames[0].save(
                filepath,
                save_all=True,
                append_images=frames[1:],
                duration=100,
                loop=0
            )
            
            print(f"Generated draw animation at {filepath}")
            return True
        except Exception as e:
            print(f"Error generating draw animation: {e}")
            return False
