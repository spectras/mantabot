import discord, logging
from mantabot import command, messages

logger = logging.getLogger(__name__)


class Ban(command.Command):
    """ Bot command that bans a user """
    name = 'ban'

    errors = {
        'usage': '{name} member reason',
        'mention_number': 'you must mention exactly one member.',
        'bot_permission': 'I am not allowed to ban {user}.',
        'user_permission': 'you are not allowed to ban {user}.',
    }

    messages = {
        'ban': '{user} was banned: *{reason}*',
    }

    async def execute(self, message, args):
        if len(args) < 2:
            await self.error('usage', name=self.name)
            return

        if len(message.mentions) != 1:
            await self.error('mention_number')
            return

        member = message.mentions[0]
        if member.top_role >= message.author.top_role:
            await self.error('user_permission', user=member.display_name)
            return

        reason = ' '.join(args[1:])

        try:
            await member.ban(reason=reason, delete_message_days=0)
        except discord.Forbidden:
            await self.error('bot_permission', user=member.display_name)
        else:
            logger.info('banning {member.display_name} [{member.id}]: {reason}'.format(
                        member=member, reason=reason))
            messages.bus(member.guild).publish('ban', user=message.author, member=member, reason=reason)
            await self.send(self.messages['ban'].format(user=member.display_name, reason=reason))
