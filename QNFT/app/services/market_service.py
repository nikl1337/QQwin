import datetime
import time # Not strictly needed here but often useful for time.time() if used
import random
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_minted_nfts = [] # In-memory store

def add_minted_nft_to_market(nft_data: dict):
    """Appends nft_data to the _minted_nfts list."""
    logging.info(f"MARKET_SERVICE: Adding NFT to market: {nft_data.get('name')}")
    _minted_nfts.append(nft_data)

def get_marketplace_nfts():
    """Returns the current list of _minted_nfts."""
    logging.info(f"MARKET_SERVICE: Fetching all marketplace NFTs. Count: {len(_minted_nfts)}")
    return list(_minted_nfts) # Return a copy

def get_price_chart_data(time_range_hours=24):
    """
    Generates sample time-series data for SOL/USDC and correlates with minted NFTs.
    """
    logging.info(f"MARKET_SERVICE: Generating price chart data for time range: {time_range_hours} hours.")
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    start_time_dt = now_utc - datetime.timedelta(hours=time_range_hours)
    
    price_history = []
    # Simulate SOL price starting point for the beginning of the time_range_hours
    # This ensures the chart starts from a plausible historical value, not current price going backwards
    initial_price_point_dt = start_time_dt 
    current_price = random.uniform(15.0, 25.0) # Initial SOL price for simulation at start_time_dt

    # Generate price points every 15 minutes within the time range
    num_intervals = time_range_hours * 4  # 4 intervals per hour (every 15 minutes)
    
    for i in range(num_intervals + 1): # +1 to include the current time point or close to it
        entry_time_dt = start_time_dt + datetime.timedelta(minutes=i * 15)
        
        if entry_time_dt > now_utc: # Don't project into the future
            break
        
        # For the first point, use the initial price. For subsequent, vary it.
        if i > 0:
            current_price += random.uniform(-0.25, 0.25) # Simulate small price fluctuation
            current_price = max(1.0, current_price) # Ensure price doesn't go below 1.0

        price_history.append([int(entry_time_dt.timestamp() * 1000), round(current_price, 2)])

    nft_events = []
    logging.info(f"MARKET_SERVICE: Processing {len(_minted_nfts)} NFTs for chart events.")
    for nft in _minted_nfts:
        mint_timestamp_iso_str = nft.get('mint_timestamp_iso')
        
        if not isinstance(mint_timestamp_iso_str, str):
            logging.warning(f"MARKET_SERVICE: NFT {nft.get('id')} has malformed timestamp (not a string). Skipping.")
            continue 
            
        try:
            # Ensure the string is compatible with fromisoformat (e.g. no 'Z' if not supported by version)
            # Python 3.7+ fromisoformat handles timezone offsets like +00:00
            # If a 'Z' is present, it needs to be replaced for older Pythons or handled.
            # Assuming timestamps are stored with timezone info compatible with fromisoformat.
            nft_mint_time_dt = datetime.datetime.fromisoformat(mint_timestamp_iso_str)
        except ValueError as e:
            logging.warning(f"MARKET_SERVICE: NFT {nft.get('id')} timestamp '{mint_timestamp_iso_str}' parse error: {e}. Skipping.")
            continue

        # Ensure nft_mint_time_dt is timezone-aware for comparison if start_time_dt is.
        # If nft_mint_time_dt is naive, it should be localized or assumed to be UTC.
        # Since now_utc and start_time_dt are timezone-aware (UTC), nft_mint_time_dt must also be.
        # fromisoformat should handle this if the string has timezone info. If not, it's naive.
        # For simplicity, if it's naive, assume UTC.
        if nft_mint_time_dt.tzinfo is None:
            nft_mint_time_dt = nft_mint_time_dt.replace(tzinfo=datetime.timezone.utc)


        if start_time_dt <= nft_mint_time_dt <= now_utc:
            nft_events.append({
                'timestamp': int(nft_mint_time_dt.timestamp() * 1000),
                'type': nft.get('mint_type'),
                'nft_name': nft.get('name'),
                'sol_price_at_mint': nft.get('sol_price_at_mint'), # Use SOL price for SOL chart
                'id': nft.get('id'),
                'gif_url': nft.get('gif_url')
            })
    logging.info(f"MARKET_SERVICE: Found {len(nft_events)} NFT events in time range.")
            
    return {'price_history': price_history, 'nft_events': nft_events}

def _populate_dummy_nfts():
    """Populates _minted_nfts with dummy data if it's empty."""
    if not _minted_nfts:
        logging.info("MARKET_SERVICE: No existing NFTs found, populating with dummy data.")
        # Use a fixed seed for dummy data generation for consistent testing if needed
        # random.seed(42) 
        
        base_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=random.randint(20, 40)) # Spread further back
        
        for i in range(5): # Create 5 dummy NFTs
            # Ensure mint times are somewhat spread out and can fall within typical query ranges (e.g., last 24h, 72h)
            mint_hour_offset = random.uniform(1, 5) # Use float for more variability
            nft_time = base_time + datetime.timedelta(hours=mint_hour_offset * i) 
            
            # Ensure dummy data is within a reasonable past timeframe
            if nft_time > datetime.datetime.now(datetime.timezone.utc):
                nft_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=random.randint(1,3))


            dummy_nft_data = {
                'id': f'dummy_nft_uuid_{i+1}', 
                'name': f'QNFT Dummy #{i+1:03d}', 
                'gif_url': f'/static/generated_gifs/dummy_final_qnft_{i+1}.gif', # More realistic dummy path
                'mint_type': random.choice(['long', 'short']), 
                'mint_timestamp_iso': nft_time.isoformat(), # Standard ISO format
                'btc_price_at_mint': round(60000 + random.uniform(-2000, 2000), 2), 
                'sol_price_at_mint': round(20 + random.uniform(-7, 7), 2),
                'original_image_url': f'/static/uploads/dummy_original_image_{i+1}.png'
            }
            add_minted_nft_to_market(dummy_nft_data)
        logging.info(f"MARKET_SERVICE: Populated {len(_minted_nfts)} dummy NFTs.")
    else:
        logging.info("MARKET_SERVICE: NFTs already exist, skipping dummy data population.")

# Populate dummy data when the module is loaded if no NFTs are present
_populate_dummy_nfts()


# --- New Placeholders for Rarity & Leaderboard ---
def get_marketplace_nfts_filtered(filters=None, sort_by=None, user_wallet_address=None):
    '''Placeholder for advanced filtering and sorting.'''
    global _minted_nfts # Ensure we are using the global list
    
    # Attempt to import for feature checking, handle if not available during testing
    try:
        from app.services.user_service import check_feature_access # Corrected import path
        can_use_rarity_filter = True
    except ImportError:
        logging.warning("MARKET_SERVICE: user_service not available for filter check during get_marketplace_nfts_filtered.")
        can_use_rarity_filter = False # Assume no access if service is missing

    if user_wallet_address and filters and 'rarity_min' in filters:
        if can_use_rarity_filter:
            if not check_feature_access(user_wallet_address, "rarity_filtering"):
                # In a real app, you might raise an exception or return a specific error structure
                logging.warning(f"MARKET_SERVICE: User {user_wallet_address} denied rarity filtering access.")
                # For now, just ignore the filter if access denied, or return error:
                # return {"error": "VIP access required for rarity filtering"} 
                # Let's return all NFTs but log it for this placeholder
                filters.pop('rarity_min', None) # Remove the filter they can't use
                logging.info("MARKET_SERVICE: Rarity filter ignored due to access level.")
        else:
            # If user_service itself is missing, we can't check.
            # Depending on policy, either allow or deny. For placeholder, let's log and ignore.
            filters.pop('rarity_min', None)
            logging.info("MARKET_SERVICE: Rarity filter check skipped as user_service is unavailable.")


    logging.info(f"MARKET_SERVICE: Getting filtered NFTs with filters: {filters}, sort_by: {sort_by}")
    # Actual filtering logic would go here if implemented
    # For now, just returns all NFTs as a placeholder
    return list(_minted_nfts) # Return a copy

def get_leaderboard():
    '''Placeholder for generating a leaderboard.'''
    logging.info("MARKET_SERVICE: Generating leaderboard (Placeholder).")
    # Dummy leaderboard data
    return [
        {"user": "USER_PUBLIC_KEY_1", "score": 1500, "rank": 1, "tier": "vip"},
        {"user": "USER_PUBLIC_KEY_2", "score": 1200, "rank": 2, "tier": "pro"},
        {"user": "USER_DUMMY_PUBLIC_KEY_HERE_12345", "score": 800, "rank": 3, "tier": "basic"},
        {"user": "EuSgddsfPspi1kkdnosEcndymiKE998zUqWfKBpDAbG2", "score": 500, "rank": 4, "tier": "admin"} # Admin might not be on leaderboard
    ]
# --- End New Placeholders ---


# For direct testing of this module:
if __name__ == '__main__':
    print("--- Testing Market Service ---")
    
    print(f"\nInitial Marketplace NFTs (Total: {len(get_marketplace_nfts())}):")
    # for nft_item in get_marketplace_nfts()[:2]: # Print first 2
    #     print(nft_item)

    print("\nTesting Price Chart Data (last 24h):")
    chart_data_24h = get_price_chart_data(time_range_hours=24)
    print(f"  Price History points: {len(chart_data_24h['price_history'])}")
    if chart_data_24h['price_history']:
        print(f"    Sample price point: {chart_data_24h['price_history'][0]}")
    print(f"  NFT Events: {len(chart_data_24h['nft_events'])}")
    if chart_data_24h['nft_events']:
        print(f"    Sample NFT Event: {chart_data_24h['nft_events'][0]}")

    print("\nTesting Price Chart Data (last 72h to see more dummy NFTs if populated further back):")
    chart_data_72h = get_price_chart_data(time_range_hours=72)
    print(f"  Price History points: {len(chart_data_72h['price_history'])}")
    print(f"  NFT Events: {len(chart_data_72h['nft_events'])}")
    if chart_data_72h['nft_events']: # Potentially more events if dummy data is older
        # Find an event to print if any exist
        for event in chart_data_72h['nft_events']:
            if event['id'].startswith("dummy_nft_uuid"):
                print(f"    Sample Dummy NFT Event from 72h range: {event}")
                break
    
    # Test adding a new NFT (simulating post-mint call)
    print("\nTesting adding a new NFT post-mint...")
    new_nft_timestamp = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=30)
    new_nft = {
        'id': 'new_real_nft_123', 
        'name': 'QNFT Live #001', 
        'gif_url': '/static/generated_gifs/live_qnft_123.gif',
        'mint_type': 'short', 
        'mint_timestamp_iso': new_nft_timestamp.isoformat(),
        'btc_price_at_mint': 65000.00, 
        'sol_price_at_mint': 22.50,
        'original_image_url': '/static/uploads/live_original_123.png'
    }
    add_minted_nft_to_market(new_nft)
    print(f"Total NFTs after adding new one: {len(get_marketplace_nfts())}")
    
    chart_data_after_add = get_price_chart_data(time_range_hours=1) # Check very recent range
    print("\nPrice Chart Data (last 1h after adding new NFT):")
    print(f"  Price History points: {len(chart_data_after_add['price_history'])}")
    print(f"  NFT Events: {len(chart_data_after_add['nft_events'])}")
    found_new_event = False
    for event in chart_data_after_add['nft_events']:
        if event['id'] == 'new_real_nft_123':
            print(f"    Newly added NFT event found: {event}")
            found_new_event = True
            break
    assert found_new_event, "Newly added NFT event was not found in the 1-hour chart data!"

    print("\n--- Market Service Test Complete ---")

    # Test new placeholder functions
    print("\n--- Testing New Market Service Placeholders ---")
    print("\nTesting get_marketplace_nfts_filtered (no actual filter logic yet):")
    # Simulate a VIP user trying to use rarity filter
    vip_user = "USER_PUBLIC_KEY_1"
    basic_user = "USER_DUMMY_PUBLIC_KEY_HERE_12345"

    filtered_nfts_vip_allowed = get_marketplace_nfts_filtered(filters={'rarity_min': 0.8}, user_wallet_address=vip_user)
    print(f"Filtered NFTs for VIP (rarity allowed, but filter not implemented): {len(filtered_nfts_vip_allowed)} items.")
    
    # Simulate a basic user trying to use rarity filter
    # The current placeholder removes the filter if access is denied or service unavailable.
    filtered_nfts_basic_denied = get_marketplace_nfts_filtered(filters={'rarity_min': 0.8}, user_wallet_address=basic_user)
    print(f"Filtered NFTs for Basic User (rarity filter should be ignored): {len(filtered_nfts_basic_denied)} items.")
    # To truly test the error return, you'd uncomment `return {"error": ...}` in the function.

    print("\nTesting get_leaderboard:")
    leaderboard_data = get_leaderboard()
    print(f"Leaderboard Data: {leaderboard_data}")
    assert len(leaderboard_data) > 0
    assert leaderboard_data[0]['rank'] == 1
    
    print("\n--- New Market Service Placeholders Test Complete ---")
