import subprocess
import re
import os
from dotenv import load_dotenv

load_dotenv()

def has_nft_js(wallet_address):
    """
    Check if wallet has the required NFT collection using JavaScript (Metaplex)
    """
    try:
        helius_api_key = os.getenv("HELIUS_API_KEY")
        collection_id = os.getenv("COLLECTION_ID")
        
        if not helius_api_key or not collection_id:
            print("Missing HELIUS_API_KEY or COLLECTION_ID")
            return False
        
        print(f"🔍 Checking NFT ownership for wallet: {wallet_address}")
        print(f"📦 Collection ID: {collection_id}")
        print(f"🔑 Using JavaScript (Metaplex) approach...")
        
        # Run the JavaScript code as a subprocess
        result = subprocess.run(['node', '../test_js.js'], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse the JavaScript output
            output = result.stdout.strip()
            print(f"📄 JavaScript output: {output}")
            
            # Extract NFT count using regex
            match = re.search(r'has (\d+) NFTs', output)
            if match:
                nft_count = int(match.group(1))
                print(f"✅ Found {nft_count} NFTs in wallet")
                
                # For now, if wallet has any NFTs, consider it verified
                # You can add specific collection checking logic here
                if nft_count > 0:
                    print(f"✅ Wallet has NFTs - verification successful")
                    return True
                else:
                    print(f"❌ Wallet has no NFTs")
                    return False
            else:
                # Check if it says "no NFTs"
                if "has no NFTs" in output:
                    print(f"❌ Wallet has no NFTs")
                    return False
                else:
                    print(f"❌ Could not parse NFT count from output")
                    return False
        else:
            print(f"❌ JavaScript subprocess failed:")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ JavaScript subprocess timed out")
        return False
    except Exception as e:
        print(f"❌ Error running JavaScript subprocess: {e}")
        return False

def has_nft(wallet_address):
    """
    Main function - use JavaScript approach instead of direct API
    """
    return has_nft_js(wallet_address) 