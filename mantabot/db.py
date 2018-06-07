import aiopg.sa
import asyncio
import mantabot.conf
import json
import sqlalchemy
from sqlalchemy import *
from sqlalchemy import sql

engines = {}

metadata = sqlalchemy.MetaData()


async def connection(name='default'):
    """ Get an asynchronous database connection for given database """
    global engines
    try:
        return engines[name].acquire()
    except KeyError:
        pass

    try:
        config = mantabot.conf.settings['databases'][name]
    except KeyError:
        raise mantabot.conf.ConfigurationError('Unconfigured database %s' % name)

    engines[name] = engine = await aiopg.sa.create_engine(**config)
    return engine.acquire()

def management_connection(name='default'):
    """ Get a management connection (synchronous) for given database """
    try:
        config = mantabot.conf.settings['databases'][name]
    except KeyError:
        raise mantabot.conf.ConfigurationError('Unconfigured database %s' % name)

    engine = sqlalchemy.create_engine(sqlalchemy.engine.url.URL('postgresql', **config))
    return engine.connect()

async def shutdown():
    """ Close all open database connections """
    global engines
    for engine in engines.values():
        engine.close()

    await asyncio.gather(*[engine.wait_closed() for engine in engines.values()])

# ============================================================================
# Generic app settings

SettingsTable = sqlalchemy.Table('settings', metadata,
    sqlalchemy.Column('guild_id', sqlalchemy.BigInteger, primary_key=True),
    sqlalchemy.Column('app', sqlalchemy.String(250), primary_key=True),
    sqlalchemy.Column('data', sqlalchemy.Text()),
)

class DBSettingsProxy(dict):
    def __init__(self, app, guild_id, data):
        super(DBSettingsProxy, self).__init__()
        self._app = app
        self._guild_id = guild_id
        self.sequence = 1
        self.update(data)

    async def save(self):
        data = json.dumps(self)

        async with await connection() as conn:
            while True:
                async with conn.begin():
                    result = await conn.execute(
                        SettingsTable.update().where(SettingsTable.c.guild_id==self._guild_id)
                                            .where(SettingsTable.c.app==self._app)
                                            .values(data=data)
                    )
                    if result.rowcount > 0:
                        break
                    try:
                        await conn.execute(
                            SettingsTable.insert().values(
                                guild_id=self._guild_id, app=self._app, data=data
                            )
                        )
                    except sqlalchemy.exc.IntegrityError:
                        continue
                    break
        self.sequence += 1


class DBSettingsCache(object):
    def __init__(self):
        self.cache = {}

    async def get(self, app, guild, loader=None):
        key = (app, guild.id)
        try:
            return self.cache[key]
        except KeyError:
            pass
        query = (SettingsTable.select().where(SettingsTable.c.guild_id==guild.id)
                                       .where(SettingsTable.c.app==app))

        data = {}
        async with await connection() as conn:
            result = await conn.execute(query)
            row = await result.first()
            data = json.loads(row['data']) if row else {}

        if callable(loader):
            data = loader(data)
        obj = DBSettingsProxy(app, guild.id, data)
        self.cache[key] = obj
        return obj

    def invalidate(self, app, guild):
        try:
            del self.cache[(app, guild.id)]
        except KeyError:
            pass

settings = DBSettingsCache()
