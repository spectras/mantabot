""" Command Group plugin

A command group is a set of commands that can be attached to a dispatcher.
It watches its designated channels and runs commands it recognizes.
"""
import asyncio
import discord
import logging
import shlex
from mantabot import messages

logger = logging.getLogger(__name__)

class PermissionDenied(RuntimeError):
    pass

# ============================================================================

class Command(object):
    """ Single abstract command, inherited by commands """
    name = None
    errors = None

    def __init__(self, group, client, output):
        self.group = group
        self.client = client
        self.output = output

    async def execute(self, message, args):
        """ Execute the command with given arguments in message's context """
        raise NotImplementedError

    async def send(self, *args, **kwargs):
        """ Send output to command initiator - arguments are passed through to output plugin """
        return await self.output.send(*args, **kwargs)

    async def error(self, error, *args, **kwargs):
        """ Send error to command initiator - arguments are formatted with the error message """
        return await self.output.error(self.errors[error].format(*args, **kwargs))

# ============================================================================

class CommandGroup(object):
    """ Holds a group of command - instantiated once per run """

    registry = []   # class-level registry

    def __init__(self, name, register=True):
        self.name = name
        self.commands = {}
        if register:
            CommandGroup.registry.append(self)

    def clone(self):
        obj = self.__class__(self.name, register=False)
        obj.commands = self.commands.copy()
        return obj

    def register(self, command):
        """ decorator to register commands onto this command group """
        self.commands[command.name] = command
        logger.debug('registered command %s -> %s' % (self.name, command.name))
        return command

    async def on_command(self, client, message, name, args, settings, output):
        """ Run the command of the group """

        command = self.commands[name](self, client, output)

        # Check command permissions
        try:
            await self.check_permissions(client, message, command)
        except PermissionDenied as exc:
            if getattr(exc, 'message', None) is not None:
                await output.error(exc.message)
            return

        # Run command and handle errors
        logger.info('{user} [{userid}] runs {name} {args}'.format(
            user=message.author.name,
            userid=message.author.id,
            name=name,
            args=' '.join(shlex.quote(arg) for arg in args),
        ))
        messages.bus(message.channel.guild).publish('command.run', command=command,
                                                    name=name, args=args,
                                                    message=message, user=message.author)

        try:
            await command.execute(message, args)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                'Execution of command "{name}" with arguments ({args}) raised unhandled exception'
                .format(name=name, args=', '.join(repr(arg) for arg in args))
            )
            await output.error('Internal error')

    async def check_permissions(self, client, message, command):
        """ Raise PermissionDenied if command is not allowed """
        pass
