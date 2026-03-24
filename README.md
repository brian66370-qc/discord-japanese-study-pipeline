# Discord Japanese Study Pipeline

Discord bot and parser pipeline for exporting Japanese study notes from Discord, structuring them, and generating NotebookLM-ready materials.

## Screenshots

Add screenshots here after you capture your setup:

- `docs/images/discord-export-command.png`
- `docs/images/normalized-json-preview.png`
- `docs/images/notebooklm-files.png`

Example Markdown:

```md
![Discord export command](docs/images/discord-export-command.png)
![Normalized JSON preview](docs/images/normalized-json-preview.png)
![NotebookLM files](docs/images/notebooklm-files.png)
```

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

## 中文

### 專案用途

這個專案用來把 Discord 頻道中的日文單字與文法筆記整理成可複習資料。

你可以用它：

- 用 bot 匯出 Discord 頻道訊息
- 記住每個頻道的上次匯出位置，做增量匯出
- 把原始訊息轉成結構化學習條目
- 產生適合餵給 NotebookLM 的 Markdown
- 為之後的複習軟體或單字卡做準備

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

## 日本語

### 概要

このプロジェクトは、Discord のチャンネルにある日本語の単語メモや文法メモを、復習しやすい形に整理するためのものです。

できること：

- Bot で Discord チャンネルをエクスポートする
- チャンネルごとの前回位置を記録して増分エクスポートする
- 生のメッセージを学習用エントリに正規化する
- NotebookLM に入れやすい Markdown を生成する
- 今後の復習アプリや単語カードの元データを作る

### 主な機能

- プライベートチャンネル向け slash command エクスポート
- チャンネルごとのチェックポイントによる増分エクスポート
- 必要に応じた全件再エクスポート
- 生 JSON の保存
- 単語と文法メモの基本解析
- NotebookLM 向け Markdown 生成

### Slash Commands

- `/export_here`
  前回以降の新しいメッセージだけをエクスポート
- `/export_here full_export:true`
  チェックポイントを無視して全件再エクスポート
- `/export_status`
  現在のチャンネルのチェックポイントを表示
- `/export_reset_here`
  現在のチャンネルのチェックポイントをリセット
- `/whoami`
  自分の Discord ユーザー ID を表示

### Discord 側の設定

- Bot 権限:
  - `View Channel`
  - `Read Message History`
  - `Send Messages`
  - `Use Application Commands`
- Developer Portal:
  - `Message Content Intent` を有効化

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

## Roadmap

- Improve grammar detection and extraction quality
- Split mixed long-form messages into multiple study entries
- Add automatic pipeline command after export
- Export directly to flashcard-friendly formats such as CSV
- Add a lightweight review UI for spaced repetition
- Add test coverage for parser rules

## Suggested GitHub Topics

- `discord`
- `discord-bot`
- `python`
- `japanese`
- `language-learning`
- `notebooklm`
- `study-tools`
- `text-processing`
- `flashcards`
- `automation`
