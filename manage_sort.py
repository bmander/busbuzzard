from subprocess import call, Popen
import sys
import os
from math import log, ceil

CHUNKSIZE = 1000

def main(fp_in, chunksize=CHUNKSIZE):
	# print "splitting file into chunks of %d lines"%chunksize
	# call( ["split", "-l", str(chunksize), fp_in, "sort00"] )
	# print "done"

	chunkfns = [x for x in os.listdir(".") if x[0:6]=="sort00"]

	# for chunkfn in chunkfns:
	# 	print "sorting %s"%chunkfn
	# 	call( ["sort", "-k1,2", "-t,", "-o", chunkfn, chunkfn] )

	nsteps = int(ceil(log(len(chunkfns),2)))
	for i in range(nsteps):
		chunkfns = [x for x in os.listdir(".") if x[0:6]=="sort%02d"%i]

		print "merge round %d"%i

		for j in range(0,len(chunkfns)/2+1):
			fns = chunkfns[j*2:j*2+2]
			if len(fns)==0:
				continue

			fnout = "sort%02d-%02d"%(i+1,j)

			print "merge %s -> %s"%(fns,fnout)
			call(["sort", "-k1,2", "-m", "-o", fnout]+fns)

if __name__=='__main__':
	if len(sys.argv)<2:
		print "usage: python cmd.py fp_in [chunksize]"
		exit()

	fp_in = sys.argv[1]
	if len(sys.argv)==3:
		CHUNKSIZE = int(sys.argv[2])

	main(fp_in, CHUNKSIZE)