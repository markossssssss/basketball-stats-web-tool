import argparse
import json
import pandas as pd
import os
from BasketballEvents import BasketballEvents

parser = argparse.ArgumentParser(description='Run Example')
parser.add_argument('data_dir', type=str, help='path of config file')
args = parser.parse_args()

config = json.load(open(os.path.join(args.data_dir, "config.json")))
event_data = pd.read_csv(os.path.join(args.data_dir, "events.csv"),)
event_data = event_data.fillna("")

events = BasketballEvents(event_data, config)
events.get_stats()
events.plot_stats_both_team(show=False, save=args.data_dir)
events.plot_stats_single_team(0, show=False, save=args.data_dir)
events.plot_stats_single_team(1, show=False, save=args.data_dir)
