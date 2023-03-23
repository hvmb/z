import json
import helper
import objects
import discord
import asyncio
import simplejson
import aiohttp
import time

from datetime import datetime
from discord.ext import commands
from discord import app_commands
from dateutil.relativedelta import relativedelta

class Reserve(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot


    @staticmethod
    def check_if_plan_expired(user_id: int):
        with open('purchases.json', 'r') as _file:
            purchases = json.load(_file)

        for index, _ in enumerate(purchases):
            if str(user_id) == purchases[index]['User ID']:
                expiry_date, today = datetime.strptime(purchases[index]['Expiry date'], '%Y-%m-%d %H:%M:%S.%f'), datetime.today()

                if expiry_date.date() <= today.date():
                    return True


    async def update_embed_followers(self, interaction: discord.Interaction, amounttoadd: str, information: str):
        gamertag = information[0]
        display_pic_raw = information[1]
        primary_color = information[3]
        follower_count = information[2]
        if primary_color is None:
            color = 0x107c10
        else:
            color = int(primary_color, 16)
        embed = discord.Embed(title=f'Target: {gamertag}', url=f'https://xboxgamertag.com/search/{gamertag.replace(" ", "-")}', color=color)
        embed.set_thumbnail(url=display_pic_raw)
        embed.add_field(name='*Follower count*', value=f'` {follower_count} `')
        embed.add_field(name='*Amount to add*', value=f'` {amounttoadd} `')
        embed.set_footer(text='Developed By Putin')
        await interaction.edit_original_response(embed=embed)
        await asyncio.sleep(0.5)


    async def follow(self, xuid: str, amounttoadd: str):
        print()
        for _ in range(int(amounttoadd)):
            token = helper.xbl3_token()
            url = f'https://social.xboxlive.com/users/xuid({token.xuid})/people/xuids?method=add'
            headers = {
                'Authorization': f'XBL3.0 x={token.uhs};{token.token}',
                'Accept-Charset': 'UTF-8',
                'x-xbl-contract-version': '2',
                'Accept': 'application/json',
                'Content-Type': "application/json",
                'Host': 'social.xboxlive.com',
                'Expect': '100-continue',
                'Connection': 'Keep-Alive',
            }
            payload = {
                'xuids': [xuid.split("|")[0]]
            }
            async with helper.aiohttp_session.post(url, headers=headers, json=payload) as res:
                if res.status == 200 or res.status == 204:
                    print("Successfully Followed User")
                else:
                    pass
            time.sleep(1)

    @app_commands.command(name='follow')
    async def _follow(self, interaction: discord.Interaction, gamertag: str, amounttoadd: str):
         if helper.settings['Application']['Test mode'] and interaction.user.id != 532576383331860544:
             return await interaction.response.send_message(':warning: I am currently in **Test Mode**. Please try this command again later!', ephemeral=True)

         with open('purchases.json', 'r') as _file:
             purchases = json.load(_file)

         user_id = interaction.user.id

         if str(user_id) not in [purchases[index]['User ID'] for index, _ in enumerate(purchases)]:
             return await interaction.response.send_message(':warning: This feature is paid only.')

         expired = self.check_if_plan_expired(user_id)

         if expired:
             return await interaction.response.send_message(f':warning: <@{user_id}> your plan has expired! If you\'d like to renew it, PM <@1057753454388453416>.', ephemeral=True)

         await interaction.response.defer(ephemeral=True)

         found = await helper.grab_xuids(gamertag)

         if not found:
             embed = discord.Embed(color=0xff0000)
             embed.set_author(name=f'Target is invalid!', icon_url='https://th.bing.com/th/id/R.c1ab0eaefe96d3c24dbcd1f706f9b772?rik=8flRJ%2bS8UxeReQ&pid=ImgRaw&r=0')

             return await interaction.edit_original_response(embed=embed)

         xuid = found[0].split('|')[0]

         information = await helper.gather_information(xuid, options=['gamertag', 'displayPicRaw', 'primaryColor', 'followerCount'])

         asyncio.create_task(self.update_embed_followers(interaction, amounttoadd, information))
         asyncio.create_task(self.follow(found[0], amounttoadd))

    @app_commands.command(name='auth', description='Authenticates user from discord ID')
    async def _auth(self, interaction: discord.Interaction, user_id: str, days: int):
        if await self.bot.is_owner(interaction.user) == False:
           return await interaction.response.send_message('You are not authorized to use this command', ephemeral=True)
        with open('purchases.json', 'r') as _file:
            purchases = json.load(_file)

        if any(purchases[index]['User ID'] == user_id for index, _ in enumerate(purchases)):
            #return await ctx.reply(f':warning: **{user_id}** already has a plan!')
            return await interaction.response.send_message('user is already registered', ephemeral=True)

        purchase_date = datetime.now()
        expiry_date = purchase_date + relativedelta(days=days)

        purchases.append({
            "User ID": user_id,
            "Purchase date": str(purchase_date),
            "Expiry date": str(expiry_date),
        })

        with open('purchases.json', 'w+') as _file:
            _file.write(simplejson.dumps(purchases, indent=4))

        return await interaction.response.send_message(f'**{user_id}** is now authenticated', ephemeral=True)


async def setup(bot):
    reserve = Reserve(bot)

    await bot.add_cog(reserve)
