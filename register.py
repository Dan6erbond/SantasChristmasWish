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
    channel = bot.get_channel(596006191981789255)
    for user in get_users():
        embed = discord.Embed(
            colour=discord.Colour(0).from_rgb(152, 0, 0)
        )
        embed.set_author(name=user["Reddit Username"],
                         url="https://www.reddit.com/u/{}".format(user["Reddit Username"]))
        embed.description = "**Full Name:** {}\n" \
                            "**Country:** {}\n" \
                            "**Full address:** {}\n" \
                            "**ID:** {}\n" \
                            "**Proof of address:** {}\n" \
                            "**Family photo:** {}\n" \
                            "**Number of children:** {}".format(user["Full Name "], user["Country "],
                                                            user["Full address"],
                                                            user[
                                                                "ID - please paste the imgur link for your blanked out ID "],
                                                            user["Proof of address -  please paste the imgur link for your proof of address"],
                                                            user[
                                                                "Family Photo -  please paste the imgur link for your family photo "],
                                                            len(user["children"]))
        for child in user["children"]:
            embed.add_field(name=child["Childs name "], value=child["Childs age "], inline="False")
        await channel.send(embed=embed)

    print(str(bot.user) + ' is running.')


def get_users():
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("SantasChristmasWish Registration  (Responses)").sheet1

    print("Got sheet.")

    CHILD_COLUMNS = 5

    keys = sheet.get_all_values()[0]
    child_start = -1
    for i in range(len(keys)):
        key = keys[i]
        child_in_key = "child" in key.lower() and not "number" in key.lower()
        child_verification = "for silver verification only" in key.lower()
        if child_in_key or child_verification:
            if child_start == -1: child_start = i
            # print(key)
            break
    # print(keys[child_start])

    users = list()

    # Extract and print all of the values
    for user in sheet.get_all_values()[
                1:]:  # sheet.get_all_records() if we only want the filled out columns in ALL rows
        u = dict()
        u["children"] = list()
        column_count = 0
        curr_child = dict()
        data_found = False
        for i in range(len(keys)):
            key = keys[i]
            if i >= child_start:
                if column_count == CHILD_COLUMNS:
                    if len(curr_child.keys()) >= CHILD_COLUMNS:
                        u["children"].append(curr_child)
                        curr_child = dict()
                    data_found = False
                    column_count = 0
                else:
                    if user[i] != "": curr_child[key] = user[i]
                    column_count += 1
            else:
                u[key] = user[i]
        users.append(u)
    return users


config = configparser.ConfigParser()
config.read("discord.ini")
bot.run(config["RB"]["token"])
