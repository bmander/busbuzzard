import csv
from transitfeed import Loader, util
from time import gmtime
from pytz import timezone
from datetime import datetime, date
import os
from shapely.geometry import LineString, Point
import simplejson as json
import bisect

def get_trip_instances( points, header ):
	# chops a list of points up into a list of trip instances
	# this assumes the trip is ordered by time and trip instance

	tripinst_ix = header.index("tripInst")

	tripinst_id = None

	for i, point in enumerate( points ):
		curtripinst_id = point[tripinst_ix]

		if curtripinst_id!=tripinst_id:
			if tripinst_id is not None:
				yield tripinst_id, tripinst
			tripinst = []
			tripinst_id = point[tripinst_ix]

		tripinst.append( point )

	yield tripinst_id, tripinst

def get_tripinst_date( tripinst, time_ix, tz ):
	tripStart = datetime.fromtimestamp( float(tripinst[0][time_ix])/1000.0, tz )
	return tripStart.date()

def parse_gtfs_date( datestr ):
	year = datestr[0:4]
	month = datestr[4:6]
	day = datestr[6:]

	return date(int(year),int(month),int(day))

class Trip(object):
	def __init__(self, trip_id, direction_id, service_id):
		self.trip_id = trip_id
		self.direction_id = direction_id
		self.service_id = service_id
		self.stop_times = []

	def add_stoptime(self, trip_id, arrival_time, departure_time, stop_id, stop_sequence):
		self.stop_times.append( (trip_id, arrival_time, departure_time, stop_id, stop_sequence) )

	def _sort(self):
		self.stop_times.sort( key=lambda x:x[4] )

	def _to_points( self, stops, time=True ):
		for trip_id,arrival_time,departure_time,stop_id,stop_sequence in self.stop_times:
			lat, lon = stops[stop_id]

			if time:
				yield lon, lat, arrival_time
			else:
				yield lon, lat

	def get_shape( self, stops, time=True ):
		return list( self._to_points( stops, time ) )

	def midway_time( self ):
		start_time = self.stop_times[0][2]
		end_time = self.stop_times[-1][1]

		return (start_time+end_time)/2.0

	def __float__(self):
		return float(self.midway_time())

	def __lt__( self, b ):
		return float(self) < b

	def __gt__( self, b ):
		return float(self) > b

	def __eq__( self, b ):
		return float(self) == b

	def __ne__( self, b ):
		return float(self) != b

	def __ge__( self, b ):
		return float(self) >= b

	def __le__( self, b ):
		return float(self) <= b

	def __repr__(self):
		first_st = self.stop_times[0]
		last_st = self.stop_times[-1]
		return "<Trip id:%s dir:%s sid:%s %s@%s->%s@%s>"%(self.trip_id, self.direction_id, self.service_id, first_st[3],first_st[2],last_st[3],last_st[1])

class TripGroup(object):
	# A TripGroup is a set of trips that are equivalent at arrival time i.e. if you're waiting
	# at a stop for a vehicle implementing one trip but a vehicle serving a different trip shows up
	# it'll work.

	# TripGroups are generally all the trips in a GTFS with the same route_id, service_id, and direction_id.

	def __init__(self, direction_id, service_id):
		self.direction_id = direction_id
		self.service_id = service_id
		self.trips = []
		self.rep_shape_cache = None
		self.sorted = False

	def add_trip( self, trip ):
		self.sorted = False
		self.trips.append( trip )

	def _sort(self):
		self.trips.sort( key=lambda x:x.midway_time() )
		self.sorted = True

	@property
	def rep_trip(self):
		"""get a representitive trip"""
		return self.trips[0]

	def cache_rep_shape(self,stops):
		self.rep_shape_cache = self.get_rep_shape(stops)

	@property
	def rep_shape(self):
		if self.rep_shape_cache is None:
			raise Exception("rep_shape not in cache; run cache_rep_shape() first")

		return self.rep_shape_cache

	def get_rep_shape(self, stops):
		return LineString( self.rep_trip.get_shape(stops) )

	def same_direction(self, points):
		"""returns True if the string of points is traveling in the same direction as the tripgroup"""
		start_point = Point( points[0] )
		end_point = Point( points[-1] )	

		return self.rep_shape.project( start_point ) < self.rep_shape.project( end_point )

	def nearest(self, tt):
		# find the position in the trip list closest to it
		ix = bisect.bisect( self.trips, tt )

		if ix==0:
			return self.trips[0]
		if ix==len(self.trips):
			return self.trips[-1]

		left = abs( float(self.trips[ix-1])-tt )
		right = abs( float(self.trips[ix])-tt )

		if left<right:
			return self.trips[ix-1]
		else:
			return self.trips[ix]

	def __repr__(self):
		return "<TripGroup dir:%s sid:%s>"%(self.direction_id, self.service_id)

def compile_trips( gtfs, gtfs_dir, route_short_name, verbose=True ):
	# get the route object from the gtfs file corresponding to route_short_name
	routes = dict( [(x.route_short_name, x) for x in gtfs.GetRouteList()] )
	route = routes[ route_short_name ]

	# generate a Trip object for each gtfs trip...
	trips = {}
	for gtfs_trip in route.trips:
		trip = Trip( gtfs_trip.trip_id, gtfs_trip.direction_id, gtfs_trip.service_id )
		trips[trip.trip_id]=trip

	# fill out the trips with stop_times
	fn = os.path.join( gtfs_dir, "stop_times.txt" )
	fp = open( fn )
	rd = csv.reader( fp )

	header = rd.next()

	trip_id_ix        = header.index("trip_id")
	arrival_time_ix   = header.index("arrival_time")
	departure_time_ix = header.index("departure_time")
	stop_id_ix        = header.index("stop_id")
	stop_sequence_ix  = header.index("stop_sequence")

	for i, row in enumerate( rd ):
		if i%1000==0:
			print "\r%d"%i,; sys.stdout.flush()

		trip_id        = row[trip_id_ix]
		if trip_id not in trips:
			continue

		arrival_time   = util.TimeToSecondsSinceMidnight( row[arrival_time_ix] )
		departure_time = util.TimeToSecondsSinceMidnight( row[departure_time_ix] )
		stop_id        = row[stop_id_ix]
		stop_sequence  = int( row[stop_sequence_ix] )

		trips[trip_id].add_stoptime( trip_id,arrival_time,departure_time,stop_id,stop_sequence )

	for trip in trips.values():
		trip._sort()

	return trips.values()

def tripinst_to_points( tripinst, lat_ix, lon_ix, time_ix, tz, day_cutoff=4*3600 ):
	for point in tripinst:
		lat = float(point[lat_ix])
		lon = float(point[lon_ix])
		dt = datetime.fromtimestamp( float(point[time_ix])/1000.0, tz )
		secs_since_midnight = dt.hour*3600+dt.minute*60+dt.second+dt.microsecond/1000000.0
		if secs_since_midnight < day_cutoff:
			secs_since_midnight += 3600*24

		yield (lon,lat,secs_since_midnight)

def main(fn_in, gtfs_dir, route_id, fn_out):
	ll = Loader( gtfs_dir, load_stop_times=False )
	sched = ll.Load()

	# compile stop_id->(lat,lon) for convenience
	stops = dict( [(stop.stop_id, (stop.stop_lat, stop.stop_lon)) for stop in sched.GetStopList()] )

	# sift through the huge stop_times.txt file looking for stop_times that have one of those trip_ids,
	# and group them by trip_id
	print "reading gtfs stop_times into trips..."
	trips = compile_trips( sched, gtfs_dir, route_id )
	print "done"

	print "filing trips away into affinity groups..."
	tripgroups = {}
	for trip in trips:
		sig = (trip.direction_id, trip.service_id)
		if sig not in tripgroups:
			tripgroups[sig] = TripGroup( trip.direction_id, trip.service_id )
		tripgroups[sig].add_trip( trip )

	for tripgroup in tripgroups.values():
		tripgroup._sort()
		tripgroup.cache_rep_shape(stops)
	print "done"

	print "indexing tripgroups by service id..."
	serviceid_tripgroups = {}
	for (direction_id, service_id), tripgroup in tripgroups.items():
		if service_id not in serviceid_tripgroups:
			serviceid_tripgroups[service_id] = []
		serviceid_tripgroups[service_id].append( tripgroup )
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

	print "matching trip instances with trips..."
	fpout = open( fn_out, "w" )
	for i, (tripinst_id, tripinst) in enumerate( get_trip_instances(rd,header) ):
		if i%100==0:
			print "\r%d"%(i+1,),; sys.stdout.flush()

		tripinst_date = get_tripinst_date( tripinst, time_ix, tz )
		service_periods = serviceperiods.get( tripinst_date )

		if service_periods is None:
			continue

	 	tripinst_shape = list( tripinst_to_points( tripinst, lat_ix, lon_ix, time_ix, tz ) )
	 	# print "tripinst shape %s"%tripinst_shape

		#pick out the tripinst midpoint
		start_time = tripinst_shape[0][2]
		end_time = tripinst_shape[-1][2]

		# print "start time %s"%start_time
		# print "end time %s"%end_time

		mid_time = (end_time+start_time)/2.0

	 	matched_trips = []	
	 	# for each service period running on the day of tripinst
		for service_period in service_periods:
			# print "checking service period ", service_period.service_id
			# find the tripgroup running on that service period 
			for tripgroup in serviceid_tripgroups.get(service_period.service_id,[]):
				# print "checking with trip group ", tripgroup
				# print "same direction?"
				if tripgroup.same_direction( tripinst_shape ):
					# print "yes"
					# print "tripgroup candidate trips..."
					# for trip in tripgroup.trips:
					# 	print trip

					# print "looking for nearest trip to %s"%mid_time
					nearest_trip = tripgroup.nearest( mid_time )
					# print "nearest trip: ", nearest_trip
					matched_trips.append( nearest_trip )

		if len(matched_trips)==0:
			continue

		matched_trip = min(matched_trips, key=lambda x:abs(float(x)-mid_time))

		fpout.write( "%s,%s\n"%(tripinst_id, matched_trip.trip_id) ); fpout.flush()
	print "done"


if __name__=='__main__':
	import sys

	if len(sys.argv)<5:
		print "usage: python cmd.py chained_csv_fn gtfs_dir route_id fn_out"
		exit()

	chained_csv_fn = sys.argv[1]
	gtfs_dir = sys.argv[2]
	route_id = sys.argv[3]
	fn_out = sys.argv[4]

	main( chained_csv_fn, gtfs_dir, route_id, fn_out )
