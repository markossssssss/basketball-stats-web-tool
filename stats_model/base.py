import numpy as np
from plottable import Table, ColDef
import matplotlib
import matplotlib.pyplot as plt
import argparse
import json
import pandas as pd

from datetime import datetime
import os

import platform


system = platform.system()
if system == "Windows":
    matplotlib.rc("font", family='microsoft YaHei')
    plt.rcParams['font.family'] = ['microsoft YaHei']
elif system == "Darwin":
    font_type = 'Heiti TC'
    plt.rcParams['font.family'] = [font_type]


terms = {
    "name": "姓名",
    "time": "上场时间",
    "scores": "得分",
    "assists": "助攻",
    "rebounds": "篮板",
    "steals": "抢断",
    "blocks": "盖帽",
    "2PTs": "2分",
    "3PTs": "3分",
    "FTs": "罚球",
    "OD_rebounds": "后场+前场篮板",
    "fouls": "犯规",
    "TOs": "失误",
    "make_fouls": "造成犯规",
    "EFF": "效率值",
    "oncourt_per_scores": "在场得分(10回合)",
    "oncourt_per_loses": "在场失分(10回合)",
    "TS": "真实命中率",
    "USG": "球权使用率",
    "atps": "出手",
    "ft_atps": "罚球出手"
}

# 需要等所有基础数据都出来之后才能计算的数据
high_level_stats = ["EFF", "USG"]


def append(df, row_dict):
    return pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)

def parse_shoots(shoots):
    shoots = shoots.split("/")
    return int(shoots[1]) - int(shoots[0])

def decimal_to_percent(val: float) -> str:
    if abs(val - 0) < 0.0001:
        return "/"
    elif abs(val - 1) < 0.0001:
        return "100%"
    else:
        return f"{str(round(val * 100))}%"


class BaseStatsModel():
    # True: 检测：助攻必须来自同队、抢断盖帽犯规必须来自其他队
    check_event_team = True
    def __init__(self, event_data, config):
        self.event_data = event_data
        self.config = config
        self.quarters = self.config["quarters"]
        # self.target_stats = self.config["stats"]
        self.quarter_time = self.config["quarter_time"]
        self.match_date = datetime.strptime(self.config["match_name"].split("_")[0], '%Y%m%d').strftime('%m月%d日')
        self.court_name = self.config["court"]
        try:
            self.match_time = self.config["match_time"]
        except:
            self.match_time = None
        self.preprocess()
        self.player_stats = None
        self.scores = None

    def check_switch_people(self):
        return


    def preprocess(self):
        # get team names
        self.team_names = []
        i = 0
        while len(self.team_names) < self.max_teams:
            name = self.event_data.iloc[i]["Team"]
            if not (name in self.team_names) and (name != ""):
                self.team_names.append(name)
            i += 1

        self.num_teams = len(self.team_names)
        # get player names
        self.player_names = [[] for i in self.team_names]
        event_data_switch = self.event_data[self.event_data.Event == "换人"]
        for i, r in event_data_switch.iterrows():
            team_idx = self.team_names.index(r["Team"])
            if not r["Object"] in self.player_names[team_idx]:
                self.player_names[team_idx].append(r["Object"])
        # get actual match time for each quarter
        self.actual_quarter_times = [0 for i in range(self.quarters)]
        for i, r in self.event_data.iterrows():
            t = r["Time"].split(" - ")
            t_ = t[1].split(" : ")
            q, m, s = int(t[0]), int(t_[0]), int(t_[1])
            time = m * 60 + s
            self.actual_quarter_times[q - 1] = max(self.actual_quarter_times[q - 1], time + 1)

        # get start time for each quarter
        self.quarter_start_times = [0 for i in range(self.quarters)]
        for i, r in self.event_data[self.event_data.Event == "计时开始"].iterrows():
            # print(r)
            self.quarter_start_times[int(r["Object"]) - 1] = int(r["Info"])

        # parse time
        self.event_data["OriginTime"] = self.event_data["Time"]
        self.event_data["OriginQuarterTime"] = self.event_data["Time"].apply(self.parse_origin_quarter_time)
        self.event_data["Quarter"] = self.event_data["Time"].apply(self.parse_quarter)
        self.event_data["Time"] = self.event_data["Time"].apply(self.parse_time)
        self.event_data.sort_values(by=['Time'], ascending=[True])

    def get_stats(self):
        self.check_switch_people()
        self.get_stat_item_dfs()
        columns = [terms[stat_item] for stat_item in self.config["stats"]]
        self.player_stats = [pd.DataFrame(columns=columns) for i in range(self.num_teams)]
        for i, team in enumerate(self.team_names):
            for name in self.player_names[i]:
                row = {terms["name"]: name}
                for stat_item in self.target_stats:
                    if stat_item in high_level_stats:
                        continue
                    value = eval("self.get_{}('{}', {})".format(stat_item, name, i))
                    row[terms[stat_item]] = value
                # print(row)
                self.player_stats[i] = append(self.player_stats[i], row)
        for stat_item in high_level_stats:
            if stat_item in self.target_stats:
                eval("self.get_{}()".format(stat_item))
        for i in range(self.num_teams):
            self.player_stats[i].set_index('姓名', inplace = True)
        # print(self.player_stats)
        scores = self.get_total_scores()
        self.scores = "{}:{}".format(scores[0], scores[1])
        try:
            self.scores = self.config["scores"]
        except:
            pass
        self.scores_rev = "{}:{}".format(scores[1], scores[0])

    def get_total_scores(self):
        return sum(list(self.player_stats[0]["得分"])), sum(list(self.player_stats[1]["得分"]))


    def plot_stats_single_team(self, team_idx, show=False, save=None, title=None):
        if self.player_stats is None:
            self.get_stats()
        fig, ax = plt.subplots(figsize=(20, 10), dpi=80)

        table = self.plot_table(fig, ax, team_idx, plot_team_name=False)

        game_scores_txt = "{} {} {}".format(self.team_names[0], self.scores, self.team_names[1])
        team_names_txt = "{} {}".format(self.team_names[0], self.team_names[1])
        info_txt = "{} {}".format(self.match_date, self.court_name)

        JUSHOOP_title_txt = self.JUSHOOP_title_txt if title is None else title

        plt.title(label="{}\n{}".format(JUSHOOP_title_txt, "_" * 110),
                  fontsize=25,
                  fontweight="bold",
                  color="#e0e8df",
                  y=1)
        plt.suptitle("{} {} {}".format(self.team_names[team_idx], 65 * "  ", info_txt), fontsize=19, color='#e0e8df',
                     x=0.5, y=0.94, fontweight="bold")

        matplotlib.pyplot.subplots_adjust(left=0.02, bottom=0.001, right=0.982, top=0.893)

        if show:
            plt.show()
        if save is not None:
            plt.savefig(os.path.join(save, "{}".format(self.team_names[team_idx])), dpi=300)
        plt.close()

    def plot_stats_both_team(self, show=False, save=None, title=None):
        fig = plt.figure(num=1, figsize=(20, 10), dpi=80)

        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)

        table1 = self.plot_table(fig, ax1, 0)
        table2 = self.plot_table(fig, ax2, 1)

        game_scores_txt = "{} {} {}".format(self.team_names[0], self.scores, self.team_names[1])
        info_txt = "{} {}".format(self.match_date, self.court_name)

        JUSHOOP_title_txt = self.JUSHOOP_title_txt if title is None else title
        
        plt.title(label="{} \n____________________________________________________________________________________________________________".format(JUSHOOP_title_txt),
                  fontsize=25,
                  fontweight="bold",
                  color="#e0e8df",
                  y=2.22)
        # plt.rcParams["text.color"] = "#000000"
        plt.suptitle("{} {} {}".format(game_scores_txt, (68 - int(len(game_scores_txt) / 2)) * "  ", info_txt),
                     fontsize=19, color='#e0e8df', x=0.5, y=0.94, fontweight="bold")
        # logo = Image.open('logo1.png')
        # plt.imshow(logo)
        # for font in matplotlib.font_manager.fontManager.ttflist:
        #     print(font.name, '-', font.fname)
        matplotlib.pyplot.subplots_adjust(left=0.02, bottom=0.001, right=0.982, top=0.893)

        if show:
            plt.show()
        if save is not None:
            plt.savefig(os.path.join(save, "{}_vs_{}".format(self.team_names[0], self.team_names[1])), dpi=300)
        plt.close()

    def print_info(self):
        print(self.team_names)
        print(self.player_names)
        print(self.event_data.head(20))
        print(self.event_data.tail(20))
        print(self.match_date)
        print(self.actual_quarter_times)

    # 从比赛开始时为起点计时
    def parse_time(self, time):
        t = time.split(" - ")
        t_ = t[1].split(" : ")

        q, m, s = int(t[0]), int(t_[0]), int(t_[1])
        return sum(self.actual_quarter_times[:q - 1]) + m * 60 + s

    def parse_quarter(self, time):
        t = time.split(" - ")
        t_ = t[1].split(" : ")

        q, m, s = int(t[0]), int(t_[0]), int(t_[1])
        return q

    # 从视频最初开始计时
    def parse_origin_quarter_time(self, time):
        t = time.split(" - ")
        t_ = t[1].split(" : ")

        q, m, s = int(t[0]), int(t_[0]), int(t_[1])
        return m * 60 + s + int(self.quarter_start_times[q - 1])

    def get_stat_item_dfs(self):
        # 一次性筛选好各数据项,避免重复处理
        self.scores_df = self.event_data[(self.event_data.Info == "进球")]

        self.twopts_atpt_df = self.event_data[(self.event_data.Event == "2分球出手")]
        self.threepts_atpt_df = self.event_data[(self.event_data.Event == "3分球出手")]
        self.fts_atpt_df = self.event_data[(self.event_data.Event == "罚球出手")]

        self.rebounds_df = self.event_data[(self.event_data.Event == "篮板")]
        self.assists_df = self.event_data[(self.event_data.Event == "助攻")]
        self.steals_df = self.event_data[(self.event_data.Event == "抢断")]
        self.blocks_df = self.event_data[(self.event_data.Event == "盖帽")]
        self.tos_df = self.event_data[(self.event_data.Event == "失误")]
        self.fouls_df = self.event_data[(self.event_data.Event == "犯规")]




    def df_query(self, Event, Team=None, Player=None, Object=None, Info=None):
        df = eval(f"self.{Event}_df")
        query_str = "1&"
        same_team = True
        if Object is not None:
            # 这些数据，说明要查找的数据项，队伍和目标球员不在一个队
            if Event in ["steals", "blocks", "fouls"]:
                same_team = False
            query_str += f"(df.Object == '{Object}')&"
        if Team is not None:
            # not check_event_team 说明不检测队伍（比如有临时换队情况，这时会出现抢断自己队、助攻别的队等）
            if not self.check_event_team and Event in ["assists", "steals", "blocks", "fouls"]:
                pass
            else:
                equal = "==" if same_team else "!="
                query_str += f"(df.Team {equal} '{Team}')&"
        if Player is not None:
            query_str += f"(df.Player == '{Player}')&"

        if Info is not None:
            query_str += f"(df.Info == '{Info}')&"

        if query_str[-1] == "&":
            query_str = query_str[:-1]

        # print(query_str)
        return df[eval(query_str)]


    def get_scores(self, name, team_id):
        team_name = self.team_names[team_id]
        scores = 0
        # 独立进球记录
        scores_df = self.df_query(Event="scores", Team=team_name, Player=name)
        # scores_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Info == "进球")]
        # 受助攻记录

        # assisted_df = self.event_data[(self.event_data.Team != team_name) & (self.event_data.Object == name) & (self.event_data.Event == "助攻")]
        assisted_df = self.df_query(Event="assists", Team=team_name, Object=name)




        scores += len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(scores_df[scores_df.Event == "2分球出手"]) * 2 + len(scores_df[scores_df.Event == "罚球出手"])
        scores += len(assisted_df[assisted_df.Info == "3分"]) * 3 + len(assisted_df[assisted_df.Info == "2分"]) * 2

        return scores



    def get_TS(self, name, team_id):
        team_name = self.team_names[team_id]
        scores = 0
        # 独立进球记录
        # scores_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Info == "进球")]
        scores_df = self.df_query(Event="scores", Team=team_name, Player=name)
        # 受助攻记录
        # get_assist_df = self.event_data[
        #     (self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "助攻")]
        get_assist_df = self.df_query(Event="assists", Team=team_name, Object=name)


        scores += len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(
            scores_df[scores_df.Event == "2分球出手"]) * 2 + len(
            scores_df[scores_df.Event == "罚球出手"])
        scores += len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(
            get_assist_df[get_assist_df.Info == "2分"]) * 2


        twopts_atpt_df = self.df_query(Event="twopts_atpt", Team=team_name, Player=name)
        threepts_atpt_df = self.df_query(Event="threepts_atpt", Team=team_name, Player=name)
        fts_atpt_df = self.df_query(Event="fts_atpt", Team=team_name, Player=name)


        # twopts_atpt_df = self.event_data[
        #     (self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "2分球出手")]
        # threepts_atpt_df = self.event_data[
        #     (self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "3分球出手")]
        # fts_atpt_df = self.event_data[
        #     (self.event_data.Team == team_name) & (self.event_data.Player == name)]

        assisted_df = self.df_query(Event="assists", Object=name, Team=team_name)
        blocked_df = self.df_query(Event="blocks", Object=name, Team=team_name)

        # assisted_df = self.event_data[
        #     (self.event_data.Object == name) & (self.event_data.Event == "助攻")]
        # blocked_df = self.event_data[ (self.event_data.Object == name) & (
        #             self.event_data.Event == "盖帽")]

        atpt = len(twopts_atpt_df) + len(threepts_atpt_df) + len(assisted_df) + len(blocked_df)
        ft_atpt = len(fts_atpt_df)

        if scores == 0:
            return 0

        return round(scores / (2 * (atpt + 0.44 * ft_atpt)), 3)

    def get_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        rebounds_df = self.df_query(Event="rebounds", Player=name, Team=team_name)
        # rebounds_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "篮板")]
        return len(rebounds_df)

    def get_assists(self, name, team_id):
        team_name = self.team_names[team_id]
        assists_df = self.df_query(Event="assists", Player=name, Team=team_name)
        # assists_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "助攻")]
        return len(assists_df)

    def get_time(self, name, team_id):
        team_name = self.team_names[team_id]

        get_on_arr = sorted(list(self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "换人")]["Time"]))
        get_off_arr = sorted(list(self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "换人")]["Time"]))


        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))

        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]

        time *= (float(self.quarter_time) / (float(sum(self.actual_quarter_times)) / 60. / self.quarters))
        time = int(time)

        return "{:0>2d}:{:0>2d}".format(int(time / 60), time % 60)

    def get_steals(self, name, team_id):
        team_name = self.team_names[team_id]
        steals_df = self.df_query(Event="steals", Player=name, Team=team_name)
        # steals_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "抢断")]
        return len(steals_df)


    def get_blocks(self, name, team_id):
        team_name = self.team_names[team_id]
        blocks_df = self.df_query(Event="blocks", Player=name, Team=team_name)
        # blocks_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "盖帽")]
        return len(blocks_df)

    def get_atps(self, name, team_id):
        team_name = self.team_names[team_id]
        # team_name_op = self.team_names[1 - team_id]

        twopts_atpt_df = self.df_query(Event="twopts_atpt", Player=name, Team=team_name)
        threepts_atpt_df = self.df_query(Event="threepts_atpt", Player=name, Team=team_name)
        assisted_df = self.df_query(Event="assists", Object=name, Team=team_name)
        blocked_df = self.df_query(Event="blocks", Object=name, Team=team_name)

        # twopts_atpt_df = self.event_data[
        #     (self.event_data.Player == name) & (self.event_data.Event == "2分球出手")]
        # threepts_atpt_df = self.event_data[
        #     (self.event_data.Player == name) & (self.event_data.Event == "3分球出手")]
        # assisted_df = self.event_data[
        #     (self.event_data.Object == name) & (self.event_data.Event == "助攻")]
        # blocked_df = self.event_data[
        #     (self.event_data.Object == name) & (
        #             self.event_data.Event == "盖帽")]

        return len(twopts_atpt_df) + len(threepts_atpt_df) + len(assisted_df) + len(blocked_df)

    def get_ft_atps(self, name, team_id):
        team_name = self.team_names[team_id]
        fts_atpt_df = self.df_query(Event="fts_atpt", Player=name, Team=team_name)
        # fts_atpt_df = self.event_data[
        #     (self.event_data.Player == name) & (self.event_data.Event == "罚球出手")]

        return len(fts_atpt_df)


    def get_2PTs(self, name, team_id):
        team_name = self.team_names[team_id]
        # team_name_op = self.team_names[1 - team_id]
        twopts_atpt_df = self.df_query(Event="twopts_atpt", Player=name, Team=team_name)
        # twopts_atpt_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "2分球出手")]
        twopts_made_df = twopts_atpt_df[twopts_atpt_df.Info == "进球"]

        twopts_assisted_df = self.df_query(Event="assists", Object=name, Info="2分", Team=team_name)
        twopts_blocked_df = self.df_query(Event="blocks", Object=name, Info="2分", Team=team_name)
        # twopts_assisted_df = self.event_data[(self.event_data.Object == name) & (self.event_data.Event == "助攻") & (self.event_data.Info == "2分")]
        # twopts_blocked_df = self.event_data[(self.event_data.Object == name) & (self.event_data.Event == "盖帽") & (self.event_data.Info == "2分")]
        return "{}/{}".format(len(twopts_made_df) + len(twopts_assisted_df), len(twopts_atpt_df)+ len(twopts_assisted_df) + len(twopts_blocked_df))


    def get_3PTs(self, name, team_id):
        team_name = self.team_names[team_id]
        # team_name_op = self.team_names[1 - team_id]

        threepts_atpt_df = self.df_query(Event="threepts_atpt", Player=name, Team=team_name)

        # threepts_atpt_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "3分球出手")]
        threepts_made_df = threepts_atpt_df[threepts_atpt_df.Info == "进球"]

        threepts_assisted_df = self.df_query(Event="assists", Object=name, Team=team_name, Info="3分")
        threepts_blocked_df = self.df_query(Event="blocks", Object=name, Team=team_name, Info="3分")
        # threepts_assisted_df = self.event_data[(self.event_data.Object == name) & (self.event_data.Event == "助攻") & (self.event_data.Info == "3分")]
        # threepts_blocked_df = self.event_data[(self.event_data.Object == name) & (self.event_data.Event == "盖帽") & (self.event_data.Info == "3分")]
        return "{}/{}".format(len(threepts_made_df) + len(threepts_assisted_df), len(threepts_atpt_df) + len(threepts_assisted_df) + len(threepts_blocked_df))


    def get_FTs(self, name, team_id):
        team_name = self.team_names[team_id]
        fts_atpt_df = self.df_query(Player=name, Event="fts_atpt", Team=team_name)
        # fts_atpt_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "罚球出手")]
        fts_made_df = fts_atpt_df[fts_atpt_df.Info == "进球"]
        return "{}/{}".format(len(fts_made_df), len(fts_atpt_df))


    def get_OD_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        rebounds_df = self.df_query(Team=team_name, Player=name, Event="rebounds")
        # rebounds_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "篮板")]
        return "{}+{}".format(len(rebounds_df[rebounds_df.Info == "后场"]), len(rebounds_df[rebounds_df.Info == "前场"]))


    def get_TOs(self, name, team_id):
        team_name = self.team_names[team_id]
        # team_name_op = self.team_names[1 - team_id]

        TOs_df = self.df_query(Event="tos", Player=name, Team=team_name)
        # TOs_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "失误")]

        stealed_df = self.df_query(Event="steals", Object=name, Team=team_name)
        # stealed_df = self.event_data[(self.event_data.Object == name) & (self.event_data.Event == "抢断")]

        off_fouls_df = self.df_query(Player=name, Event="fouls", Info="进攻犯规", Team=team_name)
        # off_fouls_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Info == "进攻犯规")]

        return len(TOs_df) + len(stealed_df) + len(off_fouls_df)

    def get_fouls(self, name, team_id):
        team_name = self.team_names[team_id]
        fouls_df = self.df_query(Player=name, Event="fouls", Team=team_name)
        # fouls_df = self.event_data[(self.event_data.Player == name) & (self.event_data.Event == "犯规")]
        return len(fouls_df)

    def get_make_fouls(self, name, team_id):
        team_name = self.team_names[team_id]
        # team_name_op = self.team_names[1 - team_id]
        make_fouls_df = self.df_query(Event="fouls", Team=team_name, Object=name)
        # make_fouls_df = self.event_data[(self.event_data.Team == team_name_op) & (self.event_data.Object == name) & (
        #             self.event_data.Event == "犯规")]
        return len(make_fouls_df)

    def get_EFF(self):
        for idx, team in enumerate(self.team_names):
            for i, r in self.player_stats[idx].iterrows():
                EFF = 0
                EFF += (int(r["得分"]) + int(r["篮板"]) + int(r["助攻"]) + int(r["抢断"]) + int(
                    r["盖帽"] - int(r["失误"])))
                EFF -= (parse_shoots(r["2分"]) + parse_shoots(r["3分"]) + parse_shoots(r["罚球"]))
                self.player_stats[idx].loc[i, "效率值"] = EFF

    def get_USG(self):
        for idx, team in enumerate(self.team_names):
            tos_total = 0
            atps_total = 0
            ft_atps_total = 0

            for i, r in self.player_stats[idx].iterrows():
                tos_total += r["失误"]
                atps_total += r["出手"]
                ft_atps_total += r["罚球出手"]

            for i, r in self.player_stats[idx].iterrows():
                USG = 0
                time = int(r["上场时间"][:2]) * 60 + int(r["上场时间"][-2:])
                if (time):
                    USG += (r["出手"] + 0.44 * r["罚球出手"] + r["失误"]) * self.quarter_time * self.quarters * 60
                    USG /= (atps_total + 0.44 * ft_atps_total + tos_total) * time

                self.player_stats[idx].loc[i, "球权使用率"] = round(USG, 3)


    def get_oncourt_per_scores(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        get_on_arr = sorted(list(
            self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (
                        self.event_data.Event == "换人")]["Time"]))
        get_off_arr = sorted(list(
            self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (
                        self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))

        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]

        if time == 0:
            return 0

        team_scores = 0
        rounds = 0
        """计算在场得分与失分"""
        for i in range(len(get_on_arr)):
            scores_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name) & (self.event_data.Info == "进球")]
            get_assist_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name) & (self.event_data.Event == "助攻")]
            team_scores += (
                    len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(
                scores_df[scores_df.Event == "2分球出手"]) * 2 + len(
                scores_df[scores_df.Event == "罚球出手"]))
            team_scores += (
                    len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(
                get_assist_df[get_assist_df.Info == "2分"]) * 2)

        """计算在场回合数"""
        """
        进攻结束回合标志：被抢断，进攻犯规/违体犯规进攻，失误，进球，对方投篮犯规/普通犯规犯满, 被抢到后场篮板
        """
        for i in range(len(get_on_arr)):
            filtered_event_data = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i])]
            stealed_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Event == "抢断")])
            off_foul_rounds = len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name) & (filtered_event_data.Info == "进攻犯规")]) + len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name) & (filtered_event_data.Info == "违体进攻犯规")])
            scored_rounds = len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name) & (filtered_event_data.Info == "进球")]) + len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name) & (filtered_event_data.Event == "助攻")]) - len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "进球") & (
                        filtered_event_data.Event == "罚球出手")])
            TO_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Event == "失误")])
            def_rebounded_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "后场")])
            fouled_rounds = len(filtered_event_data[(filtered_event_data.Team == team_name_op) & (
                        filtered_event_data.Info == "普通犯规犯满")]) + len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "投篮犯规")])

            rounds += (
                        stealed_rounds + off_foul_rounds + scored_rounds + TO_rounds + def_rebounded_rounds + fouled_rounds)

        if rounds == 0:
            rounds += 1

        # print(name, team_scores, rounds)

        return round(team_scores / rounds * 10, 1)

    def get_oncourt_per_loses(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        get_on_arr = sorted(list(
            self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (
                        self.event_data.Event == "换人")]["Time"]))
        get_off_arr = sorted(list(
            self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (
                        self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))

        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]
        if time == 0:
            return 0

        op_team_scores = 0
        rounds = 0
        """计算在场得分与失分"""
        for i in range(len(get_on_arr)):
            op_scores_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name_op) & (self.event_data.Info == "进球")]
            op_get_assist_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name_op) & (self.event_data.Event == "助攻")]

            op_team_scores += (
                    len(op_scores_df[op_scores_df.Event == "3分球出手"]) * 3 + len(
                op_scores_df[op_scores_df.Event == "2分球出手"]) * 2 + len(
                op_scores_df[op_scores_df.Event == "罚球出手"]))
            op_team_scores += (
                    len(op_get_assist_df[op_get_assist_df.Info == "3分"]) * 3 + len(
                op_get_assist_df[op_get_assist_df.Info == "2分"]) * 2)

        """计算在场回合数"""
        """
        进攻结束回合标志：被抢断，进攻犯规/违体犯规进攻，失误，进球，对方投篮犯规/普通犯规犯满, 被抢到后场篮板
        减去进攻篮板数增加的回合

        #bug 出手后直接出界
        #bug 争球
        #bug 2+1算两回合
        """
        for i in range(len(get_on_arr)):
            filtered_event_data = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i])]
            stealed_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Event == "抢断")])
            off_foul_rounds = len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "进攻犯规")]) + len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "违体进攻犯规")])
            scored_rounds = len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "进球")]) + len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name_op) & (filtered_event_data.Event == "助攻")]) - len(
                filtered_event_data[
                    (filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "进球") & (
                            filtered_event_data.Event == "罚球出手")])
            TO_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Event == "失误")])
            def_rebounded_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "后场")])
            fouled_rounds = len(filtered_event_data[(filtered_event_data.Team == team_name) & (
                    filtered_event_data.Info == "普通犯规犯满")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "投篮犯规")])

            rounds += (
                    stealed_rounds + off_foul_rounds + scored_rounds + TO_rounds + def_rebounded_rounds + fouled_rounds)
        if rounds == 0:
            rounds += 1

        # print(name, op_team_scores, rounds)

        return round(op_team_scores / rounds * 10, 1)

    def save_table_file(self, save=None):
        if save is not None:
            self.player_stats[0].to_csv(os.path.join(save, f"{self.team_names[0]}数据.csv"), encoding='utf-8')
            self.player_stats[1].to_csv(os.path.join(save, f"{self.team_names[1]}数据.csv"), encoding='utf-8')

    def plot_table(self, fig, ax, team_idx, plot_team_name=True):
        raise NotImplementedError


if __name__ == '__main__':
    config = json.load(open("/Users/Markos/Desktop/basketball-stats-web-tool/GameStatsData/20230825_PURDUE_TG/config.json"))
    event_data = pd.read_csv("/Users/Markos/Desktop/basketball-stats-web-tool/GameStatsData/20230825_PURDUE_TG/events.csv")
    event_data = event_data.fillna("")

    print(config)


            