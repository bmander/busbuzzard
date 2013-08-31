from gen_schedule import generate_schedule
from transitfeed import Loader
from pytz import timezone
from datetime import datetime, date
import calendar
import bisect
from scipy.stats.mstats import mquantiles

MAX_WAIT = 3600 # one hour

def split_gtfs_date( datestr ):
	year = int(datestr[0:4])
	month = int(datestr[4:6])
	day = int(datestr[6:])

	return (year,month,day)	

def split_time( timestr ):
	return [int(x) for x in timestr.split(":")]

def parse_gtfs_date( datestr ):
	year = datestr[0:4]
	month = datestr[4:6]
	day = datestr[6:]

	return date(int(year),int(month),int(day))

if __name__=='__main__':
	import sys

	if len(sys.argv) < 4:
		print "usage: python cmd.py passby_fn gtfs_dir patterns_fn time [stop_id [pattern_id [service_id]]]"
		exit()

	passby_fn = sys.argv[1]
	gtfs_dir = sys.argv[2]
	patterns_fn = sys.argv[3]
	timestr = sys.argv[4]

	if len(sys.argv)>5:
		stop_id = sys.argv[5]
	else:
		stop_id = None

	if len(sys.argv)>6:
		pattern_id = sys.argv[6]
	else:
		pattern_id = None

	if len(sys.argv)>7:
		service_id = sys.argv[7]
	else:
		service_id = None

	passby_secs, scheduled_secs = generate_schedule(passby_fn, gtfs_dir, patterns_fn, stop_id, pattern_id, service_id, since_midnight=False)

	# parse the gtfs, so we can get all dates on which the service_id is active
	ll = Loader( gtfs_dir, load_stop_times=False )
	sched = ll.Load()

	# get timezone information from gtfs
	tzname = sched.GetDefaultAgency().agency_timezone
	tz = timezone( tzname )
	utc = timezone('UTC')
	# get service period
	sp = sched.GetServicePeriod( service_id )
	# get all dates this service period is active
	sample_date_tuples = [split_gtfs_date(date) for date in sp.ActiveDates()]

	sample_secs_since_midnight = 3600*12
	# get sample time from arguments
	sample_hr, sample_min = split_time( timestr )
	# convert dates to localized datetimes at the sample time
	sample_dts = [tz.localize( datetime(year,month,day,sample_hr,sample_min) ) for year,month,day in sample_date_tuples]
	# convert sample datetimes to utc datetimes
	utc_dts = [dt.astimezone(utc) for dt in sample_dts]
	# convert utc datetimes to unix timestamps
	sample_times = [calendar.timegm( dt.timetuple() ) for dt in utc_dts]

	passby_secs.sort()

	waits = []
	for sample_time in sample_times:
		i = bisect.bisect( passby_secs, sample_time )	
		if i>=len(passby_secs):
			continue
		wait = passby_secs[i] - sample_time
		print sample_time, passby_secs[i], wait
		if wait>MAX_WAIT:
			continue
		waits.append( wait )

	print mquantiles( waits, [0.25,0.5,0.75,0.95] )

	from matplotlib import pyplot as plt

	plt.hist( waits, bins=30 )
	plt.show()


	# start_date, end_date = [parse_gtfs_date(x) for x in sched.GetDateRange()]
	# # dict of date->[service periods]
	# serviceperiods = dict( sched.GetServicePeriodsActiveEachDate( start_date, end_date ) )

	# print serviceperiods


	# from matplotlib import pyplot as plt

	# plt.vlines( passby_secs, 0, 1.5, lw=0.05 )
	# plt.vlines( scheduled_secs, 0.5, 2, color="red" )

	# plt.show()
