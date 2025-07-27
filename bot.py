import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv
from verifier import has_nft
import json

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

user_pending_verification = {}

async def auto_remove_unverified(user_id, username, context):
    await asyncio.sleep(300)  # 5 minutes
    if user_id in user_pending_verification:
        try:
            await context.bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            await context.bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"❌ <b>User Removed</b>\n\n👤 @{username} was automatically removed for not completing NFT verification within the 5-minute time limit.\n\n💡 To rejoin, please verify your NFT ownership first.",
                parse_mode='HTML'
            )
            del user_pending_verification[user_id]
        except Exception as e:
            print(f"Error removing user {user_id}: {e}")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id == GROUP_ID:
        user_id = update.message.from_user.id
        username = update.message.from_user.username
        
        # Check if user is already pending verification
        if user_id in user_pending_verification:
            return  # Don't send duplicate messages

        # Create verification link - UPDATE THIS URL
        verify_link = f"https://dancing-lollipop-fc680a.netlify.app/?tg_id={user_id}"

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

# Create app and add handler
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("analytics", analytics))

print("🤖 Bot running...")

# Add error handling for conflicts
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot"""
    print(f"Exception while handling an update: {context.error}")

app.add_error_handler(error_handler)

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
    import time
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
