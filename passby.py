import os
import csv
from shapely.geometry import LineString, Point
import sys
import simplejson as json

def get_trip_instances( points, header ):
	# chops a list of points up into a list of trip instances
	# this assumes the trip is ordered by time and trip instance

	tripinst_ix = header.index("tripInst")

	tripinstId = None

	for point in points:
		curtripinstId = point[tripinst_ix]

		if curtripinstId!=tripinstId:
			if tripinstId is not None:
				yield tripinstId, tripinst
			tripinst = []
			tripinstId = point[tripinst_ix]

		tripinst.append( point )

	yield tripinstId, tripinst

def group(ary, key=lambda x:x):
	groups = {}
	for item in ary:
		k = key(item)
		if k not in groups:
			groups[k] = []
		groups[k].append(item)
	return groups

def cons(ary):
	for i in range(len(ary)-1):
		yield ary[i], ary[i+1]

def main(gtfs_dir, patterns_fn, chained_points_fn, match_fn, output_fn ):
	shapes_fn = os.path.join( gtfs_dir, "shapes.txt" )
	shapes_rd = csv.reader( open( shapes_fn ) )
	header = shapes_rd.next()
	shape_id_ix = header.index("shape_id")
	shape_pt_sequence_ix = header.index("shape_pt_sequence")
	shape_pt_lon_ix = header.index("shape_pt_lon")
	shape_pt_lat_ix = header.index("shape_pt_lat")

	print "reading in all shape points...",;sys.stdout.flush()
	shape_points = list(shapes_rd)
	print "done"

	print "grouping shape points by shape...",;sys.stdout.flush()
	grouped_shape_points = group(shape_points, lambda x:x[shape_id_ix])
	print "done"

	print "building linestrings out of shapes...",;sys.stdout.flush()
	shape_linestrings = {}
	for shape_id, shape_points in grouped_shape_points.items():
		shape_points.sort( key=lambda x:int(x[shape_pt_sequence_ix]) )

		shape_ls = LineString( [(float(x[shape_pt_lon_ix]),float(x[shape_pt_lat_ix])) for x in shape_points] )
		shape_linestrings[shape_id] = shape_ls
	print "done"

	print "pairing trip_ids with shape_ids...",;sys.stdout.flush()
	trips_fn = os.path.join( gtfs_dir, "trips.txt" )
	trips_rd = csv.reader( open( trips_fn ) )
	header = trips_rd.next()
	trip_id_ix = header.index("trip_id")
	shape_id_ix = header.index("shape_id")
	trip_shape = {}
	for row in trips_rd:
		trip_id = row[trip_id_ix]
		shape_id = row[shape_id_ix]
		trip_shape[trip_id] = shape_id
	print "done"

	print "getting stop information...",;sys.stdout.flush()
	stops_fn = os.path.join( gtfs_dir, "stops.txt" )
	stops_rd = csv.reader( open( stops_fn ) )
	header = stops_rd.next()
	stop_id_ix = header.index("stop_id")
	stop_lat_ix = header.index("stop_lat")
	stop_lon_ix = header.index("stop_lon")
	stop_shape = {}
	for row in stops_rd:
		stop_id = row[stop_id_ix]
		stop_lat = float(row[stop_lat_ix])
		stop_lon = float(row[stop_lon_ix])

		stop_shape[stop_id] = Point(stop_lon,stop_lat)
	print "done"

	patterns, trip_patterns = json.loads( open( patterns_fn ).read() )

	print "linear referencing stops along shapes...",;sys.stdout.flush()
	stop_shape_ref = {}
	for trip_id, shape_id in trip_shape.items():
		pattern_id = trip_patterns[trip_id]
		for stop_id in patterns[pattern_id]:
			if (stop_id,shape_id) in stop_shape_ref:
				continue

			prj = shape_linestrings[shape_id].project( stop_shape[stop_id], normalized=True )	
			stop_shape_ref[(stop_id,shape_id)] = prj
	print "done"

	print "getting chain_id->trip_id matches...",;sys.stdout.flush()
	matches = dict([row.strip().split(",") for row in open( match_fn )])
	print "done"

	print "generating passbys...",;sys.stdout.flush()
	fpout = open(output_fn, "w")
	fpout.write( "chain_id,trip_id,stop_id,time\n" )

	points = csv.reader( open(chained_points_fn) )
	header = points.next()
	lat_ix = header.index("lat")
	lon_ix = header.index("lon")
	time_ix = header.index("time")
	secsSinceReport_ix = header.index("secsSinceReport")
	for chain_id, chain in get_trip_instances( points, header ):
		print chain_id

		# if we don't know the trip_id for this chain, continue
		if chain_id not in matches:
			continue

		trip_id = matches[chain_id]
		pattern_id = trip_patterns[trip_id]
		stop_ids = patterns[ pattern_id ]
		shape_id = trip_shape[ trip_id ]
		shape_linestring = shape_linestrings[ shape_id ]

		# find the linear reference of every point in the chain along its imputed path
		chain_points = [Point(float(pt[lon_ix]),float(pt[lat_ix])) for pt in chain]
		chain_linrefs = [shape_linestring.project(pt,normalized=True) for pt in chain_points]

		# cut any point out of the chain that moves backward
		# TODO: there is a bug in this assumption - it's possible that noise could kick a point forward, which would result
		# in ignoring every legitimate point before the erroniously forwarded point
		cleaned_chain = []
		cleaned_linrefs = []
		last_linref=0
		for pt, linref in zip(chain,chain_linrefs):
			if linref < last_linref:
				continue
			last_linref = linref
			cleaned_chain.append( pt )
			cleaned_linrefs.append( linref )

		# get linear reference chain for this trip's stops along this trip's shape
		trip_linrefs = [(stop_id,stop_shape_ref[(stop_id,shape_id)]) for stop_id in stop_ids]

		# make sure the tirp linrefs never move backward
		for lr1, lr2 in cons(trip_linrefs):
			if lr1[1]>lr2[1]:
				raise Exception( "subsequent stop on shape can't be behind previous stop")

		# print trip_linrefs
		# print cleaned_linrefs

		# for every pair of chained, observed points, if they enclose one of the trip's stops, then that trip was passed by
		# during the period between observed points. deduce the passby time
		for (pt1, linref1), (pt2, linref2) in cons(zip(cleaned_chain, cleaned_linrefs)):
			# print linref1, linref2
			# print pt1, pt2
			t1 = float(pt1[time_ix])/1000.0 - float(pt1[secsSinceReport_ix])
			t2 = float(pt2[time_ix])/1000.0 - float(pt2[secsSinceReport_ix])
			dt = (t2-t1)

			for stop_id, stop_linref in trip_linrefs:
				if stop_linref>=linref1 and stop_linref<linref2:
					aa = (stop_linref-linref1)/(linref2-linref1)
					tt = aa*dt+t1

					fpout.write( "%s,%s,%s,%s\n"%(chain_id,trip_id,stop_id,tt) )
					#print "chain id:%s following trip id:%s passes stop %s at %s"%(chain_id, trip_id, stop_id, tt)
					#print "stop_id:%s (%s) is %s%% between at %s"%(stop_id, stop_linref, aa*100, tt)
		# 	print

		# print "chain id:%s follows trip id:%s"%(chain_id, trip_id)
		# print "pattern_id is %s"%pattern_id
		# print "stop_ids are %s"%stop_ids
		# print "shape_id is %s"%shape_id
		# print "shape is %s"%shape_linestring

if __name__=='__main__':
	import sys
	if len(sys.argv) < 6:
		print "usage: python cmd.py gtfs_dir patterns_fn chained_points_fn match_fn output_fn"
		exit()

	gtfs_dir = sys.argv[1]
	patterns_fn = sys.argv[2]
	chained_points_fn = sys.argv[3]
	match_fn = sys.argv[4]
	output_fn = sys.argv[5]

	main(gtfs_dir, patterns_fn, chained_points_fn, match_fn, output_fn)