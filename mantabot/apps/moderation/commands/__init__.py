from mantabot import command
from mantabot.apps.moderation.commands.ban import Ban
from mantabot.apps.moderation.commands.clear import Clear
from mantabot.apps.moderation.commands.mute import Mute, Unmute
from mantabot.apps.moderation.commands.readonly import ReadOnly

moderation_group = command.CommandGroup('moderation')
moderation_group.register(Ban)
moderation_group.register(Clear)
moderation_group.register(Mute)
moderation_group.register(ReadOnly)
moderation_group.register(Unmute)

__all__ = ('Ban', 'Clear', 'Mute', 'ReadOnly', 'Unmute')
