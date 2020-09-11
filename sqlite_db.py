# Local sqlite database to data for DiscordBot
# TODO: Put all user checks into one function. Create an extra variable so that after user check function is called, app knows which function to call next.
# TODO: Check if valid youtube_link in both register_user and change_theme. If valid, convert it to mp3 and store it in filesystem.
import sqlite3
import youtube_dl as ydl
import pathlib

'''
TABLE STRUCTURE
table_name = themes
_______________________
user_id | user_name | theme_name | theme_id
_______________________
'''

'''
DATABASE FUNCTIONS
'''

# Creates a connection to the database
def create_connection():
    conn = sqlite3.connect('gangbot.db')
    return conn

# Function to register new discord user to database
def register_user(id: str, name: str, theme_url = None):
    # Create database connection
    conn = create_connection()
    c = conn.cursor()

    # Check if user exists in the database
    user_id = (id,)
    c.execute('SELECT * FROM themes WHERE user_id=?', user_id)
    if c.fetchone():
        print("User already exists")
        # Print all users. Keep for debugging purposes
        for row in c.execute("SELECT * FROM themes"):
            print(row)
        # return "User already exists"
    else:
        # Check if theme is a valid youtube url
        if theme_url is not None:
            if valid_url(theme_url):
                theme_info = get_metadata(theme_url)
                user_details = [id, name, theme_info.get('title', None), theme_info.get('id', None)]
                c.execute("INSERT INTO themes values (?, ?, ?, ?)", user_details)
                conn.commit()
        else:
            # TODO: Add else code. Can be optimized
            user_details = [id, name, None, None]
            c.execute("INSERT INTO themes values (?, ?, ?, ?)", user_details)
            conn.commit()
    conn.close()

# Changes the theme of the discord user
# Gets theme from youtube url
def change_theme(id: str, theme: str):
    # Create database connection
    conn = create_connection()
    c = conn.cursor()

    # Check if user exists in the database
    user_id = (id,)
    c.execute('SELECT * FROM themes WHERE user_id=?', user_id)
    if not c.fetchone():
        print("User does not exist. Create one first")
        # Print all users. Keep for debugging purposes
        for row in c.execute("SELECT * FROM themes"):
            print(row)
        # return "User does not exist. Create one first"
    else:
        # Get user details and edit the theme
        if valid_url(theme):
            theme_info = get_metadata(theme)
            data = [theme_info.get('title', None), theme_info.get('id', None), id]
            query = ("""UPDATE themes set theme_title = ?, theme_id = ? where user_id = ?""")
            c.execute(query, data)

            conn.commit()
            print("Edited user details")
        else:
            print("Youtube url is invalid")

    conn.close()

# Gets all the users in the database
def user_list():
    conn = create_connection()
    print('Value of conn var: ', conn)
    c = conn.cursor()
    print('Value of c var: ', c)

    for row in c.execute('SELECT * FROM themes ORDER BY user_id'):
        print('Value of row: ', row)

# Creates a video_id column if it does not exist in the database.
# Temp function
def videoid_column():
    conn = create_connection()
    c = conn.cursor()

    add_column = 'ALTER TABLE themes ADD COLUMN theme_id varchar(32)'
    c.execute(add_column)
    user_list()

# Creates the database if it does not exist
def create_database():
    try:
        open('gangbot.db')
        print('Database exists. Skipping creation...')
    except OSError as e:
        conn = create_connection()
        print('Database created')
        c = conn.cursor()

        # Create table
        c.execute('''CREATE TABLE themes
                        (user_id text, user_name text, theme_title text, theme_id text)''' )

        conn.commit()
        conn.close()
    

'''
YOUTUBE FUNCTIONS 
'''

class MyLogger(object):
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

# Checks if link is a valid youtube url
def valid_url(url: str):
    extractors = ydl.extractor.gen_extractors()
    for e in extractors:
        if e.suitable(url) and e.IE_NAME != 'generic':
            return True
    return False

# Gets the title and id of a youtube video
def get_metadata(url: str):
    with ydl.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
        # video_title = info_dict.get('title', None)
        # video_id = info_dict.get('id', None)
        return info_dict

# Converts youtube link to mp3 and saves it to local filesystem
def youtube_mp3(url: str):
    # Check if themes folder exists
    p = pathlib.Path('themes')
    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=False)
            print("Themes directory created")

            # print(pathlib.PureWindowsPath('themes').joinpath('%(title)s.%(ext)s'))
            print(type(pathlib.PureWindowsPath('themes').joinpath('/test.mp3').as_posix()))
        except IOError as ex:
            print("Unexpected error occurred: ", ex)
            return False
    else:
        print('Folder already exists')
    # Download youtube link as mp3
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': (pathlib.PureWindowsPath('themes').joinpath('%(title)s.%(ext)s')).as_posix(),
        # 'outtmpl': 'themes/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }

    ydl.YoutubeDL(ydl_opts).download([url])
    
register_user('15549', 'Test')
# change_theme('15548', 'Violet')
# change_theme('15546', 'http://www.youtube.com/watch?v=BaW_jenozKc')
user_list()
# youtube_mp3("https://www.youtube.com/watch?v=HaGkk60kcjQ")
# videoid_column()
# create_database()

