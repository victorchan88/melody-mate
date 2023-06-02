
# MelodyMate

MelodyMate is a plugin that interacts with Spotify's API to create personalized playlists based on user's preferences. It can create playlists, fetch playlists, and add tracks to playlists.

# Run on ChatGPT

Prerequisite: Make sure you have ChatGPT Plus along with Plugins with Development mode. Fork the code into your own GitHub so that you can deploy it on your own vercel account. Set your redirect URI in your Spotify Developer App as https://chat.openai.com/aip/enter-plugin-id-after-first-try/oauth/callback.

    1. Go to ChatGPT 4 and click Plugins
    2. Go to the Plugin Store and on the bottom right, click on develop your own plugin
    3. Use your vercel url to the deployment when it asks for the domain to find the manifest file
    4. Enter your Client ID and Client Secret from your Spotify Developer account
        i. You have to create a new app in your Spotify Developer account and it will generate a client id and secret for you
    5. Update the openai verification token as highlighted in the ai-plugin.json
        i. ChatGPT will generate this for you after step 4
    6. When you click Login, it will initially fail due to the redirect URI being incorrect
    7. Copy the section of the url that has "plugin-{ids}" and replace it in the "enter-plugin-id-after-first-try" section as highlighted above
        i. Ex: plugin-fwef2862e-d8b7-413f-8230-9108ec3db71a
    8. Use this new redirect URI and put it into your Spotify Developer part of your App
    9. Repeat steps 1-6 and you will have your own ChatGPT plugin

# Usage (ChatGPT)
    1. Enter phrases such as "Give me a playlist for motivation"
    2. Try to use less words as possible for the query as it will help with returning relevant results

# Run on Local (Testing/Development)
    1. Git clone the application and copy the src/dev folder into a separate folder outside of melody-mate
    2. Install any missing modules (pip install <module-name> works for all of them)
    3. Fill in the Spotify client id, client secret, and database_uri in the .env file

# .env File
SPOTIFY_CLIENT_ID=""\
SPOTIFY_CLIENT_SECRET=""\
DATABASE_URI=""

# Run on Local (cont.)
    4. Run python main.py
    5. If there are errors with the database, put in db.create_all() in the main.py file before any of the route functions

# Usage (Local)
    1. After starting the application, go to http://localhost:8080 to login
    2. Enter your Spotify username and password to login and you should see a success message returned
    3. Now you can run http://localhost:8080/playlist?query="<Desired search for music>"
    
