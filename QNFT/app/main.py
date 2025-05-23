import os
from flask import Flask, request, jsonify, send_from_directory, render_template # Added render_template
# Corrected import path assuming 'app' is the root for Python's import resolution
# when running from QNFT directory (e.g. python -m app.main)
# or if QNFT/app is in PYTHONPATH.
from .services.image_upload_service import handle_image_upload
from .services.gif_generator import generate_nft_gif
from .services.solana_service import mint_qnft as mint_qnft_service
from .services.market_service import get_marketplace_nfts, get_price_chart_data, add_minted_nft_to_market # Added market service and add_minted_nft_to_market

app = Flask(__name__)

# Configuration
APP_ROOT = os.path.dirname(os.path.abspath(__file__)) # QNFT/app
PROJECT_ROOT = os.path.dirname(APP_ROOT) # QNFT/

UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads') # QNFT/uploads/
# Define static folder for Flask if not default ('static')
# app.static_folder = os.path.join(APP_ROOT, 'static') # Default is 'static' relative to app root
STATIC_FOLDER_GIFS = os.path.join(app.static_folder, 'generated_gifs') # QNFT/app/static/generated_gifs

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure the upload folder and static GIF folder exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(STATIC_FOLDER_GIFS, exist_ok=True)

# --- HTML Serving Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/marketplace')
def marketplace_page():
    return render_template('marketplace.html')

@app.route('/chart')
def chart_page():
    return render_template('price_chart.html')

# --- API Endpoints ---
@app.route('/upload_image', methods=['POST'])
def upload_image_route():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in the request.'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file.'}), 400

    result = handle_image_upload(
        file_storage_object=file,
        upload_folder=app.config['UPLOAD_FOLDER'],
        allowed_extensions=ALLOWED_EXTENSIONS,
        max_size_bytes=app.config['MAX_CONTENT_LENGTH']
    )
    
    if result['status'] == 'success':
        # Include image_id for the next step (GIF generation)
        return jsonify({'status': 'success', 'file_id': result['file_id'], 'message': 'Image uploaded successfully. Ready for GIF generation.'}), 200
    else:
        if "File type not allowed" in result.get('message', ''):
            return jsonify(result), 415
        elif "No file provided" in result.get('message', '') or "No file selected" in result.get('message', ''):
            return jsonify(result), 400
        elif "exceeds maximum size" in result.get('message', ''):
            return jsonify(result), 413
        else:
            return jsonify(result), 500

@app.route('/generate_gif/<image_id>', methods=['GET'])
def generate_gif_route(image_id):
    if not image_id:
        return jsonify({'status': 'error', 'message': 'Image ID must be provided.'}), 400

    # Sanitize image_id to prevent directory traversal attacks if it's used directly in file paths
    # The image_id from upload_image_service is already processed by secure_filename and includes a UUID,
    # so it should be relatively safe. However, further validation here is good practice.
    # For example, ensure it matches an expected pattern or doesn't contain '..'
    if '..' in image_id or '/' in image_id:
        return jsonify({'status': 'error', 'message': 'Invalid image ID format.'}), 400

    gif_result = generate_nft_gif(
        uploaded_image_id=image_id,
        uploads_folder=app.config['UPLOAD_FOLDER'],
        static_folder_gifs=STATIC_FOLDER_GIFS # Pass the absolute path
    )

    if gif_result['status'] == 'success':
        # Construct a URL path for the GIF
        # gif_url = url_for('static', filename=os.path.join('generated_gifs', os.path.basename(gif_result['gif_path'])), _external=True)
        # Simpler relative path for client to construct full URL or for direct serving.
        # The `relative_gif_path` should be like 'generated_gifs/final_xyz.gif'
        return jsonify({
            'status': 'success',
            'message': 'GIF generated successfully.',
            'gif_url': f"/static/{gif_result['relative_gif_path']}", # This is a common way to serve static files
            'gif_server_path': gif_result['gif_path'] # For reference or other uses
        }), 200
    else:
        if 'not found' in gif_result.get('message', '').lower():
            return jsonify(gif_result), 404 # Not Found
        else:
            return jsonify(gif_result), 500 # Internal Server Error

@app.route('/mint_nft', methods=['POST'])
def mint_nft_route():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No JSON data provided.'}), 400

    image_id = data.get('image_id')
    # The gif_path provided by the client should be the server path returned by /generate_gif
    # Example: "QNFT/app/static/generated_gifs/final_some_uuid_original.gif"
    # Or, it could be just the filename, and we reconstruct the full path.
    # For robustness, let's assume client might send full path or just filename.
    # We need the local server path to the GIF.
    gif_server_path_from_client = data.get('gif_server_path') 
    mint_type = data.get('mint_type')
    user_description = data.get('user_description') # Optional

    if not all([image_id, gif_server_path_from_client, mint_type]):
        return jsonify({'status': 'error', 'message': 'Missing image_id, gif_server_path, or mint_type.'}), 400

    if mint_type not in ["short", "long"]:
        return jsonify({'status': 'error', 'message': 'Invalid mint_type. Must be "short" or "long".'}), 400

    # Construct the full local path to the GIF if not already full
    # This logic assumes STATIC_FOLDER_GIFS is the base for these GIFs.
    # If gif_server_path_from_client is already an absolute path, os.path.join might not behave as expected on its own.
    # A safer way: check if it's absolute. If not, join with STATIC_FOLDER_GIFS.
    if not os.path.isabs(gif_server_path_from_client):
        local_gif_path = os.path.join(STATIC_FOLDER_GIFS, os.path.basename(gif_server_path_from_client))
    else:
        # If client sends an absolute path, verify it's within the allowed directory to prevent security issues.
        if not gif_server_path_from_client.startswith(STATIC_FOLDER_GIFS):
            return jsonify({'status': 'error', 'message': 'Invalid gif_server_path.'}), 400
        local_gif_path = gif_server_path_from_client
        
    if not os.path.exists(local_gif_path):
         return jsonify({'status': 'error', 'message': f'GIF not found at specified path: {local_gif_path}'}), 404

    # We also need the original uploaded image path. image_id is typically the filename.
    # The original image is in UPLOAD_FOLDER.
    uploaded_image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_id)
    if not os.path.exists(uploaded_image_path):
         return jsonify({'status': 'error', 'message': f'Original uploaded image not found: {uploaded_image_path}'}), 404

    minting_result = mint_qnft_service(
        user_choice_mint_type=mint_type,
        generated_gif_local_path=local_gif_path,
        uploaded_image_local_path=uploaded_image_path,
        user_description=user_description
    )

    if minting_result['status'] == 'success':
        # --- Integration Point: Add minted NFT to market service ---
        # The minting_result['raw_metadata'] contains the detailed metadata.
        # We need to structure what market_service.add_minted_nft_to_market expects.
        # It expects a dict with id, name, gif_url, mint_type, mint_timestamp_iso, etc.
        raw_meta = minting_result.get('raw_metadata', {})
        market_nft_data = {
            'id': minting_result.get('transaction_id', raw_meta.get('name', 'unknown_id')), # Use TxID or name as ID
            'name': raw_meta.get('name'),
            'gif_url': raw_meta.get('animation_url'), # This is the arweave/ipfs URL
            'mint_type': mint_type, # This was input to mint_nft_route
            'mint_timestamp_iso': raw_meta.get('attributes', [{}])[1].get('value') if len(raw_meta.get('attributes',[])) > 1 else datetime.datetime.now(datetime.timezone.utc).isoformat(), # Extract from attributes or use now
            'btc_price_at_mint': next((attr['value'] for attr in raw_meta.get('attributes', []) if attr.get('trait_type') == "BTC Price at Mint"), None),
            'sol_price_at_mint': next((attr['value'] for attr in raw_meta.get('attributes', []) if attr.get('trait_type') == "SOL Price at Mint"), None),
            'original_image_url': raw_meta.get('properties', {}).get('files', [{},{}])[1].get('uri') if len(raw_meta.get('properties', {}).get('files',[])) > 1 else None
        }
        # Ensure prices are floats if they are strings in metadata
        if market_nft_data['btc_price_at_mint'] is not None:
            try: market_nft_data['btc_price_at_mint'] = float(market_nft_data['btc_price_at_mint'])
            except ValueError: market_nft_data['btc_price_at_mint'] = None
        if market_nft_data['sol_price_at_mint'] is not None:
            try: market_nft_data['sol_price_at_mint'] = float(market_nft_data['sol_price_at_mint'])
            except ValueError: market_nft_data['sol_price_at_mint'] = None

        add_minted_nft_to_market(market_nft_data)
        # --- End Integration Point ---
        return jsonify(minting_result), 200
    elif 'balance' in minting_result.get('message', '').lower(): # Specific error for insufficient balance
        return jsonify(minting_result), 402 # Payment Required
    else: # General internal errors during minting
        return jsonify(minting_result), 500

# --- Marketplace and Chart API Endpoints (already exist from previous step) ---
@app.route('/marketplace/nfts', methods=['GET'])
def marketplace_nfts_route():
    nfts = get_marketplace_nfts()
    return jsonify(nfts), 200

@app.route('/chart/price_data', methods=['GET'])
def price_chart_data_route():
    try:
        time_range_str = request.args.get('time_range_hours', default='24')
        time_range_hours = int(time_range_str)
        if time_range_hours <= 0:
            return jsonify({'status': 'error', 'message': 'time_range_hours must be positive.'}), 400
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid time_range_hours format. Must be an integer.'}), 400
    
    chart_data = get_price_chart_data(time_range_hours=time_range_hours)
    return jsonify(chart_data), 200


# Optional: A route to serve the generated GIFs if they are in app.static_folder
# Flask automatically serves files from the 'static' folder if `static_url_path` is not changed.
# So, if STATIC_FOLDER_GIFS is `QNFT/app/static/generated_gifs`, then a GET request to
# `/static/generated_gifs/your_gif_name.gif` should work by default.
# The `gif_url` returned above reflects this.

# If you need to serve from a directory not under the default static path for some reason:
# @app.route('/serve_gif/<path:filename>')
# def serve_gif(filename):
#     # This route would serve from STATIC_FOLDER_GIFS
#     # Ensure filename is safe (e.g., no '..')
#     return send_from_directory(STATIC_FOLDER_GIFS, filename, as_attachment=False)


if __name__ == '__main__':
    # For testing, it might be useful to add a dummy NFT via solana_service's result
    # to the market_service if solana_service.mint_qnft is called and market_service.add_minted_nft_to_market
    # is not integrated into it directly.
    # However, solana_service.mint_qnft currently does NOT call market_service.add_minted_nft_to_market.
    # is not integrated into it directly. (NOW IT IS, see above in /mint_nft route)
    # For now, market_service populates itself with dummy data on load.
    
    # A more integrated approach would be:
    # In solana_service.py, after successful (simulated) mint: (This is now handled in main.py's mint_nft_route)
    # from .market_service import add_minted_nft_to_market
    # ...
    # actual_nft_data_for_market = { 'id': ..., 'name': raw_metadata_dict['name'], ... }
    # add_minted_nft_to_market(actual_nft_data_for_market)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
