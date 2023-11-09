import time, datetime

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def unit(num):
    num = num % 10

    if num == 1: return "st"
    elif num == 2: return "nd"
    elif num == 3: return "rd"
    else: return "th"

def current_time():
    lt = time.localtime()

    hour = lt.tm_hour - 1 # -1 for japan reasons

    lang = ""
    if hour >= 5 and hour < 12: lang = "morning"
    elif hour >= 12 and hour < 17: lang = "afternooon"
    elif hour >= 17 and hour < 20: lang = "sunset"
    else: lang = "night"

    return f"{hour}:{lt.tm_min} on the {lt.tm_mday}{unit(lt.tm_mday)} of {months[lt.tm_mon]} {lt.tm_year}", lang

def season():
    doy = datetime.datetime.now().timetuple().tm_yday
    
    # https://stackoverflow.com/questions/16139306/determine-season-given-timestamp-in-python-using-datetime
    # "day of year" ranges for the northern hemisphere
    spring = range(80, 172)
    summer = range(172, 264)
    fall = range(264, 355)
    # winter = everything else

    if doy in spring:
        season = 'Spring'
    elif doy in summer:
        season = 'Summer'
    elif doy in fall:
        season = 'Fall'
    else:
        season = 'Winter'
    
    return season

def time_summary():
    ct, lang = current_time()
    
    return f"### It is {ct}. It is currently {season()}. It is {lang.split(',')[0]}"