import csv
import sys

SPLIT_PAUSE = 60*15*1000 #the gap in milliseconds between two reports from a vehicle that we should consider the beginning of a new trip

def group( ary, key, verbose=True ):
	ret = {}

	for i, item in enumerate( ary ):
		if verbose and i%1000==0:
			print "\r%d"%i,; sys.stdout.flush()

		k = key(item)	

		if k not in ret:
			ret[k] = []
		ret[k].append(item)


	return ret


def main(fn_in, fn_out):
	fpout = open(fn_out,"w")

	rd = csv.reader( open( fn_in ) )
	header = rd.next()

	vehicleId_ix = header.index("id")
	time_ix = header.index("time")
	dirTag_ix = header.index("dirTag")

	print "reading all points...",; sys.stdout.flush()
	all_points = list(rd)
	print "done"

	print "sorting by time, vehicleid...",; sys.stdout.flush()
	all_points.sort( key=lambda x:(x[vehicleId_ix],float(x[time_ix])) )
	print "done"

	fpout.write( ",".join( header + ["tripInst"]) )
	fpout.write( "\n" )
	last_vehicleId=None
	last_dirTag=None
	last_time=0.0
	cur_trip = 0
	for pt in all_points:
		vehicleId = pt[vehicleId_ix]
		dirTag = pt[dirTag_ix]
		time = float(pt[time_ix])

		pause = time-last_time

		if vehicleId!=last_vehicleId:
			cur_trip += 1
			print "new trip %d from vehicleId %s"%(cur_trip,vehicleId)
		elif dirTag!=last_dirTag:
			cur_trip += 1
			print "new trip %d from dirTag %s"%(cur_trip,dirTag)
		elif pause>SPLIT_PAUSE:
			cur_trip += 1
			print "new trip %d from pause %fs"%(cur_trip,pause/1000.0)

		pt.append( str(cur_trip	) )
		fpout.write( ",".join(pt) )
		fpout.write( "\n" )

		last_dirTag = dirTag
		last_time = time
		last_vehicleId = vehicleId

if __name__=='__main__':
	if len(sys.argv)<3:
		print "usage: python cmd.py fp_in fp_out"
		exit()

	fp_in = sys.argv[1]
	fp_out = sys.argv[2]	

	main(fp_in, fp_out)