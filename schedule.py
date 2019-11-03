# Import third party libraries.
import numpy as np

# Import from other sourcecode files
from utils import *


def get_distance(iv, iw):
    """
    Returns distance between interviewer's and inviewee's interests.
    Higher penelty for interests mentioned first.

    Inputs :
        list of interests category ids for interviewer and interviewee.
    Output :
        Distance between two lists.
    """
    iv = list(iv)
    dist = 0
    if len(iv) == 0:
        iv = [0]
    if len(iw) == 0:
        iw = [0]
    min_len = min(len(iv), len(iw))

    # Adds distance based on level of interest.
    for i in range(min_len):
        if iv[i] == iw[i]:
            dist += i / len(iw)
        elif iv[i] in iw:
            dist += iw.index(iv[i]) / len(iw)
        else:
            dist += min_len - i
    return dist


def get_neighbours(k, interv, intervwee):
    """
    find 'k' nearest neighbours.
    Input :
        Value of k
        Numpy array with interests for interviewers , python list with interests for interviwee
    Output :
        k indices of interviwers. In case of k = 1, returns a list with single element.
                                    In case of k > 1, returns a list in the descending order of distances.
    """
    if k < 1:
        k = 1  # k should be greater than 1
    if k > np.shape(interv)[0]:
        # cant execute neighbours for k > no. of interviewers.
        k = np.shape(interv)[0] - 1
    dist = []
    for i in range(np.shape(interv)[0]):
        dist.append(get_distance(interv[i], intervwee))
    result = []
    for i in range(k):
        result.append(dist.index(min(dist)))
        dist[result[i]] = max(dist) + 1
    return(result)


def scheduleInterviewes(start_time, end_time, interval=20, event_id=1, k=2):
    """
    This method is used to schedule interviewes. First part matches interviewers and interviewees. Second part schedules their interview.
    Input :
        Start time, End time for a meeting in "HHMM" format.
        int indicating length of each interview.
        Event id and k.
    Output :
        interview schedule.
    """
    slots = get_time_slots(start_time, end_time, interval)

    # PART 1

    student_id_map = []
    student_int_map = []
    interviewer_id_map = []
    interviewer_int_map = []

    for interviewer_id, interviewer_interest in interviewers.items():
        interviewer_id_map.append(interviewer_id)
        interviewer_int_map.append(interviewer_interest)

    interviewer_int_map = np.array(interviewer_int_map)
    match = []

    for student_id, student_interests in students.items():
        student_int_map.append(student_interests)
        student_id_map.append(student_id)

        neighbours = get_neighbours(k, interviewer_int_map, student_interests)

        for i in range(len(neighbours)):
            neighbours[i] = interviewer_id_map[neighbours[i]]

        match.append((student_id, neighbours))

    # PART 2

    result = []
    this_round = []
    for slot_id in range(len(slots)):
        prev_round = this_round.copy()
        this_round = []
        for interviewer_id in interviewer_id_map:
            for ele in match:
                if interviewer_id in ele[1]:
                    if interviewer_id not in this_round:
                        if ele[0] not in prev_round and ele[0] not in this_round:
                            this_round.append(interviewer_id)
                            this_round.append(ele[0])
                            result.append([interviewer_id, ele[0], slots[slot_id], increment_time(
                                slots[slot_id], interval)])
                            ele[1].remove(interviewer_id)

    # putMatch(result,event_id)
