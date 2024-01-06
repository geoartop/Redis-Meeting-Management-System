__author__ = 'Theodoros Malikourtis & Georgios Artopoulos'

import mysql.connector as mysql
import redis
import datetime
import time
import random

# establish a connection to the redis server listening on port 6379
r = redis.Redis(host='localhost', port=6379, db=0)
# establish a connection to the mysql server listening on port 3306
# change the host, user, password and database parameters as required

connection = mysql.connect(host='...',
                           user='...',
                           password='...',
                           database='...')
# create a cursor object and call its execute() method to perform SQL commands
# to get the user emails from the database

cursor = connection.cursor()
cursor.execute("SELECT userID, email FROM ismgroup52.users")
user_emails = cursor.fetchall()

# to get the meeting ids and isPublic from the database
cursor.execute("SELECT meetingID,isPublic FROM ismgroup52.meetings")
meeting_ids = cursor.fetchall()

# to get everything from the meeting audience table from the database
cursor.execute("SELECT * FROM ismgroup52.meeting_audience")
meeting_audience = cursor.fetchall()

# to get everything from the meeting instances table from the database
cursor.execute("SELECT * FROM ismgroup52.meeting_instances")
meeting_instances = cursor.fetchall()

# Initialize the meetings as inactive
for meeting in meeting_ids:
    # get the meeting id
    meeting_id = meeting[0]
    # initialize the meeting as inactive
    r.set(f"meeting:{meeting_id}:is_active", 1)


# Function for a user to join a meeting
def join_meeting(user_id, meeting_id):
    # check if the meeting is public or if the user is in the audience
    is_public = meeting_ids[meeting_id - 1][1] == 0
    email = user_emails[user_id - 1][1]
    is_in_audience = False
    for row in meeting_audience:
        if row[0] == meeting_id and row[1] == email:
            is_in_audience = True
    # check if the meeting is active
    if int(r.get(f"meeting:{meeting_id}:is_active")) == 0:
        # check if the user is allowed to join the meeting
        if is_public or is_in_audience:
            # check if the user is already in the meeting
            if r.sismember(f"meeting:{meeting_id}:participants", user_id):
                print("User is already in this meeting")
                return
            # add the user to the list of participants for this meeting
            r.sadd(f"meeting:{meeting_id}:participants", user_id)

            # log the join event in the events log
            event_data = {
                'userID': user_id,
                'event_type': 1,  # join_meeting
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            r.rpush(f"meeting:{meeting_id}:eventsLog", str(event_data))
            print("User:", user_id, "joined meeting", meeting_id)
        else:
            print("User is not allowed to join this meeting")
    else:
        print("Meeting is not active")


# Function for a user to leave a meeting
# i is the event type (2 for leave_meeting , 3 for timeout)
def leave_meeting(user_id, meeting_id, i):
    # check if the user is in the meeting
    if user_id in r.smembers(f"meeting:{meeting_id}:participants"):
        # remove the user from the list of participants for this meeting
        r.srem(f"meeting:{meeting_id}:participants", user_id)

        # log the leave event in the events log
        event_data = {
            'userID': user_id,
            'event_type': i,  # leave_meeting
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        r.rpush(f"meeting:{meeting_id}:eventsLog", str(event_data))
        print("User:", user_id, "left meeting:", meeting_id)
    else:
        print("User is not in this meeting")


# Function to show the list of participants in a meeting
def show_current_participants(meeting_id):
    # get the list of participants for this meeting
    participants = r.smembers(f"meeting:{meeting_id}:participants")
    # convert the set of participants to a list of integers
    participants = [int(participant.decode('utf-8')) for participant in participants]
    print("meeting", meeting_id, "participants:", participants)


# Function to show the list of active meetings
def show_active_meetings():
    # get the list of active meetings
    active_meetings = []
    for meeting in meeting_ids:
        # get the meeting id
        meeting_id = meeting[0]
        # check if the meeting is active
        if int(r.get(f"meeting:{meeting_id}:is_active")) == 0:
            active_meetings.append(meeting_id)
    print("active meetings", active_meetings)


# Function to timeout all participants in a meeting
def timeout_all_participants(meeting_id):
    # get the list of participants for this meeting
    participants = r.smembers(f"meeting:{meeting_id}:participants")
    print("timeout all participants in meeting:", meeting_id)
    # timeout each participant
    for participant in participants:
        leave_meeting(participant, meeting_id, 3)


# Function for a user to post a chat message in a meeting
def post_chat_message(meeting_id, user_id, message):
    # create a dictionary with the chat message data
    chat_data = {"user_id": user_id, "message": message,
                 "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    # add the chat message to the list of chat messages for this meeting
    r.rpush(f"meeting:{meeting_id}:chat", str(chat_data))
    print("User:", user_id, "posted message in meeting:", meeting_id)


# Function to show the chat messages in chronological order in a meeting
def get_chat_inorder(meeting_id):
    # get the list of chat messages for this meeting
    chat_messages = r.lrange(f"meeting:{meeting_id}:chat", 0, -1)
    # Decode the chat messages from bytes to strings
    chat_messages = [eval(message.decode('utf-8')) for message in chat_messages]
    print("meeting", meeting_id, "chat messages:", chat_messages)


# Function to show for each active meeting when the current participants joined
def get_join_timestamp():
    # for each meeting in the database
    for meeting in meeting_ids:
        # get the meeting id
        meeting_id = meeting[0]
        # check if the meeting is active
        if int(r.get(f"meeting:{meeting_id}:is_active")) == 0:
            # get the events log for this meeting
            events_log = r.lrange(f"meeting:{meeting_id}:eventsLog", 0, -1)
            # decode the events log from bytes to strings
            for event in events_log:
                event = eval(event.decode('utf-8'))
                # check if the event is a join event
                if event['event_type'] == 1:
                    print("meeting", meeting_id, "user", event['userID'], "joined at", event['timestamp'])


# Function to get a users chat messages in an active meeting
def get_user_meeting_chat_messages(meeting_id, user_id):
    # check if the meeting is active
    if int(r.get(f"meeting:{meeting_id}:is_active")) == 0:
        # get the list of chat messages for this meeting
        chat_messages = r.lrange(f"meeting:{meeting_id}:chat", 0, -1)
        # decode the chat messages from bytes to strings
        chat_messages = [eval(message.decode('utf-8')) for message in chat_messages]
        print("meeting", meeting_id, "user", user_id, "chat messages:")
        # print the chat messages for this user
        for message in chat_messages:
            if message['user_id'] == user_id:
                print(message)
    else:
        print("Meeting is not active")


# Function to activate or deactivate a meeting
def scheduler():
    # get current time
    present = datetime.datetime.now()
    # for each meeting in the database
    for meeting in meeting_ids:
        # get the meeting id
        meeting_id = meeting[0]
        # for each meeting instance in the database
        change = False
        for meeting_instance in meeting_instances:
            # check if the meeting instance is for this meeting
            if meeting_instance[0] == meeting_id:
                # get the start and end time for this meeting instance
                start_time = meeting_instance[2]
                end_time = meeting_instance[3]
                # if the current time is between the start and end time activate the meeting
                if start_time <= present <= end_time:
                    r.set(f"meeting:{meeting_id}:is_active", 0)
                    change = True
                    break
        # if the meeting is not active deactivate the meeting
        # And if it was active deactivate it and timeout all participants
        if not change:
            r.set(f"meeting:{meeting_id}:is_active", 1)
            if r.get(f"meeting:{meeting_id}:is_active") == 0:
                timeout_all_participants(meeting_id)


# get the start time for the program
start_time = time.time()
# get the start time for the scheduler
start_time2 = time.time()
# get the start time for the variable x
start_time1 = time.time()

# initialize the variable x if x=9 then scheduler will run in the first iteration
x = 9
# run the program for 2 minutes
while time.time() - start_time < 121:
    # get the elapsed time for the scheduler
    elapsed_time = time.time() - start_time1
    # get the elapsed time for the variable x
    elapsed_time2 = time.time() - start_time2
    # run the scheduler every 60 seconds or when in the first iteration
    if elapsed_time >= 60 or x == 9:
        scheduler()
        start_time1 = time.time()
    # run a random function every 1 second or when in the first iteration
    if elapsed_time2 >= 1 or x == 9:
        x = random.randint(1, 8)
        start_time2 = time.time()
        # if x=1 then a random user will join a random meeting
        if x == 1:
            user = random.randint(1, len(user_emails))
            meeting = random.randint(1, len(meeting_ids))
            join_meeting(user, meeting)
        # if x=2 then a random user will leave a random meeting
        elif x == 2:
            user = random.randint(1, len(user_emails))
            meeting = random.randint(1, len(meeting_ids))
            leave_meeting(user, meeting, 2)
        # if x=3 then a random meeting will be selected and the current participants will be shown
        elif x == 3:
            meeting = random.randint(1, len(meeting_ids))
            show_current_participants(meeting)
        # if x=4 then the active meetings will be shown
        elif x == 4:
            show_active_meetings()
        # if x=5 then a random user will send a random message in a random meeting
        elif x == 5:
            meeting = random.randint(1, len(meeting_ids))
            user = random.randint(1, len(user_emails))
            messages = [
                "Hello, how are you?",
                "What's up?",
                "How's your day going?",
                "Nice to see you!",
                "How can I help you?"
            ]
            random_message = random.choice(messages)
            post_chat_message(meeting, user, random_message)
        # if x=6 then a random meeting will be selected and the chat messages will be shown in order
        elif x == 6:
            meeting = random.randint(1, len(meeting_ids))
            get_chat_inorder(meeting)
        # if x=7 then the join timestamp for each active meeting will be shown
        elif x == 7:
            get_join_timestamp()
        # if x=8 then a random user will be selected and the chat messages for a random active meeting will be shown
        elif x == 8:
            meeting = random.randint(1, len(meeting_ids))
            user = random.randint(1, len(user_emails))
            get_user_meeting_chat_messages(meeting, user)

# close the connection to the database
connection.close()
# close the connection to redis
r.close()
