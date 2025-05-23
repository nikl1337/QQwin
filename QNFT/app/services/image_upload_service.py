import os
import uuid
from werkzeug.utils import secure_filename

# ALLOWED_EXTENSIONS will be passed from the caller (e.g., Flask app)
# MAX_CONTENT_LENGTH will be checked by Flask app's MAX_CONTENT_LENGTH config

def allowed_file(filename, allowed_extensions):
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def handle_image_upload(file_storage_object, upload_folder, allowed_extensions, max_size_bytes):
    """
    Handles the image upload, validation, and saving.
    Args:
        file_storage_object: The file object from the request (e.g., request.files['file']).
        upload_folder: The folder where valid files will be saved.
        allowed_extensions: A set of allowed file extensions (e.g., {'png', 'jpg'}).
        max_size_bytes: Maximum allowed file size in bytes.
    Returns:
        A dictionary with status and filename (on success) or error message.
    """
    if not file_storage_object:
        return {'status': 'error', 'message': 'No file provided.'}

    if file_storage_object.filename == '':
        return {'status': 'error', 'message': 'No file selected.'}

    filename = secure_filename(file_storage_object.filename)

    if not allowed_file(filename, allowed_extensions):
        return {'status': 'error', 'message': f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"}

    # File size check is primarily handled by Flask's app.config['MAX_CONTENT_LENGTH']
    # However, a check here can be a secondary measure if the file object is already in memory.
    # For large files, it's better to rely on the web server/Flask's initial check.
    # If file_storage_object has a way to check size without reading fully into memory (e.g. content_length attribute from stream)
    # file_storage_object.seek(0, os.SEEK_END)
    # file_length = file_storage_object.tell()
    # file_storage_object.seek(0)
    # if file_length == 0:
    #    return {'status': 'error', 'message': 'File is empty.'}
    # if file_length > max_size_bytes:
    #    return {'status': 'error', 'message': f'File exceeds maximum size of {max_size_bytes // (1024*1024)}MB.'}


    unique_id = uuid.uuid4().hex
    # Keep original extension
    original_extension = filename.rsplit('.', 1)[1].lower()
    new_filename = f"{unique_id}_{filename.rsplit('.', 1)[0]}.{original_extension}"
    # To ensure the full original filename isn't too long or problematic,
    # it might be better to just use the UUID and the extension:
    # new_filename = f"{unique_id}.{original_extension}"


    save_path = os.path.join(upload_folder, new_filename)

    try:
        # Ensure the upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
        file_storage_object.save(save_path)
        return {'status': 'success', 'file_id': new_filename, 'path': save_path}
    except Exception as e:
        # In a real app, log this error
        print(f"Error saving file: {e}")
        return {'status': 'error', 'message': 'Failed to save file due to an internal error.'}
