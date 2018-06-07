import json
from collections import namedtuple
from mantabot import db
from mantabot.command import command, dispatcher, models, reply

# ============================================================================

Entry = namedtuple('Entry', 'group_name role channels settings')


class DBDispatcher(dispatcher.Dispatcher):
    """ A dispatcher that stores command configuration in the database """

    def __init__(self, *args, **kwargs):
        super(DBDispatcher, self).__init__(*args, **kwargs)
        self.guilds = {}
        group = command_group.clone()
        group.dispatcher = self
        self.groups.append(group)

    async def check_permissions(self, message, group, name):
        """ Raise command.PermissionDenied to prevent user from running command """
        if message.author.guild_permissions.administrator:
            return
        if await self.get_entry(message.channel, message.author, group):
            return
        raise command.PermissionDenied()

    async def get_settings(self, message, group, name):
        """ Return a setttings dictionary for a command group """
        if message.author.guild_permissions.administrator:
            return {}
        entry = await self.get_entry(message.channel, message.author, group)
        return entry.settings

    async def get_guild(self, guild):
        """ Load guild configuration from database - with caching """
        try:
            return self.guilds[guild.id]
        except KeyError:
            pass

        query = models.CommandPermission.select().where(
            models.CommandPermission.c.guild_id==guild.id
        )

        entries = []
        async with await db.connection() as conn:
            async for row in conn.execute(query):
                channels = row['channels'] or None
                if channels is not None:
                    channels = tuple(int(channel) for channel in channels.split(','))

                settings = json.loads(row['settings'])
                reply_class = settings.pop('reply_class', None)
                if reply_class and hasattr(reply, reply_class):
                    settings['reply_class'] = getattr(reply, reply_class)

                entries.append(Entry(
                    group_name=row['group_name'],
                    role=row['role_id'],
                    channels=channels,
                    settings=settings,
                ))
                
        self.guilds[guild.id] = entries
        return entries

    async def get_entry(self, channel, member, group):
        """ Locate a specific configuration entry for the triplet """
        return next((
            entry for entry in await self.get_guild(channel.guild)
            if entry.group_name == group.name and
               (not entry.channels or channel.id in entry.channels) and
               any(role.id == entry.role for role in member.roles)
            ), None
        )

    def clear_cache(self, guild):
        self.guilds.pop(guild.id, None)

# ============================================================================

command_group = command.CommandGroup('command', register=False)

@command_group.register
class List(command.Command):
    """ Bot command that lists all command settings """
    name = 'cmdlist'

    errors = {
        'no_group': 'Unknown command group: “{name}”',
    }

    async def execute(self, message, args):
        dispatcher = self.group.dispatcher
        
        if len(args) == 1:
            group_name = args[0].lower()
            try:
                groups = [next(group for group in dispatcher.groups
                               if group.name.lower() == group_name)]
            except StopIteration:
                return await self.error('no_group', name=group_name)
        else:
            groups = dispatcher.groups
        guild = message.channel.guild
        entries = sorted(await dispatcher.get_guild(guild),
                         key=lambda entry: (entry.role, entry.channels or ()))
        roles = dict((role.id, role) for role in guild.roles)
        channels = dict((channel.id, channel) for channel in guild.channels)

        message = []
        for group in sorted(groups, key=lambda group: group.name):
            message.append('{name} — [{commands}]'.format(
                name=group.name,
                commands=', '.join(group.commands.keys()),
            ))
            for entry in entries:
                if entry.group_name != group.name:
                    continue
                role_text = roles[entry.role].name if entry.role else '<admin>'
                channel_text = (', '.join('#' + channels[channel].name
                                          for channel in entry.channels)
                                if entry.channels else '<all channels>')
                message.append('    · %s: %s' % (role_text, channel_text))
            
        await self.send("```\n%s\n```" % '\n'.join(message))

@command_group.register
class Add(command.Command):
    """ Bot command that adds a command group permission set """
    name = 'cmdadd'
    
    errors = {
        'usage': '{name} "role" <group> [#channel1 #channel2 ...]',
        'no_group': 'Unknown command group: “{name}”',
        'no_role': 'Unknown role: “{name}”',
        'no_channel': 'Unknown channel: : “{name}”',
    }
    
    async def execute(self, message, args):
        if len(args) < 2:
            return await self.error('usage', name=self.name)

        guild = message.channel.guild
        dispatcher = self.group.dispatcher

        role_name, group_name = args[0].lower(), args[1].lower()

        # Lookup role
        role = next((role for role in guild.roles if role.name.lower() == role_name), None)
        if not role:
            return await self.error('no_role', name=role_name)

        # Lookup group
        group = next((group for group in dispatcher.groups if group.name.lower() == group_name), None)
        if not group:
            return await self.error('no_group', name=group_name)

        # Build channel collection
        channels = []
        for channel_name in args[2:]:
            channel_name = channel_name.lower().lstrip('#')
            channel = next((channel for channel in guild.text_channels
                            if channel.name == channel_name or channel.mention == channel_name), None)
            if not channel:
                return await self.error('no_channel', name=channel_name)
            channels.append(channel)

        query = models.CommandPermission.insert().values(
            guild_id=guild.id,
            group_name=group.name,
            role_id=role.id,
            channels=','.join(str(channel.id) for channel in channels),
            settings='{}',
        )
        async with await db.connection() as conn:
            async with conn.begin():
                await conn.execute(query)
        dispatcher.clear_cache(guild)

        await self.send('ajouté')
        

@command_group.register
class Remove(command.Command):
    """ Bot command that remove a command group permisison set """
    name = 'cmdremove'

    errors = {
        'usage': '{name} ["role"] <group>',
        'no_group': 'Unknown command group: “{name}”',
        'no_role': 'Unknown role: “{name}”',
    }

    async def execute(self, message, args):
        if len(args) == 1:
            role_name, group_name = None, args[0]
        elif len(args) == 2:
            role_name, group_name = args[0].lower(), args[1].lower()
        else:
            return await self.error('usage', name=self.name)

        guild = message.channel.guild
        dispatcher = self.group.dispatcher
        
        # Lookup group
        try:
            group = next(group for group in dispatcher.groups if group.name.lower() == group_name)
        except StopIteration:
            return await self.error('no_group', name=group_name)
        
        # Lookup role
        if role_name:
            try:
                role = next(role for role in guild.roles if role.name.lower() == role_name)
            except StopIteration:
                return await self.error('no_role', name=role_name)
        else:
            role = None

        query = models.CommandPermission.delete().where(
            models.CommandPermission.c.guild_id==guild.id
        ).where(
            models.CommandPermission.c.group_name==group.name
        )
        if role:
            query = query.where(models.CommandPermission.c.role_id==role.id)

        async with await db.connection() as conn:
            async with conn.begin():
                await conn.execute(query)
        dispatcher.clear_cache(guild)

        await self.send('supprimé')
