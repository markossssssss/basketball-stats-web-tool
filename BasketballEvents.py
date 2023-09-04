import numpy as np
from plottable import Table, ColDef
import matplotlib
import matplotlib.pyplot as plt
import argparse
import json
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from plottable.cmap import normed_cmap
from PIL import Image
import matplotlib.font_manager as font_manager
from datetime import datetime
import os

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
    "oncourt_per_loses": "在场失分(10回合)"
}

# 需要等所有基础数据都出来之后才能计算的数据
high_level_stats = ["EFF"]

def append(df, row_dict):
    return pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    
def parse_shoots(shoots):
    shoots = shoots.split("/")
    return int(shoots[1]) -int(shoots[0])

class BasketballEvents():
    def __init__(self, event_data, config):
        self.event_data = event_data
        self.config = config
        self.quarters = self.config["quarters"]
        self.target_stats = self.config["stats"]
        self.quarter_time = self.config["quarter_time"]
        self.match_date = datetime.strptime(self.config["match_name"].split("_")[0], '%Y%m%d').strftime('%m月%d日')
        self.court_name = self.config["court"]
        self.preprocess()
        self.player_stats = None
        self.scores = None
    
    def preprocess(self):
        # get team names
        self.team_names = []
        i = 0
        while len(self.team_names) < 2:
            name = self.event_data.iloc[i]["Team"]
            if not (name in self.team_names) and (name != ""):
                self.team_names.append(name)
            i += 1
        # get player names
        self.player_names = [[], []]
        event_data_switch = self.event_data[self.event_data.Event == "换人"]
        for i,r in event_data_switch.iterrows():
            team_idx = self.team_names.index(r["Team"])
            if not r["Object"] in self.player_names[team_idx]:
                self.player_names[team_idx].append(r["Object"])
        # get actual match time for each quarter 
        self.actual_quarter_times = [0, 0, 0, 0] 
        for i,r in self.event_data.iterrows():
            t = r["Time"].split(" - ")
            t_ = t[1].split(" : ")
            q, m, s = int(t[0]), int(t_[0]), int(t_[1])
            time = m*60 + s
            self.actual_quarter_times[q-1] = max(self.actual_quarter_times[q-1], time + 1)
            
        
        # get start time for each quarter
        self.quarter_start_times = [0 for i in range(self.quarters)]
        for i,r in self.event_data[self.event_data.Event=="计时开始"].iterrows():
            # print(r)
            self.quarter_start_times[int(r["Object"])-1] = int(r["Info"])
    
        # parse time
        self.event_data["OriginQuarterTime"] = self.event_data["Time"].apply(self.parse_origin_quarter_time)
        self.event_data["Quarter"] = self.event_data["Time"].apply(self.parse_quarter)
        self.event_data["Time"] = self.event_data["Time"].apply(self.parse_time)
        
    
    def get_stats(self):
        columns = [terms[stat_item] for stat_item in self.config["stats"]]
        self.player_stats = [pd.DataFrame(columns=columns) for i in range(2)]
        for i, team in enumerate(self.team_names):
            for name in self.player_names[i]:
                row = {terms["name"]:name}
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
        self.player_stats[0].set_index('姓名', inplace = True)
        self.player_stats[1].set_index('姓名', inplace = True)
        scores = self.get_total_scores()
        self.scores = "{}:{}".format(scores[0], scores[1])
            
    def get_total_scores(self):
        return sum(list(self.player_stats[0]["得分"])), sum(list(self.player_stats[1]["得分"]))
    
    
    def plot_stats_single_team(self, team_idx, show=False, save=None):
        if self.player_stats is None:
            self.get_stats()
        fig, ax = plt.subplots(figsize=(20, 10),dpi=80)
        
        table = self.plot_table(fig, ax, team_idx)

        plt.title(label="{} {} {}\n___________________________________________________________________________________________________".format(self.team_names[0], self.scores, self.team_names[1]),
                  fontsize=25,
                  fontweight="bold",
                  color="#e0e8df",
                  y=1)
        plt.suptitle("JUSHOOP {} {} {}".format(61 * "   ", self.match_date, self.court_name), fontsize=19, color='#e0e8df', x=0.5, y=0.94, fontweight="bold")

        matplotlib.pyplot.subplots_adjust(left=0.02, bottom=0.001, right=0.982, top=0.893)
        
        if show:
            plt.show()
        if save is not None:
            plt.savefig(os.path.join(save, "{}".format(self.team_names[team_idx])), dpi=300)
        plt.close()
        
        
    def plot_stats_both_team(self, show=False, save=None):
        fig = plt.figure(num=1, figsize=(20, 10),dpi=80)
        
        ax1 = fig.add_subplot(2,1,1)
        ax2 = fig.add_subplot(2,1,2)
        
        table1 = self.plot_table(fig, ax1, 0)
        table2 = self.plot_table(fig, ax2, 1)
        
        game_scores_txt = "{} {} {}".format(self.team_names[0], self.scores, self.team_names[1])
        info_txt = "{} {}".format(self.match_date, self.court_name)
        JUSHOOP_title_txt = "JUSHOOP球局"
        
        
        plt.title(label="{} \n___________________________________________________________________________________________________".format(JUSHOOP_title_txt),
                  fontsize=25,
                  fontweight="bold",
                  color="#e0e8df",
                  y=2.22)
        # plt.rcParams["text.color"] = "#000000"
        plt.suptitle("{} {} {}".format(game_scores_txt, 61 * "   ", info_txt), fontsize=19, color='#e0e8df', x=0.5, y=0.94, fontweight="bold")
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
        return sum(self.actual_quarter_times[:q-1]) + m * 60 + s
    
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
        return m * 60 + s + int(self.quarter_start_times[q-1])
        
    
    def get_scores(self, name, team_id):
        team_name = self.team_names[team_id]
        scores = 0
        # 独立进球记录
        scores_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Info == "进球")]
        # 受助攻记录
        get_assist_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "助攻")]
        scores += len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(scores_df[scores_df.Event == "2分球出手"]) * 2 + len(scores_df[scores_df.Event == "罚球出手"])
        scores += len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(get_assist_df[get_assist_df.Info == "2分"]) * 2
    
        return scores
    
    
    def get_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        rebounds_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "篮板")]
        return len(rebounds_df)
    
    
    def get_assists(self, name, team_id):
        team_name = self.team_names[team_id]
        assists_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "助攻")]
        return len(assists_df)
    
    def get_time(self, name, team_id):
        team_name = self.team_names[team_id]
        get_on_arr = sorted(list(self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "换人")]["Time"]))
        get_off_arr = sorted(list(self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "换人")]["Time"]))
    
    
        # print(name)
        # print(len(get_on_arr), len(get_off_arr))
        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)
    
    
        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))
        # print(name, get_off_arr)
    
        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]
    
        time *= (float(self.quarter_time) / (float(sum(self.actual_quarter_times)) / 60. / self.quarters))
        time = int(time)
    
        return "{:0>2d}:{:0>2d}".format(int(time/60), time%60)
    
    
    def get_steals(self, name, team_id):
        team_name = self.team_names[team_id]
        steals_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "抢断")]
        return len(steals_df)
    
    
    def get_blocks(self, name, team_id):
        team_name = self.team_names[team_id]
        blocks_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "盖帽")]
        return len(blocks_df)
    
    
    def get_2PTs(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        twopts_atpt_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "2分球出手")]
        twopts_made_df = twopts_atpt_df[twopts_atpt_df.Info == "进球"]
        twopts_assisted_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "助攻") & (self.event_data.Info == "2分")]
        twopts_blocked_df = self.event_data[(self.event_data.Team == team_name_op) & (self.event_data.Object == name) & (self.event_data.Event == "盖帽") & (self.event_data.Info == "2分")]
        return "{}/{}".format(len(twopts_made_df) + len(twopts_assisted_df), len(twopts_atpt_df)+ len(twopts_assisted_df) + len(twopts_blocked_df))
    
    
    def get_3PTs(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        threepts_atpt_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "3分球出手")]
        threepts_made_df = threepts_atpt_df[threepts_atpt_df.Info == "进球"]
        threepts_assisted_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "助攻") & (self.event_data.Info == "3分")]
        threepts_blocked_df = self.event_data[(self.event_data.Team == team_name_op) & (self.event_data.Object == name) & (self.event_data.Event == "盖帽") & (self.event_data.Info == "3分")]
        return "{}/{}".format(len(threepts_made_df) + len(threepts_assisted_df), len(threepts_atpt_df) + len(threepts_assisted_df) + len(threepts_blocked_df))
    
    
    def get_FTs(self, name, team_id):
        team_name = self.team_names[team_id]
        fts_atpt_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "罚球出手")]
        fts_made_df = fts_atpt_df[fts_atpt_df.Info == "进球"]
        return "{}/{}".format(len(fts_made_df), len(fts_atpt_df))
    
    
    def get_OD_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        rebounds_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "篮板")]
        return "{}+{}".format(len(rebounds_df[rebounds_df.Info == "后场"]), len(rebounds_df[rebounds_df.Info == "前场"]))
    
    
    def get_TOs(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        TOs_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "失误")]
        stealed_df = self.event_data[(self.event_data.Team == team_name_op) & (self.event_data.Object == name) & (self.event_data.Event == "抢断")]
        off_fouls_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Info == "进攻犯规")]
    
        return len(TOs_df) + len(stealed_df) + len(off_fouls_df)
    
    
    def get_fouls(self, name, team_id):
        team_name = self.team_names[team_id]
        fouls_df = self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "犯规")]
        return len(fouls_df)
    
    
    def get_make_fouls(self, name, team_id):
        team_name_op = self.team_names[1-team_id]
        make_fouls_df = self.event_data[(self.event_data.Team == team_name_op) & (self.event_data.Object == name) & (self.event_data.Event == "犯规")]
        return len(make_fouls_df)

    
    def get_EFF(self):
        for idx, team in enumerate(self.team_names):
            for i,r in self.player_stats[idx].iterrows():
                EFF = 0
                EFF += (int(r["得分"]) + int(r["篮板"]) + int(r["助攻"]) + int(r["抢断"]) + int(r["盖帽"] - int(r["失误"])))
                EFF -= (parse_shoots(r["2分"]) + parse_shoots(r["3分"]) + parse_shoots(r["罚球"]))
                self.player_stats[idx].loc[i, "效率值"] = EFF
            
    def get_oncourt_per_scores(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        get_on_arr = sorted(list(
            self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "换人")]["Time"]))
        get_off_arr = sorted(list(
            self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "换人")]["Time"]))
    
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
            scores_df = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                    self.event_data.Team == team_name) & (self.event_data.Info == "进球")]
            get_assist_df = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                    self.event_data.Team == team_name) & (self.event_data.Event == "助攻")]
            team_scores += (
                    len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(scores_df[scores_df.Event == "2分球出手"]) * 2 + len(
                scores_df[scores_df.Event == "罚球出手"]))
            team_scores += (
                    len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(get_assist_df[get_assist_df.Info == "2分"]) * 2)
    
        """计算在场回合数"""
        """
        进攻结束回合标志：被抢断，进攻犯规/违体犯规进攻，失误，进球，对方投篮犯规/普通犯规犯满, 被抢到后场篮板
        """
        for i in range(len(get_on_arr)):
            filtered_event_data = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i])]
            stealed_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Event == "抢断")])
            off_foul_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "进攻犯规")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "违体进攻犯规")])
            scored_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "进球")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Event == "助攻")]) - len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "进球") & (
                        filtered_event_data.Event == "罚球出手")])
            TO_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Event == "失误")])
            def_rebounded_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "后场")])
            fouled_rounds = len(filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "普通犯规犯满")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "投篮犯规")])
    
            rounds += (stealed_rounds + off_foul_rounds + scored_rounds + TO_rounds + def_rebounded_rounds + fouled_rounds)
    
        if rounds == 0:
            rounds += 1
    
        # print(name, team_scores, rounds)
    
        return round(team_scores / rounds * 10, 1)
    
    
    
    def get_oncourt_per_loses(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        get_on_arr = sorted(list(
            self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "换人")]["Time"]))
        get_off_arr = sorted(list(
            self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "换人")]["Time"]))
    
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
            op_scores_df = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                    self.event_data.Team == team_name_op) & (self.event_data.Info == "进球")]
            op_get_assist_df = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
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
            filtered_event_data = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i])]
            stealed_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Event == "抢断")])
            off_foul_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "进攻犯规")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "违体进攻犯规")])
            scored_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "进球")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Event == "助攻")]) - len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "进球") & (
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
        
    
    def plot_table(self, fig, ax, team_idx):
        plt.rcParams['font.family'] = ['Arial Unicode MS']  # 用黑体显示中文
    
        row_colors = {
            "top4": "#2d3636",
            "top6": "#516362",
            "playoffs": "#8d9386",
            "relegation": "#c8ab8d",
            "even": "#627979",
            "odd": "#68817e",
        }
    
        bg_color = row_colors["odd"]
        text_color = "#FFFFFF"
    
        # fig, ax = plt.subplots()
    
        fig.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
    
        cmap = LinearSegmentedColormap.from_list(
            name="bugw", colors=["#FF0000", "#e0e8df", "#00EE76"], N=256
        )
        cmap_r = LinearSegmentedColormap.from_list(
            name="bugw", colors=["#00EE76", "#e0e8df", "#FF0000"], N=256
        )
    
        table_cols = ["上场时间", "得分", "篮板", "助攻", "抢断", "盖帽", "2分", "3分", "罚球",
                      "后场+前场篮板", "犯规", "失误", "造成犯规", "效率值", "在场得分(10回合)", "在场失分(10回合)"]
    
        table_col_defs = [
            ColDef("姓名", width=1.3, textprops={"ha": "left", "weight": "bold"}, title=self.team_names[team_idx]),
            ColDef("上场时间", width=0.8),
            ColDef("得分", width=0.5),
            ColDef("助攻", width=0.5),
            ColDef("篮板", width=0.5),
            ColDef("抢断", width=0.5),
            ColDef("盖帽", width=0.5),
            ColDef("2分", width=0.5),
            ColDef("3分", width=0.5),
            ColDef("罚球", width=0.5),
            ColDef("后场+前场篮板", width=0.8, title="后场+\n前场篮板"),
            ColDef("被犯规", width=0.8),
            ColDef("犯规", width=0.5),
            ColDef("失误", width=0.5),
            ColDef("效率值", width=0.5, text_cmap=normed_cmap(self.player_stats[team_idx]["效率值"], cmap=cmap, num_stds=2)),
            ColDef("在场得分(10回合)", width=1.0, title="在场得分\n(10回合)",
                   text_cmap=normed_cmap(self.player_stats[team_idx]["在场得分(10回合)"], cmap=cmap, num_stds=2)),
            ColDef("在场失分(10回合)", width=1.0, title="在场失分\n(10回合)",
                   text_cmap=normed_cmap(self.player_stats[team_idx]["在场失分(10回合)"], cmap=cmap_r, num_stds=2))
        ]
    
        tab = Table(self.player_stats[team_idx],
              ax= ax,
              column_definitions=table_col_defs,
              row_dividers=True,
              col_label_divider=False,
              footer_divider=True,
              columns=table_cols,
              even_row_color=row_colors["even"],
              footer_divider_kw={"color": bg_color, "lw": 2},
              row_divider_kw={"color": bg_color, "lw": 2},
              column_border_kw={"color": bg_color, "lw": 2},
              # 如果设置字体需要添加"fontname": "Roboto"
              textprops={"fontsize": 15, "ha": "center"}, )
        return tab
    
    
        
        
if __name__ == '__main__':
    config = json.load(open("/Users/Markos/Desktop/basketball-stats-web-tool/GameStatsData/20230825_PURDUE_TG/config.json"))
    event_data = pd.read_csv("/Users/Markos/Desktop/basketball-stats-web-tool/GameStatsData/20230825_PURDUE_TG/events.csv")
    event_data = event_data.fillna("")
    
    print(config)
    print(event_data)
    events = BasketballEvents(event_data, config)
    events.print_info()
    events.get_stats()
    print(events.player_stats)
    # events.plot_stats_single_team(1)
    events.plot_stats_both_team()
            
            
            
            
            