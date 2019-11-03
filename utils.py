def increment_time(time, offset):
    """
        Adds offdet to a given time.
    """
    time = int(time)
    time = time + offset
    if time % 100 >= 60:
        time += 100
        time -= 60
    return str(time).zfill(4)


def get_time_slots(starttime, endtime, interview_interval, lunch_hours=None):
    """
    returns starttimes of each interview period as a list.
    Input :
        Starttime,Endtime,
    returns :
        timeslots
    """
    ttime = starttime
    start_times = []
    while(int(endtime) > int(ttime)):
        start_times.append(ttime)
        ttime = increment_time(ttime, interview_interval)
        if lunch_hours is not None:
            if int(ttime) > int(lunch_hours[0]):
                ttime = lunch_hours[1]

    return start_times
