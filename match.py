import csv
from transitfeed import Loader, util
from time import gmtime
from pytz import timezone
from datetime import datetime, date
import os
from shapely.geometry import LineString 
import simplejson as json


def trip_instances( points, header ):
	# chops a list of points up into a list of trip instances
	# this assumes the trip is ordered by time and trip instance

	tripInst_ix = header.index("tripInst")

	tripInstId = None

	for point in points:
		curTripInstId = point[tripInst_ix]

		if curTripInstId!=tripInstId:
			if tripInstId is not None:
				yield tripInst
			tripInst = []
			tripInstId = point[tripInst_ix]

		tripInst.append( point )

	yield tripInst

def get_tripInst_date( tripInst, time_ix, tz ):
	tripStart = datetime.fromtimestamp( float(tripInst[0][time_ix])/1000.0, tz )
	return tripStart.date()

class CheapGTFS(object):
	def __init__(self, gtfs_dir):
		self.gtfs_dir = gtfs_dir

def parse_gtfs_date( datestr ):
	year = datestr[0:4]
	month = datestr[4:6]
	day = datestr[6:]

	return date(int(year),int(month),int(day))

def compile_trips( gtfs_dir, interesting_trip_ids, verbose=True ):
	fn = os.path.join( gtfs_dir, "stop_times.txt" )
	fp = open( fn )
	rd = csv.reader( fp )

	header = rd.next()

	trip_id_ix        = header.index("trip_id")
	arrival_time_ix   = header.index("arrival_time")
	departure_time_ix = header.index("departure_time")
	stop_id_ix        = header.index("stop_id")
	stop_sequence_ix  = header.index("stop_sequence")

	ret = {}
	for i, row in enumerate( rd ):
		if i%1000==0:
			print "\r%d"%i,; sys.stdout.flush()

		trip_id        = row[trip_id_ix]
		if trip_id not in interesting_trip_ids:
			continue

		arrival_time   = util.TimeToSecondsSinceMidnight( row[arrival_time_ix] )
		departure_time = util.TimeToSecondsSinceMidnight( row[departure_time_ix] )
		stop_id        = row[stop_id_ix]
		stop_sequence  = int( row[stop_sequence_ix] )

		if trip_id not in ret:
			ret[trip_id] = []

		ret[trip_id].append( (trip_id,arrival_time,departure_time,stop_id,stop_sequence) )

	return ret

def trip_to_points( trip, stops ):
	trip.sort( key=lambda x:x[4] )

	for trip_id,arrival_time,departure_time,stop_id,stop_sequence in trip:
		lat, lon = stops[stop_id]

		if arrival_time != departure_time:
			yield lon, lat, arrival_time
		yield lon, lat, departure_time

def tripinst_to_points( tripinst, lat_ix, lon_ix, time_ix, tz, day_cutoff=4*3600 ):
	for point in tripinst:
		lat = float(point[lat_ix])
		lon = float(point[lon_ix])
		dt = datetime.fromtimestamp( float(point[time_ix])/1000.0, tz )
		secs_since_midnight = dt.hour*3600+dt.minute*60+dt.second+dt.microsecond/1000000.0
		if secs_since_midnight < day_cutoff:
			secs_since_midnight += 3600*24

		yield (lon,lat,secs_since_midnight)

def main(fn_in, gtfs_dir, route_id):
	ll = Loader( gtfs_dir, load_stop_times=False )
	sched = ll.Load()

	# compile stop_id->(lat,lon) for convenience
	stops = dict( [(stop.stop_id, (stop.stop_lat, stop.stop_lon)) for stop in sched.GetStopList()] )

	# get all trip_ids corresponding to route_id
	routes = dict( [(x.route_short_name, x) for x in sched.GetRouteList()] )
	route = routes[ route_id ]
	interesting_trip_ids = set([trip.trip_id for trip in route.trips])

	# sift through the huge stop_times.txt file looking for stop_times that have one of those trip_ids,
	# and group them by trip_id
	print "grouping stop times by trip_id..."
	stop_time_groups = compile_trips( gtfs_dir, interesting_trip_ids )
	print "done"

	print "converting each trip to a shape, sorting by service id"
	trip_shapes = {} # dict of service_id -> [(trip_id,shape),...]
	for trip_id, stop_time_group in stop_time_groups.items():
		shp = LineString( list( trip_to_points( stop_time_group, stops ) ) )

		service_id = sched.GetTrip( trip_id ).service_id

		if service_id not in trip_shapes:
			trip_shapes[service_id] = []
		trip_shapes[service_id].append( (trip_id, shp) )
	print "done"

	tzname = sched.GetDefaultAgency().agency_timezone
	tz = timezone( tzname )

	rd = csv.reader( open(fn_in) )

	header = rd.next()
	time_ix = header.index("time")
	lat_ix = header.index("lat")
	lon_ix = header.index("lon")

	start_date, end_date = [parse_gtfs_date(x) for x in sched.GetDateRange()]
	# dict of date->[service periods]
	serviceperiods = dict( sched.GetServicePeriodsActiveEachDate( start_date, end_date ) )

	for i, tripInst in enumerate( trip_instances( rd, header ) ):
		tripInst_date = get_tripInst_date( tripInst, time_ix, tz )
		service_periods = serviceperiods.get( tripInst_date )

		if service_periods is None:
			continue

		tripinst_shape = list( tripinst_to_points( tripInst, lat_ix, lon_ix, time_ix, tz ) )

		if len(tripinst_shape)<30:
			continue

		for service_period in service_periods:
			print "check tripInst %d against all trips in service id %s"%(i, service_period.service_id)

			for trip_id, trip_shape in trip_shapes[service_period.service_id]:
				print "checking against shape for trip_id:%s"%trip_id
				print tripinst_shape
				print list(trip_shape.coords)

				fpout = open("linestrings.json","w")
				fpout.write( json.dumps([tripinst_shape,list(trip_shape.coords)],indent=2 ) )
				exit()
		exit()


if __name__=='__main__':
	import sys

	if len(sys.argv)<4:
		print "usage: python cmd.py chained_csv_fn gtfs_dir route_id"
		exit()

	chained_csv_fn = sys.argv[1]
	gtfs_dir = sys.argv[2]
	route_id = sys.argv[3]

	main( chained_csv_fn, gtfs_dir, route_id )
