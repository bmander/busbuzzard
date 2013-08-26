Busbuzzard
==========

Inference of probabilistic schedules from empirical data about transit vehicles.

#### Step 0: Get the data

* A CSV of points logged from the NextBus API.
* For example: https://dl.dropboxusercontent.com/u/1158424/route_5.csv.zip
* Try to find someone with a larger data dump, to get a larger data dump.
* An unzipped GTFS that describes the service recorded in the NextBus CSV
* Try http://www.gtfs-data-exchange.com/ for current and past GTFS feeds

#### Step 1: Slice a route out of the NextBus CSV dump

`$ python slice_route.py data/nextbus.csv data/route_27.csv 27`

#### Step 2: Chain NextBus vehicle fixes into strings representing trip instances

`$ python chain.py data/route_27.csv data/route_27_chained.csv`

#### Step 3: Assign NextBus fix chains to GTFS trips

`$ python python match.py data/route_27_chained.csv data/your_gtfs_dir 27 data/route_27_your_gtfs.matches`

#### Step 4: Cache GTFS patterns

`$ python find_gtfs_patterns.py data/your_gtfs_dir data/your_gtfs_patterns.json`

#### Step 5: Compute passbys

`$ python passby.py data/your_gtfs_dir data/your_gtfs_patterns.json data/route_27_chained.csv data/route_27_your_gtfs.matches data/route_27_your_gtfs_passbys.csv`
