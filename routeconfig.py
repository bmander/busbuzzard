from bs4 import BeautifulSoup
from urllib2 import urlopen
import simplejson as json
import os
import csv
import sys


def gen_route_config( nextbus_agency, gtfs_dir, out_fn ):
	url = "http://webservices.nextbus.com/service/publicXMLFeed?command=routeList&a="+nextbus_agency
	xml = urlopen(url).read()
	soup = BeautifulSoup(xml)

	nextbus_tags = [route["tag"] for route in soup("route")]

	routes_fn = os.path.join( gtfs_dir, "routes.txt" )

	rd = csv.reader( open( routes_fn ) )
	header = rd.next()
	route_short_name_ix = header.index("route_short_name")

	gtfs_route_short_names = [row[route_short_name_ix].strip() for row in rd]

	matches = {}
	for nextbus_tag in nextbus_tags:
		matches[nextbus_tag] = nextbus_tag if nextbus_tag in gtfs_route_short_names else None

	fpout = open( out_fn, "w" )
	fpout.write( json.dumps( matches, indent=2 ) )


if __name__=='__main__':
	if len(sys.argv)<4:
		print "usage: python cmd.py nextbus_agency gtfs_dir out_fn"
		exit()

	nextbus_agency = sys.argv[1]
	gtfs_dir = sys.argv[2]	
	out_fn = sys.argv[3]

	gen_route_config(nextbus_agency, gtfs_dir, out_fn)
