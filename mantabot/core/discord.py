import asyncio, collections, discord, logging, sys, weakref
from mantabot import conf
from mantabot.core import messages, private

logger = logging.getLogger(__name__)


class CancelContext(object):
    """ Request that current task gets early cancellation from discord Client on shutdown """
    def __init__(self, client):
        self.client = client

    def __enter__(self):
        self.task = task = asyncio.Task.current_task()
        self.client._close_tasks.append(task)

    def __exit__(self, exc_type, exc_value, tb):
        ref = self.client._close_tasks
        idx = ref.index(self.task)
        if idx == len(ref) - 1:
            ref.pop()
        else:
            ref[idx] = ref.pop()


class Client(discord.Client):
    """ Main bot object, handling connection to discord and receiving events """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._close_tasks = []
        self._handlers = collections.OrderedDict()
        self.private_chats = weakref.WeakValueDictionary()
        self.initialized = False

    def add_handlers(self, handlers, **kwargs):
        self._handlers.update(handlers, **kwargs)

    def get_handler(self, name):
        return self._handlers[name]

    def cancellable(self):
        """ Returns a context manager that registers calling task for on-close cancellation """
        return CancelContext(self)

    async def close(self):
        """ Cancel event _handlers before closing the connection.
            This lets them send some last instructions to discord before shutting down.
        """
        if self.is_closed():
            return
        await messages.bus().publish_sync('core.close', client=self)
        gathered = asyncio.gather(*self._close_tasks, loop=self.loop, return_exceptions=True)
        gathered.cancel()
        for result in await gathered:
            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                logger.error("exception at close: %r" % result)
        await super(Client, self).close()

    def get_private_chat(self, user):
        """ Obtain a direct communication channel to the user """
        try:
            return self.private_chats[user.id]
        except KeyError:
            chat = private.PrivateChat(self, user)
            self.private_chats[user.id] = chat
            return chat

    async def _forward_event(self, event, *args, **kwargs):
        """ Internal helper to forward event to handlers outside of automatic event """
        with CancelContext(self):
            for handler in self._handlers.values():
                try:
                    handler = getattr(handler, event)
                except AttributeError:
                    continue
                await handler(*args, **kwargs)

    async def on_ready(self):
        """ Called when discord api is ready """
        if self.initialized:
            logger.info('Reconnected as %s [%s]', self.user.name, self.user.id)
            return
        self.initialized = True

        logger.info('Connected as %s [%s]', self.user.name, self.user.id)
        for guild in self.guilds:
            logger.info('    -> on guild %s [%s]', guild.name, guild.id)

        await self._forward_event('on_ready')
        messages.bus().publish('core.ready', client=self)

    async def on_error(self, event, *args, **kwargs):
        if conf.settings.get('debug', False):
            logger.exception('discord error in event: %s' % event)
        else:
            info = sys.exc_info()
            logger.error('%s in %s event: %s', info[0].__name__, event, info[1])

    async def on_guild_remove(self, guild):
        await self._forward_event('on_guild_remove', guild)
        messages.destroy_bus(key=guild)

    def __getattr__(self, key):
        """ Generate automatic forwarding of events to plugins as requested

            This automatically generates an event handler, that loops through
            self._handlers and invokes the matching handler if it exists.
        """
        if key.startswith('on_'):
            async def caller(client, *args, **kwargs):
                with CancelContext(client):
                    for handler in client._handlers.values():
                        try:
                            method = getattr(handler, key)
                        except AttributeError:
                            continue
                        await method(*args, **kwargs)
            caller.__name__ = key
            method = caller.__get__(self)
            setattr(self, key, method)
            return method
        raise AttributeError("'%s' object has no attribute '%s'"
                             % (self.__class__.__name__, key))
