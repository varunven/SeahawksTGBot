from MineTweets import TweetMiner
import os
from time import sleep
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import MessageHandler, Filters, ConversationHandler, Updater, CommandHandler, CallbackContext

# MAJOR CHANGE MADE TO TELEPOT IN PYTHON3100/LIB/SITE-PACKAGES/LOOP.PY TO CHANGE
# _EXTRACT_MESSAGE TO INCLUDE 'update_id' AS PART OF KEY. MAKE SURE TO ADD TO END OF LIST

# general handling of messages- small, niche number of cases for each command

GETINSIDER = range(1)
GETKEYWORD = range(1)
GETINSIDERUPDATE = range(1)
chat_ids = set()


def add_chat_id(update: Update, context: CallbackContext) -> None:
    chat_ids.add(update.message.chat_id)

# sends to a chat the updates from update_tweets automatically


def schedule_tweets(context: CallbackContext) -> None:
    data = miner.mine_all_tweets()
    for chat_id in chat_ids:
        if len(data) != 0:
            for i in data:
                context.bot.send_message(chat_id=chat_id, text=i)

# what to send on starting the bot


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        f'Hello {update.effective_user.first_name}\nI am Seahawks Twitter Feed, a bot that routinely accesses twitter to pull the most recent Seahawks-related information from a list of reputable, verified sources.')


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Cancelled request.', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# returns a list of all insiders used


def getinsiders(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(miner.get_insiders())

# returns the latest tweets of all users


def getlatesttweets(update: Update, context: CallbackContext) -> None:
    data = miner.get_insiders_latest_tweets()
    for i in range(len(data)):
        item = data[i]
        try:
            update.message.reply_text(item)
        except:
            update.message.reply_text(
                "Timed out. There may be too many tweets with this keyword to handle")
            i -= 1

# process the latest tweet provided based on insider


def processlatest(update: Update, context: CallbackContext) -> int:
    msg = update.message.text
    update.message.reply_text(miner.get_insider_latest_tweet(
        screen_name=msg))
    return ConversationHandler.END

# returns the latest tweet of a user selected by the user from the latesttweetbuttonboard


def getlatesttweetfromuser(update: Update, context: CallbackContext) -> int:
    reply_markup = ReplyKeyboardMarkup(
        keyboard=tweetboard, one_time_keyboard=True)
    update.message.reply_text(
        'Select an Insider To Get the Latest Tweet Of (Type /cancel to cancel)', reply_markup=reply_markup)
    return GETINSIDER

# process the list of tweets based on the keyword


def processkeyword(update: Update, context: CallbackContext) -> int:
    msg = update.message.text
    data = miner.mine_for_new_tweets_with_keyword(msg)
    if len(data) == 0:
        update.message.reply_text(
            "No tweets found in the last 12 hours containing " + msg)
    else:
        for i in data:
            update.message.reply_text(i)
    return ConversationHandler.END

# returns the latest tweet of a user selected by the user from the latesttweetbuttonboard


def gettweetswithkeyword(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "First, ensure Seahawks Twitter Feed has access to messages. Then, please type your keyword in the chat (Type /cancel to cancel)")
    return GETKEYWORD

# updates tweets to newest cycle


def updatetweets(update: Update, context: CallbackContext) -> None:
    data = miner.mine_all_tweets()
    if len(data) == 0:
        update.message.reply_text("No new tweets found since last request")
    else:
        for i in data:
            update.message.reply_text(i)

# process the latest tweet provided based on insider


def processupdate(update: Update, context: CallbackContext) -> int:
    msg = update.message.text
    data = miner.mine_user_tweets(screen_name=msg)
    if data == "":
        update.message.reply_text("No new tweets found from " + msg)
    else:
        update.message.reply_text(data)
    return ConversationHandler.END


# returns the latest tweet of a user selected by the user from the latesttweetbuttonboard

def updatetweetfromuser(update: Update, context: CallbackContext) -> int:
    reply_markup = ReplyKeyboardMarkup(
        keyboard=tweetboard, one_time_keyboard=True)
    update.message.reply_text(
        'Select an Insider To Get the Latest Tweet Of (Type /cancel to cancel)', reply_markup=reply_markup)
    return GETINSIDERUPDATE


# Program startup, establishes miner, keyboard prompts, and connects with telegram API
# Initiates scheduler for updating tweets every 15 minutes and getting 5 most relevant tweets
if __name__ == "__main__":
    miner = TweetMiner()

    tweetboard = []
    for item in miner.insider_handles:
        tweetboard.append(KeyboardButton(
            text="@"+item))
    tweetboard = [tweetboard[i:i + 4]
                  for i in range(0, len(tweetboard), 4)]

    TOKEN = os.environ.get("TelegramAPI")
    updater = Updater(TOKEN, use_context=True)
    updates = updater.bot.get_updates()
    updater.dispatcher.add_handler(CommandHandler('start', start))

    updater.dispatcher.add_handler(CommandHandler('getinsiders', getinsiders))
    updater.dispatcher.add_handler(
        CommandHandler('getlatesttweets', getlatesttweets))

    latest_tweet_conv_handler = ConversationHandler(
        entry_points=[CommandHandler(
            'getlatesttweetfromuser', getlatesttweetfromuser)],
        states={
            GETINSIDER: [MessageHandler(
                Filters.regex('^[@].*$'), processlatest)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    updater.dispatcher.add_handler(latest_tweet_conv_handler)

    keyword_conv_handler = ConversationHandler(
        entry_points=[CommandHandler(
            'gettweetswithkeyword', gettweetswithkeyword)],
        states={
            GETKEYWORD: [MessageHandler(
                Filters.text, processkeyword)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    updater.dispatcher.add_handler(keyword_conv_handler)

    updater.dispatcher.add_handler(
        CommandHandler('updatetweets', updatetweets))

    update_tweet_conv_handler = ConversationHandler(
        entry_points=[CommandHandler(
            'updatetweetfromuser', updatetweetfromuser)],
        states={
            GETINSIDERUPDATE: [MessageHandler(
                Filters.regex('^[@].*$'), processupdate)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    updater.dispatcher.add_handler(update_tweet_conv_handler)

    updater.dispatcher.add_handler(MessageHandler(
        Filters._StatusUpdate.new_chat_members, add_chat_id))

    print("Listening...")
    job_queue = updater.job_queue
    job_queue.run_repeating(schedule_tweets, interval=900)

    updater.start_polling()
    updater.idle()
