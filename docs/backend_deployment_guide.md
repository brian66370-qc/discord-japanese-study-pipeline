# kotoba-flow Backend and Deployment Guide

This guide summarizes how to configure kotoba-flow on the Discord side, run the bot locally, and deploy it to the cloud.

## Scope

This project includes:

- `bot/private_reader_bot.py`
- `bot/export_channel.py`
- `parser/normalize.py`
- `parser/build_notebooklm_files.py`

The intended workflow is:

1. Create and configure a Discord bot in Developer Portal
2. Invite the bot to your server with the correct permissions
3. Store the bot token and Discord IDs in `.env`
4. Start the bot locally or on a cloud service
5. Export channel messages into JSON
6. Normalize the export and build NotebookLM-ready Markdown

---

## 1. Discord Developer Portal Setup

### Step 1: Create the application and bot

1. Open [Discord Developer Portal](https://discord.com/developers/applications)
2. Click `New Application`
3. Give it a name such as `Japanese Study Exporter`
4. Open the `Bot` tab
5. Click `Add Bot`
6. Copy the bot token and store it in `.env` as `DISCORD_BOT_TOKEN`

Important notes:

- Treat the token like a password
- If the token leaks, use `Reset Token`
- Never commit the real token to GitHub

### Step 2: Enable privileged intent

This bot reads message text, so you must enable:

- `MESSAGE CONTENT INTENT`

Path:

- `Bot` -> `Privileged Gateway Intents`

You do not need these for this project:

- `SERVER MEMBERS INTENT`
- `PRESENCE INTENT`

### Step 3: Collect Discord IDs

You will need:

- `Client ID`
  Used for the OAuth2 invite URL
- `Guild ID`
  Your server ID, used as `DISCORD_GUILD_ID`
- `Allowed User ID`
  Your user ID, used in `DISCORD_ALLOWED_USER_IDS`
- `Channel ID`
  Optional for the CLI exporter script

To enable Developer Mode in Discord:

1. Open `User Settings`
2. Open `Advanced`
3. Turn on `Developer Mode`

Then:

- Right-click the server name -> `Copy Server ID`
- Right-click your user profile -> `Copy User ID`
- Right-click a channel -> `Copy Channel ID`

---

## 2. Bot Permissions

Recommended permissions for this repo:

- `View Channel`
- `Read Message History`
- `Send Messages`
- `Use Application Commands`

If the target is a private channel or private thread:

- the bot must be added to that channel
- the bot must be granted access there explicitly

You do not need broad permissions like:

- `Administrator`
- `Manage Channels`
- `Manage Messages`
- `Mention Everyone`

---

## 3. OAuth2 Invite URL

### Generate the URL in Developer Portal

1. Open `OAuth2`
2. Open `URL Generator`
3. In `Scopes`, enable:
   - `bot`
   - `applications.commands`
4. In `Bot Permissions`, enable:
   - `View Channel`
   - `Read Message History`
   - `Send Messages`
   - `Use Application Commands`
5. Copy the generated URL and open it in your browser
6. Add the bot to your server

The URL will look like this:

```text
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot%20applications.commands&permissions=GENERATED_PERMISSION_INTEGER
```

Use the Portal generator instead of manually editing permission values.

---

## 4. Local Environment Variables

Create `.env` with these values:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=123456789012345678
DISCORD_CHANNEL_ID=123456789012345678
DISCORD_ALLOWED_USER_IDS=123456789012345678,234567890123456789
```

What they mean:

- `DISCORD_BOT_TOKEN`
  Your Discord bot token
- `DISCORD_GUILD_ID`
  The server where slash commands will be registered
- `DISCORD_CHANNEL_ID`
  Optional default channel for `bot/export_channel.py`
- `DISCORD_ALLOWED_USER_IDS`
  Users allowed to run export commands

The private slash-command bot mainly requires:

- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- `DISCORD_ALLOWED_USER_IDS`

---

## 5. Run the Bot Locally

### Step 1: Install dependencies

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: Create `.env`

```powershell
Copy-Item .env.example .env
```

Then fill in your real values.

### Step 3: Start the bot

```powershell
python bot/private_reader_bot.py
```

If successful, you should see something like:

```text
Private reader bot logged in as YourBotName#0000 (123456789012345678)
```

### Step 4: Test slash commands in Discord

Try:

- `/whoami`
- `/export_status`
- `/export_here`
- `/export_here full_export:true`

### Step 5: Process the export

```powershell
python parser/normalize.py --input data/raw/exports/YOUR_EXPORT.json --output data/normalized/normalized_entries.json
python parser/build_notebooklm_files.py --input data/normalized/normalized_entries.json --output-dir data/notebooklm
```

Output locations:

- raw exports: `data/raw/exports/`
- export checkpoints: `data/raw/export_state.json`
- normalized entries: `data/normalized/normalized_entries.json`
- NotebookLM files: `data/notebooklm/`

---

## 6. Common Troubleshooting

### Missing required environment variable

Possible causes:

- `.env` does not exist
- variable names are wrong
- command is not being run from the project root

Fix:

1. Confirm `.env` exists
2. Confirm all required variables are filled in
3. Run the command from the repo root

### Slash commands do not appear

Possible causes:

- `DISCORD_GUILD_ID` is wrong
- bot is not in the correct server
- bot was invited without `applications.commands`

Fix:

1. Check `DISCORD_GUILD_ID`
2. Confirm the bot is in the target server
3. Re-invite the bot with the correct scopes
4. Restart the bot and wait a short moment

### `PrivilegedIntentsRequired`

Cause:

- `MESSAGE CONTENT INTENT` is not enabled in Developer Portal

Fix:

1. Open `Bot` in Developer Portal
2. Enable `MESSAGE CONTENT INTENT`
3. Save changes
4. Restart the bot

### `/export_here` returns no messages

Possible causes:

- bot cannot access the private channel
- bot lacks `View Channel`
- bot lacks `Read Message History`
- an export checkpoint already points to the latest message

Fix:

1. Confirm the bot can see the target channel
2. Confirm the bot has the required permissions
3. Run `/export_status`
4. If needed, run `/export_here full_export:true`

### Cloud deployment loses checkpoint state

Cause:

- the platform uses ephemeral storage

Fix:

- use persistent disk or volume storage
- keep `data/raw/export_state.json` on persistent storage

---

## 7. Cloud Deployment

This bot is a long-running process. It is not a webhook app and not a cron job.

Good cloud targets:

- Render Background Worker
- Railway service
- VPS

### Option A: Render Background Worker

Recommended when you want:

- GitHub-based deployment
- always-on background process
- optional persistent disk

Suggested settings:

- Build Command:

```text
pip install -r requirements.txt
```

- Start Command:

```text
python bot/private_reader_bot.py
```

Environment variables:

- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- `DISCORD_CHANNEL_ID`
- `DISCORD_ALLOWED_USER_IDS`
- optional `PYTHON_VERSION`

Important:

- if you want export checkpoints to survive restarts, mount persistent storage for `data/`

### Option B: Railway

Recommended when you want:

- fast GitHub deployment
- simple environment variable setup
- persistent volume support

Suggested settings:

- Start Command:

```text
python bot/private_reader_bot.py
```

- Build Command:

```text
pip install -r requirements.txt
```

Environment variables:

- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- `DISCORD_CHANNEL_ID`
- `DISCORD_ALLOWED_USER_IDS`

If you use checkpoints in production, persist the `data/` directory.

### Avoid plain static web hosting

This project is not a static site and not a short-lived function. It needs a long-running process.

---

## 8. Rebuilding From GitHub

If you delete your local files, you can rebuild from GitHub.

### Step 1: Clone the repo

```powershell
git clone YOUR_GITHUB_REPO_URL
cd Discord_chat
```

### Step 2: Install dependencies

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3: Recreate `.env`

```powershell
Copy-Item .env.example .env
```

Then fill in:

- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- `DISCORD_CHANNEL_ID`
- `DISCORD_ALLOWED_USER_IDS`

### Step 4: Confirm Discord bot setup

If the Discord application still exists:

- reuse the same bot token and settings

If the Discord application was deleted:

1. create a new Discord application
2. add a new bot
3. enable `MESSAGE CONTENT INTENT`
4. generate a new invite URL
5. invite the new bot to your server
6. update `.env` with the new token

### Step 5: Start and test

```powershell
python bot/private_reader_bot.py
```

Then in Discord:

- `/whoami`
- `/export_status`
- `/export_here`

---

## Summary

The shortest setup flow is:

1. Create a bot in Discord Developer Portal
2. Enable `Message Content Intent`
3. Invite the bot to your server with the correct OAuth2 scopes
4. Fill in `.env`
5. Start the bot
6. Run `/export_here`
7. Normalize the export
8. Build NotebookLM files
