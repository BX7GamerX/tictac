import customtkinter as ctk
from PIL import Image, ImageTk
import time
import os
import _tkinter  # Add explicit import for _tkinter

def convert_to_ctk_image(pil_image, size=None):
    """Convert a PIL image to CTkImage for proper scaling on HighDPI displays
    
    Args:
        pil_image (PIL.Image): PIL image to convert
        size (tuple): Optional size to resize image to (width, height)
        
    Returns:
        CTkImage: CustomTkinter image
    """
    if size is not None:
        pil_image = pil_image.resize(size)
    
    # Create CTkImage from PIL image
    return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)

def load_gif_frames_as_ctk(filepath, size=None):
    """Load GIF frames as CTkImage objects
    
    Args:
        filepath (str): Path to GIF file
        size (tuple): Optional size to resize frames to (width, height)
        
    Returns:
        list: List of CTkImage frames
    """
    from PIL import Image, ImageSequence
    
    frames = []
    try:
        with Image.open(filepath) as img:
            for frame in ImageSequence.Iterator(img):
                # Convert frame to RGBA and resize if needed
                frame = frame.convert("RGBA")
                if size:
                    frame = frame.resize(size)
                
                # Convert to CTkImage
                ctk_frame = convert_to_ctk_image(frame)
                frames.append(ctk_frame)
    except Exception as e:
        print(f"Error loading GIF frames from {filepath}: {e}")
    
    return frames

def safe_after(widget, delay, callback):
    """Schedule a callback safely with existence checking
    
    Args:
        widget: Tkinter widget to schedule after on
        delay: Delay in milliseconds
        callback: Function to call
        
    Returns:
        after_id: ID that can be used to cancel, or None if scheduling failed
    """
    # Check if widget exists
    try:
        if not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
            return None
    except _tkinter.TclError:
        # Application is being destroyed
        return None
    
    # Check if the widget's owner is closing
    if hasattr(widget, 'master') and hasattr(widget.master, 'is_closing') and widget.master.is_closing:
        return None
        
    # Create a wrapper that checks if widget still exists before executing callback
    def safe_callback():
        try:
            if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                try:
                    callback()
                except Exception as e:
                    print(f"Error in after callback: {e}")
        except _tkinter.TclError:
            # Application is being destroyed, ignore
            pass
    
    # Schedule the callback
    try:
        return widget.after(delay, safe_callback)
    except _tkinter.TclError:
        # Application is being destroyed
        return None
    except Exception as e:
        print(f"Error scheduling after callback: {e}")
        return None

def cancel_after_safely(widget, after_id):
    """Cancel an after callback safely
    
    Args:
        widget: Tkinter widget to cancel after on
        after_id: ID returned from after()
        
    Returns:
        bool: True if canceled successfully, False otherwise
    """
    if after_id is None:
        return False
    
    try:
        if hasattr(widget, 'after_cancel') and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
            widget.after_cancel(after_id)
            return True
    except Exception:
        pass
    
    return False

def safe_widget_update(widget, **kwargs):
    """Safely update a widget's properties with existence check
    
    Args:
        widget: Tkinter widget to update
        **kwargs: Configuration properties to set
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        # Check if the application is closing
        if hasattr(widget, 'master') and hasattr(widget.master, 'is_closing') and widget.master.is_closing:
            return False
            
        if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
            widget.configure(**kwargs)
            return True
        return False
    except _tkinter.TclError:
        # Application is being destroyed
        return False
    except Exception as e:
        print(f"Error updating widget: {e}")
        return False

def safe_widget_method(widget, method_name, *args, **kwargs):
    """Safely call a method on a widget with existence check
    
    Args:
        widget: Tkinter widget to call method on
        method_name: Name of method to call
        *args, **kwargs: Arguments to pass to method
        
    Returns:
        Result of method call or None if widget doesn't exist
    """
    try:
        if hasattr(widget, 'winfo_exists') and widget.winfo_exists() and hasattr(widget, method_name):
            method = getattr(widget, method_name)
            return method(*args, **kwargs)
        return None
    except Exception as e:
        print(f"Error calling method {method_name} on widget: {e}")
        return None

def ensure_ui_thread(root, callback, *args, **kwargs):
    """Ensure a callback runs on the UI thread
    
    Args:
        root: Tkinter root window
        callback: Function to call
        *args, **kwargs: Arguments to pass to callback
        
    Returns:
        after_id: ID from after() call or None if failed
    """
    try:
        if hasattr(root, 'winfo_exists') and root.winfo_exists():
            return root.after(0, lambda: callback(*args, **kwargs))
        return None
    except Exception as e:
        print(f"Error scheduling callback on UI thread: {e}")
        return None

def find_ui_root(obj):
    """Find a UI root object in an instance
    
    Args:
        obj: Object to search for UI root
        
    Returns:
        UI root object or None if not found
    """
    # Common UI object names
    for attr_name in ['window', 'root', 'master', 'app', 'frame', 'parent', 'tk', 'top']:
        if hasattr(obj, attr_name):
            ui_obj = getattr(obj, attr_name)
            if hasattr(ui_obj, 'after') and hasattr(ui_obj, 'winfo_exists'):
                if ui_obj.winfo_exists():
                    return ui_obj
    
    # Also try checking if the object itself is a UI object
    if hasattr(obj, 'after') and hasattr(obj, 'winfo_exists') and obj.winfo_exists():
        return obj
        
    return None

def cleanup_after_commands():
    """Clean up invalid Tkinter after commands
    
    This helps prevent "invalid command name" errors that can occur
    when the application is shutting down or switching between windows.
    """
    try:
        # Get the root Tk instance
        from tkinter import _default_root
        if _default_root:
            # Get all after commands
            after_ids = _default_root.tk.call('after', 'info')
            
            # Convert to Python list
            if isinstance(after_ids, str):
                after_ids = after_ids.split()
            
            # Cancel all after commands
            for after_id in after_ids:
                try:
                    _default_root.after_cancel(after_id)
                except Exception:
                    # If can't cancel, just continue
                    pass
    except Exception as e:
        print(f"Error cleaning up after commands: {e}")

def ensure_ctk_images(images):
    """Ensure all images in a collection are CTkImages
    
    Args:
        images: List, tuple or dictionary of images
        
    Returns:
        Same collection with all PIL images converted to CTkImage
    """
    try:
        if isinstance(images, list):
            return [_ensure_single_ctk_image(img) for img in images]
        elif isinstance(images, tuple):
            return tuple(_ensure_single_ctk_image(img) for img in images)
        elif isinstance(images, dict):
            return {k: _ensure_single_ctk_image(v) for k, v in images.items()}
        else:
            return _ensure_single_ctk_image(images)
    except Exception as e:
        print(f"Error ensuring CTkImages: {e}")
        return images
        
def _ensure_single_ctk_image(image):
    """Convert a single image to CTkImage if needed
    
    Args:
        image: Image object
        
    Returns:
        CTkImage if conversion needed and possible, otherwise original image
    """
    if image is None:
        return None
        
    # If it's already a CTkImage, return as is
    if isinstance(image, ctk.CTkImage):
        return image
        
    # If it's a PIL.ImageTk.PhotoImage, convert from the original PIL image if possible
    if isinstance(image, ImageTk.PhotoImage):
        if hasattr(image, 'pil_image'):
            return convert_to_ctk_image(image.pil_image)
        # Can't recover original PIL image, return as is
        return image
        
    # If it's a PIL.Image, convert it
    if hasattr(image, 'mode'):  # Simple check for PIL.Image
        return convert_to_ctk_image(image)
        
    # Can't convert, return as is
    return image
