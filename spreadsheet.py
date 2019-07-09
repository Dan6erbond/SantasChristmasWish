import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials


# use creds to create a client to interact with the Google Drive API
scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("SantasChristmasWish Registration  (Responses)").sheet1

print("Got sheet.")

keys = sheet.get_all_values()[0]
users = list()

# Extract and print all of the values
for user in sheet.get_all_values()[1:]:  # sheet.get_all_records() if we only want the filled out columns in ALL rows
    u = dict()
    u["children"] = list()
    for i in range(len(keys)):
        key = keys[i]
        child_in_key = "child" in key.lower() and not "number" in key.lower()
        child_verification = "for silver verification only" in key.lower()
        if child_in_key or child_verification:
            found = False
            for child in u["children"]:
                if key not in child:
                    child[key] = user[i]
                    found = True
            if not found:
                child = dict()
                child[key] = user[i]
                u["children"].append(child)
        else:
            u[key] = user[i]
    users.append(u)

with open("users.json", "w+") as f:
    f.write(json.dumps(users, indent=4))
