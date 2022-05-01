"""logic for shitposting on twitter"""
import time
import random
import re
from happytransformer import HappyGeneration, GENSettings
import schedule
import tweepy

from access import config
from prompts import prompts


def twitter_login():
    """login to twitter"""
    auth = tweepy.OAuthHandler(
        config.API_KEY, config.API_KEY_SECRET,
        )
    auth.set_access_token(config.ANON_TOKEN, config.ANON_TOKEN_SECRET)
    api = tweepy.API(auth)
    return api


def get_prompt():
    """get a prompt from prompts.py"""
    key = random.choice(list(prompts.keys()))
    noun = random.choice(prompts[key]["prompts"])
    verb = random.choice(prompts[key]["continuations"])

    return " ".join([noun, verb]).strip()


def get_shitpost(model, settings, prompt):
    """get a shitpost from the AI"""
    #strip of # so the AI is not confused
    result = model.generate_text(prompt.lstrip("#"), args = settings)
    return result.text


def prep_shitpost(prompt, post, reply_id=None):
    """prepare a shitpost for posting"""
    #strip prompt from post if if just ends the sentence there
    post = post.strip()
    if post.startswith((".", "!", "?")) or reply_id is not None:
        post = post.lstrip(".!?")
        result = post
    else:
        result = prompt + " " + post

    try:
        result = re.search(r"(.*)[.!?;]", result).group(0)
    except Exception:
        pass


    result = " ".join(result.split())
    result = re.sub(r"\s*'\s*", "'", result)
    result = re.sub(r"\s*,\s*", ", ", result)
    result = re.sub(r"\s*\.\s*", ". ", result)
    result = re.sub(r"\s*>\s*", "\n>", result)

    return result


def shitpost(api, model, settings, prompt=None, reply_id=None):
    """put it all together. prompt gets selected randomly if none is given"""
    if prompt is None:
        prompt = get_prompt()
    post = get_shitpost(model, settings, prompt)
    cleaned_post = prep_shitpost(prompt, post, reply_id)

    if reply_id is not None:
        print(f"replying to post with id:{reply_id} - original message:{prompt}")
        api.update_status(cleaned_post, in_reply_to_status_id=reply_id, auto_populate_reply_metadata=True)
    else:
        print(f"posting message with prompt:{prompt}")
        api.update_status(cleaned_post)

    print("___________________before cleaning___________________")
    print(post)
    print("___________________after cleaning____________________")
    print(cleaned_post)

    #TODO: maybe put posts into a queue first.


def get_mentions(api, path: str, latest_id: int, user_id: int):
    """get mentions timeline and write newest id to file"""
    mentions = api.mentions_timeline(trim_user=True, entities=False, since_id=latest_id)

    arr = []
    if len(mentions) > 0:
        for i in mentions:
            if i.author.id != user_id: #don't reply to self. avoid trolls
                arr.append((i.id, i.text.replace("@AnonI9k", "")))

        f = open(path, "w")
        f.write(str(arr[-1][0]))
        f.close()

    return arr

def get_latest_mention_id(path:str):
    """get the latest mention id from file"""
    latest_mention_id = open(path, "r").read()
    if latest_mention_id == "": #first run
        latest_mention_id = 1000000000000000000
    return int(latest_mention_id )


def reply_to_mentions(api, model, settings, user_id):
    """reply to all mentions"""
    path = "app/data/mention_id.txt"
    latest_id = get_latest_mention_id(path)
    print("latest id:", latest_id)
    mentions = get_mentions(api, path, latest_id, user_id)
    if len(mentions) > 0:
        for tweet in mentions:
            shitpost(api, model, settings, reply_id=tweet[0], prompt=tweet[1])


def main():
    """setup everything and schedule posts every hour"""
    #login
    api = twitter_login()
    user_id = api.verify_credentials().id
    # set up AI
    happy_gen = HappyGeneration("GPT-NEO", "rankarusu/AnonI")
    settings = GENSettings(
                do_sample = True,
                early_stopping = True,
                top_k = 100,
                temperature = 0.7,
                no_repeat_ngram_size = 2,
                max_length = 64,
                )
    #schedule to post every hour and check for mentions every 10 minutes
    schedule.every().hour.at(":00").do(shitpost, api=api, model=happy_gen, settings=settings)
    schedule.every(10).minutes.do(reply_to_mentions, api=api, model=happy_gen, settings=settings, user_id=user_id)
    while True:
        schedule.run_pending()
        time.sleep(1)

    #shitpost(api, happy_gen, settings)
    #reply_to_mentions(api, happy_gen, settings, user_id)



if __name__ == "__main__":
    main()

# auth stuff
# print(auth.get_authorization_url())
# verifier = text("PIN (oauth_verifier= parameter): ")

# auth.get_access_token(verifier)
# print(auth.access_token)
