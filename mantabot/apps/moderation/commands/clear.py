import datetime
from mantabot import command


class Clear(command.Command):
    """ Bot command that deletes messages """
    name = 'clear'

    errors = {
        'usage': '{name} <number>|<text>|me\n'
                 '→ *<number>*: clear that many messages.\n'
                 '→ *<text>*: clear all messages since that text last appeared.\n'
                 '→ me: clear all messages since last time you wrote.',
        'permission_denied': 'I cannot manage messages in this channel.',
        'not_found': 'I did not find that message in the last {limit} ones.',
        'need_force': 'This is a lot of messages. Please confirm with `!{name} {number} force`.',
    }

    async def execute(self, message, args):
        if len(args) == 0:
            await self.error('usage', name=self.name)

        elif len(args) == 1 or (len(args) == 2 and args[1].lower() == 'force'):
            if args[0] == 'help':
                await self.error('usage', name=self.name)
            elif args[0] == 'me':
                await self.self_clear(message)
            else:
                try:
                    number = int(args[0])
                except ValueError:
                    await self.search_clear(message, args[0])
                else:
                    if number < 100 or len(args) == 2:
                        await self.count_clear(message, number)
                    else:
                        await self.error('need_force', name=self.name, number=number)
        else:
            await self.search_clear(message, ' '.join(args))

    async def clear_while(self, message, check, inclusive=False):
        """ clear all messages until the check is false """
        now = datetime.datetime.now().timestamp()
        async with message.channel.typing():
            to_delete = []
            async for msg in message.channel.history(limit=100, before=message):
                if now - msg.created_at.timestamp() >= 1209600:
                    break   # cannot clear messages older than 14 days
                if not check(msg):
                    if inclusive:
                        to_delete.append(msg)
                    break
                to_delete.append(msg)
            else:
                return False

            for idx in range(0, len(to_delete), 100):
                await message.channel.delete_messages(to_delete[idx:idx+100])
        return True

    async def self_clear(self, message):
        found = await self.clear_while(message, lambda msg: msg.author.id != message.author.id)
        if not found:
            await self.error('not_found', limit=100)

    async def count_clear(self, message, number):
        async with message.channel.typing():
            await message.channel.purge(before=message, limit=number)

    async def search_clear(self, message, text):
        text = text.lower()
        found = await self.clear_while(message, lambda msg: text not in msg.content.lower(), inclusive=True)
        if not found:
            await self.error('not_found', text=text, limit=100)
