import pytest
import tempfile
import os
# Adjust the import according to your project structure
# Assuming QNFT is the root package detectable by Python
from app.main import app as flask_app 

@pytest.fixture
def app_instance(): # Renamed from app to avoid conflict with pytest-flask's own 'app' fixture if used directly
    """Create and configure a new app instance for each test."""
    # Create a new app instance for each test to ensure isolation
    # If your flask_app is a global variable that gets modified, this approach is better.
    # However, the prompt implies flask_app is directly usable.
    # For simplicity and adherence to prompt, directly configuring the imported flask_app.
    
    # Create a temporary directory for UPLOAD_FOLDER and STATIC_FOLDER_GIFS for testing
    # This is good practice to avoid polluting the actual project folders.
    temp_upload_dir = tempfile.mkdtemp()
    temp_static_gifs_dir = os.path.join(tempfile.mkdtemp(), 'generated_gifs')
    os.makedirs(temp_static_gifs_dir, exist_ok=True)

    flask_app.config.update({
        "TESTING": True,
        "UPLOAD_FOLDER": temp_upload_dir,
        # Update other paths if your app uses them and they need to be temporary for tests
        # e.g., if STATIC_FOLDER_GIFS is derived from app.static_folder
        # For this example, let's assume STATIC_FOLDER_GIFS in main.py will be updated
        # or that the test client handles static file resolution correctly in testing mode.
        # The main.py already sets STATIC_FOLDER_GIFS based on app.static_folder,
        # so we just need to ensure app.static_folder is also test-friendly if used.
        # For now, let's assume the default 'static' folder resolution works or is handled by test client.
    })
    
    # This is a key part for making STATIC_FOLDER_GIFS in main.py use a temp dir during tests.
    # We need to modify where STATIC_FOLDER_GIFS points in the actual app module if it's
    # calculated at import time. If it's calculated dynamically per request, this might be different.
    # Given the current main.py structure, STATIC_FOLDER_GIFS is set at module level.
    # This is tricky. A better way is for main.py to have a function to create_app()
    # where config can be passed. For now, we'll try to patch it or rely on Flask's testing config.
    
    # Let's assume main.py's STATIC_FOLDER_GIFS needs to be overridden for tests.
    # This is a bit of a hack. Ideal solution is app factory pattern.
    from app import main as main_module
    main_module.STATIC_FOLDER_GIFS = temp_static_gifs_dir


    # If you have initialization logic that needs to run after config (e.g., db setup)
    # context = flask_app.app_context()
    # context.push()

    yield flask_app

    # context.pop()
    # Clean up temporary directories after tests if needed, though tempfile module often handles this.
    # For explicit cleanup:
    import shutil
    shutil.rmtree(temp_upload_dir)
    shutil.rmtree(os.path.dirname(temp_static_gifs_dir)) # remove parent of generated_gifs


@pytest.fixture
def client(app_instance): # Depends on the app_instance fixture
    """A test client for the app."""
    return app_instance.test_client()

# If you need a runner for CLI commands if you had any
# @pytest.fixture
# def runner(app_instance):
#     return app_instance.test_cli_runner()
