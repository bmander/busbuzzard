from gen_schedule import generate_schedule

def parse_gtfs_date( datestr ):
	year = datestr[0:4]
	month = datestr[4:6]
	day = datestr[6:]

	return date(int(year),int(month),int(day))

if __name__=='__main__':
	import sys

	if len(sys.argv) < 3:
		print "usage: python cmd.py passby_fn gtfs_dir [stop_id [direction_id [service_id]]]"
		exit()

	passby_fn = sys.argv[1]
	gtfs_dir = sys.argv[2]

	if len(sys.argv)>3:
		stop_id = sys.argv[3]
	else:
		stop_id = None

	if len(sys.argv)>4:
		direction_id = sys.argv[4]
	else:
		direction_id = None

	if len(sys.argv)>5:
		service_id = sys.argv[5]
	else:
		service_id = None


	passby_secs, scheduled_secs = generate_schedule(passby_fn, gtfs_dir, stop_id, direction_id, service_id)

	from matplotlib import pyplot as plt

	plt.vlines( passby_secs, 0, 1.5, lw=0.05 )
	plt.vlines( scheduled_secs, 0.5, 2, color="red" )

	plt.show()
