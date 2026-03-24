# kotoba-flow

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Discord Bot](https://img.shields.io/badge/Discord-Bot-5865F2.svg)](https://discord.com/developers/docs/intro)
[![NotebookLM Ready](https://img.shields.io/badge/NotebookLM-Ready-34A853.svg)](https://notebooklm.google/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

Turn a Discord study channel into structured Japanese learning data with kotoba-flow.

This project helps you export Japanese vocabulary and grammar notes from Discord, keep incremental checkpoints, normalize raw messages into study entries, and generate NotebookLM-ready Markdown for summaries, quizzes, and future review tools.

## Screenshots

### Discord export command

![Discord export command](docs/images/discord_export_command.png)

### Bot response

![Bot response](docs/images/discord_export_result.png)

### Raw JSON export

![Raw JSON export](docs/images/raw_export_json.png)

### NotebookLM-ready files

![NotebookLM-ready files](docs/images/notebooklm_files.png)

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python bot/private_reader_bot.py
```

Inside Discord, run:

- `/export_here`
- `/export_status`

Then process the exported file:

```powershell
python parser/normalize.py --input data/raw/exports/your_export.json --output data/normalized/normalized_entries.json
python parser/build_notebooklm_files.py --input data/normalized/normalized_entries.json --output-dir data/notebooklm
```

## Simple Workflow

1. Create a bot in Discord Developer Portal.
2. Enable the required bot settings, especially `Message Content Intent`.
3. Invite the bot to your server with the correct OAuth2 scopes and permissions.
4. Put the bot token and Discord IDs into your local `.env`.
5. Start the bot from your terminal.
6. Run `/export_here` in the target Discord channel.
7. Export the messages into a JSON file, then process them with the parser.

Full implementation guide:

- [docs/backend_deployment_guide.md](docs/backend_deployment_guide.md)

## English

### Overview

This project helps you:

- export messages from a Discord channel with a bot
- keep incremental checkpoints for each channel
- normalize Japanese learning notes into structured entries
- generate Markdown files for NotebookLM
- prepare data for future review apps or flashcards

### Features

- private channel export with slash commands
- incremental export with per-channel checkpoints
- full re-export when needed
- raw JSON archive output
- starter parser for vocabulary and grammar notes
- NotebookLM-friendly Markdown generation

### Slash Commands

- `/export_here`
  Export only new messages since the last checkpoint
- `/export_here full_export:true`
  Export the whole channel again
- `/export_status`
  Show the saved checkpoint for the current channel
- `/export_reset_here`
  Reset the checkpoint for the current channel
- `/whoami`
  Show your Discord user ID

### Required Discord Settings

- Bot permissions:
  - `View Channel`
  - `Read Message History`
  - `Send Messages`
  - `Use Application Commands`
- Developer Portal:
  - enable `Message Content Intent`

### Basic Workflow

1. Create a bot in Discord Developer Portal.
2. Enable the required intents and bot settings.
3. Invite the bot to your server.
4. Add the bot token and Discord IDs to `.env`.
5. Start the bot locally from your terminal.
6. Run `/export_here` in the target channel.
7. Save the export as JSON and continue with normalization.

## 中文

### 專案用途

這個專案用來把 Discord 頻道中的日文單字與文法筆記整理成可複習資料。

你可以用它：

- 用 bot 匯出 Discord 頻道訊息
- 記住每個頻道的上次匯出位置，做增量匯出
- 把原始訊息轉成結構化學習條目
- 產生適合餵給 NotebookLM 的 Markdown
- 為之後的複習軟體或單字卡做準備

### 簡單流程

1. 在 Discord Developer Portal 建立 bot
2. 開啟需要的設定，尤其是 `Message Content Intent`
3. 用正確的 OAuth2 scope 和權限把 bot 邀請進 server
4. 把 bot token 和 Discord 相關 ID 填進本機 `.env`
5. 在終端機啟動 bot
6. 回到指定頻道執行 `/export_here`
7. 匯出成 JSON 後再交給 parser 處理

### 主要功能

- 私人頻道 slash command 匯出
- 頻道級 checkpoint 增量匯出
- 可重新完整匯出
- 保留原始 JSON 匯出檔
- 基礎單字與文法解析
- 生成 NotebookLM 可讀 Markdown

### Slash Commands

- `/export_here`
  只匯出上次之後新增的訊息
- `/export_here full_export:true`
  忽略 checkpoint，重新完整匯出
- `/export_status`
  查看目前頻道的匯出記錄點
- `/export_reset_here`
  清除目前頻道的匯出記錄點
- `/whoami`
  顯示你的 Discord 使用者 ID

### Discord 端需求

- Bot 權限：
  - `View Channel`
  - `Read Message History`
  - `Send Messages`
  - `Use Application Commands`
- Developer Portal：
  - 開啟 `Message Content Intent`

## Project Structure

```text
bot/
  export_channel.py
  private_reader_bot.py
parser/
  normalize.py
  build_notebooklm_files.py
data/
  raw/
  normalized/
  notebooklm/
docs/
  images/
```

## Output Files

- `data/raw/exports/`
  Raw Discord channel exports
- `data/raw/export_state.json`
  Incremental export checkpoints
- `data/normalized/normalized_entries.json`
  Structured study entries
- `data/notebooklm/`
  Markdown files ready for NotebookLM

## Example Files

Safe example outputs are included in `examples/`:

- `examples/sample_export.json`
- `examples/sample_normalized_entries.json`
- `examples/sample_notebooklm_vocab.md`
- `examples/sample_notebooklm_grammar.md`

These are small demonstration files for GitHub readers and do not contain your private Discord data.

## Roadmap

- Improve grammar detection and extraction quality
- Split mixed long-form messages into multiple study entries
- Add automatic pipeline command after export
- Export directly to flashcard-friendly formats such as CSV
- Add a lightweight review UI for spaced repetition
- Add test coverage for parser rules
