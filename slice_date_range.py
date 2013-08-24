import csv

def slice_date_range(fp_in, fp_out, start_time, end_time):
	i=0

	rd = csv.reader( open(fp_in) )
	header = rd.next()
	time_ix = header.index('time')

	fpout = open(fp_out,"w")
	fpout.write(",".join(header))
	fpout.write("\n")
	for i, row in enumerate( rd ):
		if i%100000==0:
			print i

		if i%1000000==0:
			print row

		if row[time_ix]!='':
			row_time=float(row[time_ix])/1000.0
			if row_time>start_time and row_time<end_time:
				fpout.write( ",".join(row) )
				fpout.write( "\n" )

	print i

if __name__=='__main__':
	import sys
	if len(sys.argv)<4:
		print "usage: python cmd.py fp_in fp_out start_time end_time"
		exit()

	fp_in = sys.argv[1]
	fp_out = sys.argv[2]
	start_time = int(sys.argv[3])
	end_time = int(sys.argv[4])

	slice_date_range( fp_in, fp_out, start_time, end_time )


