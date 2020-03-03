#!/usr/bin/env python3

from datetime import date, timedelta


TEAM = (
    # Week 0.
    'Casey',
    'Francesco',
    'Allan',
    'JC',
    'Martin',
    # Week 1.
    'Francesco',
    'Ales',
    'Fabrice',
    'Domas',
    'Austin',
)


day = date.today()
_, weeknum, weekday = day.isocalendar()
if weekday > 5:
    weekday = 1
    weeknum += 1
index = weekday - 1 + 5 * (weeknum % 2)
people = TEAM * 2
one_day = timedelta(days=1)
summary = [{'name': '', 'people': []} for _ in range(5)]

print('Calendar:')
for _ in range(14):
    wday = day.weekday()
    if wday < 5:
        prefix = '* ' if wday == 0 else '  '
        print('{}{}: {}'.format(prefix, day.strftime('%a %m-%d'), people[index]))
        summary[wday]['people'].append(people[index])
        summary[wday]['name'] = day.strftime('%a')
        index +=1
    day += one_day

print('\nSummary:')
for num, day in enumerate(summary):
    prefix = '* ' if num+1 == weekday else '  '
    print('{}{}: {}'.format(prefix, day['name'], ', '.join(day['people'])))
