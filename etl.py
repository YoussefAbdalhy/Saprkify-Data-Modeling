import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *



def process_song_file(cur, filepath):
    
    """
    Process songs files and insert records into the Postgres database.
    the function takes both the established cursor(cur) to the database and
    filepath to the log file (filepath)

     Parameters
    """
    # open song file
    df = df = pd.read_json(filepath,lines=True)

    # insert song record
    song_data = song_data = df[['song_id','title','artist_id','year','duration']].values.tolist()[0]
    cur.execute(song_table_insert, song_data)
    
    # insert artist record
    artist_data = artist_data = df[['artist_id', 'artist_name', 'artist_location', 'artist_latitude', 'artist_longitude']].values.tolist()[0]
    cur.execute(artist_table_insert, artist_data)


def process_log_file(cur, filepath):
    """
    Process log files and insert records into the Postgres database.
    the function takes both the established cursor(cur) to the database and
    filepath to the log file (filepath)
     Parameters
    """
    # open log file
    df  = pd.read_json(filepath,lines=True)
    """
        Now we are going to filter the data by the nextsong actions and convert the timestamp to datatime in order to do extract
        the year, month, week, day, hour, and weekday to insert it to the time table
    """
    # filter by NextSong action
    df = df[df['page'] == 'NextSong']
    # convert timestamp column to datetime
    t = df[df['page'] == 'NextSong'].copy(deep=True)
    t['ts'] = pd.to_datetime(t['ts'])
    
    # insert time data records
    time_data = (t['ts'],t['ts'].dt.year,t['ts'].dt.month,t['ts'].dt.week,t['ts'].dt.day,t['ts'].dt.hour, t['ts'].dt.weekday_name)
    column_labels = ('timestamp','year','month','week','day','hour','weekday_name') 
    zipped_dict = zip(column_labels,time_data)
    time_df = pd.DataFrame(dict(zipped_dict)) 
    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))
    """
        Now we are going to load user and songplay tables and insert new records
    """
    # load user table
    user_df = df[['userId','firstName','lastName','gender','level']].dropna()
    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)
    # insert songplay records
    for index, row in df.iterrows():
    # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
    
        if results:
            songId, artistId = results
        else:
            songId, artistId = None, None
    # insert songplay record
        songplay_data = ([pd.to_datetime(row.ts), row.userId, row.level, songId, artistId, row.sessionId, row.location, row.userAgent])
        cur.execute(songplay_table_insert, songplay_data)
        
def process_data(cur, conn, filepath, func):
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()