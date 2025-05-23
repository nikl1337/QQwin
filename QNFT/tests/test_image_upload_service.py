import pytest
import os
import uuid
from unittest.mock import MagicMock, patch
# Adjust import path based on your project structure
from app.services.image_upload_service import allowed_file, handle_image_upload

# Define allowed extensions for testing, matching what's in main.py or service
TEST_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
TEST_MAX_SIZE_BYTES = 5 * 1024 * 1024 # 5MB, should match app config

@pytest.mark.parametrize("filename, expected", [
    ("test_image.jpg", True),
    ("document.pdf", False),
    ("image.PNG", True),
    ("image.jpeg", True),
    ("archive.zip", False),
    ("no_extension", False),
    (".hiddenfile", False), # No actual extension part
])
def test_allowed_file(filename, expected):
    assert allowed_file(filename, TEST_ALLOWED_EXTENSIONS) == expected

def test_handle_image_upload_no_file_object():
    result = handle_image_upload(None, "/tmp/uploads", TEST_ALLOWED_EXTENSIONS, TEST_MAX_SIZE_BYTES)
    assert result['status'] == 'error'
    assert result['message'] == 'No file provided.'

def test_handle_image_upload_empty_filename():
    mock_file = MagicMock()
    mock_file.filename = ""
    result = handle_image_upload(mock_file, "/tmp/uploads", TEST_ALLOWED_EXTENSIONS, TEST_MAX_SIZE_BYTES)
    assert result['status'] == 'error'
    assert result['message'] == 'No file selected.'

def test_handle_image_upload_disallowed_extension():
    mock_file = MagicMock()
    mock_file.filename = "test.gif"
    result = handle_image_upload(mock_file, "/tmp/uploads", TEST_ALLOWED_EXTENSIONS, TEST_MAX_SIZE_BYTES)
    assert result['status'] == 'error'
    assert "File type not allowed" in result['message']

@patch('app.services.image_upload_service.os.makedirs')
@patch('app.services.image_upload_service.uuid.uuid4')
def test_handle_image_upload_success(mock_uuid, mock_makedirs):
    # Mocking external dependencies
    mock_uuid.return_value = MagicMock(hex='test_uuid_123')
    
    mock_file = MagicMock()
    mock_file.filename = "my_photo.jpg"
    # The save method is called on the file object itself
    mock_file.save = MagicMock()

    upload_folder = "/tmp/test_uploads"
    
    result = handle_image_upload(mock_file, upload_folder, TEST_ALLOWED_EXTENSIONS, TEST_MAX_SIZE_BYTES)
    
    mock_makedirs.assert_called_once_with(upload_folder, exist_ok=True)
    
    expected_filename_stem = "test_uuid_123_my_photo" 
    expected_filename = f"{expected_filename_stem}.jpg"
    expected_save_path = os.path.join(upload_folder, expected_filename)
    
    mock_file.save.assert_called_once_with(expected_save_path)
    
    assert result['status'] == 'success'
    assert result['file_id'] == expected_filename
    assert result['path'] == expected_save_path

@patch('app.services.image_upload_service.os.makedirs')
@patch('app.services.image_upload_service.uuid.uuid4')
def test_handle_image_upload_save_exception(mock_uuid, mock_makedirs):
    mock_uuid.return_value = MagicMock(hex='test_uuid_fail')
    
    mock_file = MagicMock()
    mock_file.filename = "another.png"
    mock_file.save = MagicMock(side_effect=IOError("Disk full")) # Simulate a save error

    upload_folder = "/tmp/test_uploads_fail"
    
    result = handle_image_upload(mock_file, upload_folder, TEST_ALLOWED_EXTENSIONS, TEST_MAX_SIZE_BYTES)
    
    mock_makedirs.assert_called_once_with(upload_folder, exist_ok=True)
    
    assert result['status'] == 'error'
    assert result['message'] == 'Failed to save file due to an internal error.'

# Note: MAX_CONTENT_LENGTH is primarily enforced by Flask.
# If the service itself had a secondary check based on file_storage_object.seek/tell,
# that could be tested here by mocking those methods on the file object.
# The current service implementation comments out direct size check, relying on Flask.
# Thus, testing that aspect here is less relevant for the current service code.
# e.g. test_handle_image_upload_file_too_large
# mock_file.seek = MagicMock()
# mock_file.tell = MagicMock(return_value=TEST_MAX_SIZE_BYTES + 100)
# result = handle_image_upload(...)
# assert result['status'] == 'error' and "exceeds maximum size" in result['message']
