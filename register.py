import asyncio
import configparser

import discord
import gspread
import praw
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

import apraw
import uslapi

import json

SHEET_NAME = "SCW Registration  (Responses)"
REGGIE_COLOR = discord.Colour(0).from_rgb(152, 0, 0)

bot = commands.Bot("!", description="SCW's registration bot 🤓.")

aReddit = apraw.Reddit("RB")
reddit = praw.Reddit("RB")

usl = uslapi.UniversalScammerList('bot for SCW by /u/SantasChristmasWish')
usl_user = usl.login('SantasChristmasWish', 'Harvey98')

approvers = [592816167190790160, 592803234368716801, 495503769451102210, 598159671651729409, 597803503951544320, 383657174674702346] # remove the last one before release

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(str(error))


@bot.event
async def on_ready():
    print(str(bot.user) + ' is running.')


# @bot.command()
async def getregs(ctx):
    await ctx.send("✔ Fetching registrations.")

    channel = bot.get_channel(596006191981789255)

    users = get_users()
    print(len(users))

    for user in users:
        embed = get_user_embed(user)
        await channel.send(embed=embed)


def get_user_embed(user):
    embed = discord.Embed(
        colour=REGGIE_COLOR
    )
    url = "https://www.reddit.com/u/{}".format(user["username"])
    embed.set_author(name="/u/" + user["username"], url=url)
    embed.description = "**Full Name:** {}\n\n" \
                        "**Country:** {}\n" \
                        "**Full address:** {}\n\n" \
                        "**ID:** {}\n" \
                        "**Proof of address:** {}\n\n" \
                        "**Family photo:** {}\n" \
                        "**Number of children:** {}".format(user["name"], user["country"],
                                                            user["full_address"],
                                                            user["id_proof"],
                                                            user["address_proof"],
                                                            user["family_photo"],
                                                            len(user["children"]))
    for child in user["children"]:
        val = "**Age:** {}\n\n" \
              "Wishlist:\n{}".format(child["child_age"], child["child_wishlist"])
        embed.add_field(name=child["child_name"], value=val, inline=False)

    data = usl.query(usl_user, user["username"])
    embed.add_field(name="Banned on USL", value=data["banned"], inline=False)

    return embed


def get_dict_key(key):
    key = key.lower()
    if "timestamp" in key:
        return "timestamp"
    elif "reddit" in key and "username" in key:
        return "username"
    elif "full" in key and "name" in key:
        return "name"
    elif "country" in key:
        return "country"
    elif "full" in key and ("adress" in key or "address" in key):
        return "full_address"
    elif "proof" in key and ("adress" in key or "address" in key):
        return "address_proof"
    elif "family" in key and "photo" in key:
        return "family_photo"
    elif "child" in key and "age" in key:
        return "child_age"
    elif "child" in key and "name" in key:
        return "child_name"
    elif "child" in key and "wishlist" in key:
        # print("child_wishlist")
        return "child_wishlist"
    elif "silver" in key and "verification" in key and "age" in key:
        return "child_age_proof"
    elif "silver" in key and "verification" in key and ("custody" in key or "address" in key):
        return "child_custody_proof"
    elif "number" in key and "children" in key:
        return "num_children"
    elif "please copy below" in key and "rules":
        return "rule_confirmation"
    elif "please copy below" in key and "christmas" in key and "subreddit" in key:
        return "crosspost_confirmation"
    elif "id" in key:
        return "id_proof"
    else:
        print(key)
        return key


def get_users():
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open(SHEET_NAME).sheet1

    # print("Got sheet.")

    CHILD_COLUMNS = 5
    REQUIRED_CHILD_COLUMNS = 2

    keys = sheet.get_all_values()[0]
    child_start = -1
    for i in range(len(keys)):
        if "child_" in get_dict_key(keys[i]):
            if child_start == -1: child_start = i
            # print(key)
            break
    # print(keys[child_start])

    users = list()

    # Extract and print all of the values
    # sheet.get_all_records() if we only want the filled out columns in ALL rows
    for user in sheet.get_all_values()[1:]:
        # print(user)
        u = dict()
        u["children"] = list()
        column_count = 0
        curr_child = dict()
        for i in range(len(keys)):
            key = keys[i]
            if i >= child_start:
                if column_count == CHILD_COLUMNS:
                    child_keys = curr_child.keys()
                    if "child_name" in child_keys and "child_age" in child_keys and "child_wishlist" in child_keys:
                        u["children"].append(curr_child)
                    curr_child = dict()
                    column_count = 0
                else:
                    if user[i] != "": curr_child[get_dict_key(key)] = user[i]
                    column_count += 1
            else:
                if user[i] != "": u[get_dict_key(key)] = user[i] if get_dict_key(key) != "username" else user[
                    i].replace("u/", "").replace("/", "")
        if len(u.keys()) - 1 == child_start:
            users.append(u)
    return users


@bot.event
async def on_raw_reaction_add(p):
    c = bot.get_channel(p.channel_id)

    u = bot.get_user(p.user_id)
    if u.bot or u.id not in approvers:
        return

    m = await c.fetch_message(p.message_id) if c is not None else 
    e = p.emoji.name if not p.emoji.is_custom_emoji() else "<:{}:{}>".format(p.emoji.name, p.emoji.id)

    if len(m.embeds) != 1:
        return

    post = reddit.submission(url=m.embeds[0].author.url)

    if c.id == 596006191981789255:
        if e == "🥉":
            await aReddit.post_request("/r/SantasChristmasWish/api/selectflair",
                                       {"link": post.name, "flair_template_id": "8de4659c-dd59-11e9-89a3-0ee420649c9a"})
            post.mod.approve()
        elif e == "🥈":
            await aReddit.post_request("/r/SantasChristmasWish/api/selectflair",
                                       {"link": post.name, "flair_template_id": "11be290c-dd5a-11e9-9621-0ed81c20b56a"})
            post.mod.approve()
        elif e == "🥇":
            await aReddit.post_request("/r/SantasChristmasWish/api/selectflair",
                                       {"link": post.name, "flair_template_id": "302f0b54-dd5a-11e9-865f-0e6be140e43a"})
            post.mod.approve()
        elif e == "💎":
            with open("files/platinum.json") as f:
                platinum = json.loads(f.read())
                platinum.append({
                    "id": post.id,
                    "approvers": [u.id]
                })
                with open ("files/platinum.json", "w+") as f:
                    f.write(json.dumps(platinum, indent=4))

            post_embed = discord.Embed(
                colour=REGGIE_COLOR
            )
            title = "Should this submission by /u/ be marked as Platinum?".format(post.author)
            url = "https://www.reddit.com" + post.permalink
            post_embed.set_author(name=title, url=url if url != "" else discord.Embed.Empty)

            post_embed.add_field(name="Body", value=post.selftext if post.selftext != "" else "Empty",
                                 inline=False)
            for approver in approvers:
                if approver != u.id:
                    message = await bot.get_user(approver).send(embed=post_embed)
                    for emoji in ["✔", "✖"]:
                        await message.add_reaction(emoji)
        elif e == "✖":
            post.author.message(subject="Your request has been rejected",
                                message="Hi,\n\n"
                                        "Thank you for your registration with SCW unfortunately at this time it has been rejected."
                                        "For further information please feel free to contact the mods.\n\n"
                                        "Many thanks,\n"
                                        "SCW Team",
                                from_subreddit="SantasChristmasWish")
            post.mod.remove()

        id = 0
        async for msg in m.channel.history():
            if id != 0:
                await msg.delete()
                break
            if msg.id == m.id:
                id = msg.id

        await m.delete()
    else:
        if e == "✔":
            with open("files/platinum.json") as f:
                platinum = json.loads(f.read())
                for plat in platinum:
                    if plat["id"] == post.id:
                        if u.id not in plat["approvers"]:
                            plat["approvers"].append(u.id)
                            with open("files/platinum.json", "w+") as f:
                                f.write(json.dumps(platinum, indent=4))
                        if len(plat["approvers"]) == 3:
                            await aReddit.post_request("/r/SantasChristmasWish/api/selectflair",
                                                       {"link": post.name,
                                                        "flair_template_id": "5600f6ee-dd5a-11e9-a4fc-0e59b2f870f2"})
                            post.mod.approve()
                        break
        await m.edit(content="Your action has been recorded.")


async def reddit_task():
    await bot.wait_until_ready()

    channel = bot.get_channel(596006191981789255)

    sub = await aReddit.subreddit("santaschristmaswish")
    ids = set()

    while True:
        print("Scanning queue...")
        async for post in sub.mod.modqueue():
            if post.id in ids:
                continue
            else:
                ids.add(post.id)
            print("Found post.")
            post_embed = discord.Embed(
                colour=REGGIE_COLOR
            )

            author = await post.author()
            title = "New submission by /u/{}!".format(author)
            url = "https://www.reddit.com" + post.permalink
            post_embed.set_author(name=title, url=url if url != "" else discord.Embed.Empty)

            if not post.data["is_self"]:
                continue

            post_embed.add_field(name="Body", value=post.selftext if post.selftext != "" else "Empty",
                                 inline=False)

            user_embed = None
            for user in get_users():
                if user["username"].lower() == author.name.lower():
                    user_embed = get_user_embed(user)
                    break

            if user_embed is not None:
                await channel.send(embed=user_embed)
                msg = await channel.send(embed=post_embed)
                for emoji in ["🥉", "🥈", "🥇", "💎", "✖"]:
                    await msg.add_reaction(emoji)
            else:
                await channel.send("Post made but no corresponding user found!", embed=post_embed)
        print("Done scanning!")
        await asyncio.sleep(30)


config = configparser.ConfigParser()
config.read("discord.ini")
bot.loop.create_task(reddit_task())
bot.run(config["RB"]["token"])
