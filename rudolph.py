import configparser

import praw
from discord.ext import commands

import banhammer

bot = commands.Bot("!", description="SCW's Banhammer 🔨.")
bh = banhammer.Banhammer(praw.Reddit("RTR"), bot=bot, change_presence=True)

bh.add_subreddits("SantasChristmasWish")


@bot.event
async def on_command_error(ctx, error):
    print(error)


@bot.event
async def on_ready():
    print(str(bot.user) + ' is running.')
    bh.run()


@bot.command()
async def subreddits(ctx):
    await ctx.send(embed=bh.get_subreddits_embed())


@bot.command()
async def reactions(ctx):
    await ctx.send(embed=bh.get_reactions_embed())


@bh.mail()
async def handle_mail(p):
    msg = await bot.get_channel(596006288987783180).send(embed=p.get_embed())
    await p.add_reactions(msg)


config = configparser.ConfigParser()
config.read("discord.ini")
bot.run(config["RTR"]["token"])
