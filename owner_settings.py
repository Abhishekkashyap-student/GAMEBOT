"""
Owner-only customization system for AXL BOT
Allows the bot owner to customize bot behavior
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

SETTINGS_FILE = Path(__file__).resolve().parent / "bot_settings.json"


class BotSettings:
    """Manage owner-customizable bot settings"""
    
    DEFAULT_SETTINGS = {
        # Game settings
        "daily_reward": 500,
        "revive_cost": 200,
        "protect_cost": 200,
        "kill_reward_min": 90,
        "kill_reward_max": 150,
        "max_bet": 10000,
        "min_bet": 1,
        
        # Rates
        "steal_success_rate": 0.5,  # 50%
        "steal_min_percent": 0.05,  # 5%
        "steal_max_percent": 0.30,  # 30%
        
        # UI
        "ui_theme": "professional",
        "use_decorative_borders": True,
        "use_emojis": True,
        
        # Features
        "auto_register_groups": False,
        "premium_users_bypass_login": True,
        "allow_dead_users_act": False,  # Only premium can act while dead
        
        # Economy
        "prevent_negative_balance": True,
        "atomic_transfers": True,
        
        # Cooldowns (in seconds)
        "daily_cooldown": 86400,  # 24 hours
        "protect_duration": 86400,  # 24 hours
        
        # Branding
        "bot_name": "AXL GAME BOT",
        "owner_mention": "@vfriendschat",
    }
    
    def __init__(self):
        """Load settings from file or create with defaults"""
        self.settings = self.load()
    
    def load(self) -> Dict[str, Any]:
        """Load settings from file, or return defaults if not found"""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Return defaults
        return self.DEFAULT_SETTINGS.copy()
    
    def save(self):
        """Save settings to file"""
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception:
            return False
    
    def get(self, key: str, default=None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a setting value (for owner only)"""
        if key not in self.DEFAULT_SETTINGS:
            return False  # Unknown setting
        
        # Type checking
        expected_type = type(self.DEFAULT_SETTINGS[key])
        if not isinstance(value, expected_type):
            return False
        
        # Range checking for certain values
        if key == "daily_reward" and value <= 0:
            return False
        if key == "max_bet" and value <= 0:
            return False
        if key == "steal_success_rate" and not (0 <= value <= 1):
            return False
        
        self.settings[key] = value
        return self.save()
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        return self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings (for info display)"""
        return self.settings.copy()
    
    def to_string(self) -> str:
        """Format settings as readable string"""
        lines = ["⚙️ BOT SETTINGS\n"]
        lines.append("=" * 40)
        
        for key, value in self.settings.items():
            # Format the key nicely
            display_key = key.replace("_", " ").title()
            lines.append(f"• {display_key}: {value}")
        
        return "\n".join(lines)


# Global settings instance
settings = BotSettings()


async def cmd_settings(update, context):
    """Owner-only command to view/change settings"""
    from telegram import Update
    from telegram.ext import ContextTypes
    import os
    
    if update.effective_user is None:
        return
    
    owner_id = int(os.environ.get("OWNER_ID", "0"))
    if update.effective_user.id != owner_id:
        await update.message.reply_text("⛔ Owner only!")
        return
    
    if not context.args:
        # Show current settings
        text = settings.to_string()
        await update.message.reply_text(text)
    else:
        # Change a setting
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /settings <setting_name> <value>\n"
                "Example: /settings max_bet 5000"
            )
            return
        
        key = context.args[0].lower()
        value_str = context.args[1]
        
        # Try to parse value as integer or float
        try:
            if "." in value_str:
                value = float(value_str)
            else:
                value = int(value_str)
        except ValueError:
            # Try as string (for ui_theme, bot_name, etc)
            value = value_str
        
        if settings.set(key, value):
            await update.message.reply_text(
                f"✅ Setting updated!\n"
                f"{key} = {value}\n\n"
                f"Use /settings to see all settings."
            )
        else:
            await update.message.reply_text(
                f"❌ Failed to update setting '{key}'\n"
                f"Check the value is valid."
            )
