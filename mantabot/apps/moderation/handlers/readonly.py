import discord
from mantabot.apps.moderation import service


class ReadOnly(object):
    """ Simple plugin that deletes messages sent to some channels """
    name = 'moderation.readonly'

    def __init__(self, client):
        self.client = client

    async def on_message(self, message):
        channel = message.channel
        if not isinstance(channel, discord.abc.GuildChannel):
            return
        if message.author.bot:
            return

        # Handle readonly
        if await service.get_readonly(channel):
            try:
                await message.delete()
            except discord.NotFound:
                pass # this is okay, message is already deleted
            except discord.Forbidden:
                await service.set_readonly(channel, False, user=channel.guild.me, reason='forbidden')

        # Handle mutes
        if await service.get_channel_member_muted(channel, message.author):
            try:
                await message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
