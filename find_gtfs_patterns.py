import os
import simplejson as json
import csv
import sys

def find_gtfs_patterns(gtfs_dir, verbose=True):
	fn = os.path.join( gtfs_dir, "stop_times.txt" )
	rd = csv.reader( open(fn) )

	header = rd.next()
	trip_id_ix = header.index("trip_id")
	stop_sequence_ix = header.index("stop_sequence")
	stop_id_ix = header.index("stop_id")

	trips = {}
	if verbose: 
		print "grouping stop_times into trips..."
	for i, row in enumerate( rd ):
		if verbose and i%1000==0:
			print "\r%d"%i,; sys.stdout.flush()

		trip_id = row[trip_id_ix]
		stop_sequence = int(row[stop_sequence_ix])
		stop_id = row[stop_id_ix]

		if trip_id not in trips:
			trips[trip_id] = []

		trips[trip_id].append( (stop_sequence,stop_id) )
	if verbose:
		print "done"

	if verbose:
		print "group trips by pattern"

	patterns = {}
	for trip_id, stops in trips.items():
		stops.sort( key=lambda x:x[0] )
		pattern_signature = tuple( [x[1] for x in stops] )

		if pattern_signature not in patterns:
			patterns[pattern_signature] = []

		patterns[pattern_signature].append( trip_id )

	return patterns

def main(gtfs_dir, fn_out):
	patterns_trips = find_gtfs_patterns(gtfs_dir)

	pattern_defs = {}
	trip_patterns = {}
	for i, (pattern_sig, trip_ids) in enumerate( patterns_trips.items() ):
		pattern_defs[i] = pattern_sig
		for trip_id in trip_ids:
			trip_patterns[trip_id] = str(i)

	print "%d patterns"%len(pattern_defs)
	print "%d trips"%len(trip_patterns)

	fpout = open( fn_out, "w" )
	fpout.write( json.dumps( [pattern_defs,trip_patterns], indent=2 ) )

if __name__=='__main__':
	import sys
	if len(sys.argv)<3:
		print "usage: python cmd.py gtfs_dir fn_out"
		exit()

	gtfs_dir = sys.argv[1]
	fn_out = sys.argv[2]

	main(gtfs_dir, fn_out)