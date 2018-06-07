from mantabot.core import management
from mantabot import db


@management.Command.register
class CreateDB(management.Command):
    help = 'create the database'

    def handle(self, **kwargs):
        with db.management_connection() as connection:
            self.write(', '.join(table.name for table in db.metadata.sorted_tables))
            db.metadata.create_all(connection)
        return 0


@management.Command.register
class DropDB(management.Command):
    help = 'destroy the database'

    def add_arguments(self, parser):
        parser.add_argument('confirm', nargs='?', help='write confirm in capital letters')

    def handle(self, **kwargs):
        if kwargs.get('confirm') != 'CONFIRM':
            self.write('Operation not confirmed, not performing it')
            return 1

        with db.management_connection() as connection:
            self.write(', '.join(table.name for table in db.metadata.sorted_tables))
            db.metadata.drop_all(connection)
        return 0
