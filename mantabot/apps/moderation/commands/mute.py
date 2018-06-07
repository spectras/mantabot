from mantabot import command
from mantabot.apps.moderation import service


class Mute(command.Command):
    """ Bot command that mutes a user on current channel """
    name = 'mute'
    default_duration = 600   # minutes

    errors = {
        'usage': '{name} *time* <\@name> [<\@name> …]\n{name} *time* *number*',
        'invalid_time': 'this duration is too short.',
        'bot_permissions': 'I cannot manage messages in this channel.',
        'user_permissions': 'you do not have permissions to mute those members: {names}.',
    }

    messages = {
        'show_mutes': 'those members are *muted*: {mutes}.',
        'mute': '{member.display_name} [{duration:.0f}s]',
        'no_mutes': 'no mute is active on this channel.',
        'added': 'those members will be muted for {duration:.0f} seconds: {names}.',
    }

    async def execute(self, message, args):
        channel = message.channel

        # Check permissions
        if not channel.permissions_for(channel.guild.me).manage_messages:
            return await self.error('bot_permissions')

        # With no arguments, show list of mutes
        if len(args) == 0:
            mutes = await service.get_channel_mutes(channel)
            if not mutes:
                return await self.send(self.messages['no_mutes'])
            return await self.send(self.messages['show_mutes'].format(
                mutes=', '.join(self.messages['mute'].format(member=mute[0], duration=mute[1]) for mute in mutes)
            ))

        # Otherwise arguments are duration and user mentions
        try:
            duration = 60 * float(args[0])
        except ValueError:
            duration = self.default_duration
        else:
            if duration < 15:
                return await self.error('invalid_time', time=duration)

        members = message.mentions
        if not members:
            return await self.error('usage', name=self.name)

        vetoed = [member for member in members if member.top_role >= message.author.top_role]
        if vetoed:
            return await self.error('user_permissions', names=', '.join(member.display_name for member in vetoed))

        await service.add_channel_mutes(channel, members, duration, user=message.author)

        await self.send(self.messages['added'].format(
            names=', '.join(member.display_name for member in members),
            duration=duration,
        ))


class Unmute(command.Command):
    """ Bot command that enables / disabled read-only mode """
    name = 'unmute'

    errors = {
        'usage': '{name} <\@name> [<\@name> …]',
        'user_permissions': 'you do not have permissions to unmute those members: {names}.',
    }

    messages = {
        'removed': 'those members are no longer muted: {names}.',
    }

    async def execute(self, message, args):
        channel = message.channel

        members = message.mentions
        if not members:
            return await self.error('usage', name=self.name)

        vetoed = [member for member in members if member.top_role >= message.author.top_role]
        if vetoed:
            return await self.error('user_permissions', names=', '.join(member.display_name for member in vetoed))

        await service.remove_channel_mutes(channel, members, user=message.author)

        await self.send(self.messages['removed'].format(
            names=', '.join(member.mention for member in members),
        ))
