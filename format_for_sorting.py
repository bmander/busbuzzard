import sys
import csv

def main(fn_in, fn_out):
	rd = csv.reader( open(fn_in) )
	header = rd.next()

	print header

	id_ix = header.index("id")
	secssincereport_ix = header.index("secsSinceReport")
	time_ix = header.index("time")
	routetag_ix = header.index("routeTag")
	dirtag_ix = header.index("dirTag")
	lat_ix = header.index("lat")
	lon_ix = header.index("lon")

	fpout = open( fn_out, "w" )
	for i, row in enumerate( rd ):
		if i%1000==0:
			print "\r%s"%i,;sys.stdout.flush()

		if row[0]=='':
			continue

		secssincereport = int(row[secssincereport_ix])
		time = float(row[time_ix])/1000.0
		routetag = row[routetag_ix]
		dirtag = row[dirtag_ix]
		lat = row[lat_ix]
		lon = row[lon_ix]
		id = row[id_ix]

		report_time = time-secssincereport

		fpout.write( "%s,%.2f,%s,%s,%s,%s\n"%(id,time,routetag,dirtag,lon,lat) )

if __name__=='__main__':
	if len(sys.argv)<3:
		print "usage: python cmd.py fp_in fp_out"
		exit()

	fp_in = sys.argv[1]
	fp_out = sys.argv[2]	

	main(fp_in, fp_out)