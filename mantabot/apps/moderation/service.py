import datetime
from mantabot import db, messages

SETTINGS_KEY = 'moderation'

class BotPermissionDenied(RuntimeError):
    pass

# ============================================================================

def settings_loader(data):
    mute = {}
    for member_id, member_mutes in data.get('mute', {}).items():
        mute[int(member_id)] = {int(channel_id): expiration
                                for channel_id, expiration in member_mutes.items()}
    data['mute'] = mute
    return data

# ============================================================================
# User mute feature

async def get_channel_mutes(channel):
    guild = channel.guild
    settings = await db.settings.get(SETTINGS_KEY, channel.guild, loader=settings_loader)
    mutes = settings['mute']

    timestamp = datetime.datetime.utcnow().timestamp()

    return [(guild.get_member(user_id), channel_list[channel.id] - timestamp)
            for user_id, channel_list in mutes.items()
            if channel.id in channel_list and channel_list[channel.id] > timestamp]

async def get_channel_member_muted(channel, member):
    settings = await db.settings.get(SETTINGS_KEY, channel.guild, loader=settings_loader)
    mutes = settings['mute']

    timestamp = datetime.datetime.utcnow().timestamp()

    try:
        member_mutes = mutes[member.id]
    except KeyError:
        return False
    try:
        expiration = member_mutes[channel.id]
    except KeyError:
        return False

    if expiration < timestamp:
        del member_mutes[channel.id]
        if not member_mutes:
            del mutes[member.id]
        await settings.save()
        return False

    return True

async def add_channel_mutes(channel, members, duration, **context):
    settings = await db.settings.get(SETTINGS_KEY, channel.guild, loader=settings_loader)
    mutes = settings['mute']

    timestamp = int(datetime.datetime.utcnow().timestamp() + duration)

    for member in members:
        mutes.setdefault(member.id, {})[channel.id] = timestamp
        messages.bus(member.guild).publish('mute.add',
            channel=channel, member=member, duration=duration,
            **context
        )
    await settings.save()

async def remove_channel_mutes(channel, members, **context):
    settings = await db.settings.get(SETTINGS_KEY, channel.guild, loader=settings_loader)
    mutes = settings['mute']

    timestamp = datetime.datetime.utcnow().timestamp()

    dirty = False
    for member in members:
        try:
            member_mutes = mutes[member.id]
        except KeyError:
            continue
        try:
            expiration = member_mutes[channel.id]
        except KeyError:
            continue
        del member_mutes[channel.id]
        dirty = True

        if not member_mutes:
            del mutes[member.id]
        if expiration > timestamp:
            messages.bus(member.guild).publish('mute.remove', channel=channel, member=member, **context)
    if dirty:
        await settings.save()

# ============================================================================
# Readonly channel feature

async def get_readonly(channel):
    settings = await db.settings.get(SETTINGS_KEY, channel.guild, loader=settings_loader)
    return channel.id in settings.setdefault('readonly', [])

async def set_readonly(channel, enable, **context):
    settings = await db.settings.get(SETTINGS_KEY, channel.guild, loader=settings_loader)
    enabled = channel.id in settings.setdefault('readonly', [])
    if enabled == enable:
        return

    if enable and not channel.permissions_for(channel.guild.me).manage_messages:
        raise BotPermissionDenied()

    if enable:
        settings['readonly'].append(channel.id)
    else:
        settings['readonly'].remove(channel.id)
    await settings.save()
    messages.bus(channel.guild).publish('readonly.set', channel=channel, enable=enable, **context)
