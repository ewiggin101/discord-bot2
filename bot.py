"""
Multi-Language Discord Translation Bot
Supports: English, Korean, Spanish, French, Portuguese
"""

import discord
from discord.ext import commands
import asyncio
import logging
from config import Config
from secrets import load_secrets
from translator import TranslationService
from channel_manager import ChannelManager

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("TranslatorBot")

# ── Bot Setup ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ── Secrets ───────────────────────────────────────────────────────────────────
_secrets = load_secrets()

translator = TranslationService(_secrets["DEEPL_API_KEY"])
channel_manager = ChannelManager()

# ── Events ────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    log.info(f"Bot online as {bot.user} (ID: {bot.user.id})")
    log.info(f"Serving {len(bot.guilds)} guild(s)")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🌐 Translating across languages"
        )
    )

@bot.event
async def on_message(message: discord.Message):
    # Ignore bots (including self) to prevent translation loops
    if message.author.bot:
        return

    # Ignore bot commands
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # Check if this message is in a watched translation channel
    channel_info = channel_manager.get_channel_info(message.channel.id)
    if not channel_info:
        await bot.process_commands(message)
        return

    source_lang = channel_info["lang"]
    channel_type = channel_info["type"]  # "general" or "announcements"

    # Get all sibling channels (same type, different languages)
    targets = channel_manager.get_target_channels(
        guild_id=message.guild.id,
        source_lang=source_lang,
        channel_type=channel_type
    )

    if not targets:
        await bot.process_commands(message)
        return

    # Translate and post to each target channel concurrently
    tasks = []
    for target_lang, target_channel_id in targets.items():
        target_channel = bot.get_channel(target_channel_id)
        if target_channel:
            tasks.append(
                translate_and_post(message, source_lang, target_lang, target_channel)
            )

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    await bot.process_commands(message)


async def translate_and_post(
    message: discord.Message,
    source_lang: str,
    target_lang: str,
    target_channel: discord.TextChannel
):
    """Translate a message and post it via webhook to the target channel."""
    try:
        translated_text = await translator.translate(
            text=message.content,
            source_lang=source_lang,
            target_lang=target_lang
        )

        if not translated_text:
            return

        # Use a webhook so messages appear with the original author's name/avatar
        webhook = await get_or_create_webhook(target_channel)
        if not webhook:
            return

        # Build embed for clean presentation
        embed = discord.Embed(
            description=translated_text,
            color=Config.LANGUAGE_COLORS.get(target_lang, 0x7289DA)
        )
        embed.set_footer(
            text=f"Translated from {Config.LANGUAGE_NAMES[source_lang]} • #{message.channel.name}"
        )

        # Attach any images from the original message
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        await webhook.send(
            username=f"{message.author.display_name}",
            avatar_url=message.author.display_avatar.url,
            embed=embed
        )

        log.info(
            f"Translated {source_lang}→{target_lang} | "
            f"#{message.channel.name} → #{target_channel.name} | "
            f"Author: {message.author}"
        )

    except Exception as e:
        log.error(f"Failed to translate/post {source_lang}→{target_lang}: {e}")


async def get_or_create_webhook(channel: discord.TextChannel) -> discord.Webhook | None:
    """Retrieve existing bot webhook or create a new one for the channel."""
    try:
        webhooks = await channel.webhooks()
        for wh in webhooks:
            if wh.user == bot.user:
                return wh
        # Create a new webhook if one doesn't exist
        return await channel.create_webhook(name="TranslatorBot")
    except discord.Forbidden:
        log.warning(f"Missing webhook permissions in #{channel.name}")
        return None
    except Exception as e:
        log.error(f"Webhook error in #{channel.name}: {e}")
        return None


# ── Commands ──────────────────────────────────────────────────────────────────
@bot.command(name="tsetup")
@commands.has_permissions(administrator=True)
async def setup_channels(ctx):
    """Auto-register all translation channels in this server."""
    guild = ctx.guild
    registered = []

    for channel in guild.text_channels:
        for lang_code, keywords in Config.CHANNEL_KEYWORDS.items():
            for channel_type, type_keywords in keywords.items():
                if any(kw in channel.name.lower() for kw in type_keywords):
                    channel_manager.register_channel(
                        guild_id=guild.id,
                        channel_id=channel.id,
                        lang=lang_code,
                        channel_type=channel_type
                    )
                    registered.append(f"#{channel.name} → `{lang_code}` ({channel_type})")

    if registered:
        embed = discord.Embed(
            title="✅ Translation Channels Registered",
            description="\n".join(registered),
            color=0x57F287
        )
    else:
        embed = discord.Embed(
            title="⚠️ No Channels Found",
            description=(
                "No matching channels detected. Make sure your channels follow the naming convention:\n"
                "`en-general`, `ko-general`, `es-announcements`, etc."
            ),
            color=0xFEE75C
        )

    await ctx.send(embed=embed)


@bot.command(name="tregister")
@commands.has_permissions(administrator=True)
async def register_channel(ctx, lang: str, channel_type: str):
    """Manually register the current channel. Usage: !tregister ko general"""
    lang = lang.lower()
    channel_type = channel_type.lower()

    if lang not in Config.LANGUAGE_NAMES:
        await ctx.send(f"❌ Unknown language `{lang}`. Valid: {', '.join(Config.LANGUAGE_NAMES.keys())}")
        return

    if channel_type not in ("general", "announcements"):
        await ctx.send("❌ Channel type must be `general` or `announcements`.")
        return

    channel_manager.register_channel(
        guild_id=ctx.guild.id,
        channel_id=ctx.channel.id,
        lang=lang,
        channel_type=channel_type
    )

    await ctx.send(
        f"✅ Registered **#{ctx.channel.name}** as `{lang}` {channel_type} channel."
    )


@bot.command(name="tstatus")
@commands.has_permissions(administrator=True)
async def show_status(ctx):
    """Show all registered translation channels for this server."""
    channels = channel_manager.get_guild_channels(ctx.guild.id)

    if not channels:
        await ctx.send("No translation channels registered yet. Run `!tsetup` to auto-detect.")
        return

    embed = discord.Embed(title="🌐 Translation Channel Map", color=0x5865F2)

    by_type = {"general": [], "announcements": []}
    for ch_id, info in channels.items():
        channel = bot.get_channel(ch_id)
        name = f"#{channel.name}" if channel else f"(deleted: {ch_id})"
        by_type[info["type"]].append(
            f"{Config.LANGUAGE_FLAGS[info['lang']]} {name} (`{info['lang']}`)"
        )

    for ch_type, entries in by_type.items():
        if entries:
            embed.add_field(
                name=f"📌 {ch_type.capitalize()}",
                value="\n".join(entries),
                inline=False
            )

    await ctx.send(embed=embed)


@bot.command(name="tunregister")
@commands.has_permissions(administrator=True)
async def unregister_channel(ctx):
    """Remove current channel from translation routing."""
    removed = channel_manager.unregister_channel(ctx.channel.id)
    if removed:
        await ctx.send(f"✅ **#{ctx.channel.name}** removed from translation routing.")
    else:
        await ctx.send(f"⚠️ **#{ctx.channel.name}** was not registered.")


@bot.command(name="ttest")
@commands.has_permissions(administrator=True)
async def test_translation(ctx, lang: str, *, text: str):
    """Test translation to a specific language. Usage: !ttest ko Hello world"""
    lang = lang.lower()
    if lang not in Config.LANGUAGE_NAMES:
        await ctx.send(f"❌ Unknown language `{lang}`.")
        return

    async with ctx.typing():
        result = await translator.translate(text, "en", lang)

    if result:
        embed = discord.Embed(color=Config.LANGUAGE_COLORS.get(lang, 0x7289DA))
        embed.add_field(name="Original (EN)", value=text, inline=False)
        embed.add_field(
            name=f"Translated ({Config.LANGUAGE_NAMES[lang]})",
            value=result,
            inline=False
        )
        embed.set_footer(text=f"Engine: {'Papago' if lang == 'ko' else 'DeepL'}")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Translation failed. Check your API keys in `.env`.")


@bot.command(name="thelp")
async def show_help(ctx):
    """Show all bot commands."""
    embed = discord.Embed(
        title="🌐 TranslatorBot Commands",
        color=0x5865F2
    )
    commands_list = [
        ("!tsetup", "Auto-detect & register all language channels (Admin)"),
        ("!tregister <lang> <type>", "Manually register current channel (Admin)"),
        ("!tunregister", "Remove current channel from translation (Admin)"),
        ("!tstatus", "Show all registered translation channels (Admin)"),
        ("!ttest <lang> <text>", "Test translation to a language (Admin)"),
        ("!thelp", "Show this help message"),
    ]
    for name, value in commands_list:
        embed.add_field(name=f"`{name}`", value=value, inline=False)

    embed.set_footer(text="Supported languages: en | ko | es | fr | pt")
    await ctx.send(embed=embed)


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(_secrets["DISCORD_TOKEN"])
