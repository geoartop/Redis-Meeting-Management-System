# Meeting Management System

This program allows users to manage and participate in meetings. The program uses Redis to store data related to
meetings, and MySQL to store user and meeting data.

## Dependencies

- Python 3.6+
- Redis
- mysql-connector-python library

## Usage

1. Start the Redis server by running the following command:

```
redis-server
```

2. Modify the `connection` variable in the code to match your MySQL server details.
3. Run the program

## Functions

### join_meeting(user_id, meeting_id)

This function allows a user to join a meeting. It checks if the meeting is public or if the user is in the audience. It
also checks if the meeting is active and if the user is already in the meeting.

### leave_meeting(user_id, meeting_id, i)

This function allows a user to leave a meeting. It checks if the user is in the meeting.

### show_current_participants(meeting_id)

This function shows the list of participants in a meeting.

### show_active_meetings()

This function shows the list of active meetings.

### timeout_all_participants(meeting_id)

This function timeouts all participants in a meeting by calling the leave meeting function in repeat.

### post_chat_message(meeting_id, user_id, message)

This function allows a user to post a chat message in a meeting.

### scheduler()
This function is used to activate or deactivate a meeting based on its start and end time.
It checks if a meeting has ended and if it has, it calls the timeout_all_participants function.

## Authors

- Theodoros Malikourtis (8200097)
- Georgios Artopoulos (8200016)