import discord, re
from mantabot import db, messages

# ============================================================================

class FeedsHandler(object):
    publish_types = {}
    @classmethod
    def register(cls, name):
        def decorator(klass):
            cls.publish_types[name] = klass
            return klass
        return decorator

    def __init__(self, client):
        self.client = client
        self.guilds = {}

    async def on_ready(self):
        for guild in self.client.guilds:
            await self.init_guild(guild)

    async def on_guild_join(self, guild):
        await self.init_guild(guild)

    async def init_guild(self, guild):
        if guild.id in self.guilds:
            return

        settings = await db.settings.get('log', guild)
        objects = []

        for kind, channel_id in settings.get('feeds', {}).items():
            channel = guild.get_channel(channel_id)
            publisher = self.publish_types[kind](guild, channel)
            messages.bus(guild).subscribe(publisher)
            objects.append(publisher)

        self.guilds[guild.id] = objects

    async def on_member_ban(self, guild, user):
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                break
        else:
            return
        if entry.user.id != guild.me.id:
            messages.bus(guild).publish('ban', user=entry.user, member=user, reason=entry.reason)

    async def on_member_unban(self, guild, user):
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.unban):
            if entry.target.id == user.id:
                break
        else:
            return
        if entry.user.id != guild.me.id:
            messages.bus(guild).publish('unban', user=entry.user, member=user)

# ============================================================================

@FeedsHandler.register('logs')
class Logger(object):
    templates = {
        'action.grant_role': 'I granted role **{role.name}** to '
                             '{member.mention} [{member.name}#{member.discriminator}] :'
                             '*{reason}*.',
        'ban': '{user.display_name} banned {member.display_name} '
               '[{member.name}#{member.discriminator}]: *{reason}*.',
        'mute.add': '{user.display_name} muted {member.mention} from {channel.mention} for {duration:.0f}s.',
        'mute.remove': '{user.display_name} unmuted {member.mention} from {channel.mention}.',
        'readonly.set': '{user.display_name} {verb} readonly mode in {channel.mention}.',
        'unban': '{user.display_name} lifted ban for {member.display_name} '
                 '[{member.name}#{member.discriminator}]',
    }

    def __init__(self, guild, channel):
        self.guild = guild
        self.channel = channel

    @messages.event_handler('*')
    async def log(self, event, **data):
        await getattr(self, 'log_' + event.replace('.', '__'), self.default_logger)(event, **data)

    async def default_logger(self, event, **data):
        template = self.templates.get(event)
        if template:
            await self.channel.send(template.format(**data))

    async def log_readonly__set(self, event, **data):
        data['verb'] = 'enabled' if data['enable'] else 'disabled'
        await self.default_logger(event, **data)
