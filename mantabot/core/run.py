import asyncio, importlib, logging, os, signal
from mantabot.core import discord, management
from mantabot import conf, db, session

logger = logging.getLogger(__name__)


@management.Command.register
class Run(management.Command):
    help = 'run the bot'

    def handle(self, **kwargs):
        """ Bot entry point """
        token = os.environ.get('DISCORD_TOKEN') or conf.settings.get('discord_token')
        if not token:
            logger.critical('DISCORD_TOKEN missing')
            return 1

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.check_connection())

        mainbot = discord.Client(max_messages=100, loop=loop)
        mainbot.add_handlers(self.load_handlers(mainbot))

        def shutdown():
            asyncio.ensure_future(mainbot.close(), loop=loop)
        loop.add_signal_handler(signal.SIGINT, shutdown)
        loop.add_signal_handler(signal.SIGTERM, shutdown)

        try:
            loop.run_until_complete(mainbot.start(token))
        except Exception as exc:
            # In debug mode, let the exception through (to potential debugger),
            # otherwise log it normally
            if conf.settings.get('debug', False):
                raise
            logger.exception('aborting bot')
            return 2

        finally:
            # Notify all tasks we are shutting down and try our best to let them complete
            pending = [task for task in asyncio.Task.all_tasks(loop=loop) if not task.done()]
            logger.info('shutting down %s background tasks', len(pending))
            gathered = asyncio.gather(*pending, return_exceptions=True, loop=loop)
            gathered.cancel()

            for result in loop.run_until_complete(gathered):
                if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                    logger.error("exception at shutdown: %r" % result)

            # Shutdown remaining services
            loop.run_until_complete(db.shutdown())      # let database sessions disconnect
            loop.run_until_complete(session.shutdown()) # free all utility resources
            loop.close()                                # job done
            logging.shutdown()
        return 0

    async def check_connection(self):
        """ attempt to connect to database """
        async with await db.connection():
            logger.debug('successfully connected to default database')

    def load_handlers(self, client):
        """ load and instantiate all discord event handlers """

        paths = conf.settings.get('handlers')
        if paths is None:
            raise conf.ConfigurationError('Handler list is missing')

        handlers = {}
        for path in paths:
            module_path, key = path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            klass = getattr(module, key)
            name = getattr(klass, 'name', klass.__name__)
            handlers[name] = klass(client)
        return handlers
