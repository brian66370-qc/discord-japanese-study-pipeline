# Discord Japanese Study Pipeline

Discord channel export bot and study-note pipeline for Japanese vocabulary and grammar review.

## English

### Overview

This project helps you:

- export messages from a Discord channel with a bot
- normalize Japanese learning notes into structured entries
- generate Markdown files for NotebookLM
- prepare data for future review apps or flashcards

### Features

- private channel export with slash commands
- incremental export with per-channel checkpoints
- raw JSON export for archive safety
- parser for vocabulary and grammar notes
- NotebookLM-friendly Markdown generation

### Commands

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

### Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python bot/private_reader_bot.py
```

### Required Discord settings

- Bot permissions:
  - `View Channel`
  - `Read Message History`
  - `Send Messages`
  - `Use Application Commands`
- Developer Portal:
  - enable `Message Content Intent`

### Pipeline

```powershell
python parser/normalize.py --input data/raw/exports/your_export.json --output data/normalized/normalized_entries.json
python parser/build_notebooklm_files.py --input data/normalized/normalized_entries.json --output-dir data/notebooklm
```

## 中文

### 專案用途

這個專案用來把 Discord 頻道中的日文單字與文法筆記整理成可複習資料。

你可以用它：

- 用 bot 匯出 Discord 頻道訊息
- 把原始訊息轉成結構化學習條目
- 產生適合餵給 NotebookLM 的 Markdown
- 為之後的複習軟體或單字卡做準備

### 目前功能

- 私人頻道 slash command 匯出
- 記住每個頻道上次匯出位置的增量匯出
- 保留原始 JSON 匯出檔
- 初步解析單字與文法筆記
- 生成 NotebookLM 可讀的 Markdown

### 指令

- `/export_here`
  只匯出上次之後新增的訊息
- `/export_here full_export:true`
  忽略進度，重新完整匯出
- `/export_status`
  查看目前頻道的匯出記錄點
- `/export_reset_here`
  清除目前頻道的匯出記錄點
- `/whoami`
  顯示你的 Discord 使用者 ID

### 基本安裝

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python bot/private_reader_bot.py
```

### Discord 端需求

- Bot 權限：
  - `View Channel`
  - `Read Message History`
  - `Send Messages`
  - `Use Application Commands`
- Developer Portal：
  - 開啟 `Message Content Intent`

### 資料流程

```powershell
python parser/normalize.py --input data/raw/exports/你的匯出檔.json --output data/normalized/normalized_entries.json
python parser/build_notebooklm_files.py --input data/normalized/normalized_entries.json --output-dir data/notebooklm
```

## 日本語

### 概要

このプロジェクトは、Discord のチャンネルにある日本語の単語メモや文法メモを、復習しやすい形に整理するためのものです。

できること：

- Bot で Discord チャンネルをエクスポートする
- 生のメッセージを学習用エントリに正規化する
- NotebookLM に入れやすい Markdown を生成する
- 今後の復習アプリや単語カードの元データを作る

### 主な機能

- プライベートチャンネル向け slash command エクスポート
- チャンネルごとのチェックポイントを使った増分エクスポート
- 生 JSON の保存
- 単語と文法メモの基本的な解析
- NotebookLM 向け Markdown 生成

### コマンド

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

### セットアップ

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python bot/private_reader_bot.py
```

### Discord 側の設定

- Bot 権限:
  - `View Channel`
  - `Read Message History`
  - `Send Messages`
  - `Use Application Commands`
- Developer Portal:
  - `Message Content Intent` を有効化

### 処理の流れ

```powershell
python parser/normalize.py --input data/raw/exports/export.json --output data/normalized/normalized_entries.json
python parser/build_notebooklm_files.py --input data/normalized/normalized_entries.json --output-dir data/notebooklm
```

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
