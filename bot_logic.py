# bot_logic.py
# Nyonyix

# Stored functions and classes related to the logic of the "Auto Name" bot.

import discord
import asyncio
import os
import json
import aiohttp
import async_timeout
from dotenv import load_dotenv

load_dotenv()

async def getCharacterData(character: str) -> tuple:
    """
    Gathers character data from Planetside API

    Returns 2 values: 
     - Fetched character data (dict)
     - If the character actaully exists (bool)
    """
    http_session = aiohttp.ClientSession()
    character_data = {}
    response_data = {}
    exists = False
    url = f"http://census.daybreakgames.com/get/ps2:v2/character/?name.first_lower={character.lower()}"

    with async_timeout.timeout(10):
        async with http_session.get(url) as response:
            response_data = await response.json()
            await http_session.close()
    
    character_data = response_data["character_list"][0]

    if response_data["returned"] == 1:
        exists = True
        return character_data, exists
    else:
        character_data = {}
        return character_data, exists



def isWithVoice(voice: str) -> bool:
    """
    Takes command string imput and determins if true or false
    """
    if voice in ["FALSE", "False", "false"]:
        return False
    else:
        return True



async def assembleData(message: discord.Message, character: str, voice: str) -> tuple:
    """
    Gathers and assembles the incoming data for a new register event

    Returns 2 values:
     - Fully assembled data from command message and fetched character data (dict)
     - If character exists, Passed through from 'getCharacterData' (bool)
    """
    guild = message.guild.id
    user = getMemberObj(message)
    character_data, exists = await getCharacterData(character)
    with_voice = isWithVoice(voice)
    new_data = {}

    if exists == True:
        new_data[str(guild)] = {}
        new_data[str(guild)][str(character)] = {}
        new_data[str(guild)][str(character)]["character_lower"] = character.lower()
        new_data[str(guild)][str(character)]["character"] = character_data["name"]["first"]
        new_data[str(guild)][str(character)]["character_id"] = character_data["character_id"]
        new_data[str(guild)][str(character)]["discord_user_id"] = user.id
        new_data[str(guild)][str(character)]["with_voice"] = with_voice

        return new_data
    else:
        new_data = {}
        return new_data



def alreadyRegistered(guild_id: int, character: str, json_file: dict) -> bool:
    """
    Checks if the character has already been registered within this server
    """
    try:
        json_file[str(guild_id)][str(character)]
        return True
    except KeyError:
        return False



async def putTogether(message: discord.Message, character: str, voice: str) -> bool:
    """
    Puts all the peices of data together and saves to file for the primary bot event loop
    """
    guild_id = message.guild.id
    character_data = await assembleData(message, character, voice)
    filename = "registered_users.json"

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            json_file = json.load(f)
            f.close()
    else:
        dummy = {}
        json_file = {}
        with open(filename, 'w') as f:
            json.dump(dummy, f)
            f.close()

    is_registered = alreadyRegistered(guild_id, character, json_file)

    try:
        json_file[str(guild_id)]
    except KeyError:
        json_file[str(guild_id)] = {}

    try:
        json_file[str(guild_id)][str(character)]
    except KeyError:
        json_file[str(guild_id)][str(character)] = {}

    json_file[str(guild_id)][str(character)] = character_data[str(guild_id)][str(character)]

    print(json.dumps(json_file, indent=4))

    if is_registered == True:
        return False
    else:
        with open(filename, 'w') as f:
            json.dump(json_file, f)
            f.close()



def getMemberObj(message: discord.Message) -> discord.Member:
    """
    Generates a discord.Member object from a discord.Message object
    """
    return message.guild.get_member(message.author.id)



def stripCommand(command: str) -> tuple:
    """
    Splits command into a list for better handling

    Returns 2 values:
     - Command string split into list of individual word strings (str)
     - If command has other words besides 'base_commands' (bool)
    """
    command = command.split()
    has_extra_words = False

    if len(command) >= 2:
        has_extra_words = True

    return command, has_extra_words



class BotClient(discord.Client):
    TOKEN = os.getenv("DISCORD_TOKEN") 

    async def on_ready(self: discord.Client) -> None:
        print(f"{self.user} has connected to Discord")

    async def on_message(self: discord.Client, message: discord.Message) -> None:
        if message.author == self.user:
            return

        base_commands = ["!auto-name"]
        command, has_extra_words = stripCommand(message.content)

        if base_commands[0] == command[0]:
            if has_extra_words == True:
                sub_commands = ["test"]

                if sub_commands[0] == command[1]:
                    try:
                        try:
                            command[3]
                        except IndexError:
                            command.append("true")
                        if await putTogether(message, command[2].lower(), command[3]) == False:
                            await message.channel.send(f"{command[2]} has already been registered")
                    except IndexError:
                        await message.channel.send(f"```Missing Argument```")
                else:
                    await message.channel.send(f"```{command[1:len(command)]} are invalid arguments.```")
            else:
                await message.channel.send("```Invalid Command. Missing arguments```")
            
        print(f"Recived {message.content}")



# def registerToFile(message: discord.Message, character: str) -> None:
#     registered_users = {}
#     time_stamp = formatTime()
#     user = getMemberObj(message)
    
#     if os.path.exists("registered_users.json"):
#         with open("registered_users.json", 'r') as f:
#             registered_users = json.load(f)
#             f.close()
#     else:
#         print("ERR: registered_users.json not found")

#     with open("registered_users.json", 'w') as f:
#         registered_users["character"] = {}
#         registered_users["character"]["user_id"] = user.id
#         registered_users["character"]["guild_id"] = user.guild.id
#         json.dump(registered_users, f)
#         f.close()




# def alreadyRegistered(guild_id: int, character_id: int) -> bool:
#     """
#     Checks with json file if this ps2 character has already been registered with this user in this server
#     """
#     filename = "registered_users.json"

#     if os.path.exists(filename):
#         with open(filename, 'r') as f:
#             in_json = json.load(f)
#             f.close()

#         for k1, v1 in in_json.items():
#             print(v1)
#             if guild_id == k1:
#                 for k2, v2 in v1.items():
#                     print(f"2nd For Loop - {k2} : {v2}")
#                     if k2 == "character_id" and v2 == character_id:
#                         print("True")
#                         return True
#                     else:
#                         print("False")
#                         return False
#     else:
#         print(f"ERR: No file to compare. '{filename}' not found")
#         return False