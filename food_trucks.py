#!/usr/bin/env python3

import csv
import sys
from copy import copy
import math
import hashlib
import argparse
from pathlib import Path
from io import StringIO
from pprint import pprint
import __main__

import requests


HEADERS = ['locationid', 'Applicant', 'FacilityType', 'cnn',
  'LocationDescription', 'Address', 'blocklot', 'block', 'lot', 'permit',
  'Status', 'FoodItems', 'X', 'Y', 'Latitude', 'Longitude', 'Schedule',
  'dayshours', 'NOISent', 'Approved', 'Received', 'PriorPermit',
  'ExpirationDate', 'Location', 'Fire Prevention Districts',
  'Police Districts', 'Supervisor Districts', 'Zip Codes',
  'Neighborhoods (old)']




def find_crow(position1, position2):

    delta_lat = math.fabs(position1[0] - position2[0])
    delta_long = math.fabs(position1[1] - position2[1])
    dist_lat = delta_lat * 69.048
    dist_long = delta_long * 54.751
    crow_dist = math.sqrt(dist_lat*dist_lat + dist_long*dist_long)
    return crow_dist


def command_line_parsing():

    parser = argparse.ArgumentParser(description='Food Truck Finder.')
    parser.add_argument('latlong', metavar='latlong', type=str, nargs='?',
                        help='current location as latitude,longitude '  \
                            '(no spaces)')
    args = parser.parse_args()
    if args.latlong is None:
        return (37.78240, -122.40705)

    parts = args.latlong.split(',')
    return (float(parts[0]), float(parts[1]))


def get_csv_data():
    csv_resp = requests.get("https://data.sfgov.org/api/views/rqzj-sfat/rows.csv")
    csv_file = StringIO(csv_resp.text)

    csv_reader = csv.reader(csv_file)
    return csv_reader


def sort_key(item):
    key = 200 * item[1]
    return key


def process_csv(reader):
    results_list = list()
    header = True
    position = {'name': 1, 'type': 2, 'address': 5, 'appr': 10, 'food': 11,
        'food2': 12, 'lat':14, 'long': 15}
    for row in reader:
        if header:
            headers = copy(row)
            if headers != HEADERS:
                print('ERROR: csv file format changed!')
                sys.exit(1)  
            header = False
            continue

        if len(row) != len(headers):
            print('Error: wrong # fields:')
            pprint(row)
            sys.exit(1)
        if row[position['type']] not in ('Truck'):
            continue
        if len(row[position['lat']]) == 0 or len(row[position['long']]) == 0:
            print('empty lat/long:')
            pprint(row)
            continue
        try:
            truck_lat = float(row[position['lat']])
            truck_long = float(row[position['long']])
        except ValueError:
            print('cannot convert input to floats')
            pprint(row)
            continue
        if truck_lat == 0.0 or truck_long == 0.0:
            continue
        if truck_lat > 180.0 or truck_long > 180.0 or  \
            truck_lat < -180.0 or truck_long < -180.0:
            continue
        if row[position['appr']] != 'APPROVED':
            continue

        dist = find_crow(my_position, (truck_lat, truck_long))
        hash_string = ''.join([row[position["name"]], row[position["address"]],
            row[position["food"]], row[position['lat']], row[position['long']]])
        hashvalue = hashlib.md5(hash_string.encode()).hexdigest()
    
        entry = [hashvalue, dist, row[position["name"]],
                 row[position["address"]], row[position["food"]]]
        results_list.append(entry)

    results_list.sort(key=sort_key)
    return results_list


def present_results(results):

    max_index = len(results)
    index = 0
    chose = False
    while index < max_index and not chose:
        print('\n')
        subindex = 0
        while subindex < 5 and index < max_index:
            entry = results[index]
            round_dist = round(entry[1], 1)
            print(f'{index+1}) {entry[2]}  {entry[3]}  {round_dist} mi.')
            print(entry[4])
            print()
            index += 1
            subindex += 1
        still_choosing = True
        while still_choosing:
            choice = input('press return to list more,\nor "q" to quit: ')
            if len(choice) > 0:
                try:
                    number_choice = int(choice) - 1
                    still_choosing = False
                    chose = True
                except ValueError:
                    if choice == 'q':
                        return None
                    print('invalid input, enter "q" or just press enter')
            else:
                still_choosing = False
                number_choice = -1

    if not chose:
        return None

    chosen_entry = results[number_choice]
    chosen_hash = chosen_entry[0]
    return chosen_hash




my_position = command_line_parsing()
reader = get_csv_data()
results = process_csv(reader)
present_results(results)
