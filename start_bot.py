#!/usr/bin/env python3
"""
Bot Startup Script - Prevents conflicts and ensures safe startup
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def check_for_conflicts():
    """Check if another bot instance is running"""
    print("🔍 Checking for conflicts...")
    
    # Check for lock file
    lock_file = "bot_server.lock"
    if os.path.exists(lock_file):
        print(f"❌ Lock file {lock_file} exists!")
        print("💡 Another bot instance might be running.")
        
        # Try to read PID from lock file
        try:
            with open(lock_file, 'r') as f:
                pid = f.read().strip()
                print(f"📊 Lock file PID: {pid}")
        except:
            print("⚠️ Could not read lock file PID")
        
        # Ask user what to do
        response = input("🗑️ Delete lock file and continue? (y/N): ").lower()
        if response == 'y':
            try:
                os.remove(lock_file)
                print("✅ Lock file removed")
                return True
            except Exception as e:
                print(f"❌ Error removing lock file: {e}")
                return False
        else:
            print("💡 Exiting...")
            return False
    
    print("✅ No conflicts detected")
    return True

def kill_existing_processes():
    """Kill any existing Python processes that might be running the bot"""
    print("🔪 Checking for existing Python processes...")
    
    try:
        # Find Python processes
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        bot_processes = []
        for line in lines:
            if 'python' in line.lower() and ('bot.py' in line or 'bot_server' in line):
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    bot_processes.append(pid)
                    print(f"🔍 Found bot process: PID {pid}")
        
        if bot_processes:
            print(f"⚠️ Found {len(bot_processes)} existing bot processes")
            response = input("🔪 Kill existing processes? (y/N): ").lower()
            if response == 'y':
                for pid in bot_processes:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"✅ Killed process {pid}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"❌ Error killing process {pid}: {e}")
            else:
                print("💡 Keeping existing processes")
        else:
            print("✅ No existing bot processes found")
            
    except Exception as e:
        print(f"⚠️ Error checking processes: {e}")

def start_bot():
    """Start the bot safely"""
    print("🚀 Starting bot...")
    
    try:
        # Start the bot
        subprocess.run([sys.executable, 'bot.py'])
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

def main():
    """Main startup function"""
    print("🤖 Bot Startup Script")
    print("=" * 50)
    
    # Check for conflicts
    if not check_for_conflicts():
        sys.exit(1)
    
    # Kill existing processes if needed
    kill_existing_processes()
    
    # Wait a moment
    print("⏳ Waiting 3 seconds...")
    time.sleep(3)
    
    # Start the bot
    start_bot()

if __name__ == "__main__":
    main() 