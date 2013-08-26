import csv
import simplejson as json
import os
from pytz import timezone
from datetime import datetime

def get_trip_service_ids( gtfs_dir ):
	fn = os.path.join( gtfs_dir, "trips.txt" )
	rd = csv.reader( open(fn) )

	header = rd.next()
	trip_id_ix = header.index("trip_id")
	service_id_ix = header.index("service_id")

	for row in rd:
		yield row[trip_id_ix], row[service_id_ix]

def get_gtfs_timezone( gtfs_dir ):
	fn = os.path.join( gtfs_dir, "agency.txt" )
	rd = csv.reader( open(fn) )

	header = rd.next()
	timezone_ix = header.index("agency_timezone")

	default_agency = rd.next()
	timezone_name = default_agency[timezone_ix]

	tz = timezone( timezone_name )
	return tz

def get_secs_since_midnight( dt ):
	return dt.hour*3600+dt.minute*60+dt.second+dt.microsecond/1000000.0

def main(passby_fn, gtfs_dir, patterns_fn, stop_id=None, pattern_id=None, service_id=None):
	trip_service_ids = dict(list(get_trip_service_ids( gtfs_dir )))
	tz = get_gtfs_timezone( gtfs_dir )

	patterns, trip_patterns = json.loads( open(patterns_fn).read() )

	passby_rd = csv.reader( open(passby_fn) )
	header = passby_rd.next()
	chain_id_ix = header.index("chain_id")
	trip_id_ix = header.index("trip_id")
	stop_id_ix = header.index("stop_id")
	time_ix = header.index("time")

	passbys = list(passby_rd)

	# if 'stop_id' isn't provided, list the count of passbys per stop_id and then exit
	if stop_id is None:
		print "Pick a stop. Here are some options:"
		stop_counts = {}
		for chain_id,trip_id,stop_id,time in passbys:
			if stop_id not in stop_counts:
				stop_counts[stop_id]=0
			stop_counts[stop_id] += 1
		for stop_id, count in stop_counts.items():
			print "stop:%s\t count:%s"%(stop_id,count)
		exit()

	# cut down the passbys to the provided stop
	passbys = [pt for pt in passbys if pt[stop_id_ix]==stop_id]

	# if 'pattern_id' isn't provided, list the count of passbys per apttern_id and then exit
	if pattern_id is None:
		print "Pick a pattern. Here are some options:"
		pattern_counts = {}
		for chain_id, trip_id, stop_id, time in passbys:
			pattern_id = trip_patterns[trip_id]
			if pattern_id not in pattern_counts:
				pattern_counts[pattern_id]=0
			pattern_counts[pattern_id]+=1
		for pattern_id, count in pattern_counts.items():
			print "pattern:%s\t count:%s"%(pattern_id,count)
		exit()

	passbys = [pt for pt in passbys if trip_patterns[pt[trip_id_ix]]==pattern_id]

	# if 'service_id' isn't provided, list stop options and then exit
	if service_id is None:
		print "Pick a service_id. Here are some options:"
		service_id_counts = {}
		for chain_id,trip_id,stop_id,time in passbys:
			service_id = trip_service_ids[trip_id]
			if service_id not in service_id_counts:
				service_id_counts[service_id]=0
			service_id_counts[service_id]+=1
		for service_id, count in service_id_counts.items():
			print "service_id:%s\t count:%s"%(service_id,count)
		exit()

	passbys = [pt for pt in passbys if trip_service_ids[pt[trip_id_ix]]==service_id]

	passby_secs = []
	for chain_id, trip_id, stop_id, time in passbys:
		passby_dt = datetime.fromtimestamp( float(time), tz )

		secs = get_secs_since_midnight( passby_dt )

		passby_secs.append( secs )

	from matplotlib import pyplot as plt

	plt.vlines( passby_secs, 0, 1, lw=0.05 )
	plt.show()


if __name__=='__main__':
	import sys

	if len(sys.argv) < 4:
		print "usage: python cmd.py passby_fn gtfs_dir patterns_fn [stop_id [pattern_id [service_id]]]"
		exit()

	passby_fn = sys.argv[1]
	gtfs_dir = sys.argv[2]
	patterns_fn = sys.argv[3]

	if len(sys.argv)>4:
		stop_id = sys.argv[4]
	else:
		stop_id = None

	if len(sys.argv)>5:
		pattern_id = sys.argv[5]
	else:
		pattern_id = None

	if len(sys.argv)>6:
		service_id = sys.argv[6]
	else:
		service_id = None


	main(passby_fn, gtfs_dir, patterns_fn, stop_id, pattern_id, service_id)