# bot_main.py
# Nyonyix

# Primary execution script for the "Auto Name" bot program.

import os
import discord
import bot_logic
from dotenv import load_dotenv

def main() -> None:

    Bot = bot_logic.BotClient()
    Bot.run(Bot.TOKEN)

if __name__ == "__main__":

    main()