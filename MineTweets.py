import tweepy
import os

# twitter auth keys

# class TweetMiner to mine for the appropriate tweets- use methods as true

auth = {'consumer_key': os.environ.get("twitter_consumer_key"),
        'consumer_secret': os.environ.get("twitter_consumer_secret"),
        'access_token_key': os.environ.get("twitter_access_key"),
        'access_token_secret': os.environ.get("twitter_access_secret")}

# auth = {'consumer_key': "co90c3LN6leV6nRwnOxXxHy98",
#         'consumer_secret': "G19ZffB6EK49d5mORIIOzLLliS4mXSgqFFoPq5RTbpsPiBruIe",
#         'access_token_key': "1506422705049911297-zCPHWAyczGOv0BPUXjwe9J8jyN048p",
#         'access_token_secret': "V5NbekGAFwt5r1JrUno3DyAyZQca10ikrqF8LGsVKeo8f"}


class TweetMiner():

    result_limit = 5  # max latest tweets is 5,
    api = False  # tweety api
    insiders = set()  # set of insiders
    insiders_to_string = ""
    insider_handles = set()
    bingwords = set()  # set of key hawks-related words
    user_to_latest_tweet_id = {}  # user_id to tweet_id of latest tweet
    user_to_name = {}  # user_id to name of user
    tweet_id_to_text = {}  # tweet_id to text of tweet
    tweet_id_to_quoted_text = {}  # tweet_id to quoted text of tweet
    tweet_id_to_quoted_screen_name = {}  # tweet_id to quoted user name

    # initializes user to my acct, gets the insiders from predetermined list, result limit, tweepy API
    # gets each insider's last recorded tweet (updates every X amount of time)
    # links
    def __init__(self, keys_dict=auth, result_limit=5):

        auth = tweepy.OAuth1UserHandler(
            keys_dict['consumer_key'], keys_dict['consumer_secret'],
            keys_dict['access_token_key'], keys_dict['access_token_secret'])
        self.api = tweepy.API(auth)
        self.result_limit = result_limit
        self.insiders = set()
        self.insider_handles = set()
        self.bingwords = set()
        with open('insiders.txt') as f:
            for line in f:
                self.insiders.add(int(line.split(' ')[0]))
                self.insider_handles.add(line.split(' ')[1])

        with open('bingwords.txt') as f:
            for line in f:
                self.bingwords.add(line.strip())

        for user_id in self.insiders:
            tweets = self.api.user_timeline(
                user_id=user_id, include_rts=False, exclude_replies=True, tweet_mode="extended")
            if(tweets == None):
                continue
            tweet = tweets[0]
            self.user_to_latest_tweet_id[user_id] = tweet.id
            self.user_to_name[user_id] = self.api.get_user(
                user_id=user_id).name
            self.tweet_id_to_text[tweet.id] = tweet.full_text

            try:
                quote_text = tweet.quoted_status.full_text
                quote_name = tweet.quoted_status.user.name
            except:
                quote_text = None
                quote_name = None

            self.tweet_id_to_quoted_text[tweet.id] = quote_text
            self.tweet_id_to_quoted_screen_name[tweet.id] = quote_name
        self.insiders_to_string = "Insiders: " + \
            (", ".join(self.user_to_name.values()))

    # get list of insiders
    def get_insiders(self):
        return self.insiders_to_string

    # get latest tweet for every insider
    def get_insiders_latest_tweets(self):
        data = []
        for user_id in self.user_to_latest_tweet_id.keys():
            data.append(self.get_insider_latest_tweet(user_id=user_id))
        return data

    # get latest tweet for one insider, specified by either user_id or screen_name
    def get_insider_latest_tweet(self, user_id=None, screen_name=None):
        if(user_id == None and screen_name == None):
            return "Error: invalid user_id and screen_name"
        else:
            if(user_id == None):
                user_id = self.api.get_user(screen_name=screen_name).id
            if(user_id not in self.insiders):
                return "This user is either not valid or is not considered a reputable source"
            username = self.user_to_name[user_id]
            tweet_id = self.user_to_latest_tweet_id[user_id]
            text = self.tweet_id_to_text[tweet_id]
            quoted_text = self.tweet_id_to_quoted_text[tweet_id]
            quoted_name = self.tweet_id_to_quoted_screen_name[tweet_id]
            return self._print_tweet(username, text, quoted_text, quoted_name)

    # mine the last 5 tweets of every insider
    def mine_all_tweets(self):
        data = []
        for id in self.insiders:
            tweets = self.mine_user_tweets(user_id=id)
            if tweets != "":
                data.append(tweets)
        return data

    # mine the last 5 relevant tweets of a given insider, specified by user_id or screen_name
    # only add tweets that are a deemed true by parse_for_words
    def mine_user_tweets(self, user_id=None, screen_name=None):
        if(user_id == None and screen_name == None):
            return "Error: invalid user_id and screen_name"
        else:
            if(user_id == None):
                user_id = self.api.get_user(screen_name=screen_name).id
            data = ""
            if user_id in self.insiders:
                latest_tweet_id = self.user_to_latest_tweet_id[user_id]
                statuses = self.api.user_timeline(
                    user_id=user_id, since_id=latest_tweet_id, include_rts=False, exclude_replies=True, tweet_mode="extended")
                if len(statuses) == 0:
                    return ""
                self.user_to_latest_tweet_id[user_id] = statuses[0].id
            else:
                return "This user is either not valid or is not considered a reputable source"
            total = 0
            for item in statuses:
                if(total >= 5):
                    break
                else:
                    parseditem = self._parse_for_words(item)
                    if(parseditem == None):
                        continue
                    else:
                        username = self.user_to_name[user_id]
                        text = item.full_text
                        try:
                            quote_text = item.quoted_status.full_text
                            quote_name = item.quoted_status.user.name
                        except:
                            quote_text = None
                            quote_name = None
                        data += self._print_tweet(
                            username, text, quote_text, quote_name)+"\n"
                        total += 1
            return data

    # mine the most relevant tweets containing the keyword
    def mine_for_new_tweets_with_keyword(self, keyword):
        if(len(keyword) <= 2):
            return ["Keyword is too general"]
        else:
            data = []
            for id in self.insiders:
                tweets = self.mine_user_for_new_tweets_with_keyword(
                    keyword, user_id=id)
                if tweets != "":
                    data.append(tweets)
            return data

    # mine the last 3 tweets of a given insider, specified by either user_id or screen_name
    # only add tweets that contain the given keyword
    def mine_user_for_new_tweets_with_keyword(self, keyword, user_id=None, screen_name=None):
        if(user_id == None and screen_name == None):
            return "Error: invalid user_id and screen_name"
        else:
            if(user_id == None):
                user_id = self.api.get_user(screen_name=screen_name).id
            data = ""
            if user_id in self.insiders:
                latest_tweet_id = self.user_to_latest_tweet_id[user_id]
                statuses = self.api.user_timeline(
                    user_id=user_id, include_rts=False, exclude_replies=True, tweet_mode="extended")
                if len(statuses) == 0:
                    return "No new tweets found since last request from " + self.user_to_name[user_id]
                self.user_to_latest_tweet_id[user_id] = statuses[0].id
            else:
                return str(user_id) + " is either not valid or is not considered a reputable source"
            total = 0
            for item in statuses:
                if(total >= 3):
                    break
                else:
                    if keyword in item.full_text:
                        username = self.user_to_name[user_id]
                        text = item.full_text
                        try:
                            quote_text = item.quoted_status.full_text
                            quote_name = item.quoted_status.user.name
                        except:
                            quote_text = None
                            quote_name = None
                        data += self._print_tweet(
                            username, text, quote_text, quote_name)+"\n"
                        total += 1
                    else:
                        continue
            return data

    # Prints a tweet, and quoted response if possible
    def _print_tweet(self, username, text, quoted_text=None, quoted_name=None):
        toRet = "Tweet by "+username+": "+text+"\n"
        if(quoted_text != None):
            toRet += "In response to tweet by "+quoted_name+": "+quoted_text+"\n"
        return toRet

    # checks if given tweets contains any of the bing words, if so add first 5 to list and return
    def _parse_for_words(self, tweet):
        if any(x in tweet.full_text for x in self.bingwords):
            return tweet
        else:
            return None


# # testbench for the miner class and methods within it
# tempid = 51263592  # Schefter- for general
# tempidseattle = 157078263  # Brady Henderson- hawks based
# miner = TweetMiner()
# print(miner.get_insiders())
# print(miner.get_insider_latest_tweet(tempid))
# print(miner.get_insiders_latest_tweets())
# print(miner.mine_user_tweets(user_id=tempid))
# print(miner.mine_user_tweets(user_id=tempidseattle))
# print(miner.mine_all_tweets())
# print(miner.mine_for_new_tweets_with_keyword("Sidney"))
# print(miner.mine_user_for_new_tweets_with_keyword("Sidney", user_id=tempidseattle))
