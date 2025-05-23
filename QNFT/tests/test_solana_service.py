import pytest
from unittest.mock import patch
# Adjust import path based on your project structure
from app.services.solana_service import prepare_nft_metadata, _nft_serial_number, ADMIN_WALLET_ADDRESS
from app.utils.cryptography_utils import encrypt_metadata_kyber # Test its actual placeholder behavior

@pytest.fixture(autouse=True)
def reset_serial_number():
    """Resets the global serial number before each test."""
    global _nft_serial_number
    original_serial = _nft_serial_number
    _nft_serial_number = 0
    yield
    _nft_serial_number = original_serial


def test_prepare_nft_metadata_structure_and_encryption():
    gif_url = "https://example.com/my_awesome.gif"
    original_image_url = "https://example.com/my_original.png"
    btc_price = 60000.75
    sol_price = 200.15
    timestamp_str = "2023-10-26 12:00:00 UTC"
    mint_type = "long"
    user_description = "My first QNFT!"

    encrypted_meta_string, raw_meta_dict = prepare_nft_metadata(
        gif_url, original_image_url, btc_price, sol_price, timestamp_str, mint_type, user_description
    )

    # Test raw metadata structure
    assert raw_meta_dict['name'] == "QNFT #0001" # Serial number check
    assert raw_meta_dict['symbol'] == "QNFT"
    assert user_description in raw_meta_dict['description']
    assert mint_type in raw_meta_dict['description']
    assert raw_meta_dict['image'] == gif_url
    assert raw_meta_dict['animation_url'] == gif_url
    assert raw_meta_dict['external_url'].endswith("/1") # Serial in URL

    assert len(raw_meta_dict['attributes']) == 4 # Mint Type, Timestamp, BTC Price, SOL Price
    assert {"trait_type": "Mint Type", "value": mint_type} in raw_meta_dict['attributes']
    assert {"trait_type": "Timestamp", "value": timestamp_str} in raw_meta_dict['attributes']
    assert {"trait_type": "BTC Price at Mint", "value": str(btc_price)} in raw_meta_dict['attributes']
    assert {"trait_type": "SOL Price at Mint", "value": str(sol_price)} in raw_meta_dict['attributes']

    assert raw_meta_dict['properties']['files'][0]['uri'] == gif_url
    assert raw_meta_dict['properties']['files'][0]['type'] == "image/gif"
    assert raw_meta_dict['properties']['files'][1]['uri'] == original_image_url
    assert raw_meta_dict['properties']['creators'][0]['address'] == ADMIN_WALLET_ADDRESS
    assert raw_meta_dict['properties']['creators'][0]['share'] == 100

    # Test placeholder encryption
    assert encrypted_meta_string.startswith("kyber_encrypted_")
    # Verify that the part after prefix is the JSON string of raw_meta_dict
    import json
    expected_json_substring = json.dumps(raw_meta_dict, indent=2)
    assert encrypted_meta_string.endswith(expected_json_substring)


def test_prepare_nft_metadata_serial_increment():
    # First call
    _, meta1 = prepare_nft_metadata("g1", "o1", 1,1, "ts1", "t1")
    assert meta1['name'] == "QNFT #0001"
    
    # Second call
    _, meta2 = prepare_nft_metadata("g2", "o2", 2,2, "ts2", "t2")
    assert meta2['name'] == "QNFT #0002"

def test_prepare_nft_metadata_no_prices_or_user_desc():
    # Test case where prices might be None (e.g., API fetch failed)
    # and no user description is provided.
    gif_url = "https://example.com/another.gif"
    original_image_url = "https://example.com/another_orig.png"
    btc_price = None
    sol_price = None
    timestamp_str = "2023-10-27 10:00:00 UTC"
    mint_type = "short"

    _, raw_meta_dict = prepare_nft_metadata(
        gif_url, original_image_url, btc_price, sol_price, timestamp_str, mint_type, None
    )
    assert "My first QNFT!" not in raw_meta_dict['description'] # Ensure previous user_desc is not sticky
    assert "N/A" in raw_meta_dict['description'] # Check if N/A is correctly placed for prices
    
    # Check attributes: only Mint Type and Timestamp should be present if prices are None
    assert len(raw_meta_dict['attributes']) == 2
    assert {"trait_type": "Mint Type", "value": mint_type} in raw_meta_dict['attributes']
    assert {"trait_type": "Timestamp", "value": timestamp_str} in raw_meta_dict['attributes']
    assert not any("BTC Price at Mint" == attr.get("trait_type") for attr in raw_meta_dict['attributes'])
    assert not any("SOL Price at Mint" == attr.get("trait_type") for attr in raw_meta_dict['attributes'])

# Placeholder test for mint_qnft - primarily to show how dependencies would be mocked
# Actual minting logic is heavily placeholder, so this test mostly verifies orchestration of calls.
@patch('app.services.solana_service.get_btc_usdc_price', return_value=60000.0)
@patch('app.services.solana_service.get_sol_usdc_price', return_value=200.0)
@patch('app.services.solana_service.prepare_nft_metadata') # Mock the already tested metadata prep
@patch('app.services.solana_service.get_user_public_key', return_value="TEST_USER_WALLET")
@patch('app.services.solana_service.get_user_wallet_balance', return_value=1.0) # Sufficient balance
def test_mint_qnft_orchestration(
    mock_get_balance, mock_get_pub_key, mock_prepare_meta, mock_get_sol, mock_get_btc
):
    from app.services.solana_service import mint_qnft # Import here to use fresh mocks
    
    # Mock what prepare_nft_metadata would return
    dummy_raw_meta = {"name": "QNFT #TEST", "attributes": [], "properties": {"files": []}}
    dummy_enc_meta = "kyber_encrypted_dummy"
    mock_prepare_meta.return_value = (dummy_enc_meta, dummy_raw_meta)

    result = mint_qnft(
        user_choice_mint_type="long",
        generated_gif_local_path="/tmp/dummy.gif",
        uploaded_image_local_path="/tmp/dummy.png",
        user_description="A test NFT"
    )

    assert result['status'] == 'success'
    assert result['message'] == 'NFT Minted (Simulated)'
    assert 'transaction_id' in result
    mock_get_btc.assert_called_once()
    mock_get_sol.assert_called_once()
    mock_prepare_meta.assert_called_once()
    mock_get_pub_key.assert_called_once()
    mock_get_balance.assert_called_once_with("TEST_USER_WALLET")
    # Further assertions could check that the logging messages for placeholder steps are emitted.
    # e.g., by capturing logs or checking specific log messages if that's critical.

@patch('app.services.solana_service.get_user_wallet_balance', return_value=0.001) # Insufficient balance
@patch('app.services.solana_service.get_user_public_key', return_value="TEST_USER_WALLET_POOR")
def test_mint_qnft_insufficient_balance(mock_get_pub_key_poor, mock_get_balance_poor):
    from app.services.solana_service import mint_qnft
    result = mint_qnft("short", "/tmp/g.gif", "/tmp/i.png")
    assert result['status'] == 'error'
    assert result['message'] == 'Insufficient SOL balance for minting fee.'
