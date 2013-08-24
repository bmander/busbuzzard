import csv

def slice_date_range(fp_in, fp_out, route_tag):
	i=0

	rd = csv.reader( open(fp_in) )
	header = rd.next()

	print header

	routeTag_ix = header.index('routeTag')

	fpout = open(fp_out,"w")
	fpout.write(",".join(header))
	fpout.write("\n")
	for i, row in enumerate( rd ):
		if i%100000==0:
			print i

		if i%1000000==0:
			print row

		if row[routeTag_ix]!='':
			row_routeTag=row[routeTag_ix]
			if row_routeTag == route_tag:
				fpout.write( ",".join(row) )
				fpout.write( "\n" )

	print i

if __name__=='__main__':
	import sys
	if len(sys.argv)<4:
		print "usage: python cmd.py fp_in fp_out route_tag"
		exit()

	fp_in = sys.argv[1]
	fp_out = sys.argv[2]
	route_tag = sys.argv[3]

	slice_date_range( fp_in, fp_out, route_tag )


