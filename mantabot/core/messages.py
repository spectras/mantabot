import asyncio, collections, logging

logger = logging.getLogger(__name__)


def event_handler(name, **filters):
    """ Mark a class method as a message bus event handler """
    def decorator(method):
        method.event_name = name
        method.event_filters = filters
        return method
    return decorator


class MessageBus(object):
    """ Lightweight, non-persistent, message bus """

    def __init__(self, name=None, loop=None):
        self.name = name
        self.loop = loop
        self.subscribers = collections.defaultdict(list)

    def subscribe(self, obj):
        """ Automatically register all decorated event handlers on obj """
        for key in dir(obj):
            value = getattr(obj, key)
            event_name = getattr(value, 'event_name', None)
            if event_name and callable(value):
                self.subscribe_method(obj, key, event_name, **value.event_filters)
        return obj

    def subscribe_method(self, obj, key, event, **filters):
        """ Subscribe object method """
        if not asyncio.iscoroutinefunction(getattr(obj, key)):
            raise TypeError('Must pass an asynchronous method name')
        self.subscribers[event].append((obj, key, filters))

    def unsubscribe(self, obj):
        """ Cancal all subscribtions for given object """
        for target in self.subscribers.values():
            target[:] = (item for item in target if item[0] != obj)

    async def publish_sync(self, event, **data):
        """ Run all handlers for the event """
        logger.debug('bus(%s): publish(%r, %s)' % (
                     self.name, event, ', '.join('%s=%s' % (key, value) for key, value in data.items())))
        tasks = [
            getattr(subscriber[0], subscriber[1])(**data)
            for subscriber in self.subscribers[event]
            if all(data.get(key) == value for key, value in (subscriber[2] or {}).items())
        ]
        tasks.extend(
            getattr(subscriber[0], subscriber[1])(event, **data)
            for subscriber in self.subscribers['*']
        )
        if not tasks:
            return

        for task in asyncio.as_completed(tasks, loop=self.loop):
            try:
                await task
            except Exception:
                logger.exception('Exception while processing event %s', event)

    def publish(self, event, **data):
        """ Schedule all handlers for that event, return the controlling task """
        return asyncio.ensure_future(self.publish_sync(event, **data), loop=self.loop)

_buses = {}

def bus(key=None):
    global _buses
    try:
        obj = _buses[key]
    except KeyError:
        _buses[key] = obj = MessageBus(name=key)
    return obj

def destroy_bus(*, key):
    global _buses
    try:
        del _buses[key]
    except KeyError:
        pass
