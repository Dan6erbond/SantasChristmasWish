import configparser

import discord
import gspread
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

bot = commands.Bot("!", description="SCW's registration bot 🤓.")


@bot.event
async def on_command_error(ctx, error):
    print(error)


@bot.event
async def on_ready():
    print(str(bot.user) + ' is running.')


@bot.command()
async def getregs(ctx):
    await ctx.send("✔ Fetching registrations.")

    channel = bot.get_channel(596006191981789255)

    for user in get_users():
        embed = discord.Embed(
            colour=discord.Colour(0).from_rgb(152, 0, 0)
        )
        username = user["username"].replace("u/", "").replace("/", "")
        url = "https://www.reddit.com/u/{}".format(username)
        embed.set_author(name="/u/" + username, url=url)
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
            embed.add_field(name=child["child_name"], value=val, inline="False")
        await channel.send(embed=embed)


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
        print("child_wishlist")
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
    sheet = client.open("SantasChristmasWish Registration  (Responses)").sheet1

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
        print(user)
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
                if user[i] != "": u[get_dict_key(key)] = user[i]
        if len(u.keys()) - 1 == child_start:
            users.append(u)
    return users


config = configparser.ConfigParser()
config.read("discord.ini")
bot.run(config["RB"]["token"])
