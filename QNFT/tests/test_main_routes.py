import pytest
import os
import io
from unittest.mock import patch, MagicMock
# client fixture is from test_config.py

# Ensure app context is available for url_for if not using pytest-flask's live server
# For client.get/post, it's usually handled.

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Upload Your Image" in response.data # Check for some content from index.html

def test_marketplace_page(client):
    response = client.get('/marketplace')
    assert response.status_code == 200
    assert b"QNFT Marketplace" in response.data

def test_chart_page(client):
    response = client.get('/chart')
    assert response.status_code == 200
    assert b"SOL/USDC Price Chart" in response.data

def test_upload_image_no_file(client):
    response = client.post('/upload_image')
    assert response.status_code == 400 # Bad Request if 'file' part is missing
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert 'No file part' in json_data['message']

def test_upload_image_empty_filename(client):
    data = {'file': (io.BytesIO(b"dummy content"), '')} # Empty filename
    response = client.post('/upload_image', content_type='multipart/form-data', data=data)
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert 'No selected file' in json_data['message']

def test_upload_image_disallowed_extension(client):
    data = {'file': (io.BytesIO(b"dummy pdf content"), 'test.pdf')}
    response = client.post('/upload_image', content_type='multipart/form-data', data=data)
    # Assuming ALLOWED_EXTENSIONS in main.py is {'png', 'jpg', 'jpeg'}
    assert response.status_code == 415 # Unsupported Media Type
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert 'File type not allowed' in json_data['message']

@patch('app.main.handle_image_upload') # Mock the service called by the route
def test_upload_image_success(mock_handle_upload, client):
    mock_handle_upload.return_value = {
        'status': 'success', 
        'file_id': 'mock_file_id.png', 
        'path': '/tmp/mock_file_id.png'
    }
    
    data = {'file': (io.BytesIO(b"fake image data"), 'test_image.png')}
    response = client.post('/upload_image', content_type='multipart/form-data', data=data)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['file_id'] == 'mock_file_id.png'
    mock_handle_upload.assert_called_once()


@patch('app.main.generate_nft_gif') # Mock the service
def test_generate_gif_route_success(mock_generate_service, client):
    image_id = "test_image_123.png"
    mock_generate_service.return_value = {
        'status': 'success',
        'gif_path': f'/tmp/static/generated_gifs/final_{image_id}.gif',
        'relative_gif_path': f'generated_gifs/final_{image_id}.gif'
    }
    response = client.get(f'/generate_gif/{image_id}')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['gif_url'].endswith(f'generated_gifs/final_{image_id}.gif')
    mock_generate_service.assert_called_once_with(
        uploaded_image_id=image_id,
        uploads_folder=client.application.config['UPLOAD_FOLDER'], # Check if service is called with correct config
        static_folder_gifs=client.application.config['STATIC_FOLDER_GIFS'] # Accessing via client.application
    )

@patch('app.main.generate_nft_gif')
def test_generate_gif_route_service_error(mock_generate_service, client):
    image_id = "error_image_id.png"
    mock_generate_service.return_value = {'status': 'error', 'message': 'Service failed'}
    response = client.get(f'/generate_gif/{image_id}')
    assert response.status_code == 500 # Assuming internal server error for general service failures
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert json_data['message'] == 'Service failed'

def test_generate_gif_route_invalid_image_id(client):
    # Test with an image_id that might represent a directory traversal attempt
    response = client.get('/generate_gif/../../etc/passwd')
    assert response.status_code == 400 # Bad Request due to invalid format
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert 'Invalid image ID format' in json_data['message']


@patch('app.main.mint_qnft_service')
@patch('app.main.os.path.exists') # To mock file existence checks
def test_mint_nft_route_success(mock_path_exists, mock_mint_service, client):
    mock_path_exists.return_value = True # Assume GIF and original image exist
    mock_mint_service.return_value = {
        'status': 'success', 
        'transaction_id': 'sim_tx_123',
        'metadata_uri': 'uri_to_meta.json',
        'raw_metadata': {'name': 'Test QNFT', 'animation_url': 'url_to_gif', 'attributes': [{'trait_type': 'Timestamp', 'value':'some_timestamp'}], 'properties': {'files': [{}, {'uri': 'orig_img_url'}]}}
    }
    
    payload = {
        'image_id': 'some_image.png',
        'gif_server_path': os.path.join(client.application.config['STATIC_FOLDER_GIFS'], 'dummy.gif'), # Needs to be a valid-looking path within STATIC_FOLDER_GIFS
        'mint_type': 'long',
        'user_description': 'A test NFT'
    }
    response = client.post('/mint_nft', json=payload)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['transaction_id'] == 'sim_tx_123'
    mock_mint_service.assert_called_once()
    # Check if add_minted_nft_to_market was called (indirectly, by checking its effect)
    # This requires a bit more setup or a way to inspect market_service._minted_nfts
    # For now, we trust the route calls the service, and service calls add_minted_nft_to_market

@patch('app.main.mint_qnft_service')
def test_mint_nft_route_missing_data(mock_mint_service, client):
    payload = {'image_id': 'some_image.png'} # Missing other fields
    response = client.post('/mint_nft', json=payload)
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert 'Missing' in json_data['message']
    mock_mint_service.assert_not_called()

@patch('app.main.os.path.exists')
def test_mint_nft_route_gif_not_found(mock_path_exists, client):
    # First call to exists (for GIF) returns False, second (for original image) can be True
    mock_path_exists.side_effect = [False, True] 
    payload = {
        'image_id': 'some_image.png',
        'gif_server_path': '/tmp/non_existent.gif',
        'mint_type': 'short'
    }
    response = client.post('/mint_nft', json=payload)
    assert response.status_code == 404 # Not Found
    json_data = response.get_json()
    assert 'GIF not found' in json_data['message']


def test_get_marketplace_nfts_route(client):
    # This route calls market_service.get_marketplace_nfts()
    # The market_service populates with dummy data on import.
    response = client.get('/marketplace/nfts')
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    if json_data: # If dummy data was populated
        assert 'name' in json_data[0]
        assert 'gif_url' in json_data[0]

def test_get_price_chart_data_route(client):
    response = client.get('/chart/price_data?time_range_hours=24')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'price_history' in json_data
    assert 'nft_events' in json_data
    assert isinstance(json_data['price_history'], list)
    assert isinstance(json_data['nft_events'], list)

def test_get_price_chart_data_route_invalid_range(client):
    response = client.get('/chart/price_data?time_range_hours=abc')
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'Invalid time_range_hours format' in json_data['message']

    response = client.get('/chart/price_data?time_range_hours=0')
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'time_range_hours must be positive' in json_data['message']
