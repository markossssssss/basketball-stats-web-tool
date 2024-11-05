from . import BaseStatsModel, decimal_to_percent, terms, high_level_stats
from plottable.cmap import normed_cmap
from matplotlib.colors import LinearSegmentedColormap
from plottable import Table, ColDef
from plottable.table import create_cell, ColumnType, Row
import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import os
import pandas as pd
from typing import Callable
import matplotlib
import numpy as np
from typing import Any, Callable, Dict, List, Tuple
from numbers import Number





class FriendshipMatchStatsModel(BaseStatsModel):
    match_type = "友谊赛"
    max_teams = 2
    JUSHOOP_title_txt = "JUSHOOP全场友谊赛"

    check_team = True

    get_team_stats = True


    # 需要计算的数据项
    
    target_stats = ["atpts", "fts_atpts", "2pts_atpts", "3pts_atpts", "mades", "fts_mades", "2pts_mades", "3pts_mades",
                    "time", "scores", "assists", "rebounds", "steals", "blocks", "blocked", "2pts", "3pts",
                    "fts", "od_rebounds", "off_rebounds", "def_rebounds", "fouls", "tos", "make_fouls", "USG", "TS", "EFF", "oncourt_per_scores",
                    "oncourt_per_loses", "oncourt_scores", "oncourt_loses", "rounds", "plus_minus", "oncourt_off_rounds", "oncourt_def_rounds",
                    "oncourt_team_rebounds", "oncourt_opponent_rebounds", "used_rounds", "games_played"]

    # 需要展示的数据项
    table_cols = ["上场时间", "得分", "篮板", "助攻", "抢断", "盖帽", "2分", "3分", "罚球",
                  "后场+前场篮板", "失误", "球权使用率", "真实命中率", "效率值", "在场得分(10回合)",
                  "在场失分(10回合)"]
    
    # table_cols_ENG = ["MIN", "PTS", "REB", "AST", "STL", "BLK", "2FG", "3FG", "FT",
    #               "DREB+OREB", "TO", "USG%", "TS%", "EFF", "ORtg(10 rounds)",
    #               "DRtg(10 rounds)"]
    def get_total_scores(self):
        # 友谊赛多加了一栏全队得分，所以总得分计算翻倍了
        return sum(list(self.player_stats[0]["得分"]))//2, sum(list(self.player_stats[1]["得分"]))//2
    def check_switch_people(self):
        oncourt_players = {}
        oncourt_players[self.team_names[0]] = []
        oncourt_players[self.team_names[1]] = []


        for i, r in self.event_data.iterrows():
            # print(r)
            if r["Team"] == "":
                continue
            if r["Event"] == "换人":
                if r["Object"] in oncourt_players[r["Team"]]:
                    print("要换上的人已经在场上")
                    print(oncourt_players)
                    print(r)
                    raise ValueError
                if r["Player"] == "":
                    oncourt_players[r["Team"]].append(r["Object"])
                else:
                    if r["Player"] not in oncourt_players[r["Team"]]:
                        print("要换下的人不在场上")
                        print(oncourt_players)
                        print(r)
                        raise ValueError
                    try:
                        oncourt_players[r["Team"]].remove(r["Player"])
                        oncourt_players[r["Team"]].append(r["Object"])
                    except Exception as e:
                        print(e)
                        print("要换下的人不在场上")
                        print(oncourt_players)
                        print(r)

            else:
                if r["Player"] not in oncourt_players[r["Team"]]:
                    print("数据对象不在场上")
                    print("第{}节，{}".format(r["Quarter"], r["OriginTime"]))
                    print(oncourt_players)
                    print(r)
                    raise ValueError
                if r["Object"] != "":
                    if (r["Object"] not in oncourt_players[self.team_names[0]]) and (
                            r["Object"] not in oncourt_players[self.team_names[1]]):
                        print("数据对象不在场上")
                        print(oncourt_players)
                        print(r)
                        raise ValueError


    def save_table_file(self, save=None):
        if save is not None:
            self.player_stats[0].to_csv(os.path.join(save, f"{self.team_names[0]}数据.csv"), encoding='utf-8-sig')
            self.player_stats[1].to_csv(os.path.join(save, f"{self.team_names[1]}数据.csv"), encoding='utf-8-sig')
            pd.DataFrame(self.event_data.reset_index().sort_values(by=['Time', 'index']), columns=["Team","Player","OriginTime","Event","Info","Object"]).to_csv(os.path.join(save, f"明细数据表.csv"), encoding='utf-8-sig', index=False)


if __name__ == '__main__':
    import json
    import pandas as pd
    config = json.load(open("/Users/Markos/Desktop/basketball-stats-web-tool/20230102_JUSHOOP_光耀/config.json"))
    event_data = pd.read_csv("/Users/Markos/Desktop/basketball-stats-web-tool/20230102_JUSHOOP_光耀/events.csv")
    event_data = event_data.fillna("")

    # print(config)
    # print(event_data)
    events = FriendshipMatchStatsModel(event_data, config)
    # events.print_info()
    events.get_stats()

    tmp = events.event_data[(events.event_data.Player == events) & (events.event_data.Event == "助攻")]
    print(tmp)


    # print(events.player_stats)
    # events.plot_stats_single_team(1)
    # events.plot_stats_both_team()

    # mt_font = sorted([f.name for f in font_manager.fontManager.ttflist])
    # print(mt_font)
            
            
            
            
            