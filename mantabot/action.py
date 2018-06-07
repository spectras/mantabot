import asyncio, collections, logging
from mantabot import messages
from mantabot.util import emoji as util_emoji

default_logger = logging.getLogger(__name__)

# ============================================================================

class Action(object):
    """ Encapsulate an action taken as a consequence to a message """
    registry = {}

    @classmethod
    def register(cls, klass):
        cls.registry[klass.__name__] = klass
        return klass

    @classmethod
    def create(cls, kind, guild, logger=None, **kwargs):
        klass = Action.registry.get(kind, None)
        if not klass:
            raise ValueError('Unknown action type "%s"' % kind)
        return klass(guild, logger=logger, **kwargs)

    @classmethod
    def load(cls, data, guild, logger=None):
        if isinstance(data, collections.Sequence):
            return Multiple(guild=guild, actions=data, logger=logger)
        else:
            data = data.copy()
            type_name = data.pop('type')
            return cls.create(type_name, guild=guild, logger=logger, **data)

    def __init__(self, guild, logger=None):
        self.guild = guild
        self.logger = logger or default_logger

    async def __call__(self, message, context=None):
        raise NotImplementedError()

# ============================================================================

class Multiple(Action):
    """ Action that triggers a list of actions """
    def __init__(self, guild, actions, logger=None):
        super().__init__(guild, logger=logger)
        self.actions = tuple(
            Action.load(data, guild=guild, logger=logger) for data in actions
        )

    async def __call__(self, message, context=None):
        await asyncio.gather(*(action(message, context=context) for action in self.actions))


@Action.register
class Nothing(Action):
    async def __call__(self, message, context=None):
        pass


@Action.register
class Reply(Action):
    def __init__(self, guild, content, logger=None):
        super().__init__(guild, logger=logger)
        self.content = content

    async def __call__(self, message, context=None):
        context = context or {}
        await message.channel.send(
            '%s: %s' % (message.author.mention, self.content.format(message=message, **context))
        )


@Action.register
class Message(Action):
    def __init__(self, guild, content, channel=None, logger=None):
        super().__init__(guild, logger=logger)
        self.content = content
        self.channel = guild.get_channel(channel) if channel else None

    async def __call__(self, message, context=None):
        context = context or {}
        target = self.channel or message.author
        await target.send(self.content.format(message=message, **context))


@Action.register
class Copy(Action):
    def __init__(self, guild, channel, logger=None):
        super().__init__(guild, logger=logger)
        self.channel = guild.get_channel(channel)

    async def __call__(self, message):
        await self.channel.send(
            content=message.content,
            embed=message.embeds[0] if message.embeds else None,
        )
        messages.bus(self.guild).publish('action.copy', message=message, channel=self.channel)


@Action.register
class Delete(Action):
    async def __call__(self, message, context=None):
        await message.delete()
        messages.bus(self.guild).publish('action.delete', message=message)


@Action.register
class Pin(Action):
    async def __call__(self, message, context=None):
        await message.pin()
        messages.bus(self.guild).publish('action.pin', message=message)


@Action.register
class AddReaction(Action):
    """ Action that adds a reaction to triggering message """
    def __init__(self, guild, emoji, logger=None):
        super().__init__(guild, logger=logger)
        table = util_emoji.build_emoji_dict(guild)
        self.emoji = util_emoji.lookup_emoji(emoji, custom=table)

    async def __call__(self, message, context=None):
        await message.add_reaction(self.emoji)


@Action.register
class GrantRole(Action):
    def __init__(self, guild, role, reason=None, logger=None):
        super().__init__(guild, logger=logger)
        self.role = next(obj for obj in guild.roles if obj.id == role)
        self.reason = reason

    async def __call__(self, message, context=None):
        await message.author.add_roles(self.role, reason=self.reason)
        self.logger.info('granted role {guild.name} → {role.name} to {user.name} [{user.id}]'.format(
                         guild=self.guild, role=self.role, user=message.author))
        messages.bus(self.guild).publish('action.grant_role', member=message.author,
                                         role=self.role, reason=self.reason)
