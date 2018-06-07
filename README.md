MantaBot
========

Asynchronous Discord bot engine written in python.

Builds upon the amazing [discord.py](https://github.com/Rapptz/discord.py) library to provide all the tools required for a complex bot that can run several features in separate apps, all as a single bot, as a production service.

**This project audience is bot developers looking for a framework, it has little functionality on its own.**

This is personal code that I share. I do not intend to provide long term support, though I will do my best to help should you have issues with it. Feel free to fork it and contribute back.


Features
--------

* Full skeleton bot that actually loads and runs out of the box.
* App-based design: each feature is an app, and can be enabled/disabled independently.
* Designed for production. Well-behaved service that loads from config file and environment variables, and produces usable logs.
* Includes a toolbox for common tasks:
    - Command handling with role-based permissions.
    - Asynchronous database connection.
    - Global and per-guild publish/subscribe message buses.
    - Direct message to users with app ownership.
    - Generating Discord embeds from YAML files.
    - Decoding emojis, including custom emojis.

A few simple apps are provided as examples, namely:

* A simple moderation app with `ban`, `clear`, text-`mute` and `readonly` features.
* A logging app that formats and posts bot events to a discord channel.
* A devtools app with a simple command to query various Discord identifiers.

If there is interest, I will write documentation. Simply open an issue.

Running
-------

```bash
pip install https://github.com/spectras/mantabot/archive/master.zip
export DISCORD_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXX.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXX
SETTINGS=config.yml mantabot.py createdb
SETTINGS=config.yml mantabot.py run
```

The sample `config-example.yml` is basic but functional, simply edit database configuration at the top.
