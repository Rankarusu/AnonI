"""logic for shitposting on twitter"""
import time
import random
import re
from happytransformer import HappyGeneration, GENSettings
import schedule
import tweepy

from access import config
import prompts


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
    return random.choice(prompts.prompts)


def get_shitpost(model, settings, prompt):
    """get a shitpost from the AI"""
    result = model.generate_text(prompt, args = settings)
    return result.text


def prep_shitpost(prompt, post):
    """prepare a shitpost for posting"""

    post = post.strip()
    if post.startswith((".", "!", "?")):
        post = post.strip(".!?")
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


def shitpost(api, model, settings):
    """put it all together"""
    prompt = get_prompt()
    post = get_shitpost(model, settings, prompt)
    cleaned_post = prep_shitpost(prompt, post)

    print("___________________before cleaning___________________")
    print(post)
    print("___________________after cleaning____________________")
    print(cleaned_post)

    api.update_status(cleaned_post)
    #TODO: maybe put posts into a queue first.


def main():
    """setup everything and schedule posts every hour"""
    #login
    api = twitter_login()
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
    #schedule to post every hour
    schedule.every().hour.at(":00").do(shitpost, api=api, model=happy_gen, settings=settings)
    while True:
        schedule.run_pending()
        time.sleep(1)
    # shitpost(api, happy_gen, settings)


if __name__ == "__main__":
    main()

# auth stuff
# print(auth.get_authorization_url())
# verifier = text("PIN (oauth_verifier= parameter): ")

# auth.get_access_token(verifier)
# print(auth.access_token)
