from datetime import timedelta, datetime, date


def getCurrentSnapshot():
    now = datetime.now()
    y=now.isocalendar()[0]
    w=now.isocalendar()[1]
    sn=str(y)[2:]+'{:02}'.format(w)

    return sn


def tofirstdayinisoweek(yearweek):
    """
    :param yearweek:
    :return: the first day in a week
    """
    year=int('20'+str(yearweek)[:2])
    week=int(str(yearweek)[2:])

    d = date(year,1,1)
    d = d - timedelta(d.weekday())
    dlt = timedelta(days = (week)*7)
    return d + dlt


def toLastdayinisoweek(yearweek):
    year=int('20'+str(yearweek)[:2])
    week=int(str(yearweek)[2:])
    d = date(year,1,1)
    d = d - timedelta(d.weekday())
    dlt = timedelta(days = (week)*7)
    return d + dlt + timedelta(days=6)


def getWeekString(yearweek):
    if yearweek is None or len(str(yearweek))==0:
        return ''
    first=tofirstdayinisoweek(yearweek)
    last=toLastdayinisoweek(yearweek)
    return "{} {} - {} {}, {}".format(first.strftime("%b"), first.day,last.strftime("%b"),last.day,last.year)


def getSnapshotfromTime(now, delta=None,before=False):
    """
    Returns the snapshot for a given time (+/- a delta)
    :param now:
    :param delta: current time +/- delta
    :param before:
    :return: YYWW
    """
    if delta:
        if before:
            now -= delta
        else:
            now += delta

    y=now.isocalendar()[0]
    w=now.isocalendar()[1]
    sn=str(y)[2:]+'{:02}'.format(w)
    return int(sn)


def getPreviousWeek(snapshot):
    d = tofirstdayinisoweek(snapshot)
    return getSnapshotfromTime(d, timedelta(days=7), before=True)

def getLastNSnapshots(yearweek,n):
    d=[]
    sn=yearweek
    while n>0:
        sn=getPreviousWeek(sn)
        d.append(sn)
        n=n-1
    return d


def getWeekString1(yearweek):
    if yearweek is None or len(str(yearweek))==0:
        return ''
    year="'"+str(yearweek)[:2]
    week=int(str(yearweek)[2:])
    return 'W'+str(week)+'-'+str(year)
