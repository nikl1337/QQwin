# QNFT/app/services/user_service.py
_user_tiers = {
    "EuSgddsfPspi1kkdnosEcndymiKE998zUqWfKBpDAbG2": "admin", # Admin wallet from solana_service
    "USER_PUBLIC_KEY_1": "vip",
    "USER_PUBLIC_KEY_2": "pro",
    "USER_DUMMY_PUBLIC_KEY_HERE_12345": "basic", # Default user from solana_service
}

def get_user_tier(user_wallet_address: str) -> str:
    '''Placeholder for Wallet Tier System.'''
    tier = _user_tiers.get(user_wallet_address, "basic") # Default to 'basic' if not found
    print(f"User Service: Wallet {user_wallet_address} is tier '{tier}'.")
    return tier

def check_feature_access(user_wallet_address: str, feature_name: str) -> bool:
    '''Placeholder for checking feature access based on tier.'''
    tier = get_user_tier(user_wallet_address)
    
    print(f"User Service: Checking access for feature '{feature_name}' for tier '{tier}'.")
    
    if feature_name == "advanced_gif_styles":
        # Allows pro, vip, and admin to access advanced styles
        return tier in ["pro", "vip", "admin"]
    if feature_name == "rarity_filtering":
        # Only vip and admin can use rarity filters
        return tier in ["vip", "admin"]
    
    # Default: all other features are accessible by anyone
    print(f"User Service: Feature '{feature_name}' has default access (True).")
    return True

if __name__ == '__main__':
    print("--- Testing User Service ---")
    wallets_to_test = [
        "EuSgddsfPspi1kkdnosEcndymiKE998zUqWfKBpDAbG2",
        "USER_PUBLIC_KEY_1",
        "USER_PUBLIC_KEY_2",
        "USER_DUMMY_PUBLIC_KEY_HERE_12345",
        "UNKNOWN_WALLET_ADDRESS"
    ]
    
    features_to_test = ["advanced_gif_styles", "rarity_filtering", "general_feature"]

    for wallet in wallets_to_test:
        print(f"\nTesting Wallet: {wallet}")
        tier = get_user_tier(wallet)
        print(f"  Tier: {tier}")
        for feature in features_to_test:
            access = check_feature_access(wallet, feature)
            print(f"  Access to '{feature}': {access}")
            
    # Specific checks based on defined logic
    assert get_user_tier("EuSgddsfPspi1kkdnosEcndymiKE998zUqWfKBpDAbG2") == "admin"
    assert check_feature_access("USER_PUBLIC_KEY_1", "advanced_gif_styles") == True # vip
    assert check_feature_access("USER_PUBLIC_KEY_2", "advanced_gif_styles") == True # pro
    assert check_feature_access("USER_DUMMY_PUBLIC_KEY_HERE_12345", "advanced_gif_styles") == False # basic
    
    assert check_feature_access("USER_PUBLIC_KEY_1", "rarity_filtering") == True # vip
    assert check_feature_access("USER_PUBLIC_KEY_2", "rarity_filtering") == False # pro
    assert check_feature_access("UNKNOWN_WALLET_ADDRESS", "rarity_filtering") == False # basic (default)
    
    assert check_feature_access("USER_DUMMY_PUBLIC_KEY_HERE_12345", "general_feature") == True # basic, general access
    print("\n--- User Service Test Complete ---")
