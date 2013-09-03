from gen_schedule import generate_schedule
from transitfeed import Loader
from pytz import timezone
from datetime import datetime, date, timedelta
import calendar
import bisect
from scipy.stats.mstats import mquantiles

MAX_WAIT = 3600*24 # one hour

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

def get_waits( passby_secs, sample_dates, sample_time ):
	# convert dates to localized datetimes at the sample time
	sample_dts = [tz.localize( sample_date + timedelta(seconds=sample_time) ) for sample_date in sample_dates]
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
		if wait>MAX_WAIT:
			continue
		waits.append( wait )

	return waits

if __name__=='__main__':
	import sys

	if len(sys.argv) < 3:
		print "usage: python cmd.py passby_fn gtfs_dir [stop_id [direction_id [service_id]]]"
		exit()

	passby_fn = sys.argv[1]
	gtfs_dir = sys.argv[2]

	if len(sys.argv)>3:
		stop_id = sys.argv[3]
	else:
		stop_id = None

	if len(sys.argv)>4:
		direction_id = sys.argv[4]
	else:
		direction_id = None

	if len(sys.argv)>5:
		service_id = sys.argv[5]
	else:
		service_id = None

	passby_secs, scheduled_secs = generate_schedule(passby_fn, gtfs_dir, stop_id, direction_id, service_id, since_midnight=False)

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
	sample_dates = [datetime(*split_gtfs_date(date)) for date in sp.ActiveDates()]

	sched = []
	print "building schedule..."
	for mins in range(24*60):
		print "\r%s/%s"%(mins,24*60),; sys.stdout.flush()
		waits = get_waits( passby_secs, sample_dates, 60*mins)

		if len(waits) < 2:
			quantiles = [0,0,0,0]
		else:	
			quantiles = mquantiles( waits, [0.25,0.5,0.75,0.95] )

		sched.append( quantiles )

	quanta = [x[0] for x in sched]
	quantb = [x[1] for x in sched]
	quantc = [x[2] for x in sched]
	quantd = [x[3] for x in sched]

	from matplotlib import pyplot as plt
	plt.plot(quanta)
	plt.plot(quantb)
	plt.plot(quantc)
	plt.plot(quantd)
	plt.show()


