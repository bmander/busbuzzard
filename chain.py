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

	vehicleId_ix,time_ix,routeTag_ix,dirTag_ix,lon_ix,lat_ix = 0,1,2,3,4,5

	last_vehicleId=None
	last_dirTag=None
	last_time=0.0
	cur_trip = 0
	print "chaining GPS points..."
	for i, pt in enumerate( rd ):
		if i%1000==0:
			print "\r%d"%i,;sys.stdout.flush()	 

		vehicleId = pt[vehicleId_ix]
		dirTag = pt[dirTag_ix]
		time = float(pt[time_ix])

		pause = time-last_time

		if vehicleId!=last_vehicleId:
			cur_trip += 1
			#print "new trip %d from vehicleId %s"%(cur_trip,vehicleId)
		elif dirTag!=last_dirTag:
			cur_trip += 1
			#print "new trip %d from dirTag %s"%(cur_trip,dirTag)
		elif pause>SPLIT_PAUSE:
			cur_trip += 1
			#print "new trip %d from pause %fs"%(cur_trip,pause/1000.0)

		pt.append( str(cur_trip	) )
		fpout.write( ",".join(pt) )
		fpout.write( "\n" )

		last_dirTag = dirTag
		last_time = time
		last_vehicleId = vehicleId
	print "done"

if __name__=='__main__':
	if len(sys.argv)<3:
		print "usage: python cmd.py fp_in fp_out"
		exit()

	fp_in = sys.argv[1]
	fp_out = sys.argv[2]	

	main(fp_in, fp_out)