from gen_schedule import generate_schedule

if __name__=='__main__':
	import sys

	if len(sys.argv) < 4:
		print "usage: python cmd.py passby_fn gtfs_dir patterns_fn [stop_id [pattern_id [service_id]]]"
		exit()

	passby_fn = sys.argv[1]
	gtfs_dir = sys.argv[2]
	patterns_fn = sys.argv[3]

	if len(sys.argv)>4:
		stop_id = sys.argv[4]
	else:
		stop_id = None

	if len(sys.argv)>5:
		pattern_id = sys.argv[5]
	else:
		pattern_id = None

	if len(sys.argv)>6:
		service_id = sys.argv[6]
	else:
		service_id = None


	passby_secs, scheduled_secs = generate_schedule(passby_fn, gtfs_dir, patterns_fn, stop_id, pattern_id, service_id)

	from matplotlib import pyplot as plt

	plt.vlines( passby_secs, 0, 1.5, lw=0.05 )
	plt.vlines( scheduled_secs, 0.5, 2, color="red" )

	plt.show()
