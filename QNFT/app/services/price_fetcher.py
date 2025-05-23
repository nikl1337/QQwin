import requests
import time

CACHE_DURATION_SECONDS = 180  # 3 minutes
_price_cache = {} # Format: {'coin_id_vs_currency': {'price': 123.45, 'timestamp': 1678886400}}

def _get_cached_price(cache_key):
    """
    Retrieves a price from cache if it exists and is not expired.
    Returns the price or None.
    """
    if cache_key in _price_cache:
        cached_data = _price_cache[cache_key]
        if time.time() - cached_data['timestamp'] < CACHE_DURATION_SECONDS:
            # print(f"Cache hit for {cache_key}") # For debugging
            return cached_data['price']
        # else: # For debugging
            # print(f"Cache expired for {cache_key}")
    # else: # For debugging
        # print(f"Cache miss for {cache_key}")
    return None

def _update_cache(cache_key, price):
    """Updates the cache with the given price and current timestamp."""
    _price_cache[cache_key] = {'price': price, 'timestamp': time.time()}
    # print(f"Cache updated for {cache_key} with price {price}") # For debugging

def _fetch_price_from_api(coin_id, vs_currency='usdc'):
    """
    Fetches the price for a given coin_id and vs_currency from CoinGecko API.
    Returns the price as a float or None if an error occurs.
    """
    api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={vs_currency}"
    # print(f"Fetching from API: {api_url}") # For debugging
    try:
        response = requests.get(api_url, timeout=10) # 10 seconds timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json()
        
        price = data.get(coin_id, {}).get(vs_currency)
        
        if price is not None:
            return float(price)
        else:
            # This case means the API call succeeded but the expected data structure was not found.
            print(f"Error: Price not found for {coin_id}/{vs_currency} in API response. Data: {data}")
            return None
    except requests.exceptions.Timeout:
        print(f"API request timed out for {coin_id}/{vs_currency}: {api_url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"API request failed with HTTPError for {coin_id}/{vs_currency}: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        # Covers other network errors (DNS failure, connection refused, etc.)
        print(f"API request failed with RequestException for {coin_id}/{vs_currency}: {e}")
        return None
    except ValueError as e: # Handles JSONDecodeError if response is not valid JSON, or float conversion error
        print(f"Failed to parse API response or price for {coin_id}/{vs_currency}: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred while fetching price for {coin_id}/{vs_currency}: {e}")
        return None


def get_btc_usdc_price():
    """
    Fetches the BTC/USDC price, using cache if available.
    Returns the price as a float or None.
    """
    cache_key = 'bitcoin_usdc'
    cached_price = _get_cached_price(cache_key)
    if cached_price is not None:
        return cached_price
    
    price = _fetch_price_from_api('bitcoin', 'usdc')
    if price is not None:
        _update_cache(cache_key, price)
    return price

def get_sol_usdc_price():
    """
    Fetches the SOL/USDC price, using cache if available.
    Returns the price as a float or None.
    """
    cache_key = 'solana_usdc'
    cached_price = _get_cached_price(cache_key)
    if cached_price is not None:
        return cached_price
        
    price = _fetch_price_from_api('solana', 'usdc')
    if price is not None:
        _update_cache(cache_key, price)
    return price

if __name__ == '__main__':
    print("--- Testing Price Fetcher ---")
    
    # Test BTC/USDC
    print("\nFetching BTC/USDC price (first call, might be from API)...")
    btc_price = get_btc_usdc_price()
    if btc_price is not None:
        print(f"BTC/USDC Price: {btc_price}")
    else:
        print("Failed to fetch BTC/USDC price on first call.")

    print("\nFetching BTC/USDC price again (should be cached if first call succeeded)...")
    time.sleep(2) # Short sleep, well within cache duration
    btc_price_cached = get_btc_usdc_price()
    if btc_price_cached is not None:
        print(f"BTC/USDC Price (cached): {btc_price_cached}")
        if btc_price is not None and btc_price_cached != btc_price:
             print("Error: Cached BTC price differs from initial when it shouldn't have!")
    else:
        print("Failed to fetch BTC/USDC price from cache (or first call failed).")

    # Test SOL/USDC
    print("\nFetching SOL/USDC price (first call, might be from API)...")
    sol_price = get_sol_usdc_price()
    if sol_price is not None:
        print(f"SOL/USDC Price: {sol_price}")
    else:
        print("Failed to fetch SOL/USDC price on first call.")

    print("\nFetching SOL/USDC price again (should be cached if first call succeeded)...")
    time.sleep(2)
    sol_price_cached = get_sol_usdc_price()
    if sol_price_cached is not None:
        print(f"SOL/USDC Price (cached): {sol_price_cached}")
        if sol_price is not None and sol_price_cached != sol_price:
            print("Error: Cached SOL price differs from initial when it shouldn't have!")
    else:
        print("Failed to fetch SOL/USDC price from cache (or first call failed).")

    # Test cache expiration
    if btc_price is not None: # Only test expiration if we got an initial price
        print(f"\nWaiting for {CACHE_DURATION_SECONDS + 5} seconds to test cache expiration for BTC/USDC...")
        time.sleep(CACHE_DURATION_SECONDS + 5)
        print("Fetching BTC/USDC price again (cache should have expired)...")
        btc_price_after_expiration = get_btc_usdc_price()
        if btc_price_after_expiration is not None:
            print(f"BTC/USDC Price (after cache expiry): {btc_price_after_expiration}")
            if btc_price_after_expiration == btc_price and CACHE_DURATION_SECONDS > 10 : # if price happens to be identical, it's hard to tell if cache worked.
                 print("Note: Price after cache expiration is the same as before. This is possible if market price hasn't changed.")
        else:
            print("Failed to fetch BTC/USDC price after cache expiration.")
    
    print("\n--- Price Fetcher Test Complete ---")
