from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import threading
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
import time

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
COLLECTION_ID = os.getenv("COLLECTION_ID")

# Flask app for webhook
app = Flask(__name__)

# Store pending verifications
user_pending_verification = {}

# Create bot application
bot_app = Application.builder().token(BOT_TOKEN).build()

async def auto_remove_unverified(user_id, username, context):
    """Auto-remove user if not verified within 5 minutes"""
    await asyncio.sleep(300)  # 5 minutes
    
    if user_id in user_pending_verification:
        try:
            await context.bot.ban_chat_member(GROUP_ID, user_id)
            await context.bot.unban_chat_member(GROUP_ID, user_id)
            
            # Log removal
            log_entry = {
                "timestamp": time.time(),
                "user_id": user_id,
                "username": username,
                "status": "removed",
                "reason": "timeout"
            }
            
            with open("analytics.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            print(f"❌ Removed @{username} (ID: {user_id}) - verification timeout")
            del user_pending_verification[user_id]
            
        except Exception as e:
            print(f"Error removing user: {e}")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members and send verification link"""
    if not update.message.new_chat_members:
        return
    
    for new_member in update.message.new_chat_members:
        if new_member.is_bot:
            continue
            
        user_id = new_member.id
        username = new_member.username or new_member.first_name
        
        # Create verification link - UPDATE THIS URL
        verify_link = f"https://testverify.netlify.app?tg_id={user_id}"

        try:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"""🎉 <b>Welcome to Meta Betties Private Key!</b>

👋 Hi @{username}, we're excited to have you join our exclusive community!

🔐 <b>Verification Required</b>
To access this private group, you must verify your NFT ownership.

🔗 <b>Click here to verify:</b> <a href="{verify_link}">Verify NFT Ownership</a>

⏰ <b>Time Limit:</b> You have 5 minutes to complete verification, or you'll be automatically removed.

💎 <b>Supported Wallets:</b> Phantom, Solflare, Backpack, Slope, Glow, Clover, Coinbase, Exodus, Brave, Torus, Trust Wallet

Need help? Contact an admin!""",
                parse_mode='HTML'
            )

            user_pending_verification[user_id] = username
            # Start auto-remove timer
            asyncio.create_task(auto_remove_unverified(user_id, username, context))
            
        except Exception as e:
            print(f"Error sending message to group: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is active!")

async def analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    # Only allow group admins
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text("❌ Only group admins can use this command.")
        return
    try:
        with open("analytics.json") as f:
            lines = f.readlines()
        total_verified = sum(1 for l in lines if json.loads(l)["status"] == "verified")
        total_removed = sum(1 for l in lines if json.loads(l)["status"] == "removed")
        recent = [json.loads(l) for l in lines[-10:]]
        msg = f"📊 Group Analytics:\nTotal verified: {total_verified}\nTotal removed: {total_removed}\n\nRecent activity:\n"
        for entry in recent:
            from datetime import datetime
            t = datetime.fromtimestamp(entry["timestamp"]).strftime('%Y-%m-%d %H:%M')
            msg += f"@{entry['username']} - {entry['status']} ({t})\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error reading analytics: {e}")

# Webhook endpoints
@app.route('/verify_callback', methods=['POST'])
def verify_callback():
    """Receive verification results from API server"""
    try:
        data = request.json
        tg_id = data.get('tg_id')
        has_nft = data.get('has_nft')
        username = data.get('username', f'user_{tg_id}')
        
        if tg_id in user_pending_verification:
            if has_nft:
                # Log successful verification
                log_entry = {
                    "timestamp": time.time(),
                    "user_id": tg_id,
                    "username": username,
                    "status": "verified",
                    "reason": "nft_verified"
                }
                
                with open("analytics.json", "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
                
                print(f"✅ User @{username} (ID: {tg_id}) verified successfully")
                del user_pending_verification[tg_id]
            else:
                # Remove user if no NFT
                try:
                    asyncio.run(bot_app.bot.ban_chat_member(GROUP_ID, tg_id))
                    asyncio.run(bot_app.bot.unban_chat_member(GROUP_ID, tg_id))
                    
                    log_entry = {
                        "timestamp": time.time(),
                        "user_id": tg_id,
                        "username": username,
                        "status": "removed",
                        "reason": "no_nft"
                    }
                    
                    with open("analytics.json", "a") as f:
                        f.write(json.dumps(log_entry) + "\n")
                    
                    print(f"❌ Removed @{username} (ID: {tg_id}) - no required NFT")
                    del user_pending_verification[tg_id]
                    
                except Exception as e:
                    print(f"Error removing user: {e}")
        
        return jsonify({"status": "success", "message": "Verification result logged"})
        
    except Exception as e:
        print(f"Error in verify_callback: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "bot-server"})

def run_bot():
    """Run the bot in a separate thread"""
    # Add handlers
    bot_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("analytics", analytics))
    
    # Add error handler
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"Exception while handling an update: {context.error}")
    
    bot_app.add_error_handler(error_handler)
    
    print("🤖 Bot running...")
    
    try:
        print("🤖 Starting bot with conflict protection...")
        
        # Clear any pending updates first
        try:
            asyncio.run(bot_app.bot.delete_webhook(drop_pending_updates=True))
            print("✅ Webhook cleared successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not clear webhook: {e}")
        
        # Add a small delay to ensure webhook is cleared
        time.sleep(2)
        
        print("🔄 Starting polling with conflict protection...")
        bot_app.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30,
            bootstrap_retries=5,
            close_loop=False
        )
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == '__main__':
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.getenv("PORT", 5000))
    print(f"🌐 Webhook server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False) 