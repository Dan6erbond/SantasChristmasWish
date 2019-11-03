import configparser
import json

import praw
from discord.ext import commands

import banhammer

bot = commands.Bot("!", description="SCW's Banhammer 🔨.")
bh = banhammer.Banhammer(praw.Reddit("RTR"), bot=bot, change_presence=True)

bh.add_subreddits("SantasChristmasWish")
reddit = praw.Reddit("RTR")


# @bot.event
async def on_command_error(ctx, error):
    print(error)


@bot.event
async def on_ready():
    print(str(bot.user) + ' is running.')
    # bh.run()


@bot.command()
async def subreddits(ctx):
    await ctx.send(embed=bh.get_subreddits_embed())


@bot.command()
async def reactions(ctx):
    await ctx.send(embed=bh.get_reactions_embed())


@bot.command()
async def warning(ctx, user):
    user = user.replace("u/", "").replace("/", "").lower()
    redditor = reddit.redditor(user)

    for emoji in "🗑 👥 🎅 🖊 🔄 😠".split(" "):
        await ctx.message.add_reaction(emoji)

    def check(r, u):
        return u.id == ctx.author.id and r.message.id == ctx.message.id

    reaction = await bot.wait_for("reaction_add", check=check)

    emoji = reaction[0].emoji

    message = "You have been issued a warning from r/SantasChristmasWish for {reason}.\n" \
              "Please check our rules as a second warning will result in an immediate ban.\n" \
              "If you feel that this warning is incorrect please contact the Mods via the modmail"

    reason = "REASON"
    if emoji == "🗑":
        reason = "Deleting posts"
    elif emoji == "👥":
        reason = "Creating and using alt accounts"
    elif emoji == "🎅":
        reason = "Contacting Santas or Mods for gifts"
    elif emoji == "🖊":
        reason = "Changing your wishlist without mod permission"
    elif emoji == "🔄":
        reason = "reposting more than once every 10 days"
    elif emoji == "😠":
        reason = "Harassment of another Wisher"

    redditor.message("/r/SantasChristmasWish Warning", message.format(reason=reason),
                     from_subreddit="SantasChristmasWish")

    ux_message = "User successfully warned!"

    with open("files/warnings.json") as f:
        users = json.loads(f.read())
        found = False
        for u in users:
            if u["name"].lower() == user:
                found = True
                u["warnings"].append(reason)
                if len(u["warnings"]) >= 2:
                    ban_message = "You were banned for breaking the following rules:\n\n{}".format(
                        "\n".join(u["warnings"]))
                    note = ", ".join(u["warnings"])
                    reddit.subreddit("SantasChristmasWish").banned.add(user, ban_reason=reason, ban_message=ban_message,
                                                                       note=note)
                    redditor.message("/r/SantasChristmasWish Ban", ban_message,
                                     from_subreddit="SantasChristmasWish")
                    ux_message = "User successfully banned!"
                break
        if not found:
            users.append({
                "name": user.lower(),
                "warnings": [reason]
            })
        with open("files/warnings.json", "w+") as f:
            f.write(json.dumps(users, indent=4))

    await ctx.send(ux_message)


@bot.command()
async def ban(ctx, user):
    user = user.replace("u/", "").replace("/", "")
    for emoji in "🗑👥🎅🖊🔄😠":
        await ctx.message.add_reaction(emoji)

    def check(r, u):
        return u.id == ctx.author.id

    reaction = await bot.wait_for("reaction_add", check=check)

    emoji = reaction[0].emoji

    reason = "REASON"
    if emoji == "🗑":
        reason = "Deleting posts"
    elif emoji == "👥":
        reason = "Creating and using alt accounts"
    elif emoji == "🎅":
        reason = "Contacting Santas or Mods for gifts"
    elif emoji == "🖊":
        reason = "Changing your wishlist without mod permission"
    elif emoji == "🔄":
        reason = "reposting more than once every 10 days"
    elif emoji == "😠":
        reason = "Harassment of another Wisher"

    with open("files/warnings.json") as f:
        users = json.loads(f.read())
        found = False
        for u in users:
            if u["name"].lower() == user:
                found = True
                u["warnings"].append(reason)
                break
        if not found:
            u = {
                "name": user.lower(),
                "warnings": [reason]
            }
            users.append(u)

        ban_message = "You were banned for breaking the following rules:\n\n{}".format(
            "\n".join(u["warnings"]))
        note = ", ".join(u["warnings"])
        reddit.subreddit("SantasChristmasWish").banned.add(user, ban_reason=reason, ban_message=ban_message,
                                                           note=note)
        redditor.message("/r/SantasChristmasWish Ban", ban_message,
                         from_subreddit="SantasChristmasWish")

        with open("files/warnings.json", "w+") as f:
            f.write(json.dumps(users, indent=4))

    await ctx.send("User successfully banned!")


# @bh.mail()
async def handle_mail(p):
    msg = await bot.get_channel(596006288987783180).send(embed=p.get_embed())
    await p.add_reactions(msg)


config = configparser.ConfigParser()
config.read("discord.ini")
bot.run(config["RTR"]["token"])
