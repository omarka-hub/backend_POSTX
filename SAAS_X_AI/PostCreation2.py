import feedparser
import re
import sys
import requests
from openai import OpenAI
import tweepy
from io import BytesIO
import os



def create_post2(rss_url, BEARER_TOKEN, API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, video_option, image_option, system_prompt, user_prompt):
    # Parse the RSS feed
    feed = feedparser.parse(rss_url)

    # Get the latest post
    if not feed.entries:
        print("No entries found.")
        exit()

    last_item = feed.entries[0]


    # Title
    title = last_item.get("title", "No Title")

    # Description
    description = last_item.get("summary", "No Description")

    # Link
    link = last_item.get("link", "No Link")

    # Image URL from media_content (if it exists)
    image_url = None
    if "media_content" in last_item and isinstance(last_item["media_content"], list):
        for media in last_item["media_content"]:
            if media.get("medium") == "image" and media.get("url"):
                image_url = media["url"]
                break

    # Output
    print("Title:", title)
    print("Description:", description)
    print("Link:", link)
    print("Image URL:", image_url if image_url else "No image found")

    if image_url:
        if "amplify_video_thumb" in image_url:
            media_type =  "video_thumbnail"
        elif "pbs.twimg.com/media/" in image_url:
            media_type = "image"
        else:
            media_type = "image"
    else:
        media_type = "none"

    print(media_type)

    #text parser
    html_content = description

    tag_re = re.compile(r'<[^>]+>')
    plain_text = tag_re.sub('', html_content)

    print(f"Parsed Description: {plain_text.strip()}")
    rss_post = plain_text.strip()

    if "{rss_post}" in user_prompt:
        ai_user_prompt = user_prompt.format(rss_post=rss_post)
    else:
        ai_user_prompt = user_prompt 

    # OpenAI request
    try:
        client = OpenAI(api_key="your_openai_api_key_here")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ai_user_prompt}
            ]
        )
        tweet = response.choices[0].message.content.strip()

        if not tweet:
            raise ValueError("OpenAI returned an empty tweet.")

        print(f"OpenAI Response: {tweet}")

    except Exception as e:
        print(f"OpenAI error: {e}")
        tweet = rss_post  # fallback: use the RSS description only
        print(f"⚠️ Fallback tweet used: {tweet}")



    # Check for media status
    if media_type == "image":
        image_status = True
        video_status = False
    elif media_type == "video_thumbnail":
        image_status = False
        video_status = True
    else:
        image_status = False
        pattern = r"https:\/\/t\.co\/[a-zA-Z0-9]+|pic\.twitter\.com\/[a-zA-Z0-9]+"
        matches = re.findall(pattern, description)
        if matches:
            print("The Post Has a video")
            for match in matches:
                print(match)
                pattern = r"/status/(\d+)"
                matches = re.findall(pattern, link)
                print("Matched tweet IDs:")
            for match in matches:
                print(match)
            video_status = True
        else:
            print("No video found")
            video_status = False

    # Upload media
    if image_option == "no":
        attach_media = False
    elif image_option == "ok":
        if image_status == True:
            # URL of the media file
            media_url = image_url  # Replace with your media URL

            # Authenticate with the API
            auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
            api = tweepy.API(auth)

            try:
                # Fetch the media from the URL
                response = requests.get(media_url, stream=True)
                response.raise_for_status()  # Raise an error for bad status codes

                # Load the media into memory as binary data
                media_data = BytesIO(response.content)

                try:
                    # Upload media from binary data
                    media = api.media_upload(filename="temp.jpg", file=media_data)  # Ensure filename has a valid extension
                    print("Media uploaded successfully!")
                    media_id = media.media_id  # Get the media ID
                    print(f"Media ID: {media_id}")
                except Exception as e:
                    print(f"An error occurred while uploading the media: {e}")
                    media_id = None

                if not media_id:
                    print("Failed to upload media.")
                    
            except Exception as e:
                print(f"An error occurred while fetching the media: {e}")
            attach_media = True
        else:
            attach_media = False

    if video_option == "ok":
        if video_status == True:
            attach_post = True
        else:
            attach_post = False
    else:
        attach_post = False
    


    # Create the post on X
    client = tweepy.Client(BEARER_TOKEN, API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)    

    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    if attach_media == True:
            try:
                response = client.create_tweet(text=tweet, media_ids=[media_id])
                if response and hasattr(response, 'data') and 'id' in response.data:
                    tweet_id = response.data['id']
                    print(f"Tweet created successfully! Tweet ID: {tweet_id}")
                    tweet_status = "success"
                else:
                    print("Failed to post the tweet.")
            except Exception as e:
                print(f"An error occurred while posting the tweet: {e}")
    elif attach_media == False:
        if attach_post == True:
                    try:
                        response = client.create_tweet(text=tweet, quote_tweet_id=match)
                        if response and hasattr(response, 'data') and 'id' in response.data:
                            tweet_id = response.data['id']
                            print(f"Tweet created successfully! Tweet ID: {tweet_id}")
                            tweet_status = "success"
                        else:
                            print("Failed to post the tweet.")
                    except Exception as e:
                        print(f"An error occurred while posting the tweet: {e}")
        elif attach_post == False:
                    try:
                        response = client.create_tweet(text=tweet)
                        if response and hasattr(response, 'data') and 'id' in response.data:
                            tweet_id = response.data['id']
                            print(f"Tweet created successfully! Tweet ID: {tweet_id}")
                            tweet_status = "success"
                        else:
                            print("Failed to post the tweet.")
                    except Exception as e:
                        print(f"An error occurred while posting the tweet: {e}")
    
    return tweet_status, tweet, image_status, video_status, image_option, video_option