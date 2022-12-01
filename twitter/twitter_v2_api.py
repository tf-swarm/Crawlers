import tweepy


class TwitterApi():

    def __init__(self):
        # https://github.com/tweepy/tweepy/tree/master/examples/API_v2
        # https://docs.tweepy.org/en/stable/client.html
        # https://dev.to/twitterdev/a-comprehensive-guide-for-using-the-twitter-api-v2-using-tweepy-in-python-15d9
        self.bearer_token = "xxxxx"
        self.consumer_key = "xxxxx"
        self.consumer_secret = "xxxxx"
        self.access_token_key = "xxxxx-xxxxx"
        self.access_token_secret = "xxxxx"
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        # self.clients = tweepy.Client(
        #     consumer_key=self.consumer_key, consumer_secret=self.consumer_secret,
        #     access_token=self.access_token_key, access_token_secret=self.access_token_secret
        # )


    def get_liked_tweets(self, user_id):
        # user_id = 957716432430641152   AxieInfinity
        # tweet_id = 1567901811570536448
        response = self.client.get_liked_tweets(user_id,tweet_fields=['created_at', 'id', 'text'])
        for tweet in response.data:
            print(tweet.created_at, tweet.id, tweet.text)
        return response.data

    def get_user_info(self, username):
        response = self.client.get_user(username=username, user_fields=['created_at', 'description', 'id', 'name', 'username', 'profile_image_url'])
        user = response.data
        user_info = {"created_at": user.created_at, "name": user.name, "user_id": user.id, "image_url": user.profile_image_url, "description": user.description}
        return user_info



if __name__ == '__main__':
    username = "AxieInfinity"
    tw = TwitterApi()
    tw.get_user_info(username)