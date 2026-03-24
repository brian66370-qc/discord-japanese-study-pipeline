import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import discord
from discord import app_commands
from dotenv import load_dotenv


EXPORT_DIR = Path("data/raw/exports")
STATE_FILE = Path("data/raw/export_state.json")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parse_allowed_user_ids() -> set[int]:
    raw_value = require_env("DISCORD_ALLOWED_USER_IDS")
    user_ids = {int(part.strip()) for part in raw_value.split(",") if part.strip()}
    if not user_ids:
        raise RuntimeError("DISCORD_ALLOWED_USER_IDS must contain at least one user id")
    return user_ids


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


def load_export_state() -> dict[str, dict[str, str]]:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_export_state(state: dict[str, dict[str, str]]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_channel_checkpoint(channel_id: int) -> dict[str, str] | None:
    state = load_export_state()
    return state.get(str(channel_id))


def update_channel_checkpoint(
    channel_id: int,
    last_message_id: int,
    exported_at: str,
    message_count: int,
) -> None:
    state = load_export_state()
    state[str(channel_id)] = {
        "last_message_id": str(last_message_id),
        "exported_at": exported_at,
        "message_count": str(message_count),
    }
    save_export_state(state)


def clear_channel_checkpoint(channel_id: int) -> None:
    state = load_export_state()
    state.pop(str(channel_id), None)
    save_export_state(state)


class PrivateReaderBot(discord.Client):
    def __init__(self, guild_id: int, allowed_user_ids: set[int]) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.guild_id = guild_id
        self.allowed_user_ids = allowed_user_ids
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self) -> None:
        print(f"Private reader bot logged in as {self.user} ({self.user.id})")


load_dotenv()
GUILD_ID = int(require_env("DISCORD_GUILD_ID"))
ALLOWED_USER_IDS = parse_allowed_user_ids()
BOT = PrivateReaderBot(guild_id=GUILD_ID, allowed_user_ids=ALLOWED_USER_IDS)


def ensure_authorized(interaction: discord.Interaction) -> bool:
    return interaction.user.id in BOT.allowed_user_ids


@BOT.tree.command(
    name="export_here",
    description="Export new messages from the current channel to a local JSON file.",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    limit="Optional max number of messages to export this run",
    full_export="Ignore saved checkpoint and export from the beginning",
)
async def export_here(
    interaction: discord.Interaction,
    limit: int | None = None,
    full_export: bool = False,
) -> None:
    if not ensure_authorized(interaction):
        await interaction.response.send_message(
            "You are not allowed to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel | discord.Thread):
        await interaction.response.send_message(
            "This command only works in server text channels or threads.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    checkpoint = None if full_export else get_channel_checkpoint(channel.id)
    after = (
        discord.Object(id=int(checkpoint["last_message_id"]))
        if checkpoint and checkpoint.get("last_message_id")
        else None
    )

    messages: list[dict[str, Any]] = []
    async for message in channel.history(limit=limit, oldest_first=True, after=after):
        messages.append(serialize_message(message))

    if not messages:
        if checkpoint and not full_export:
            await interaction.followup.send(
                "No new messages found since the last export checkpoint.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "No messages found to export from this channel.",
                ephemeral=True,
            )
        return

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = EXPORT_DIR / f"{channel.id}_{timestamp}.json"
    exported_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "guild_id": str(interaction.guild_id),
        "guild_name": interaction.guild.name if interaction.guild else None,
        "channel_id": str(channel.id),
        "channel_name": getattr(channel, "name", str(channel.id)),
        "exported_at": exported_at,
        "exported_by": str(interaction.user.id),
        "export_mode": "full" if full_export else "incremental",
        "checkpoint_after_message_id": checkpoint["last_message_id"] if checkpoint else None,
        "message_count": len(messages),
        "messages": messages,
    }

    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    update_channel_checkpoint(
        channel_id=channel.id,
        last_message_id=int(messages[-1]["id"]),
        exported_at=exported_at,
        message_count=len(messages),
    )

    await interaction.followup.send(
        (
            f"Exported {len(messages)} messages from "
            f"#{getattr(channel, 'name', channel.id)} to `{output_path}` "
            f"using {'full' if full_export else 'incremental'} mode."
        ),
        ephemeral=True,
    )


@BOT.tree.command(
    name="export_status",
    description="Show the saved export checkpoint for the current channel.",
    guild=discord.Object(id=GUILD_ID),
)
async def export_status(interaction: discord.Interaction) -> None:
    if not ensure_authorized(interaction):
        await interaction.response.send_message(
            "You are not allowed to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel | discord.Thread):
        await interaction.response.send_message(
            "This command only works in server text channels or threads.",
            ephemeral=True,
        )
        return

    checkpoint = get_channel_checkpoint(channel.id)
    if not checkpoint:
        await interaction.response.send_message(
            "This channel does not have a saved export checkpoint yet.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        (
            f"Last checkpoint for #{getattr(channel, 'name', channel.id)}:\n"
            f"- last_message_id: `{checkpoint['last_message_id']}`\n"
            f"- exported_at: `{checkpoint['exported_at']}`\n"
            f"- last_export_count: `{checkpoint['message_count']}`"
        ),
        ephemeral=True,
    )


@BOT.tree.command(
    name="export_reset_here",
    description="Reset the saved export checkpoint for the current channel.",
    guild=discord.Object(id=GUILD_ID),
)
async def export_reset_here(interaction: discord.Interaction) -> None:
    if not ensure_authorized(interaction):
        await interaction.response.send_message(
            "You are not allowed to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel | discord.Thread):
        await interaction.response.send_message(
            "This command only works in server text channels or threads.",
            ephemeral=True,
        )
        return

    clear_channel_checkpoint(channel.id)
    await interaction.response.send_message(
        f"Reset the saved export checkpoint for #{getattr(channel, 'name', channel.id)}.",
        ephemeral=True,
    )


@BOT.tree.command(
    name="whoami",
    description="Show your Discord user id for allow-list setup.",
    guild=discord.Object(id=GUILD_ID),
)
async def whoami(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        f"Your user id is `{interaction.user.id}`",
        ephemeral=True,
    )


def main() -> None:
    token = require_env("DISCORD_BOT_TOKEN")
    BOT.run(token)


if __name__ == "__main__":
    main()
