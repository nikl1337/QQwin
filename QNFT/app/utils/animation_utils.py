from PIL import Image, ImageOps
import math

def get_fibonacci_sequence(n_terms):
    """Returns a list of Fibonacci numbers up to n_terms."""
    if n_terms <= 0:
        return []
    elif n_terms == 1:
        return [0]
    sequence = [0, 1]
    while len(sequence) < n_terms:
        next_val = sequence[-1] + sequence[-2]
        sequence.append(next_val)
    return sequence[:n_terms] # Ensure correct length if n_terms is small

def apply_fibonacci_animation(frames, original_image):
    """
    Applies a simple animation effect based on Fibonacci sequence values.
    Example: Slight zoom in/out based on Fibonacci numbers.
    The effect is subtle and applied to the whole frame.
    """
    if not frames:
        return []

    num_frames = len(frames)
    fib_sequence = get_fibonacci_sequence(num_frames)
    
    # Normalize Fibonacci sequence to get scaling factors (e.g., between 0.95 and 1.05)
    # We want the effect to be subtle.
    if not fib_sequence: # Handle empty fib_sequence if num_frames is 0
        return frames

    min_fib = min(fib_sequence) if fib_sequence else 0
    max_fib = max(fib_sequence) if fib_sequence else 1
    
    # Avoid division by zero if all fib numbers are the same (e.g. only one frame)
    fib_range = max_fib - min_fib if max_fib - min_fib != 0 else 1 

    # Scale factors will oscillate around 1.0
    # e.g., 1.0 +/- 0.05 (for a 5% zoom variation)
    # We use a sine wave modulated by normalized fibonacci for smoother oscillation
    scale_variation = 0.03 # Max 3% zoom in/out

    animated_frames = []
    width, height = frames[0].size

    for i, frame in enumerate(frames):
        # Use normalized fib value to influence the scale
        # The fib_sequence might not be ideal for direct scaling as it grows fast
        # Instead, use it to modulate a cyclical effect like sine wave.
        
        # Create a cyclical progression (0 to 1 and back) using sine
        # This makes the zoom smooth in and out
        cycle_progress = math.sin((i / float(num_frames)) * math.pi) # Half sine wave for one zoom in/out cycle

        # Modulate the scale_variation by the fibonacci sequence if desired,
        # or just use cycle_progress for a simple oscillation.
        # For simplicity, let's use cycle_progress for zoom intensity.
        # A large fib number could make a more pronounced effect for that frame.
        # current_fib_normalized = (fib_sequence[i] - min_fib) / fib_range if fib_range !=0 else 0
        
        current_scale = 1.0 + scale_variation * cycle_progress

        new_width = int(width * current_scale)
        new_height = int(height * current_scale)

        # Resize (zoom)
        scaled_frame = frame.resize((new_width, new_height), Image.LANCZOS)

        # Crop back to original size (centered)
        x_offset = (new_width - width) // 2
        y_offset = (new_height - height) // 2
        
        final_frame = scaled_frame.crop((x_offset, y_offset, x_offset + width, y_offset + height))
        animated_frames.append(final_frame)
        
    return animated_frames

if __name__ == '__main__':
    # Example Usage
    print("Fibonacci sequence for 10 terms:", get_fibonacci_sequence(10))
    
    # Test animation (requires Pillow and a dummy image)
    try:
        os.makedirs("test_output", exist_ok=True)
        dummy_frames = []
        for i in range(10):
            # Create slightly different frames for visual distinction if saved
            img = Image.new("RGB", (200, 150), (i*20, 100, 150-i*10))
            draw = ImageDraw.Draw(img)
            draw.text((10,10), f"Frame {i}", fill=(255,255,255))
            dummy_frames.append(img)
        
        original_dummy = Image.new("RGB", (200, 150), "green")
        
        animated_frames = apply_fibonacci_animation(list(dummy_frames), original_dummy) # Pass a copy
        
        if animated_frames:
            for i, frame in enumerate(animated_frames):
                frame.save(f"test_output/animated_fib_frame_{i}.png")
            print(f"Saved {len(animated_frames)} animated frames to test_output.")
        else:
            print("No frames were animated.")

    except ImportError:
        print("Pillow is not installed. This module requires Pillow for testing animation.")
    except NameError: # os or ImageDraw not defined if Pillow not there
        pass
    except Exception as e:
        print(f"An error occurred during animation test: {e}")
