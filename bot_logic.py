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

filename = "registered_users.json"

def openJsonFile(filename: str) -> dict:
    """
    Loads the specified json file into a 'dict'. If the file does not exist or is empty, The function return an empty dict.
    """
    out_json = {}
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            out_json = json.load(f)
            f.close()
    return out_json



def saveJsonFile(filename: str, in_data: dict) -> bool:
    """
    Saves the specified dict to the specified file
    """
    with open(filename, 'w') as f:
        json.dump(in_data, f)
        f.close()



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
    json_file = openJsonFile(filename)

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
        saveJsonFile(filename, json_file)
        return True



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



async def register(message: discord.Message, command: list) -> None:
    """
    Was apart of the 'on_message' function, Now it's own
    Now this serves as the IO hub between discord and the bot's logic functions
    """
    command[2] = command[2].lower()

    # If the command arr has less than expected objects then it will return
    # a 'missing arguments' response to discord.
    try:
        # If 'false' arg is missing, This injects 'true'
        try:
            command[3]
        except IndexError:
            command.append("true")

        # Meat of the register command. If 'putTogether' return false, Character exists.
        # If the function returns true, Character has been added to file.
        user_registered = await putTogether(message, command[2].lower(), command[3])
        if user_registered == False:
            await message.channel.send(f"```{command[2]} has already been registered```")
        elif user_registered == True:
            await message.channel.send(f"```Character successfully registered```")

    except IndexError:
        print("Index exception")
        await message.channel.send(f"```Missing Argument```")

def removeRegister(message: discord.Message) -> bool:
    guild_id = message.guild.id
    pass



class BotClient(discord.Client):
    TOKEN = os.getenv("DISCORD_TOKEN")

    async def on_ready(self: discord.Client) -> None:
        print(f"{self.user} has connected to Discord")

    # Event handler for listening to commands
    async def on_message(self: discord.Client, message: discord.Message) -> None:

        # If the message is the bot it's self, It will ignore the message
        if message.author == self.user:
            return

        # Base commands are the initial commands to be used, Most of the time '!auto-name is used
        # and sub_commands are used for actual work to avoid conflicts with other bots.
        # Example: "!auto-name(base_command) register(sub_command) example(arg1) false(arg2)"

        # sub_commands are defined and checked with the message, If message does not contain a
        # sub_command, It will return an 'invalid command' response to discord.

        # The command is also converted into a arr of words for easier computation and return the command arr.
        base_commands = ["!auto-name"]
        command, has_extra_words = stripCommand(message.content)

        # Checks if message is a base_command and has extra words afterwards
        if base_commands[0] == command[0]:
            if has_extra_words == True:
                sub_commands = ["reg", "register", "test"]

                # Register command check
                if command[1] in sub_commands[0:1]:
                    await register(message, command)

                # Test command check
                elif command[1] == sub_commands[2]:
                    msg_to_send = discord.Embed(title= "Test")
                    msg_to_send.add_field(name= "Line 1", value= "Testing Text", inline= True)
                    msg_to_send.add_field(name= "Line 2", value= "Testing Text 2 Seeing what this does", inline= True)
 
                    await message.channel.send(embed=msg_to_send)

                else:
                    await message.channel.send(f"```{command[1:len(command)]} are invalid commands.```")

            else:
                await message.channel.send("```Invalid Command. Missing arguments```")

        # Prints the received command from discord for debugging.
        print(f"Recived {message.content}")



###END OF FILE DUMP###

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
