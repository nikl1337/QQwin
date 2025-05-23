import pytest
import datetime
from unittest.mock import patch
# Adjust import path based on your project structure
from app.services.market_service import (
    add_minted_nft_to_market, 
    get_marketplace_nfts, 
    get_price_chart_data,
    _minted_nfts, # For clearing/direct manipulation in tests
    _populate_dummy_nfts # To test its behavior
)

@pytest.fixture(autouse=True)
def clear_nft_store():
    """Clears the in-memory NFT store before each test."""
    _minted_nfts.clear()

def test_add_and_get_marketplace_nfts():
    assert len(get_marketplace_nfts()) == 0 # Starts empty due to fixture
    
    nft1_data = {"id": "nft1", "name": "My First QNFT", "mint_timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    add_minted_nft_to_market(nft1_data)
    assert len(get_marketplace_nfts()) == 1
    assert get_marketplace_nfts()[0] == nft1_data

    nft2_data = {"id": "nft2", "name": "Another QNFT", "mint_timestamp_iso": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).isoformat()}
    add_minted_nft_to_market(nft2_data)
    assert len(get_marketplace_nfts()) == 2
    # Ensure order is preserved (append)
    assert get_marketplace_nfts() == [nft1_data, nft2_data]

def test_populate_dummy_nfts_on_empty_store():
    assert len(_minted_nfts) == 0
    _populate_dummy_nfts() # Should populate
    assert len(_minted_nfts) > 0 
    # Check if some expected dummy data structure is present
    assert 'dummy_nft_uuid_1' in _minted_nfts[0]['id']

def test_populate_dummy_nfts_on_non_empty_store():
    nft_manual = {"id": "manual1", "name": "Manual NFT"}
    add_minted_nft_to_market(nft_manual)
    initial_count = len(_minted_nfts)
    
    _populate_dummy_nfts() # Should NOT populate again
    assert len(_minted_nfts) == initial_count
    assert _minted_nfts[0] == nft_manual # Ensure original NFT is still there

def test_get_price_chart_data_structure():
    # Populate with some data first
    _populate_dummy_nfts()
    
    chart_data = get_price_chart_data(time_range_hours=24)
    
    assert 'price_history' in chart_data
    assert 'nft_events' in chart_data
    assert isinstance(chart_data['price_history'], list)
    assert isinstance(chart_data['nft_events'], list)

    if chart_data['price_history']:
        # Price history should be [timestamp_ms, price]
        assert isinstance(chart_data['price_history'][0], list)
        assert len(chart_data['price_history'][0]) == 2
        assert isinstance(chart_data['price_history'][0][0], int) # timestamp ms
        assert isinstance(chart_data['price_history'][0][1], float) # price

def test_get_price_chart_data_nft_events_filtering():
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # NFT minted 1 hour ago (should be included in 24h range)
    nft_recent = {
        "id": "recent_nft", "name": "Recent", "mint_type": "long",
        "mint_timestamp_iso": (now - datetime.timedelta(hours=1)).isoformat(),
        "sol_price_at_mint": 100.0, "gif_url": "url1"
    }
    add_minted_nft_to_market(nft_recent)

    # NFT minted 30 hours ago (should NOT be included in 24h range, but in 48h)
    nft_old = {
        "id": "old_nft", "name": "Old", "mint_type": "short",
        "mint_timestamp_iso": (now - datetime.timedelta(hours=30)).isoformat(),
        "sol_price_at_mint": 90.0, "gif_url": "url2"
    }
    add_minted_nft_to_market(nft_old)

    # NFT with invalid timestamp format
    nft_bad_ts = {
        "id": "bad_ts_nft", "name": "Bad TS", "mint_type": "long",
        "mint_timestamp_iso": "Not an ISO date string", # Invalid
        "sol_price_at_mint": 95.0, "gif_url": "url3"
    }
    add_minted_nft_to_market(nft_bad_ts)
    
    # NFT with no timestamp string (None)
    nft_none_ts = {
        "id": "none_ts_nft", "name": "None TS", "mint_type": "long",
        "mint_timestamp_iso": None, 
        "sol_price_at_mint": 96.0, "gif_url": "url4"
    }
    add_minted_nft_to_market(nft_none_ts)


    # Test with 24-hour range
    chart_data_24h = get_price_chart_data(time_range_hours=24)
    event_ids_24h = [event['id'] for event in chart_data_24h['nft_events']]
    assert "recent_nft" in event_ids_24h
    assert "old_nft" not in event_ids_24h
    assert "bad_ts_nft" not in event_ids_24h # Should be skipped due to parse error
    assert "none_ts_nft" not in event_ids_24h # Should be skipped due to not string

    # Test with 48-hour range
    chart_data_48h = get_price_chart_data(time_range_hours=48)
    event_ids_48h = [event['id'] for event in chart_data_48h['nft_events']]
    assert "recent_nft" in event_ids_48h
    assert "old_nft" in event_ids_48h
    assert "bad_ts_nft" not in event_ids_48h


# Placeholder tests for new functions (rarity filter, leaderboard)
# These would need more setup if the underlying logic was more than placeholder
@patch('app.services.market_service.check_feature_access', return_value=True) # Assume user has access
def test_get_marketplace_nfts_filtered_placeholder(mock_check_access):
    _populate_dummy_nfts()
    # Test with VIP user who has access
    filters = {'rarity_min': 0.8} # Example filter
    filtered_nfts = get_marketplace_nfts_filtered(filters=filters, user_wallet_address="VIP_USER")
    # Placeholder function currently returns all, so we check that
    assert len(filtered_nfts) == len(_minted_nfts)
    # To test the access denial, you'd mock check_feature_access to return False
    # and verify the filter was removed or an error/specific response was given.
    
    # Test basic call without filters
    all_nfts = get_marketplace_nfts_filtered()
    assert len(all_nfts) == len(_minted_nfts)


@patch('app.services.market_service.check_feature_access', return_value=False) # User does NOT have access
def test_get_marketplace_nfts_filtered_rarity_access_denied(mock_check_access_denied):
    _populate_dummy_nfts()
    original_filters = {'rarity_min': 0.8, 'other_filter': 'value'}
    
    # Call the function with a user who doesn't have rarity_filtering access
    # The service should log a warning and ignore the 'rarity_min' filter.
    # The `filters` dict passed to the function is modified in place by current implementation.
    # This tests that the 'rarity_min' key is removed from the filters dictionary.
    # A copy is made to check its state after the call.
    filters_copy = original_filters.copy()
    
    get_marketplace_nfts_filtered(filters=filters_copy, user_wallet_address="BASIC_USER_NO_ACCESS")
    
    # Check that 'rarity_min' was removed by the function due to lack of access
    assert 'rarity_min' not in filters_copy 
    assert 'other_filter' in filters_copy # Other filters should remain untouched

def test_get_leaderboard_placeholder():
    leaderboard = get_leaderboard()
    assert isinstance(leaderboard, list)
    if leaderboard: # If it returns data (it's a placeholder, so it should)
        assert "user" in leaderboard[0]
        assert "score" in leaderboard[0]
        assert "rank" in leaderboard[0]
        assert leaderboard[0]['rank'] == 1 # Based on dummy data provided in service
    assert len(leaderboard) >= 3 # Based on dummy data size
