import asyncio
import telepot
import telepot.aio
from telepot.aio.loop import MessageLoop
from MineTweets import TweetMiner
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

# MAJOR CHANGE MADE TO TELEPOT IN PYTHON3100/LIB/SITE-PACKAGES/LOOP.PY TO CHANGE
# _EXTRACT_MESSAGE TO INCLUDE 'update_id' AS PART OF KEY. MAKE SURE TO ADD TO END OF LIST

# general handling of messages- small, niche number of cases for each command


async def handle_msg(msg):
    # These are some useful variables
    content_type, chat_type, chat_id = telepot.glance(msg)
    # Log variables
    print("Message:", content_type, chat_type, chat_id)
    # Send our JSON msg variable as reply message
    if content_type == 'text':

        # returns all the insiders
        if msg['text'] == '/getaccess' or msg['text'] == '/getaccess@seahawks_tg_bot':
            await bot.sendMessage(chat_id, "To request access in your group chat, please fill out the following form:\n"+form_url+"\nThis helps us manage server overload. Thanks.")

        # returns all the insiders
        elif msg['text'] == '/getinsiders' or msg['text'] == '/getinsiders@seahawks_tg_bot':
            await bot.sendMessage(chat_id, miner.get_insiders())

        # returns all the latest tweets
        elif msg['text'] == '/getlatesttweets' or msg['text'] == '/getlatesttweets@seahawks_tg_bot':
            data = miner.get_insiders_latest_tweets()
            for i in data:
                await bot.sendMessage(chat_id, i)

        # returns the latest tweet of a user selected by the user from the latesttweetbuttonboard
        elif msg['text'] == '/getlatesttweetfromuser' or msg['text'] == '/getlatesttweetfromuser@seahawks_tg_bot':
            await bot.sendMessage(chat_id, 'Select an Insider To Get the Latest Tweet Of',
                                  reply_markup=ReplyKeyboardMarkup(
                                      keyboard=latesttweetboard
                                  ))

        # returns all the latest tweets with a keyword
        elif msg['text'] == '/gettweetswithkeyword' or msg['text'] == '/gettweetswithkeyword@seahawks_tg_bot':
            await bot.sendMessage(chat_id, "Please type your word, ______, in the chat with the format 'keyword: ______'")

        elif msg['text'].split()[0] == 'keyword:':
            data = miner.mine_for_new_tweets_with_keyword(
                msg['text'].split()[1])
            for i in data:
                await bot.sendMessage(chat_id, i)

        # used to check if user wants latest tweets from a specific insider
        elif msg['text'].split(' ')[-1] == 'latest' and msg['text'][0] == '@':
            screen_name = msg['text'].split(' ')[0][1:]
            await bot.sendMessage(chat_id, miner.get_insider_latest_tweet(screen_name=screen_name))

        # updates all tweets
        elif msg['text'] == '/updatetweets' or msg['text'] == '/updatetweets@seahawks_tg_bot':
            data = miner.mine_all_tweets()
            if len(data) == 0:
                await bot.sendMessage(chat_id, "No new tweets found since last request")
            else:
                for i in data:
                    await bot.sendMessage(chat_id, i)

        # updates tweets for one user
        elif msg['text'] == '/updatetweetfromuser' or msg['text'] == '/updatetweetfromuser@seahawks_tg_bot':
            await bot.sendMessage(chat_id, 'Select an Insider To Update the Tweets Of',
                                  reply_markup=ReplyKeyboardMarkup(
                                      keyboard=updatetweetboard
                                  ))

        # used to check if user wants latest tweets from a specific insider
        elif msg['text'].split(' ')[-1] == 'update' and msg['text'][0] == '@':
            screen_name = msg['text'].split(' ')[0][1:]
            data = miner.get_insider_latest_tweet(screen_name=screen_name)
            if data == "":
                await bot.sendMessage(chat_id, "No new tweets found from " + screen_name)
            else:
                await bot.sendMessage(chat_id, miner.mine_user_tweets(screen_name=screen_name))

# sends to a chat the updates from update_tweets automatically


async def update_tweets():
    data = miner.mine_all_tweets()
    if len(data) != 0:
        with open('group_chat_ids.txt') as f:
            for line in f:
                for i in data:
                    await bot.sendMessage(line, i)

# Program startup, establishes miner, keyboard prompts, and connects with telegram API
# Initiates scheduler for updating tweets every 15 minutes and getting 5 most relevant tweets
if __name__ == "__main__":
    miner = TweetMiner()

    latesttweetboard = []
    for item in miner.insider_handles:
        latesttweetboard.append(KeyboardButton(
            text="@"+item+" latest"))
    latesttweetboard = [latesttweetboard[i:i + 4]
                        for i in range(0, len(latesttweetboard), 4)]

    updatetweetboard = []
    for item in miner.insider_handles:
        updatetweetboard.append(KeyboardButton(
            text="@"+item+" update"))
    updatetweetboard = [updatetweetboard[i:i + 4]
                        for i in range(0, len(updatetweetboard), 4)]

    TOKEN = os.environ.get("TelegramAPI")
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLScAzUoQKN6edA85vrOJcp-wY0tfaUQlofk8aV_RI_pSolEkKw/viewform?usp=sf_link"
    bot = telepot.aio.Bot(TOKEN)
    asyncio.get_event_loop().create_task(MessageLoop(
        bot, handle_msg).run_forever())

    # run to see if large delay time (1 hr) is good enough- everything else works
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_tweets, 'interval', minutes=5)
    scheduler.start()

    print('Listening ...')

    # Keep the program running
    asyncio.get_event_loop().run_forever()
