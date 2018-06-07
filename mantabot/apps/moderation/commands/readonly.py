from mantabot import command
from mantabot.apps.moderation import service


class ReadOnly(command.Command):
    """ Bot command that enables / disabled read-only mode """
    name = 'readonly'

    errors = {
        'usage': '{name} [on|off]',
        'bot_permissions': 'I cannot manage messages in this channel.',
    }

    messages = {
        'enabled': 'read-only mode enabled',
        'disabled': 'read-only mode disabled',
    }

    async def execute(self, message, args):
        channel = message.channel
        enabled = await service.get_readonly(channel)

        if len(args) == 0:
            enable = not enabled

        elif len(args) == 1:
            if args[0] in ('on', 'yes'):
                enable = True
            elif args[0] in ('off', 'no'):
                enable = False
            else:
                return await self.error('usage', name=self.name)
        else:
            return await self.error('usage', name=self.name)

        try:
            await service.set_readonly(channel, enable, user=message.author)
        except service.BotPermissionError:
            return await self.error('bot_permissions')

        await self.send(self.messages['enabled' if enable else 'disabled'], delete_after=5)
