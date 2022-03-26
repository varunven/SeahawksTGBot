import mytelepot.telepot as telepot
from mytelepot.telepot.loop import MessageLoop
from MineTweets import TweetMiner
from mytelepot.telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import os
from time import sleep

# MAJOR CHANGE MADE TO TELEPOT IN PYTHON3100/LIB/SITE-PACKAGES/LOOP.PY TO CHANGE
# _EXTRACT_MESSAGE TO INCLUDE 'update_id' AS PART OF KEY. MAKE SURE TO ADD TO END OF LIST

# general handling of messages- small, niche number of cases for each command

chat_ids = set()


def handle_msg(msg):
    # These are some useful variables
    content_type, chat_type, chat_id = telepot.glance(msg)
    # Log variables
    print("Message:", content_type, chat_type, chat_id)
    if(content_type == "new_chat_member"):
        chat_ids.add(chat_id)
    elif(content_type == "left_chat_member" and (chat_id in chat_ids)):
        chat_ids.remove(chat_id)
    # Send our JSON msg variable as reply message
    if content_type == 'text':

        # returns all the insiders
        if msg['text'] == '/getinsiders' or msg['text'] == '/getinsiders@seahawks_tg_bot':
            bot.sendMessage(chat_id, miner.get_insiders())

        # returns all the latest tweets
        elif msg['text'] == '/getlatesttweets' or msg['text'] == '/getlatesttweets@seahawks_tg_bot':
            data = miner.get_insiders_latest_tweets()
            for i in data:
                bot.sendMessage(chat_id, i)

        # returns the latest tweet of a user selected by the user from the latesttweetbuttonboard
        elif msg['text'] == '/getlatesttweetfromuser' or msg['text'] == '/getlatesttweetfromuser@seahawks_tg_bot':
            bot.sendMessage(chat_id, 'Select an Insider To Get the Latest Tweet Of',
                            reply_markup=ReplyKeyboardMarkup(
                                keyboard=latesttweetboard
                            ))

        # returns all the latest tweets with a keyword
        elif msg['text'] == '/gettweetswithkeyword' or msg['text'] == '/gettweetswithkeyword@seahawks_tg_bot':
            bot.sendMessage(
                chat_id, "Please type your word, ______, in the chat with the format 'keyword: ______'")

        elif msg['text'].split()[0] == 'keyword:':
            data = miner.mine_for_new_tweets_with_keyword(
                msg['text'].split()[1])
            for i in data:
                bot.sendMessage(chat_id, i)

        # used to check if user wants latest tweets from a specific insider
        elif msg['text'].split(' ')[-1] == 'latest' and msg['text'][0] == '@':
            screen_name = msg['text'].split(' ')[0][1:]
            bot.sendMessage(chat_id, miner.get_insider_latest_tweet(
                screen_name=screen_name))

        # updates all tweets
        elif msg['text'] == '/updatetweets' or msg['text'] == '/updatetweets@seahawks_tg_bot':
            data = miner.mine_all_tweets()
            if len(data) == 0:
                bot.sendMessage(
                    chat_id, "No new tweets found since last request")
            else:
                for i in data:
                    bot.sendMessage(chat_id, i)

        # updates tweets for one user
        elif msg['text'] == '/updatetweetfromuser' or msg['text'] == '/updatetweetfromuser@seahawks_tg_bot':
            bot.sendMessage(chat_id, 'Select an Insider To Update the Tweets Of',
                            reply_markup=ReplyKeyboardMarkup(
                                keyboard=updatetweetboard
                            ))

        # used to check if user wants latest tweets from a specific insider
        elif msg['text'].split(' ')[-1] == 'update' and msg['text'][0] == '@':
            screen_name = msg['text'].split(' ')[0][1:]
            data = miner.mine_user_tweets(screen_name=screen_name)
            if data == "":
                bot.sendMessage(
                    chat_id, "No new tweets found from " + screen_name)
            else:
                bot.sendMessage(chat_id, data)

# sends to a chat the updates from update_tweets automatically


def update_tweets(chat_ids):
    print(chat_ids)
    data = miner.mine_all_tweets()
    if len(data) != 0:
        for chat_id in chat_ids:
            for i in data:
                bot.sendMessage(chat_id, i)


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
    bot = telepot.Bot(TOKEN)
    MessageLoop(bot, handle_msg).run_as_thread()

    print('Listening ...')

    while(1):
        update_tweets(chat_ids)
        sleep(900)
