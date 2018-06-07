""" Quick embed parser """
import discord, re
from mantabot.util import emoji

COLORRE = re.compile(r'rgb\(\s*([0-9]{1,3})\s*,'
                          r'\s*([0-9]{1,3})\s*,'
                          r'\s*([0-9]{1,3})\s*\)', flags=re.IGNORECASE)


class Parser(object):
    """ Simple parser for dict-based embed descriptions """

    title_limit = 256
    description_limit = 2048
    field_limit = 25
    field_name_limit = 256
    field_value_limit = 1024
    footer_limit = 2048
    author_name_limit = 256


    def __init__(self, guild=None):
        self.guild = guild
        self.emoji_dict = None if guild is None else emoji.build_emoji_dict(guild)

    def from_dict(self, data, template=None):
        embed = template or discord.Embed()
        embed.type = 'rich'

        for key, value in data.items():
            handler = getattr(self, 'parse_%s' % key, None)
            if handler:
                handler(embed, key, value)
        return embed

    def handle_emojis(self, text):
        if text is discord.Embed.Empty:
            return text
        return emoji.parse_emojis(text, custom=self.emoji_dict)

    parse_type = setattr
    parse_url = setattr
    parse_timestamp = setattr

    def parse_title(self, embed, key, value):
        if len(value) > self.title_limit:
            raise ValueError('title length cannot exceed %s' % self.title_limit)
        embed.title = value

    def parse_description(self, embed, key, value):
        value = self.handle_emojis(value)
        if len(value) > self.description_limit:
            raise ValueError('description length cannot exceed %s' % self.description_limit)
        embed.description = value

    def parse_color(self, embed, key, value):
        if isinstance(value, int):
            embed.colour = value
            return

        rgb = COLORRE.fullmatch(value)
        if rgb:
            red, green, blue = int(rgb.group(1)), int(rgb.group(2)), int(rgb.group(3))
            if red > 255 or green > 255 or blue > 255:
                raise ValueError('color channel value must be in range [0, 255]')
            embed.colour = discord.Colour.from_rgb(red, green, blue)
            return

        raise ValueError('unrecognized color format')

    def parse_image(self, embed, key, value):
        embed.set_image(url=value)

    def parse_thumbnail(self, embed, key, value):
        embed.set_thumbnail(url=value)

    def parse_author(self, embed, key, value):
        if value:
            name = self.handle_emojis(value.get('name', discord.Embed.Empty))
            if name is not discord.Embed.Empty and len(name) > self.author_name_limit:
                raise ValueError('author name length cannot exceed %s' % self.author_name_limit)

            embed.set_author(
                name=name,
                url=value.get('url', discord.Embed.Empty),
                icon_url=value.get('icon_url', discord.Embed.Empty),
            )
        else:
            embed.set_author()

    def parse_footer(self, embed, key, value):
        if value:
            text = self.handle_emojis(value.get('text', discord.Embed.Empty))
            if text is not discord.Embed.Empty and len(text) > self.footer_limit:
                raise ValueError('footer length cannot exceed %s' % self.footer_limit)

            embed.set_footer(
                text=text,
                icon_url=value.get('icon_url', discord.Embed.Empty),
            )
        else:
            embed.set_footer()

    def parse_fields(self, embed, key, value):
        if len(value) > self.field_limit:
            raise ValueError('field number cannot exceed %s' % self.field_limit)

        for field in value:
            name = self.handle_emojis(field.get('name', discord.Embed.Empty))
            value = self.handle_emojis(field.get('value', discord.Embed.Empty))
            if name is not discord.Embed.Empty and len(name) > self.field_name_limit:
                raise ValueError('field name length cannot exceed %s' % self.field_name_limit)
            if value is not discord.Embed.Empty and len(value) > self.field_value_limit:
                raise ValueError('field value length cannot exceed %s' % self.field_value_limit)

            embed.add_field(name=name, value=value, inline=field.get('inline', True))
