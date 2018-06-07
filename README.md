========
MantaBot
========

Asynchronous Discord bot engine written in python.

Builds upon the amazing `discord.py`_ library to provide all the tools required for a complex bot that can run several features in separate apps, all as a single bot, as a production service.

**This project audience is bot developers looking for a framework, it has not functionality on its own.**

This is personal code that I share. I do not intend to provide long term support, though I will do my best to help should you have issues with it. Feel free to fork it and contribute back.


Features
--------

* Full skeleton bot that actually loads and runs out of the box.
* App-based design: each feature is an app, and can be enabled/disabled independently.
* Designed for production. Well-behaved service that loads from config file and environment variables, and produces usable logs.
* Includes a toolbox for common tasks.

Running
-------

```bash
pip install mantabot
export DISCORD_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXX.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXX
SETTINGS=config-example.yml mantabot
```


.. _discord.py: https://github.com/Rapptz/discord.py

