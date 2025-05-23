import pytest
import responses # For mocking HTTP requests
import time
# Adjust import path based on your project structure
from app.services.price_fetcher import get_btc_usdc_price, get_sol_usdc_price, _price_cache, CACHE_DURATION_SECONDS

COINGECKO_API_URL_BTC = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usdc"
COINGECKO_API_URL_SOL = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usdc"

@pytest.fixture(autouse=True)
def clear_cache_and_reset_responses():
    """Clears the cache before each test and ensures responses is reset."""
    _price_cache.clear()
    responses.reset() # Reset responses library state

@responses.activate
def test_get_btc_usdc_price_success():
    responses.add(
        responses.GET,
        COINGECKO_API_URL_BTC,
        json={"bitcoin": {"usdc": 50000.50}},
        status=200
    )
    price = get_btc_usdc_price()
    assert price == 50000.50
    assert len(responses.calls) == 1 # Should make one API call
    assert 'bitcoin_usdc' in _price_cache

@responses.activate
def test_get_sol_usdc_price_success():
    responses.add(
        responses.GET,
        COINGECKO_API_URL_SOL,
        json={"solana": {"usdc": 150.75}},
        status=200
    )
    price = get_sol_usdc_price()
    assert price == 150.75
    assert len(responses.calls) == 1
    assert 'solana_usdc' in _price_cache

@responses.activate
def test_price_caching():
    responses.add(
        responses.GET,
        COINGECKO_API_URL_BTC,
        json={"bitcoin": {"usdc": 51000.00}},
        status=200
    )
    # First call - should hit API
    price1 = get_btc_usdc_price()
    assert price1 == 51000.00
    assert len(responses.calls) == 1
    assert 'bitcoin_usdc' in _price_cache
    assert _price_cache['bitcoin_usdc']['price'] == 51000.00

    # Second call - should use cache
    price2 = get_btc_usdc_price()
    assert price2 == 51000.00
    assert len(responses.calls) == 1 # Still 1, no new API call
    
@responses.activate
def test_cache_expiration():
    responses.add(
        responses.GET,
        COINGECKO_API_URL_SOL,
        json={"solana": {"usdc": 160.00}},
        status=200,
        # Adding a second response for after cache expires
        # Note: responses matches based on URL, so subsequent GETs to same URL will cycle through added responses
    )
    responses.add( 
        responses.GET,
        COINGECKO_API_URL_SOL,
        json={"solana": {"usdc": 165.00}}, # New price
        status=200
    )

    # First call
    price_initial = get_sol_usdc_price()
    assert price_initial == 160.00
    assert len(responses.calls) == 1
    
    # Second call (within cache duration)
    price_cached = get_sol_usdc_price()
    assert price_cached == 160.00
    assert len(responses.calls) == 1 # No new call

    # Simulate time passing beyond cache duration
    # We need to patch time.time() for this to be reliable and fast in tests
    # Or, manually manipulate the timestamp in the cache (less clean but works for this simple cache)
    original_timestamp = _price_cache['solana_usdc']['timestamp']
    _price_cache['solana_usdc']['timestamp'] = original_timestamp - CACHE_DURATION_SECONDS - 10 # Move it back in time

    price_after_expiry = get_sol_usdc_price()
    assert price_after_expiry == 165.00 # Should fetch new price
    assert len(responses.calls) == 2 # Should have made a second API call

@responses.activate
def test_get_price_api_error_404():
    responses.add(
        responses.GET,
        COINGECKO_API_URL_BTC,
        json={"error": "not found"},
        status=404
    )
    price = get_btc_usdc_price()
    assert price is None
    assert 'bitcoin_usdc' not in _price_cache # Should not cache failures

@responses.activate
def test_get_price_api_error_500():
    responses.add(
        responses.GET,
        COINGECKO_API_URL_SOL,
        json={"error": "server error"},
        status=500
    )
    price = get_sol_usdc_price()
    assert price is None
    assert 'solana_usdc' not in _price_cache

@responses.activate
def test_get_price_api_timeout():
    # responses library doesn't directly simulate requests.exceptions.Timeout
    # It's more for controlling the response. We can simulate a non-JSON response or error.
    # To truly test timeout, you might need more advanced patching of requests.get itself.
    # For this, we'll test a scenario where the response is not valid JSON, which is a failure mode.
    responses.add(
        responses.GET,
        COINGECKO_API_URL_BTC,
        body="not json", # Invalid JSON response
        status=200
    )
    price = get_btc_usdc_price()
    assert price is None

@responses.activate
def test_get_price_unexpected_json_structure():
    responses.add(
        responses.GET,
        COINGECKO_API_URL_SOL,
        json={"unexpected_coin": {"usdc": 100.00}}, # Correct structure but wrong coin_id
        status=200
    )
    price = get_sol_usdc_price()
    assert price is None

@responses.activate
def test_get_price_currency_not_found_in_response():
    responses.add(
        responses.GET,
        COINGECKO_API_URL_BTC,
        json={"bitcoin": {"eur": 45000.00}}, # Correct coin_id, but 'eur' instead of 'usdc'
        status=200
    )
    price = get_btc_usdc_price() # This function specifically looks for 'usdc'
    assert price is None
