import helper
import asyncio
import nest_asyncio

from discord.ext import commands
from discord import app_commands
from datetime import datetime

bot = commands.Bot(command_prefix="?", tree_cls=app_commands.CommandTree, intents=None, help_command=None)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(datetime.today())
    
    asyncio.create_task(helper.stats_updater())
            
            
async def initialize():
    await helper.set_session()
    
    await bot.load_extension('reserve')
    await bot.load_extension('commands')
    
    await bot.run(helper.settings['Bot']['Token'], log_handler=None)


if __name__ == '__main__':
    nest_asyncio.apply()

    asyncio.run(initialize())
