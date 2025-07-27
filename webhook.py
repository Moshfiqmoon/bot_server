from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/verify_callback', methods=['POST'])
def verify_callback():
    try:
        data = request.json
        tg_id = data.get('tg_id')
        has_nft = data.get('has_nft')
        username = data.get('username', f'user_{tg_id}')
        
        # Log the verification result
        log_entry = {
            "timestamp": datetime.now().timestamp(),
            "tg_id": tg_id,
            "username": username,
            "has_nft": has_nft,
            "status": "verified" if has_nft else "removed"
        }
        
        with open("analytics.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        print(f"Verification result logged: {log_entry}")
        
        return jsonify({"status": "success", "message": "Verification result logged"})
        
    except Exception as e:
        print(f"Error in verify_callback: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "webhook"})

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 