import requests
import os
from dotenv import load_dotenv

load_dotenv()

def has_nft(wallet_address):
    """
    Check if wallet has the required NFT collection
    """
    try:
        helius_api_key = os.getenv("HELIUS_API_KEY")
        collection_id = os.getenv("COLLECTION_ID")
        
        if not helius_api_key or not collection_id:
            print("Missing HELIUS_API_KEY or COLLECTION_ID")
            return False
        
        # Get NFTs for the wallet
        url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/nft-assets?api-key={helius_api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            nfts = response.json()
            
            # Check if any NFT belongs to the required collection
            for nft in nfts:
                if nft.get("grouping") and len(nft["grouping"]) > 0:
                    for group in nft["grouping"]:
                        if group.get("group_key") == "collection" and group.get("group_value") == collection_id:
                            print(f"Found required NFT: {nft.get('content', {}).get('metadata', {}).get('name', 'Unknown')}")
                            return True
            
            print(f"No required NFT found in wallet {wallet_address}")
            return False
        else:
            print(f"API request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error checking NFT ownership: {e}")
        return False 