from stats_model import LeagueStatsModel
import os


if __name__ == "__main__":
    data_dir = "/Users/Markos/Desktop/全国村BA/小组赛"

    root, dirs, files = list(os.walk(data_dir))[0]
    print(dirs)
    
    league_model = LeagueStatsModel(dirs, data_dir)