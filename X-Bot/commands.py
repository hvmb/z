import helper
import discord
import asyncio
import exceptions

from views import link
from discord.ext import commands
from discord import app_commands


class Commands(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot


    @app_commands.command(name='profile', description='Displays gamertag or XUIDs profile')
    @app_commands.describe(arg='Gamertag or XUID')
    @app_commands.guild_only
    async def _profile(self, interaction: discord.Interaction, arg: str):
        if helper.settings['Application']['Test mode'] and interaction.user.id != 1057753454388453416:
            return await interaction.response.send_message(':warning: I am currently in **Test Mode**. Please try this command again later!', ephemeral=True)

        await interaction.response.defer()

        if arg.isdigit() and len(arg) > 15:
            found = []
            
        else:
            found = await helper.grab_xuids(arg)

            if not found:
                embed = discord.Embed(color=0xff0000)
                embed.set_author(name=f'Gamertag is invalid!', icon_url='https://th.bing.com/th/id/R.c1ab0eaefe96d3c24dbcd1f706f9b772?rik=8flRJ%2bS8UxeReQ&pid=ImgRaw&r=0')

                return await interaction.edit_original_response(embed=embed)
            
            arg = found[0].split('|')[0]

        try:
            information = await helper.gather_information(arg, options=['gamertag', 'uniqueModernGamertag', 'gamerScore', 'tenure', 'displayPicRaw', 'bio', 'location', 'realName', 'followerCount', 'followingCount', 'linkedAccounts', 'primaryColor', 'presenceText', 'Device'])

        except exceptions.InvalidXUIDError:
            embed = discord.Embed(color=0xff0000)
            embed.set_author(name=f'XUID is invalid!', icon_url='https://th.bing.com/th/id/R.c1ab0eaefe96d3c24dbcd1f706f9b772?rik=8flRJ%2bS8UxeReQ&pid=ImgRaw&r=0')

            return await interaction.edit_original_response(embed=embed)

        gamertag = information[0]
        unique_modern_gamertag = information[1]
        gamerscore = information[2]
        tenure = information[3]
        display_pic_raw = information[4]
        bio = information[5]
        location = information[6]
        real_name = information[7]
        follower_count = information[8]
        following_count = information[9]
        linked_accounts = information[10]
        primary_color = information[11]
        presence_text = information[12]
        device = information[13]

        #if following_count > 0:
        #    pastebin_url = await helper.generate_friend_list_pastebin(arg)

        if primary_color is None:
            color = 0x107c10
        else:
            color = int(primary_color, 16)

        try:
            title_history = await helper.get_title_history(arg)

        except exceptions.NoTitleHistoryError:
            has_played = False
        else:
            has_played = True

        content = f'''
        {f'> **Real name:** ` {real_name} `' if real_name else '> **Real name:** ` Private `'}
        > **Gamerscore:** ` {gamerscore} `
        > **Tenure level:** ` {tenure} `
        > **Followers:** ` {follower_count} `
        > **Friends:** ` {following_count} `
        {f'> **Location:** ` {location} `' if location else '> **Location:** ` Private `'}
        {f'> **Bio:** ` {bio} `' if bio else '> **Bio:** ` Private `'}
        '''

        embed = discord.Embed(title=f'*{f"{unique_modern_gamertag} ({gamertag})" if gamertag != unique_modern_gamertag else gamertag}{helper.single_quote if gamertag[-1] == "s" else f"{helper.single_quote}s"} Profile*', url=f'https://xboxgamertag.com/search/{gamertag.replace(" ", "-")}', description=content, color=color)

        embed.set_thumbnail(url=display_pic_raw)

        if has_played:
            embed.add_field(name=f'*First Played ({title_history[1]})*', value=f'` {title_history[2]} ({title_history[0]}) `', inline=False)
            embed.add_field(name=f'*Last Played ({title_history[4]})*', value=f'` {title_history[5]} ({title_history[3]}) `', inline=False)

        embed.set_footer(text=presence_text if device is None else f'{presence_text} ({device})')

        embeds = [embed]

        if len(found) > 1:
            versions_embed = discord.Embed(description=':warning: Found multiple versions for this gamertag!', color=0x36393f)

            for combination in found:
                versions_embed.add_field(name=f'*{combination.split("|")[1]}*', value=f'**XUID:** ` {combination.split("|")[0]} `', inline=False)

            embeds.append(versions_embed)

        if linked_accounts:
            account_links = []

            #if following_count > 0:
            #    account_links.append(f'Friend List|{pastebin_url}')

            for index, _ in enumerate(linked_accounts):
                account_links.append(f'{linked_accounts[index]["networkName"]} ({linked_accounts[index]["displayName"]})|{linked_accounts[index]["deeplink"]}')

            await interaction.edit_original_response(embeds=embeds, view=link.View(account_links))

        else:
            #if following_count > 0:
            #    await interaction.edit_original_response(embeds=embeds, view=link.View([f'Friend List|{pastebin_url}']))
            #else:
                
            await interaction.edit_original_response(embeds=embeds)

    
    @app_commands.command(name='xuid', description='Grabs a gamertags XUID')
    @app_commands.guild_only
    async def _xuid(self, interaction: discord.Interaction, gamertag: str):
        if helper.settings['Application']['Test mode'] and interaction.user.id != 1057753454388453416:
            return await interaction.response.send_message(':warning: I am currently in **Test Mode**. Please try this command again later!', ephemeral=True)

        await interaction.response.defer()

        found = await helper.grab_xuids(gamertag)

        if not found:
            embed = discord.Embed(color=0xff0000)
            embed.set_author(name=f'Gamertag is invalid!', icon_url='https://th.bing.com/th/id/R.c1ab0eaefe96d3c24dbcd1f706f9b772?rik=8flRJ%2bS8UxeReQ&pid=ImgRaw&r=0')

            return await interaction.edit_original_response(embed=embed)

        xuid = found[0].split("|")[0]

        information = await helper.gather_information(xuid, options=['gamertag', 'uniqueModernGamertag', 'displayPicRaw', 'primaryColor'])

        gamertag = information[0]
        unique_modern_gamertag = information[1]
        display_pic_raw = information[2]
        primary_color = information[3]

        if primary_color is None:
            color = 0x107c10
        else:
            color = int(primary_color, 16)

        embed = discord.Embed(title=f'*{f"{unique_modern_gamertag} ({gamertag})" if gamertag != unique_modern_gamertag else gamertag}{helper.single_quote if gamertag[-1] == "s" else f"{helper.single_quote}s"} XUID*', color=color)

        embed.set_thumbnail(url=display_pic_raw)

        embed.add_field(name=f'*Hexadecimal*', value=f'` {hex(int(xuid))} `', inline=False)
        embed.add_field(name=f'*Decimal*', value=f'` {xuid} `', inline=False)

        await interaction.edit_original_response(embed=embed)

            
    @app_commands.command(name='gamerpic', description='Grabs a gamertag or XUIDs gamerpic')
    @app_commands.describe(arg='Gamertag or XUID')
    @app_commands.guild_only
    async def _gamerpic(self, interaction: discord.Interaction, arg: str):
        if helper.settings['Application']['Test mode'] and interaction.user.id != 1057753454388453416:
            return await interaction.response.send_message(':warning: I am currently in **Test Mode**. Please try this command again later!', ephemeral=True)

        await interaction.response.defer()

        if arg.isdigit() and len(arg) > 15:
            pass

        else:
            found = await helper.grab_xuids(arg)

            if not found:
                embed = discord.Embed(color=0xff0000)
                embed.set_author(name=f'Gamertag is invalid!', icon_url='https://th.bing.com/th/id/R.c1ab0eaefe96d3c24dbcd1f706f9b772?rik=8flRJ%2bS8UxeReQ&pid=ImgRaw&r=0')

                return await interaction.edit_original_response(embed=embed)
            
            arg = found[0].split('|')[0]

        try:
            information = await helper.gather_information(arg, options=['gamertag', 'uniqueModernGamertag', 'displayPicRaw', 'primaryColor'])

        except exceptions.InvalidXUIDError:
            embed = discord.Embed(color=0xff0000)
            embed.set_author(name=f'XUID is invalid!', icon_url='https://th.bing.com/th/id/R.c1ab0eaefe96d3c24dbcd1f706f9b772?rik=8flRJ%2bS8UxeReQ&pid=ImgRaw&r=0')

            return await interaction.edit_original_response(embed=embed)

        gamertag = information[0]
        unique_modern_gamertag = information[1]
        display_pic_raw = information[2]
        primary_color = information[3]

        if primary_color is None:
            color = 0x107c10
        else:
            color = int(primary_color, 16)

        embed = discord.Embed(title=f'*{f"{unique_modern_gamertag} ({gamertag})" if gamertag != unique_modern_gamertag else gamertag}{helper.single_quote if gamertag[-1] == "s" else f"{helper.single_quote}s"} Gamerpic*', url=display_pic_raw, color=color)

        embed.set_image(url=display_pic_raw)

        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name='credits', description='Displays Bot Credits')
    @app_commands.guild_only
    async def _credits(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = discord.Embed(title=f'**Bot Credits**')

        embed.add_field(name=f'*Created By*', value=f'`Horror`', inline=False)
        embed.add_field(name=f'*Edited And Optimized By*', value=f'`Putin#3649`', inline=False)

        await interaction.edit_original_response(embed=embed)

async def setup(bot):
    commands = Commands(bot)

    asyncio.create_task(helper.xbl2_token_updater())

    for user_token in [user_token.strip() for user_token in open('user_tokens.txt').readlines()]:
        asyncio.create_task(helper.xbl3_token_updater(user_token))

    await bot.add_cog(commands)
