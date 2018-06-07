from mantabot import db

CommandPermission = db.Table('command_permission', db.metadata,
    db.Column('permission_id', db.BigInteger, primary_key=True, autoincrement=True),
    db.Column('guild_id', db.BigInteger, index=True),
    db.Column('group_name', db.String(64)),
    db.Column('role_id', db.BigInteger),
    db.Column('channels', db.Text()),
    db.Column('settings', db.Text()),
)
