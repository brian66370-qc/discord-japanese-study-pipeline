import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import discord
from dotenv import load_dotenv


DEFAULT_OUTPUT = Path("data/raw/raw_messages.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Discord channel history into a JSON file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the output JSON file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for number of messages to export.",
    )
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def serialize_message(message: discord.Message) -> dict[str, Any]:
    return {
        "id": str(message.id),
        "author_id": str(message.author.id),
        "author_name": str(message.author),
        "content": message.content,
        "created_at": message.created_at.astimezone(timezone.utc).isoformat(),
        "edited_at": (
            message.edited_at.astimezone(timezone.utc).isoformat()
            if message.edited_at
            else None
        ),
        "attachments": [
            {
                "id": str(attachment.id),
                "filename": attachment.filename,
                "url": attachment.url,
                "content_type": attachment.content_type,
                "size": attachment.size,
            }
            for attachment in message.attachments
        ],
        "embeds": [embed.to_dict() for embed in message.embeds],
        "jump_url": message.jump_url,
    }


class ExportClient(discord.Client):
    def __init__(
        self,
        guild_id: int,
        channel_id: int,
        output_path: Path,
        limit: int | None,
    ) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.output_path = output_path
        self.limit = limit

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} ({self.user.id})")

        guild = self.get_guild(self.guild_id) or await self.fetch_guild(self.guild_id)
        channel = guild.get_channel(self.channel_id) or await guild.fetch_channel(
            self.channel_id
        )

        messages: list[dict[str, Any]] = []
        async for message in channel.history(limit=self.limit, oldest_first=True):
            messages.append(serialize_message(message))

        payload = {
            "guild_id": str(guild.id),
            "guild_name": guild.name,
            "channel_id": str(channel.id),
            "channel_name": getattr(channel, "name", str(channel.id)),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "message_count": len(messages),
            "messages": messages,
        }

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(f"Exported {len(messages)} messages to {self.output_path}")
        await self.close()


def main() -> None:
    load_dotenv()
    args = parse_args()

    token = require_env("DISCORD_BOT_TOKEN")
    guild_id = int(require_env("DISCORD_GUILD_ID"))
    channel_id = int(require_env("DISCORD_CHANNEL_ID"))

    client = ExportClient(
        guild_id=guild_id,
        channel_id=channel_id,
        output_path=args.output,
        limit=args.limit,
    )
    client.run(token)


if __name__ == "__main__":
    main()
