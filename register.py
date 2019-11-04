import asyncio
import configparser
import json
import re

import reggie_config

import discord
import gspread
import praw
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

import apraw
import uslapi

REGGIE_COLOR = discord.Colour(0).from_rgb(152, 0, 0)
GIFTS_PER_CHILD = 4

bot = commands.Bot("!", description="SCW's registration bot 🤓.")

aReddit = apraw.Reddit("RB")
reddit = praw.Reddit("RB")

usl = uslapi.UniversalScammerList('bot for SCW by /u/SantasChristmasWish')
usl_user = usl.login('SantasChristmasWish', 'Harvey98')

approvers = [592816167190790160, 592803234368716801, 495503769451102210, 597803503951544320,
             383657174674702346]  # remove the last one before release, find out who 598159671651729409 is




@bot.event
async def on_ready():
    print(str(bot.user) + ' is running.')


@bot.command()
async def getregs(ctx):
    await ctx.send("✔ Fetching registrations.")

    channel = bot.get_channel(596006191981789255)

    users = get_users()
    # print(len(users))

    for user in users:
        embed = get_user_embed(user)
        await channel.send(embed=embed)


def get_user_embed(user):
    # print(json.dumps(user, indent=4))
    embed = discord.Embed(
        colour=REGGIE_COLOR
    )
    url = "https://www.reddit.com/u/{}".format(user["username"])
    embed.set_author(name="/u/" + user["username"], url=url)

    # address_proof = "**Proof of address:** {}\n\n".format(user["address_proof"]) if "address_proof" in user else ""
    # need_proof = "\n**Proof of need:** {}".format(user["need_proof"]) if "need_proof" in user else ""
    # medical_condition_proof = "\n**Proof of medical condition:** {}".format(user["medical_condition_proof"]) if "medical_condition_proof" in user else ""

    embed.description = "**Full Name:** {}\n\n" \
                        "**Country:** {}\n" \
                        "**Full address:** {}\n\n" \
                        "**Documentation:** {}\n" \
                        "**Number of children:** {}\n" \
                        "**Requested wish level:** {}".format(user["name"], user["country"],
                                                            user["full_address"], user["documentation_link"],
                                                            len(user["children"]), user["wish_level"])
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
    elif "imgur" in key and "documentation" in key:
        return "documentation_link"
    elif "wish" in key and "level" in key:
        return "wish_level"
    elif "full" in key and ("adress" in key or "address" in key):
        return "full_address"
    elif "silver" in key and "verification" in key and ("custody" in key or ("adress" in key or "address" in key)):
        return "child_custody_proof"
    elif "proof" in key and ("adress" in key or "address" in key):
        return "address_proof"
    elif "family" in key and "photo" in key:
        return "family_photo"
    elif "child" in key and "age" in key:
        return "child_age"
    elif "child" in key and "name" in key:
        return "child_name"
    elif "child" in key and "wishlist" in key:
        return "child_wishlist"
    elif "silver" in key and "verification" in key and "age" in key:
        return "child_age_proof"
    elif "number" in key and "children" in key:
        return "num_children"
    elif "please copy below" in key and "rules":
        return "rule_confirmation"
    elif "please copy below" in key and "christmas" in key and "subreddit" in key:
        return "crosspost_confirmation"
    elif "proof" in key and "need" in key:
        return "need_proof"
    elif "proof" in key and "medical" in key and "condition" in key:
        return "medical_condition_proof"
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
    sheet = client.open(reggie_config.registrations_sheet_name).sheet1

    # print("Got sheet.")

    keys = sheet.get_all_values()[0]
    child_keys = set()
    child_start = -1
    child_end = -1
    for i in range(len(keys)):
        key = get_dict_key(keys[i])
        if "child_" in key:
            if key not in child_keys:
                child_keys.add(key)
            if child_start == -1:
                child_start = i
            child_end = i
        elif child_end != -1:
            break

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
            dict_key = get_dict_key(key)
            if i >= child_start and i <= child_end:
                if column_count == len(child_keys)-1:
                    if user[i] != "":
                        curr_child[dict_key] = user[i]
                    if len(curr_child.keys()) >= len(child_keys): # replace with REQUIRED_CHILD_KEYS (to define) if there are optional parameters
                        u["children"].append(curr_child)
                    curr_child = dict()
                    column_count = 0
                else:
                    if user[i] != "":
                        curr_child[dict_key] = user[i].strip()
                    column_count += 1
            else:
                if user[i] != "": u[dict_key] = user[i].strip() if dict_key != "username" else user[
                    i].replace("u/", "").replace("/", "").strip()
        if len(u.keys()) - 1 >= child_start - 1:
            users.append(u)
    return users


@bot.event
async def on_raw_reaction_add(p):
    c = bot.get_channel(p.channel_id)

    u = bot.get_user(p.user_id)
    global approvers
    if u.bot or u.id not in approvers:
        return

    m = await c.fetch_message(p.message_id) if c is not None else await u.fetch_message(p.message_id)
    e = p.emoji.name if not p.emoji.is_custom_emoji() else "<:{}:{}>".format(p.emoji.name, p.emoji.id)

    if len(m.embeds) != 1:
        return

    post = reddit.submission(url=m.embeds[0].author.url)

    if c is not None and c.id == 596006191981789255:
        if e == "🥉":
            await aReddit.post_request("/r/SantasChristmasWish/api/selectflair",
                                       {"link": post.name, "flair_template_id": reggie_config.bronze_post_flair_id})
            post.subreddit.flair.set(post.author.name, flair_template_id=reggie_config.bronze_user_flair_id)
            post.mod.approve()
        elif e == "🥈":
            await aReddit.post_request("/r/SantasChristmasWish/api/selectflair",
                                       {"link": post.name, "flair_template_id": reggie_config.silver_post_flair_id})
            post.subreddit.flair.set(post.author.name, flair_template_id=reggie_config.silver_user_flair_id)
            post.mod.approve()
        elif e == "🥇":
            await aReddit.post_request("/r/SantasChristmasWish/api/selectflair",
                                       {"link": post.name, "flair_template_id": reggie_config.gold_post_flair_id})
            post.subreddit.flair.set(post.author.name, flair_template_id=reggie_config.gold_user_flair_id)
            post.mod.approve()
        elif e == "💎":
            with open("files/platinum.json") as f:
                platinum = json.loads(f.read())

                for plat in platinum:
                    if plat["id"] == post.id:
                        platinum.remove(plat)

                platinum.append({
                    "id": post.id,
                    "approvers": [u.id]
                })
                with open("files/platinum.json", "w+") as f:
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
                found = False
                for plat in platinum:
                    if plat["id"] == post.id:
                        found = True
                        if u.id not in plat["approvers"]:
                            plat["approvers"].append(u.id)
                            plat["approvers"] = set(plat["approvers"])
                            with open("files/platinum.json", "w+") as f:
                                f.write(json.dumps(platinum, indent=4))
                        if len(plat["approvers"]) == 3:
                            await aReddit.post_request("/r/SantasChristmasWish/api/selectflair",
                                                       {"link": post.name,
                                                        "flair_template_id": reggie_config.platinum_post_flair_id})
                            post.subreddit.flair.set(post.author.name,
                                                     flair_template_id=reggie_config.platinum_user_flair_id)
                            post.mod.approve()
                        break
                if found:
                    await m.edit(content="Your action has been recorded.", embed=None)
                else:
                    await m.edit(
                        content="Your action couldn't be successfully recorded. Please contact <@383657174674702346> or <@592803234368716801> as soon as possible.",
                        embed=None)
        else:
            await m.edit(content="Your action has been recorded.", embed=None)


async def reddit_task():
    await bot.wait_until_ready()

    channel = bot.get_channel(596006191981789255)
    loop_time = 5 * 60

    sub = await aReddit.subreddit("santaschristmaswish")

    file = open("files/register_posts.txt")
    post_ids = file.read().splitlines()
    file.close()
    new_post_ids = list()

    file = open("files/gifts.json")
    gifts = json.loads(file.read())
    file.close()

    last_comment_id = None

    while True:
        users = get_users()

        print("Scanning queue...")
        async for post in sub.mod.modqueue():
            if post.id in post_ids:
                continue
            post_ids.append(post.id)
            new_post_ids.append(post.id)
            print("Found post.")
            post_embed = discord.Embed(
                colour=REGGIE_COLOR
            )

            author = await post.author()
            title = post.title
            url = "https://www.reddit.com" + post.permalink
            post_embed.set_author(name=title, url=url if url != "" else discord.Embed.Empty)

            if not post.data["is_self"]:
                continue

            post_embed.add_field(name="Body", value=post.selftext if post.selftext != "" else "Empty",
                                 inline=False)

            user_found = False
            for user in users:
                if user["username"].lower() == author.name.lower():
                    user_embed = get_user_embed(user)
                    user_found = True

                    names = [gift["username"].lower() for gift in gifts]
                    if user["username"].lower() not in names:
                        gifts.append({
                            "username": user["username"],
                            "num_children": len(user["children"]),
                            "gifts_completed": []
                        })

                    await channel.send("New post by /u/{}!".format(author.name), embed=user_embed)
                    msg = await channel.send(embed=post_embed)
                    for emoji in ["🥉", "🥈", "🥇", "💎", "✖"]:
                        await msg.add_reaction(emoji)

                    break

            if not user_found:
                await channel.send("Post made by /u/{} but no corresponding user found!".format(author.name), embed=post_embed)

        with open("files/register_posts.txt", "a+") as f:
            f.write("\n" + "\n".join(new_post_ids))

        file = open("files/register_comments.txt")
        comment_ids = file.read().splitlines()
        file.close()
        new_comment_ids = list()

        async for c in aReddit.get_listing("/r/santaschristmaswish/comments", 100):
            if c["kind"] != aReddit.comment_kind:
                continue
            if c["data"]["id"] in comment_ids:
                continue
            comment_ids.append(c["data"]["id"])
            new_comment_ids.append(c["data"]["id"])
            c["data"]["link_author"]
            x = re.search("!(\d+)", c["data"]["body"])
            if x and c["data"]["body"].startswith("!"):
                g = int(x.group(1))
                for gift in gifts:
                    if c["data"]["link_author"].lower() == gift["username"].lower():
                        for i in range(g):
                            gift["gifts_completed"].append({
                                "username": c["data"]["author"],
                                "comment": "https://www.reddit.com" + c["data"]["permalink"]
                            })
                        data = {
                            "text": "Thank you for being a part of SCW and sending gifts to /u/{}'s {}.\n\n"
                                    "They now have a total of {} gifts."
                                    "🎅".format(gift["username"], "child" if gift["num_children"] == 1 else "children", len(gift["gifts_completed"])),
                            "thing_id": "{}_{}".format(c["kind"], c["data"]["id"])
                        }
                        await aReddit.post_request("/api/comment", data)
                        break

        with open("files/register_comments.txt", "a+") as f:
            f.write("\n" + "\n".join(new_comment_ids))
        with open("files/gifts.json", "w+") as f:
            f.write(json.dumps(gifts, indent=4))

        print("Done scanning!")
        await asyncio.sleep(loop_time)

config = configparser.ConfigParser()
config.read("discord.ini")
bot.loop.create_task(reddit_task())
# bot.loop.create_task(test_task())
bot.run(config["RB"]["token"])
