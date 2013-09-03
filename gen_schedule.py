import csv
import simplejson as json
import os
from pytz import timezone
from datetime import datetime
from transitfeed import Loader, util

def get_trips( gtfs_dir ):
	fn = os.path.join( gtfs_dir, "trips.txt" )
	rd = csv.reader( open(fn) )

	header = rd.next()
	trip_id_ix = header.index("trip_id")
	service_id_ix = header.index("service_id")
	direction_id_ix = header.index("direction_id")

	for row in rd:
		yield row[trip_id_ix], row[service_id_ix], row[direction_id_ix]

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

def get_scheduled_secs( gtfs_dir, stop_id, interesting_trips ):
	fn = os.path.join( gtfs_dir, "stop_times.txt")	
	rd = csv.reader( open(fn) )

	header = rd.next()
	trip_id_ix = header.index("trip_id")
	stop_id_ix = header.index("stop_id")
	departure_time_ix = header.index("departure_time")

	for row in rd:
		if row[stop_id_ix] != stop_id:
			continue

		if row[trip_id_ix] not in interesting_trips:
			continue

		yield util.TimeToSecondsSinceMidnight( row[departure_time_ix] )

def generate_schedule(passby_fn, gtfs_dir, stop_id=None, direction_id=None, service_id=None, since_midnight=True):
	trips = list( get_trips(gtfs_dir) )
	trip_service_ids = dict( [(trip[0],trip[1]) for trip in trips] )
	trip_direction_ids = dict( [(trip[0],trip[2]) for trip in trips] )
	tz = get_gtfs_timezone( gtfs_dir )

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

	# if 'direction_id' isn't provided, list the count of passbys per direction_id and then exit
	if direction_id is None:
		print "Pick a direction. Here are some options:"
		direction_counts = {}
		for chain_id, trip_id, stop_id, time in passbys:
			direction_id = trip_direction_ids[trip_id]
			if direction_id not in direction_counts:
				direction_counts[direction_id]=0
			direction_counts[direction_id]+=1
		for direction_id, count in direction_counts.items():
			print "direction:%s\t count:%s"%(direction_id,count)
		exit()

	interesting_trips = set([tid for tid,did in trip_direction_ids.items() if did==direction_id])
	passbys = [pt for pt in passbys if pt[trip_id_ix] in interesting_trips]

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

	interesting_trips = set([tid for tid in interesting_trips if trip_service_ids[tid]==service_id])
	passbys = [pt for pt in passbys if pt[trip_id_ix] in interesting_trips]

	passby_secs = []
	for chain_id, trip_id, stop_id, time in passbys:

		if since_midnight:	
			passby_dt = datetime.fromtimestamp( float(time), tz )

			secs = get_secs_since_midnight( passby_dt )
			if secs<4*3600:
				secs += 24*3600
		else:
			secs = float(time)

		passby_secs.append( secs )

	scheduled_secs = list(get_scheduled_secs( gtfs_dir, stop_id, interesting_trips ))

	return passby_secs, scheduled_secs

if __name__=='__main__':
	import sys

	if len(sys.argv) < 4:
		print "usage: python cmd.py passby_fn gtfs_dir output_fn [stop_id [direction_id [service_id]]]"
		exit()

	passby_fn = sys.argv[1]
	gtfs_dir = sys.argv[2]
	output_fn = sys.argv[3]

	if len(sys.argv)>4:
		stop_id = sys.argv[4]
	else:
		stop_id = None

	if len(sys.argv)>5:
		direction_id = sys.argv[5]
	else:
		direction_id = None

	if len(sys.argv)>6:
		service_id = sys.argv[6]
	else:
		service_id = None


	passby_secs, scheduled_secs = generate_schedule(passby_fn, gtfs_dir, stop_id, direction_id, service_id)

	open( output_fn, "w" ).write( json.dumps([passby_secs,scheduled_secs]) )
