import asyncio
from baleine import command

devtools = command.CommandGroup('devtools')

@devtools.register
class Id(command.Command):
    """ Bot command that tells the id of some discord objects, for debugging purposes """
    name = 'idof'

    errors = {
        'usage': '{name} type name',
        'unknown_type': 'known types: {types}',
        'not_found': '{type} {name} not found',
    }

    async def execute(self, message, args):
        if len(args) != 2:
            return await self.error('usage', name=self.name)

        kind, name = args[0].lower(), args[1].lower()

        collections = {
            'channel': message.guild.channels,
            'member': message.guild.members,
            'role': message.guild.roles,
        }
        items = collections.get(kind)

        if items is None:
            return await self.error('unknown_type', types=', '.join(collections))

        for item in items:
            if item.name.lower() == name:
                await self.send('{type} {name} has id {id}'.format(
                                type=kind, name=name, id=item.id))
                break
        else:
            await self.error('not_found', type=kind, name=name)
