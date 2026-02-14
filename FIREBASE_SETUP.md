# Firebase Setup Guide for AXL Bot

## Overview
The bot has been migrated from SQLite to Firebase Realtime Database for real-time, scalable data storage.

## Prerequisites
- Firebase project (create at https://console.firebase.google.com)
- Service Account credentials JSON file

## Setup Steps

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Add Project"
3. Enter a project name (e.g., "axl-bot")
4. Enable Google Analytics (optional)
5. Create the project

### 2. Create Realtime Database
1. In Firebase Console, go to **Build** → **Realtime Database**
2. Click **Create Database**
3. Choose your database location (closest to your deployment)
4. Start in **Test Mode** for development
5. Copy the database URL - you'll need this

### 3. Generate Service Account Key
1. In Firebase Console, go to **Project Settings** (gear icon)
2. Go to **Service Accounts** tab
3. Click **Generate New Private Key**
4. Save the JSON file securely

### 4. Set Environment Variables

Extract these values from your service account JSON file:

```bash
# In your deployment environment (Koyeb, VPS, Docker, etc.), set:

FIREBASE_PROJECT_ID="your-project-id"
FIREBASE_PRIVATE_KEY_ID="your-private-key-id"
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL="your-email@appspot.gserviceaccount.com"
FIREBASE_CLIENT_ID="your-client-id"
FIREBASE_DB_URL="https://your-project-id.firebaseio.com"
BOT_TOKEN="your-telegram-bot-token"
OWNER_ID="your-telegram-user-id"
```

**Important:** When setting `FIREBASE_PRIVATE_KEY` in environment variables:
- Include the literal `\n` characters (not actual newlines)
- Or use the raw private key with actual newlines (escaping depends on your platform)

### 5. Local Development Setup

Create a `.env` file in your project root:

```bash
BOT_TOKEN=your_token_here
OWNER_ID=your_id_here
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=service-account@appspot.gserviceaccount.com
FIREBASE_CLIENT_ID=000000000000
FIREBASE_DB_URL=https://your-project-id.firebaseio.com
```

### 6. Deploy on Koyeb

1. Update your `koyeb.yml` with Firebase credentials in environment variables
2. The config already has `instances: min: 1, max: 1` to prevent multiple polling instances
3. Set environment variables in Koyeb dashboard:
   - **Settings** → **Environment variables**
   - Add all Firebase variables from step 4

### 7. Database Structure

Firebase will automatically create this structure:

```
- users/
  - {user_id}/
    - user_id: INTEGER
    - username: STRING
    - balance: INTEGER
    - is_dead: INTEGER (0 or 1)
    - is_premium: INTEGER (0 or 1)
    - protect_until: INTEGER (Unix timestamp)
    - last_daily: INTEGER (Unix timestamp)
```

### 8. Security Rules (Optional but Recommended)

In Firebase Console, go to **Realtime Database** → **Rules** and set:

```json
{
  "rules": {
    "users": {
      ".read": false,
      ".write": false
    }
  }
}
```

This restricts direct access to the database. Only your bot service account can read/write.

## Troubleshooting

### "Firebase credentials not configured"
- Check all environment variables are set correctly
- Verify `FIREBASE_DB_URL` is in format: `https://project-id.firebaseio.com`
- Check private key includes `\n` characters, not actual newlines

### "Multiple instances running" error
- This is now fixed! `koyeb.yml` has `instances: min: 1, max: 1`
- If still seeing error, verify Koyeb deployment only has 1 replica

### Database connection fails
- Verify service account email is set in Firebase
- Check database security rules allow service account access
- Ensure database is in Test Mode or has proper rules

## Commands to Test

After setup, test with these commands:
```
/daily    - Claim daily coins
/balance  - Check your balance
/leaderboard - See top players
/send <amount> (reply to user) - Transfer coins
```

## Important Notes

- All user balance operations are atomic and thread-safe
- Firebase Realtime Database handles concurrent requests
- No more SQLite file needed locally
- Premium users get free daily rewards and protection
