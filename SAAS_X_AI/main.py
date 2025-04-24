from flask import Flask, request, jsonify
from PostCreation2 import create_post2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/create-post", methods=["POST"])
def create_post_api():
    data = request.get_json()

    # Extract parameters
    rss_url = data.get("rss_url")
    BEARER_TOKEN = data.get("bearer_token")
    API_KEY = data.get("api_key")
    API_SECRET_KEY = data.get("api_secret_key")
    ACCESS_TOKEN = data.get("access_token")
    ACCESS_TOKEN_SECRET = data.get("access_token_secret")
    video_option = data.get("video_option", "no")
    image_option = data.get("image_option", "no")
    system_prompt = data.get("system_prompt", "You are a helpful assistant.")
    user_prompt = data.get("user_prompt", "Create a post from this: {rss_post}")

    # Check required fields
    if not all([rss_url, BEARER_TOKEN, API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        return jsonify({"error": "Missing required fields"}), 400

    # Call the function
    try:
        tweet_status, tweet, image_status, video_status, image_opt, video_opt = create_post2(
            rss_url, BEARER_TOKEN, API_KEY, API_SECRET_KEY,
            ACCESS_TOKEN, ACCESS_TOKEN_SECRET,
            video_option, image_option,
            system_prompt, user_prompt
        )

        return jsonify({
            "status": tweet_status,
            "tweet": tweet,
            "image_used": image_status,
            "video_used": video_status,
            "image_option": image_opt,
            "video_option": video_opt
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)