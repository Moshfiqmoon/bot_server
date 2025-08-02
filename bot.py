import os
import asyncio
import time
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import threading

load_dotenv()

# Environment variables - Fixed names
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Changed from BOT_TOKEN
GROUP_ID = os.getenv("TELEGRAM_GROUP_ID")    # Changed from GROUP_ID
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "6873bd5e-0b5d-49c4-a9ab-4e7febfd9cd3")
COLLECTION_ID = os.getenv("COLLECTION_ID", "j7qeFNnpWTbaf5g9sMCxP2zfKrH5QFgE56SuYjQDQi1")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://api-server-wcjc.onrender.com/api/verify-nft")

# Check if required environment variables are se

if not GROUP_ID:
    print("❌ TELEGRAM_GROUP_ID not found in environment variables!")
    print("💡 Please set TELEGRAM_GROUP_ID in your environment")
    GROUP_ID = "test_group"  # Fallback for testing

print(f"🤖 Bot Configuration:")
print(f"  📱 TELEGRAM_BOT_TOKEN: {'✅ Set' if BOT_TOKEN != 'test_token' else '❌ Missing'}")
print(f"  👥 TELEGRAM_GROUP_ID: {'✅ Set' if GROUP_ID != 'test_group' else '❌ Missing'}")

user_pending_verification = {}

# Flask app for webhook
flask_app = Flask(__name__)

async def auto_remove_unverified(user_id, username, context):
    """Auto-remove user if not verified within 5 minutes"""
    await asyncio.sleep(300)  # 5 minutes
    
    if user_id in user_pending_verification:
        try:
            await context.bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            await context.bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            
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
    try:
        print(f"🔔 Welcome function triggered")
        print(f"📝 Update message: {update.message}")
        print(f"👥 New chat members: {update.message.new_chat_members if update.message.new_chat_members else 'None'}")
        print(f"🏠 Chat ID: {update.message.chat.id}")
        print(f"🎯 Target GROUP_ID: {GROUP_ID}")
        
        # Check if this is the correct group
        if str(update.message.chat.id) != str(GROUP_ID):
            print(f"❌ Wrong group - expected {GROUP_ID}, got {update.message.chat.id}")
            return
        
        if not update.message.new_chat_members:
            print("❌ No new chat members found")
            return
        
        for new_member in update.message.new_chat_members:
            print(f"👤 Processing new member: {new_member.username or new_member.first_name} (ID: {new_member.id})")
            
            if new_member.is_bot:
                print("🤖 Skipping bot member")
                continue
                
            user_id = new_member.id
            username = new_member.username or new_member.first_name
            
            print(f"✅ Processing human member: @{username} (ID: {user_id})")
            
            # Check if user is already pending verification
            if user_id in user_pending_verification:
                print(f"⚠️ User @{username} already pending verification")
                return
            
            # Create verification link - UPDATE THIS URL
            verify_link = f"https://admin-q2j7.onrender.com/?tg_id={user_id}"
            print(f"🔗 Verification link: {verify_link}")

            try:
                print(f"📤 Sending welcome message to group {GROUP_ID}")
                
                # Create welcome message
                welcome_text = f"""🎉 <b>Welcome to Meta Betties Private Key!</b>

👋 Hi @{username}, we're excited to have you join our exclusive community!

🔐 <b>Verification Required</b>
To access this private group, you must verify your NFT ownership.

🔗 <b>Click here to verify:</b> <a href="{verify_link}">Verify NFT Ownership</a>

📋 <b>Or copy this link:</b>
<code>{verify_link}</code>

⏰ <b>Time Limit:</b> You have 5 minutes to complete verification, or you'll be automatically removed.

💎 <b>Supported Wallets:</b> Phantom, Solflare, Backpack, Slope, Glow, Clover, Coinbase, Exodus, Brave, Torus, Trust Wallet, Zerion

Need help? Contact an admin!"""

                # Send message to group
                sent_message = await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=welcome_text,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                
                print(f"✅ Welcome message sent successfully to @{username}")
                print(f"📄 Message ID: {sent_message.message_id}")

                # Add user to pending verification
                user_pending_verification[user_id] = username
                print(f"⏰ Started 5-minute timer for @{username}")
                print(f"📊 Pending verifications: {len(user_pending_verification)}")
                
                # Start auto-remove timer
                asyncio.create_task(auto_remove_unverified(user_id, username, context))
                
            except Exception as e:
                print(f"❌ Error sending message to group: {e}")
                print(f"🔍 Error details: {type(e).__name__}: {str(e)}")
                print(f"🔍 Error traceback:")
                import traceback
                traceback.print_exc()
                
                # Try to send a simpler message as fallback
                try:
                    fallback_message = f"👋 Welcome @{username}! Please verify your NFT ownership to stay in this group."
                    await context.bot.send_message(
                        chat_id=GROUP_ID,
                        text=fallback_message,
                        parse_mode='HTML'
                    )
                    print(f"✅ Fallback message sent to @{username}")
                except Exception as fallback_error:
                    print(f"❌ Even fallback message failed: {fallback_error}")
                    
    except Exception as e:
        print(f"❌ Critical error in welcome function: {e}")
        print(f"🔍 Error details: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text("✅ Bot is active!")

async def test_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test function to check if bot is responding"""
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        print(f"🧪 Test message received from @{user.username or user.first_name}")
        print(f"📝 Chat ID: {chat.id}")
        print(f"👤 User ID: {user.id}")
        
        # Send test response
        await update.message.reply_text("✅ Bot is working! Test message received.")
        
        # Also send to group if it's a group chat
        if chat.type in ['group', 'supergroup']:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"🧪 Test: Bot is responding to messages in this group!"
            )
            
    except Exception as e:
        print(f"❌ Error in test_message: {e}")
        await update.message.reply_text("❌ Bot test failed. Check logs.")

async def analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /analytics command"""
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
@flask_app.route('/verify_callback', methods=['POST'])
def verify_callback():
    """Receive verification results from API server"""
    try:
        data = request.json
        tg_id = data.get('tg_id')
        has_nft = data.get('has_nft')
        username = data.get('username', f'user_{tg_id}')
        
        print(f"🔍 Verification callback received:")
        print(f"  👤 User ID: {tg_id}")
        print(f"  👤 Username: {username}")
        print(f"  🎨 Has NFT: {has_nft}")
        
        if tg_id in user_pending_verification:
            if has_nft:
                # User has NFT - keep them in group
                try:
                    # Send success message to group
                    success_message = f"""✅ <b>Verification Successful!</b>

🎉 Congratulations @{username}! 

💎 You have been verified as an NFT holder and now have full access to this private group.

🔐 <b>Access Granted:</b> You can now participate in all discussions and access exclusive content.

Welcome to the Meta Betties community! 🚀"""

                    asyncio.run(app.bot.send_message(
                        chat_id=GROUP_ID,
                        text=success_message,
                        parse_mode='HTML'
                    ))
                    
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
                    
                    print(f"✅ User @{username} (ID: {tg_id}) verified successfully - KEPT IN GROUP")
                    del user_pending_verification[tg_id]
                    
                except Exception as e:
                    print(f"❌ Error sending success message: {e}")
                    
            else:
                # User has no NFT - remove them from group
                try:
                    # Send removal message to group
                    removal_message = f"""❌ <b>Verification Failed</b>

😔 Sorry @{username}, your verification was unsuccessful.

🚫 <b>Access Denied:</b> You do not have the required NFT to access this private group.

💎 <b>Requirements:</b> You must own the required NFT collection to join this group.

You will be removed from the group now."""

                    asyncio.run(app.bot.send_message(
                        chat_id=GROUP_ID,
                        text=removal_message,
                        parse_mode='HTML'
                    ))
                    
                    # Remove user from group
                    asyncio.run(app.bot.ban_chat_member(GROUP_ID, tg_id))
                    asyncio.run(app.bot.unban_chat_member(GROUP_ID, tg_id))
                    
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
                    print(f"❌ Error removing user: {e}")
        else:
            print(f"⚠️ User {tg_id} not in pending verification list")
        
        return jsonify({"status": "success", "message": "Verification result processed"})
        
    except Exception as e:
        print(f"❌ Error in verify_callback: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@flask_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "bot-server"})

# Create app and add handler
app = ApplicationBuilder().token(BOT_TOKEN).build()

print("🤖 Setting up bot handlers...")

# Add handlers
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("analytics", analytics))
app.add_handler(CommandHandler("test", test_message))  # Add test command

# Add message handler for all text messages
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, test_message))

print("✅ Bot handlers added successfully")

# Add error handling for conflicts
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot"""
    print(f"❌ Exception while handling an update: {context.error}")
    print(f"🔍 Error details: {type(context.error).__name__}: {str(context.error)}")
    import traceback
    traceback.print_exc()

app.add_error_handler(error_handler)
print("✅ Error handler added successfully")

print("🤖 Bot running...")

# Start the bot with error handling
try:
    print("🤖 Starting bot with conflict protection...")
    
    # Clear any pending updates first
    try:
        app.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook cleared successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not clear webhook: {e}")
    
    # Add a small delay to ensure webhook is cleared
    time.sleep(2)
    
    print("🔄 Starting polling with conflict protection...")
    app.run_polling(
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
    print("💡 Please make sure only one bot instance is running.")
    print("💡 Try stopping all Python processes and restart.")
    print("💡 If problem persists, try restarting your computer.")
    print("💡 You can also try using a different bot token temporarily.")
    print("💡 Check if another bot instance is running in another terminal.")

def run_flask():
    """Run Flask server in a separate thread"""
    port = int(os.getenv("PORT", 5000))
    print(f"🌐 Webhook server starting on port {port}")
    flask_app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start the bot
    print("🤖 Starting bot with webhook support...") 
