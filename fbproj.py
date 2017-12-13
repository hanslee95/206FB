import urllib3
import facebook
import requests
import json
import datetime
import sqlite3
import plotly.plotly as py
import plotly.graph_objs as go
import pandas as pd
from facepy import GraphAPI
#NOTE: I have gotten 100 interactions extracting 100 posts, however, the final data table will have 7 items (rows) in each column.
#as it's information on the 7 days of the week. Specifically, in each post of the 100, I collected how many times I either posted a story or message to see how active I am on the certain day.



# ############## CACHING THE DATA ###########################################################################################################################################################

access_token = 'access_token'
graph = GraphAPI(access_token)

# ############## CACHING THE DATA ###########################################################################################################################################################

CACHE_FNAME = "Posts_cache.json"
try:
    cache_file = open(CACHE_FNAME, 'r') # Try to read the data from the file
    cache_contents = cache_file.read()  # If it's there, get it into a string
    CACHE_DICTION = json.loads(cache_contents) # And then load it into a dictionary
    cache_file.close() # Close the file, we're good, we got the data in a dictionary.
except:
    CACHE_DICTION = {}


#checking the cache of a particular user and returns that data or retrieves that cache'd data.
def get_posts():
	# if statement is checking if you already looked it up, if you did, then use the thing you cache'd
	if 'posts' in CACHE_DICTION:
		print('using cache')
		post_results = CACHE_DICTION['posts']
	else:
		print('getting data from internet')
		post_results = graph.get('me?fields=posts.limit(118)')	
		CACHE_DICTION['posts'] = post_results['posts']
		cache_file = open(CACHE_FNAME, 'w')
		#json.dumps prints out the string of dictionary in a json file in one line
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()

	return CACHE_DICTION['posts']

posts = get_posts()	

########## HELPER FUNCTIONS #####################################################################################################################

#To convert the datetime to a day of the week 
def get_day_of_week(date): 
	return datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%a')


#stripping the created_time value to only get the year-month-day
def strip_time(time_str):
	date = time_str[:-14]
	return date

#iterate over the weeks to compare when each element was posted. Then iterate over the dictionary and if that post happened on
#first day (mon), then check and add the stories and messages separately. Then Repeat. Returns dictionary with week day as keys and 
#list of tuples (activites)
def calculate_activity(week_l, p):
	week_dict = {}
	for day in week_l:
		for elem in p['data']:
			m_count = 0
			s_count = 0
			#if the created time is equal to that day of the week. Only getting message/story from that day
			if get_day_of_week(strip_time(elem['created_time'])) == day:
				#if that day has not been added to the dictionary, add it
				if get_day_of_week(strip_time(elem['created_time'])) not in week_dict:
					week_dict[get_day_of_week(strip_time(elem['created_time']))] = []
				else: 
					for key in elem:
						if key != 'story' and key == 'message':
							m_count = m_count + 1
						if key == 'story' and key != 'message':	
							s_count = s_count + 1
						# else both story and message are in that date so add two activities
						if key == 'story' and key == 'message':
							m_count = m_count + 1
							s_count = s_count + 1
					tup = s_count, m_count		
					week_dict[get_day_of_week(strip_time(elem['created_time']))].append(tup)
	return week_dict	

#adding up all the elements in list of tuples for story and message then creating 3 element tuple to insert to table.
def insert_tup3(d):
	for key in d:
		add_s = sum(i[0] for i in d[key])	
		add_m = sum(i[1] for i in d[key])
		tup = add_s, add_m	
		d[key] = []
		d[key].append(tup)
		
		for x in d[key]:
			tup3 = key, x[0], x[1]
			cur.execute('INSERT INTO WeekDay (created_time, story, message) VALUES (?, ?, ?)', tup3)
	conn.commit() 	

########### CREATING AND LOADING IN DATA INTO DATABASE #################################################################################################

conn = sqlite3.connect('Posts_Day.sqlite', timeout = 10)
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS WeekDay')
cur.execute("CREATE TABLE WeekDay (created_time TEXT, story NUMBER, message NUMBER)")

week_lst = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
#calling helper functions to insert data in database
insert_tup3(calculate_activity(week_lst, posts))

#getting data for x-axis
cur.execute('SELECT created_time FROM WeekDay')
lst_x = cur.fetchall()
lst_day = [elem[0] for elem in lst_x]

#getting data for y-axis (story)
cur.execute('SELECT story FROM WeekDay')
lst_y1 = cur.fetchall()
lst_activity = [elem[0] for elem in lst_y1]

#getting data for y-axis (message)
cur.execute('SELECT message FROM WeekDay')
lst_y2 = cur.fetchall()
lst_message = [elem[0] for elem in lst_y2]

########### CREATE DATA VIZ USING PLOTLY #################################################################################################
#importing the data to create graph
trace_high = go.Scatter(
                x=lst_day,
                y=lst_activity,
                name = "Activity",
                line = dict(color = '#03B9DF'),
                opacity = 0.8)

trace_low = go.Scatter(
                x=lst_day,
                y=lst_message,
                name = "Message",
                line = dict(color = '#00E264'),
                opacity = 0.8)

data = [trace_high,trace_low]

#labeling graph with title, x/y axis.
layout = dict(
    title = "FACEBOOK LIFE",
    xaxis=dict(
        title='Day of Week',
        titlefont=dict(
            family='Courier New, monospace',
            size=18,
            color='#7f7f7f'
        )
    ),
    yaxis=dict(
        title='Number of Posts',
        titlefont=dict(
            family='Courier New, monospace',
            size=18,
            color='#7f7f7f'
        )
    ) 
)

fig = dict(data=data, layout=layout)
py.iplot(fig, filename = "FACEBOOK LIFE")
	

