import os
from PIL import Image, ImageDraw, ImageFont # Pillow for image manipulation, ImageFont added
import datetime # Added for timestamp
# Assuming utils are in the python path or PYTHONPATH is set up correctly for app.
from app.utils.quantum_effects import apply_quantum_transformation, generate_quantum_surroundings, transform_elements
from app.utils.animation_utils import apply_fibonacci_animation
from app.services.price_fetcher import get_btc_usdc_price, get_sol_usdc_price # Added price fetcher

def generate_nft_gif(uploaded_image_id, uploads_folder, static_folder_gifs):
    """
    Generates a GIF with quantum effects and Fibonacci animation.
    Args:
        uploaded_image_id: Filename of the uploaded image (e.g., "uuid_original.png").
        uploads_folder: Path to the directory where uploaded images are stored.
        static_folder_gifs: Path to the directory where generated GIFs will be saved.
    Returns:
        A dictionary with status and gif_path (on success) or error message.
    """
    image_path = os.path.join(uploads_folder, uploaded_image_id)

    if not os.path.exists(image_path):
        return {'status': 'error', 'message': f'Uploaded image not found: {uploaded_image_id}'}

    try:
        # 1. Load the original image
        original_image = Image.open(image_path).convert("RGBA") # Use RGBA for compositing

        # 2. Apply advanced transformation (placeholder)
        transformed_image = transform_elements(original_image.copy()) # Pass a copy

        # 3. Apply quantum visual transformation (returns list of PIL.Image frames)
        # Let's use the transformed_image path if it was modified and saved,
        # or pass the PIL image object directly if quantum_effects supports it.
        # For now, assume apply_quantum_transformation can take a PIL image.
        # If it strictly needs a path, we'd save transformed_image first.
        # Let's refine apply_quantum_transformation to accept an Image object.
        # For now, we will save transformed_image to a temp path if needed, or adapt.
        # Re-saving and re-loading is inefficient. Let's assume it can take an image obj.
        # (If not, this will need adjustment in quantum_effects.py or here)
        
        # For simplicity, let's assume apply_quantum_transformation is adapted
        # to take an image object. If it still needs a path, we'd do:
        # temp_transformed_path = os.path.join(uploads_folder, "temp_" + uploaded_image_id)
        # transformed_image.save(temp_transformed_path)
        # base_frames = apply_quantum_transformation(temp_transformed_path, num_frames=25) # Target 25 frames for ~5s @ 200ms/frame or 50 frames @ 100ms/frame
        # os.remove(temp_transformed_path)
        
        # Let's assume apply_quantum_transformation is modified to take an Image object
        # and num_frames. If not, this part needs to match its actual signature.
        # For the subtask, `apply_quantum_transformation` takes `image_path`.
        # So, we save the `transformed_image` (which is just a copy for now)
        # to a temporary path to pass to `apply_quantum_transformation`.
        
        temp_base_image_for_quantum_effect = os.path.join(uploads_folder, f"temp_q_{uploaded_image_id}")
        transformed_image.save(temp_base_image_for_quantum_effect, format=original_image.format or 'PNG')

        base_frames = apply_quantum_transformation(temp_base_image_for_quantum_effect, num_frames=50) # 50 frames for 5s @ 100ms/frame
        
        os.remove(temp_base_image_for_quantum_effect) # Clean up temp file

        if not base_frames:
            return {'status': 'error', 'message': 'Failed to apply quantum transformation.'}

        # 4. Generate quantum surroundings and composite them
        # Ensure all frames are RGBA for consistency if surroundings have alpha
        processed_frames = []
        surroundings = generate_quantum_surroundings(original_image.size, effect_intensity=0.6) # RGBA
        
        for frame_pil in base_frames:
            frame_rgba = frame_pil.convert("RGBA")
            # Composite surroundings. Surroundings can be a background or an overlay.
            # If background: create new image, paste surroundings, then paste frame.
            # If overlay: paste frame, then paste surroundings on top.
            # Let's try as an overlay first.
            combined_frame = Image.alpha_composite(Image.new("RGBA", frame_rgba.size, (0,0,0,0)), frame_rgba) # ensure base is clean for alpha_composite
            combined_frame = Image.alpha_composite(combined_frame, surroundings)
            processed_frames.append(combined_frame.convert("RGB")) # Convert to RGB for GIF if no transparency needed in final GIF
                                                                    # Or keep RGBA if transparency is desired & handled by GIF saver

        # 5. Apply Fibonacci animation
        # The Fibonacci animation function might expect RGBA if it manipulates transparency
        # or RGB if it only does geometric transforms. Let's assume it can handle RGB.
        animated_frames = apply_fibonacci_animation(list(processed_frames), original_image) # Pass a copy of list

        if not animated_frames:
            return {'status': 'error', 'message': 'Failed to apply Fibonacci animation.'}

        # 6. Save as GIF
        os.makedirs(static_folder_gifs, exist_ok=True)
        gif_filename = f"final_{uploaded_image_id.split('.')[0]}.gif"
        gif_path = os.path.join(static_folder_gifs, gif_filename)

        # Duration: target 5 seconds. If 50 frames, duration is 100ms per frame.
        # PIL save duration is in milliseconds.

        # --- Add Price and Timestamp Overlay ---
        btc_price = get_btc_usdc_price()
        sol_price = get_sol_usdc_price()
        timestamp_obj = datetime.datetime.now(datetime.timezone.utc) # Use timezone aware UTC
        timestamp_str = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S UTC")

        btc_text = f"BTC/USDC: {btc_price:.2f}" if btc_price is not None else "BTC/USDC: N/A"
        sol_text = f"SOL/USDC: {sol_price:.2f}" if sol_price is not None else "SOL/USDC: N/A"

        try:
            # font = ImageFont.truetype("arial.ttf", 15) # Example, might not be available
            font = ImageFont.load_default() 
        except IOError:
            font = ImageFont.load_default() # Fallback just in case

        final_frames_with_text = []
        if not animated_frames: # Should not happen if previous steps succeeded
             return {'status': 'error', 'message': 'No frames to apply text overlay.'}

        # Determine text color based on average background for better visibility (simple version)
        # For now, hardcode white text with black stroke, good for most backgrounds.
        text_fill_color = "white"
        stroke_fill_color = "black"
        
        # Get frame dimensions from the first animated frame
        frame_width, frame_height = animated_frames[0].size
        
        for frame_pil_obj in animated_frames: # animated_frames should be a list of PIL Image objects
            # Ensure frame is mutable (e.g. if it was an optimized GIF frame)
            current_frame_editable = frame_pil_obj.copy() if hasattr(frame_pil_obj, 'readonly') and frame_pil_obj.readonly else frame_pil_obj
            draw = ImageDraw.Draw(current_frame_editable)
            
            # Define positions for text (adjust as needed)
            # Positioning from bottom up to avoid overlapping with potential top elements
            # And add some padding from the edge
            padding = 5
            text_x_position = padding
            line_height = 10 # Default font is small, approx 10px height. Add 2px for spacing.
            
            # Calculate text sizes to potentially adjust positions or wrap (advanced)
            # For now, assume short strings and fixed positions.
            # timestamp_text_size = draw.textbbox((0,0), timestamp_str, font=font) # (left, top, right, bottom)
            # sol_text_size = draw.textbbox((0,0), sol_text, font=font)
            # btc_text_size = draw.textbbox((0,0), btc_text, font=font)
            
            # Position from bottom of the image
            pos_timestamp_y = frame_height - padding - line_height
            pos_sol_y = frame_height - padding - (2 * line_height) - (padding // 2) 
            pos_btc_y = frame_height - padding - (3 * line_height) - padding

            draw.text((text_x_position, pos_btc_y), btc_text, font=font, fill=text_fill_color, stroke_width=1, stroke_fill=stroke_fill_color)
            draw.text((text_x_position, pos_sol_y), sol_text, font=font, fill=text_fill_color, stroke_width=1, stroke_fill=stroke_fill_color)
            draw.text((text_x_position, pos_timestamp_y), timestamp_str, font=font, fill=text_fill_color, stroke_width=1, stroke_fill=stroke_fill_color)
            
            final_frames_with_text.append(current_frame_editable)
        # --- End Overlay ---

        if not final_frames_with_text:
            return {'status': 'error', 'message': 'Text overlay resulted in no frames.'}
            
        final_frames_with_text[0].save(
            gif_path,
            save_all=True,
            append_images=final_frames_with_text[1:],
            duration=100,  # 100ms per frame for 50 frames = 5 seconds
            loop=0,        # Loop indefinitely
            optimize=False # Set to True for smaller files, but can be slower
        )
        
        return {'status': 'success', 'gif_path': gif_path, 'relative_gif_path': os.path.join('generated_gifs', gif_filename)}

    except FileNotFoundError: # Specifically for the original image_path
         return {'status': 'error', 'message': f'Source image not found: {image_path}'}
    except ImportError as ie:
        # Log the error in a real application
        print(f"ImportError in GIF generation: {ie}")
        return {'status': 'error', 'message': f'Failed to generate GIF due to a missing library: {str(ie)}'}
    except Exception as e:
        # Log the error in a real application: print(f"Error in GIF generation: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        return {'status': 'error', 'message': f'Failed to generate GIF due to an internal error: {str(e)}'}

if __name__ == '__main__':
    # Example Usage (requires a dummy image in a dummy uploads folder)
    # This is more complex to test directly here without setting up Flask context
    # or mocking the file system and dependencies.
    
    # Create dummy uploads and static folders for a self-contained test
    script_dir = os.path.dirname(__file__)
    dummy_uploads = os.path.join(script_dir, "..", "..", "tests", "dummy_uploads") # QNFT/tests/dummy_uploads
    dummy_static_gifs = os.path.join(script_dir, "..", "static", "generated_gifs") # QNFT/app/static/generated_gifs
    
    os.makedirs(dummy_uploads, exist_ok=True)
    os.makedirs(dummy_static_gifs, exist_ok=True)
    
    # Create a dummy image
    try:
        # Ensure Pillow is available for Image, ImageDraw
        from PIL import Image, ImageDraw

        dummy_image = Image.new("RGB", (300, 220), "teal") # Slightly larger for text
        draw = ImageDraw.Draw(dummy_image)
        draw.text((10,10), "Test NFT Image", fill=(255,255,0))
        dummy_image_id = "test_dummy_overlay_123.png"
        dummy_image_path = os.path.join(dummy_uploads, dummy_image_id)
        dummy_image.save(dummy_image_path)
        print(f"Dummy image saved to {dummy_image_path}")

        # Test GIF generation
        # Note: This direct call might fail if imports like `from app.utils...` don't resolve
        # without the app context or proper PYTHONPATH.
        # For this test to run, ensure QNFT/ is in PYTHONPATH or run as `python -m app.services.gif_generator`
        print("Attempting to generate GIF with text overlay...")
        # Make sure price_fetcher can run in this test environment (e.g. internet access)
        result = generate_nft_gif(dummy_image_id, dummy_uploads, dummy_static_gifs)
        
        if result['status'] == 'success':
            print(f"GIF generated successfully: {result['gif_path']}")
            print(f"Relative path: {result['relative_gif_path']}")
            print("Please manually inspect the GIF to confirm text overlay.")
        else:
            print(f"GIF generation failed: {result['message']}")
            
    except ImportError as ie:
        # This will catch if PIL itself is not available in the test execution context
        print(f"ImportError during test setup or execution: {ie}. Ensure QNFT project root is in PYTHONPATH if running this script directly.")
        print("Example: PYTHONPATH=/path/to/QNFT python QNFT/app/services/gif_generator.py")
    except Exception as e:
        print(f"An error occurred during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up dummy files/folders if needed, or leave for inspection
        # if os.path.exists(dummy_image_path):
        #     os.remove(dummy_image_path)
        pass
