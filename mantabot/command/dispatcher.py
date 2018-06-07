import asyncio
import discord
import shlex
from mantabot.command import command, models, reply

# ============================================================================

class CommandError(Exception):
    def __init__(self, msg):
        self.message = msg


class Dispatcher(object):
    """ Bot plugin that dispatches user commands to command groups. """

    prefixes = tuple('!#')      # only messages starting with those are used
    delete_errors_after = 5     # basic error messages are deleted after that much time

    def __init__(self, client, groups=None):
        self.client = client
        self.groups = list(groups or command.CommandGroup.registry)

    async def on_message(self, message):
        """ Called everytime the bot sees a message """

        # Only handle messages inside guild channels
        if not isinstance(message.channel, discord.abc.GuildChannel):
            return

        # Only handle messages with correct prefix
        if not message.content.startswith(self.prefixes):
            return

        # Get name and arguments for command
        try:
            name, args = self.parse_message(message)
        except CommandError:
            return  # silently discard command, might be for another bot

        # Locate the command
        try:
            group = next(group for group in self.groups if name in group.commands)
        except StopIteration:
            return   # silently discard command, might be for another bot

        try:
            await self.check_permissions(message, group, name)
        except command.PermissionDenied:
            return

        settings = await self.get_settings(message, group, name)
        reply_class = settings.get('reply_class', reply.DeleteAndMentionReply)

        async with reply_class(self.client, message) as reply_obj:
            await self.dispatch_command(message, group, name, args,
                                        settings=settings, output=reply_obj)

    def parse_message(self, message):
        """ Split message into command name and arguments list """
        try:
            args = shlex.split(message.content[1:].split('\n', 1)[0])
            name = args.pop(0).lower()
        except (ValueError, IndexError):
            raise CommandError('invalid command format')
        return name, args

    async def check_permissions(self, message, group, name):
        """ Raise command.PermissionDenied to prevent user from running command """
        pass

    async def get_settings(self, message, group, name):
        """ Return a setttings dictionary for a command group """
        return {}

    async def dispatch_command(self, message, group, name, args, **kwargs):
        """ Dispatch the command to the group """
        await group.on_command(self.client, message, name, args, **kwargs)

