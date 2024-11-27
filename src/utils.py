
import dateutils
from datetime import datetime
import re

def time_input_test(time_input):
    return re.match(r"^(?:[01]?[0-9]|2[0-3]):[0-5][0-9]$", time_input) is None

def date_input_test(date_input):
    return date_input and re.match(r"^(?:0?[1-9]|[12][0-9]|3[01])/(?:0?[1-9]|1[0-2])$", date_input) is None

def repeat_input_test(repeat_input):
    return repeat_input and re.match(r"^(0|(1?[0-9]|2[0-4])h|(0?[1-7])j|(0?[1-4])w|(0?[1-9]|1[0-2])m)$", repeat_input) is None

def parse_time(time_input, date_input):
    now = datetime.now()

    time = datetime.strptime(time_input, "%H:%M")
    if date_input:
      date = datetime.strptime(date_input, "%d/%m")
    else:
      date = datetime.now()

    dtime = time.replace(
        day=date.day,
        month=date.month,
        year=now.year + (date.month < now.month)
    )
    while dtime <= now:
        dtime += dateutils.relativedelta(days=1)

    return dtime

def format_datetime(dt):
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime('%H:%M')
    else:
        return dt.strftime('%H:%M - %d/%m')

def binary_search(user_messages, target_time):
    inf = 0
    sup = len(user_messages)
    
    while inf < sup:
        mid = (sup + inf) // 2
        msg = user_messages[mid]

        if msg.time < target_time:
            inf = mid + 1
        else:
            sup = mid 

    return inf
