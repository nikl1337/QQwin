import pytest
import os
from unittest.mock import patch, MagicMock
# Adjust import path based on your project structure
from app.services.gif_generator import generate_nft_gif
from PIL import Image # Needed for creating dummy image objects if not mocking them completely

# Dummy paths for testing
DUMMY_UPLOADS_FOLDER = "/tmp/dummy_uploads_for_gif_test"
DUMMY_STATIC_GIFS_FOLDER = "/tmp/dummy_static_gifs_for_gif_test"
DUMMY_UPLOADED_IMAGE_ID = "test_image_123.png"
DUMMY_IMAGE_PATH = os.path.join(DUMMY_UPLOADS_FOLDER, DUMMY_UPLOADED_IMAGE_ID)

@pytest.fixture(autouse=True)
def setup_dummy_folders_and_files():
    os.makedirs(DUMMY_UPLOADS_FOLDER, exist_ok=True)
    os.makedirs(DUMMY_STATIC_GIFS_FOLDER, exist_ok=True)
    
    # Create a dummy image file that Image.open can read
    try:
        img = Image.new('RGB', (60, 30), color = 'red')
        img.save(DUMMY_IMAGE_PATH)
    except Exception as e:
        pytest.skip(f"Skipping GIF generator tests as Pillow/Image creation failed: {e}")

    yield

    # Teardown: Remove dummy files and folders
    if os.path.exists(DUMMY_IMAGE_PATH):
        os.remove(DUMMY_IMAGE_PATH)
    if os.path.exists(DUMMY_UPLOADS_FOLDER):
        os.rmdir(DUMMY_UPLOADS_FOLDER) # rmdir fails if not empty, ensure cleanup inside tests or use shutil
    if os.path.exists(DUMMY_STATIC_GIFS_FOLDER):
        # Clean up any GIFs created if tests write them
        for f in os.listdir(DUMMY_STATIC_GIFS_FOLDER):
            os.remove(os.path.join(DUMMY_STATIC_GIFS_FOLDER, f))
        os.rmdir(DUMMY_STATIC_GIFS_FOLDER)


# Mock all external dependencies of gif_generator
@patch('app.services.gif_generator.transform_elements')
@patch('app.services.gif_generator.apply_quantum_transformation')
@patch('app.services.gif_generator.generate_quantum_surroundings')
@patch('app.services.gif_generator.apply_fibonacci_animation')
@patch('app.services.gif_generator.get_btc_usdc_price')
@patch('app.services.gif_generator.get_sol_usdc_price')
@patch('app.services.gif_generator.Image.Image.save') # Mock the save method of PIL Image instances
@patch('app.services.gif_generator.Image.open') # Mock Image.open
def test_generate_nft_gif_successful_orchestration(
    mock_image_open,
    mock_image_save,
    mock_get_sol_price,
    mock_get_btc_price,
    mock_apply_fibonacci,
    mock_gen_surroundings,
    mock_apply_quantum_trans,
    mock_transform_elements
):
    # --- Setup Mocks ---
    # Mock Image.open to return a mock PIL Image object
    mock_pil_image = MagicMock(spec=Image.Image)
    mock_pil_image.size = (100, 100)
    mock_pil_image.convert.return_value = mock_pil_image # Ensure convert returns the mock itself or another mock
    mock_pil_image.copy.return_value = mock_pil_image
    mock_pil_image.format = 'PNG' # Original format
    mock_image_open.return_value = mock_pil_image

    # Mock transform_elements to return the image (or a mock)
    mock_transform_elements.return_value = mock_pil_image

    # Mock apply_quantum_transformation to return a list of mock PIL Image frames
    mock_frame = MagicMock(spec=Image.Image)
    mock_frame.convert.return_value = mock_frame # For .convert("RGBA") and .convert("RGB")
    mock_frame.copy.return_value = mock_frame
    mock_frame.size = (100, 100) # Ensure frames have a size for text overlay logic
    mock_base_frames = [mock_frame] * 5 # 5 dummy frames
    mock_apply_quantum_trans.return_value = mock_base_frames
    
    # Mock generate_quantum_surroundings
    mock_surroundings_img = MagicMock(spec=Image.Image)
    mock_gen_surroundings.return_value = mock_surroundings_img

    # Mock apply_fibonacci_animation to return a list of mock PIL Image frames
    mock_animated_frames = [mock_frame] * 5
    mock_apply_fibonacci.return_value = mock_animated_frames

    # Mock price fetchers
    mock_get_btc_price.return_value = 50000.00
    mock_get_sol_price.return_value = 150.00

    # --- Call the function ---
    result = generate_nft_gif(
        DUMMY_UPLOADED_IMAGE_ID, 
        DUMMY_UPLOADS_FOLDER, 
        DUMMY_STATIC_GIFS_FOLDER
    )

    # --- Assertions ---
    assert result['status'] == 'success'
    assert 'gif_path' in result
    assert 'relative_gif_path' in result
    assert result['gif_path'].startswith(DUMMY_STATIC_GIFS_FOLDER)
    assert result['relative_gif_path'].startswith('generated_gifs/')

    # Check if dependencies were called
    mock_image_open.assert_called_once() # Called once for the original image, and once for temp saved file by quantum_effects
                                        # The patch for Image.open might need to be more specific or the test adjusted
                                        # For now, let's check it was called with the original path
    mock_image_open.assert_any_call(DUMMY_IMAGE_PATH)


    mock_transform_elements.assert_called_once()
    mock_apply_quantum_trans.assert_called_once() # Called with a temp path
    mock_gen_surroundings.assert_called_once()
    mock_apply_fibonacci.assert_called_once()
    mock_get_btc_price.assert_called_once()
    mock_get_sol_price.assert_called_once()

    # Check if the final GIF save was attempted
    # The first frame's save method is called with save_all=True
    # mock_animated_frames[0].save.assert_called_once() - This is tricky because save is on the instance.
    # Instead, we patched Image.Image.save, which is the underlying PIL method.
    # This mock_image_save will capture all calls to .save() on any PIL Image object.
    # We expect it to be called for the temporary image in quantum_effects, and for the final GIF.
    assert mock_image_save.call_count >= 1 # At least for the final GIF
    
    # More specific check on the final GIF save
    final_gif_save_args = mock_image_save.call_args_list[-1] # Get the last call to .save()
    args, kwargs = final_gif_save_args
    assert args[0].startswith(DUMMY_STATIC_GIFS_FOLDER) # Path starts correctly
    assert kwargs.get('save_all') == True
    assert kwargs.get('duration') == 100
    assert kwargs.get('loop') == 0
    assert len(kwargs.get('append_images')) == len(mock_animated_frames) - 1


def test_generate_nft_gif_image_not_found():
    result = generate_nft_gif(
        "non_existent_image.png", 
        DUMMY_UPLOADS_FOLDER, 
        DUMMY_STATIC_GIFS_FOLDER
    )
    assert result['status'] == 'error'
    assert "Source image not found" in result['message'] or "Uploaded image not found" in result['message']


@patch('app.services.gif_generator.apply_quantum_transformation', return_value=[]) # Simulate failure in an early step
def test_generate_nft_gif_early_step_failure(mock_apply_quantum_trans_failure):
    # Need Image.open to work for this test to reach the patched step
    with patch('app.services.gif_generator.Image.open', MagicMock(return_value=MagicMock(spec=Image.Image, size=(10,10), copy=MagicMock(), format='PNG'))):
        with patch('app.services.gif_generator.transform_elements', MagicMock(return_value=MagicMock(spec=Image.Image, save=MagicMock()))): # transform_elements needs to return an image with save
            result = generate_nft_gif(
                DUMMY_UPLOADED_IMAGE_ID,
                DUMMY_UPLOADS_FOLDER,
                DUMMY_STATIC_GIFS_FOLDER
            )
    assert result['status'] == 'error'
    assert 'Failed to apply quantum transformation' in result['message']

# Add more tests for other failure points if necessary, e.g.,
# - Failure in apply_fibonacci_animation
# - Exception during file saving (though covered by the main orchestration test's mock_image_save if side_effect is used)
# - Price fetchers returning None (current code handles this by putting "N/A", so it's not an error state for gif_generator)
