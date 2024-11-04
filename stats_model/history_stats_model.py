# -*- coding: UTF-8 -*-
import json
import pandas as pd
import os
from tqdm import tqdm
from . import BaseStatsModel
from .duplicated_names import process_team_name, get_teams_from_game_name, process_name
def append(df, row_dict):
    return pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)


class HistoryStatsModel():
    def __init__(self, game_list, game_dir=None, target_team="ALL", num_games_to_keep=3, target_dir="history_data_model"):
        self.game_dir = game_dir
        if self.game_dir is None:
            self.game_dir = "GameStatsData"
        self.game_list = game_list
        self.target_dir = target_dir
        self.event_df_list = []
        self.num_games_to_keep = num_games_to_keep  # 球员至少参与多少场进入统计图
        self.stat_items = None
        self.target_team = target_team
        self.target_team_real_name = process_team_name(target_team)
        self.remove_player_list = ["黑短袖", "", "nobody"]
        self.boss_player_list = ["张佳运", "FRANK"]
        self.remove_player_list.extend(self.boss_player_list)
        self.target_team_personal_stats = None
        self.parse_game_list()

        self.parse_stats()


    def parse_game_list(self):
        if self.target_team == "ALL":
            return
        new_game_list = []
        print(self.game_list)
        for game_name in self.game_list:
            if self.target_team in get_teams_from_game_name(game_name):
                new_game_list.append(game_name)
        self.game_list = new_game_list

        print(f"{self.target_team}一共有{len(self.game_list)}场比赛\n")


    def parse_stats(self):
        print("parsing game stats....")
        for game_name in tqdm(self.game_list):
            # print(game_name)
            config = json.load(open(os.path.join(self.game_dir, game_name, "config.json")))
            event_data = pd.read_csv(os.path.join(self.game_dir, game_name, "events.csv"))
            event_data = event_data.fillna("")

            player_model = TeamAvgStatsModel(event_data, config)
            if self.target_team == "ALL":
                player_model.get_team_stats()
            else:
                player_model.get_stats()
            if self.stat_items is None:
                self.stat_items = player_model.target_stats
            # print(player_model.player_stats[0].columns)
            # print(player_model.team_names)
            if not self.target_team == "ALL":
                on_court_idx = player_model.team_names.index(self.target_team)
                if self.target_team_personal_stats is None:
                    self.target_team_personal_stats = player_model.player_stats[on_court_idx]
                else:
                    # target_team_stats[target_idx].add(events.player_stats[on_court_idx], fill_value=0)
                    self.target_team_personal_stats = pd.concat([self.target_team_personal_stats, player_model.player_stats[on_court_idx]])
                if player_model.same_team:
                    self.target_team_personal_stats = pd.concat([self.target_team_personal_stats, player_model.player_stats[1-on_court_idx]])
            else:
                for i in range(2):
                    if self.target_team_personal_stats is None:
                        self.target_team_personal_stats = player_model.player_stats[i]
                    else:
                        # target_team_stats[target_idx].add(events.player_stats[on_court_idx], fill_value=0)
                        self.target_team_personal_stats = pd.concat(
                            [self.target_team_personal_stats, player_model.player_stats[i]])

        if self.target_team == "ALL":
            # print(self.target_team_personal_stats)
            # print(self.target_team_personal_stats.index)
            # self.target_team_personal_stats = self.target_team_personal_stats.groupby(
            #     self.target_team_personal_stats.index).sum()
            # print(self.target_team_personal_stats)
            self.target_team_personal_stats = self.target_team_personal_stats.sort_values(by=["games_played"], na_position="last",
                                                                              ascending=False)
            self.target_team_personal_stats.to_csv("test_team_stats.csv")
            self.get_teams_histories()
            self.get_all_team_stat()
        else:
            self.target_team_personal_stats = self.target_team_personal_stats.groupby(
                self.target_team_personal_stats.index).sum() # concat same team
            print("________________________________\n\n")
            print(self.target_team_personal_stats)
            self.target_team_personal_stats.to_csv("source_data.csv")
            print("________________________________\n\n")
            self.get_team_basic_stat()
            self.get_team_advanced_stat()
            self.get_player_basic_stat()
            self.get_player_advanced_stat()
            self.get_team_advanced_stat_VS_AVG_VS_PROS()
            self.get_team_advanced_stat_VS_AVG_VS_OPPONENT()
            self.get_player_score_stat()
            self.get_player_team_spirit_stat()
            self.get_player_offense_options_stat()
            self.get_player_rebound_feat_stat()
        # print(self.target_team_personal_stats[0])
        # print(self.target_team_personal_stats[1])

    def get_teams_histories(self):
        self.target_team_personal_stats["win_rate"] = self.target_team_personal_stats["games_wined"] / self.target_team_personal_stats["games_played"]
        target_columns = ["win_rate", "games_wined", "games_played"]
        data = {}
        for column in target_columns:
            data[column] = self.target_team_personal_stats[column]
        df = pd.DataFrame(data)
        df = df[df["games_played"] >= 3]
        for target_team in df.index:
            games_played = df["games_played"][target_team]
            wined = df["games_wined"][target_team]
            win_rate = int(df["win_rate"][target_team]*100)
            idx = sorted(list(df["win_rate"])).index(df["win_rate"][target_team])
            rank = int(100 * (1-idx/len(df["win_rate"])))+1
            print(f"{target_team} 参加了{games_played}场, 获得{wined}场胜利，胜率超过{win_rate}%, 超过了{rank}%的球队")

    def get_all_team_stat(self):
        team_basic_stats_columns = ["场次", "得分", "篮板", "助攻", "失误", "回合数", "两分命中", "三分命中", "前场篮板", "后场篮板"]
        team_adv_stats_columns = ["进攻效率", "防守效率", "3分出手占比", "3分得分占比", "助攻得分占比","两分命中", "三分命中", "罚球命中", "篮板保护率", "前场篮板率"]
        self.team_adv_stats_df = pd.DataFrame(columns=team_adv_stats_columns)
        self.team_basic_stats_df = pd.DataFrame(columns=team_basic_stats_columns)
        sum_stats = self.target_team_personal_stats.sum()
        sum_stats.to_csv(os.path.join(self.target_dir, f"{self.target_team}_sum_stats.csv"))


        # print(self.target_team_personal_stats)


        games_played = round(sum_stats["games_played"]/2, 3)
        off_rounds = round(sum_stats["oncourt_off_rounds"] / games_played, 1)
        def_rounds = round(sum_stats["oncourt_def_rounds"] / games_played, 1)
        made_2 = round(sum_stats["2pts_mades"] / games_played, 1)
        made_3 = round(sum_stats["3pts_mades"] / games_played, 1)
        made_ft = round(sum_stats["fts_mades"] / games_played, 1)
        atp_2 = round(sum_stats["2pts_atpts"] / games_played, 1)
        atp_3 = round(sum_stats["3pts_atpts"] / games_played, 1)
        atp_ft = round(sum_stats["fts_atpts"] / games_played, 1)
        assists_2pts = round(sum_stats["assists_2pts"] / games_played, 1)
        assists_3pts = round(sum_stats["assists_3pts"] / games_played, 1)
        def_rebounds = round(sum_stats["def_rebounds"] / games_played, 1)
        opp_off_rebounds = round(sum_stats["off_rebounds"] / games_played, 1)
        off_rebounds = round(sum_stats["off_rebounds"] / games_played, 1)
        opp_def_rebounds = round(sum_stats["def_rebounds"] / games_played, 1)

        row = {"name": "JUSHOOP平均"}
        row["回合数"] = off_rounds
        row["场次"] = games_played
        row["净胜分"] = round((sum_stats["oncourt_scores"] - sum_stats["oncourt_loses"]) / games_played, 1)
        row["得分"] = round(sum_stats["scores"] / games_played, 1)
        row["篮板"] = round(sum_stats["rebounds"] / games_played, 1)
        row["助攻"] = round(sum_stats["assists"] / games_played, 1)
        row["失误"] = round(sum_stats["tos"] / games_played, 1)
        row["前场篮板"] = round(sum_stats["off_rebounds"] / games_played, 1)
        row["后场篮板"] = round(sum_stats["def_rebounds"] / games_played, 1)

        row["两分命中"] = "{}".format(round((made_2) / max(atp_2, 0.001), 3))
        row["三分命中"] = "{}".format(round(made_3 / max(atp_3, 0.001), 3))
        row["罚球命中"] = "{}".format(round(made_ft / max(atp_ft, 0.001), 3))
        self.team_basic_stats_df = append(self.team_basic_stats_df, row)
        self.team_basic_stats_df.set_index('name', inplace=True)
        self.team_basic_stats_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_team_basic_stat.csv"))
        # print(self.team_basic_stats_df)


        row = {"name": "JUSHOOP平均"}

        row["进攻效率"] = round(sum_stats["scores"] / games_played / off_rounds * 100, 2)
        row["防守效率"] = round(sum_stats["scores"] / games_played / def_rounds * 100, 2)

        row["两分命中"] = "{}".format(round((made_2) / max(atp_2, 0.001), 3))
        row["三分命中"] = "{}".format(round(made_3 / max(atp_3, 0.001), 3))
        row["罚球命中"] = "{}".format(round(made_ft / max(atp_ft, 0.001), 3))

        row["3分出手占比"] = "{}".format(round(atp_3 / (atp_2 + atp_3), 3))
        row["3分得分占比"] = "{}".format(round((made_3 * 3) / (made_2 * 2 + made_3 * 3), 3))
        row["助攻得分占比"] = "{}".format(round((assists_2pts * 2 + assists_3pts * 3) / (made_2 * 2 + made_3 * 3), 3))
        row["篮板保护率"] = "{}".format(round(def_rebounds / (opp_off_rebounds + def_rebounds), 3))
        row["前场篮板率"] = "{}".format(round(off_rebounds / (off_rebounds + opp_def_rebounds), 3))
        self.team_adv_stats_df = append(self.team_adv_stats_df, row)
        self.team_adv_stats_df.set_index('name', inplace=True)
        self.team_adv_stats_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_team_advanced_stat.csv"))
        # print(self.team_adv_stats_df)



        # row = {"name": "JUSHOOP平均"}



    def get_team_basic_stat(self):
        # print(11111)
        self.target_team_personal_stats.to_csv(os.path.join(self.target_dir, f"{self.target_team}_sum_stats.csv"))

        # print(self.target_team_personal_stats.columns)
        team_basic_stat_columns = ["场次", "净胜分", "得分", "篮板", "助攻", "抢断", "盖帽", "失误", "两分", "三分", "罚球", "命中", "三分命中", "罚球命中", "前场篮板", "后场篮板", "犯规"]
        self.team_basic_stat_df = pd.DataFrame(columns=team_basic_stat_columns)
        teams = [self.target_team, "{}_opp".format(self.target_team)]
        titles = [self.target_team, "对手"]
        for i in range(2):
            row = {"name": titles[i]}
            games_played = round(self.target_team_personal_stats.loc[teams[i]]["games_played"], 1)
            # rounds_rate = 100. / round(self.target_team_personal_stats.loc[teams[i]]["oncourt_off_rounds"] / games_played, 1)
            rounds_rate = 1
            # print(row)
            # print(self.target_team_personal_stats.loc[teams[i]])
            row["场次"] = self.target_team_personal_stats.loc[teams[i]]["games_played"]
            row["净胜分"] = round((self.target_team_personal_stats.loc[teams[i]]["oncourt_scores"] - self.target_team_personal_stats.loc[teams[i]]["oncourt_loses"]) / games_played, 1)
            row["得分"] = round(self.target_team_personal_stats.loc[teams[i]]["scores"] / games_played * rounds_rate, 1)
            row["篮板"] = round(self.target_team_personal_stats.loc[teams[i]]["rebounds"] / games_played * rounds_rate, 1)
            row["助攻"] = round(self.target_team_personal_stats.loc[teams[i]]["assists"] / games_played * rounds_rate, 1)
            row["抢断"] = round(self.target_team_personal_stats.loc[teams[i]]["steals"] / games_played * rounds_rate, 1)
            row["盖帽"] = round(self.target_team_personal_stats.loc[teams[i]]["blocks"] / games_played * rounds_rate, 1)
            row["失误"] = round(self.target_team_personal_stats.loc[teams[i]]["tos"] / games_played * rounds_rate, 1)
            row["前场篮板"] = round(self.target_team_personal_stats.loc[teams[i]]["off_rebounds"] / games_played * rounds_rate, 1)
            row["后场篮板"] = round(self.target_team_personal_stats.loc[teams[i]]["def_rebounds"] / games_played * rounds_rate, 1)
            row["犯规"] = round(self.target_team_personal_stats.loc[teams[i]]["fouls"] / games_played * rounds_rate, 1)

            made_2 = round(self.target_team_personal_stats.loc[teams[i]]["2pts_mades"] / games_played * rounds_rate, 2)
            made_3 = round(self.target_team_personal_stats.loc[teams[i]]["3pts_mades"] / games_played * rounds_rate, 2)
            made_ft = round(self.target_team_personal_stats.loc[teams[i]]["fts_mades"] / games_played * rounds_rate, 2)
            atp_2 = round(self.target_team_personal_stats.loc[teams[i]]["2pts_atpts"] / games_played * rounds_rate, 2)
            atp_3 = round(self.target_team_personal_stats.loc[teams[i]]["3pts_atpts"] / games_played * rounds_rate, 2)
            atp_ft = round(self.target_team_personal_stats.loc[teams[i]]["fts_atpts"] / games_played * rounds_rate, 2)

            row["两分"] = "{}/{}".format(made_2, atp_2)
            row["三分"] = "{}/{}".format(made_3, atp_3)
            row["罚球"] = "{}/{}".format(made_ft, atp_ft)

            # print(made_2, made_3, atp_2, atp_3)

            row["命中"] = "{}".format(round((made_2 + made_3) / max(atp_2 + atp_3, 0.001), 3))
            row["三分命中"] = "{}".format(round(made_3 / max(atp_3, 0.001), 3))
            row["罚球命中"] = "{}".format(round(made_ft / max(atp_ft, 0.001), 3))
            self.team_basic_stat_df = append(self.team_basic_stat_df, row)
        self.team_basic_stat_df.set_index('name', inplace=True)
        # self.team_basic_stat_df[idx].sort_values(by=["场次"], na_position="last")

        # print(self.team_basic_stat_df)

        self.team_basic_stat_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_team_basic_stat.csv"))

    def get_player_basic_stat(self):
        player_basic_stat_columns = ["出场次数", "上场时间", "得分", "篮板", "助攻", "抢断", "盖帽", "2分", "3分", "罚球", "2分命中", "3分命中", "罚球命中", "失误", "后+前场篮板", "造犯规",
                                     "犯规", "效率值"]

        self.player_basic_stat_df = pd.DataFrame(columns=player_basic_stat_columns)
        all_players = list(self.target_team_personal_stats.index)
        not_players_list = [self.target_team, "{}_opp".format(self.target_team)]
        not_players_list.extend(self.remove_player_list)
        for player in not_players_list:
            if player in all_players:
                all_players.remove(player)


        for player in all_players:
            row = {"name": player}
            games_played = round(self.target_team_personal_stats.loc[player]["games_played"], 1)
            # rounds_rate = 100. / round(self.target_team_personal_stats.loc[player]["oncourt_off_rounds"] / games_played, 1)

            row["出场次数"] = round(self.target_team_personal_stats.loc[player]["games_played"])
            row["上场时间"] = round(
                self.target_team_personal_stats.loc[player]["time"] / 60. / games_played, 1)
            row["得分"] = round(
                self.target_team_personal_stats.loc[player]["scores"] / games_played, 1)
            row["篮板"] = round(
                self.target_team_personal_stats.loc[player]["rebounds"] / games_played, 1)
            row["助攻"] = round(
                self.target_team_personal_stats.loc[player]["assists"] / games_played, 1)
            row["抢断"] = round(
                self.target_team_personal_stats.loc[player]["steals"] / games_played, 1)
            row["盖帽"] = round(
                self.target_team_personal_stats.loc[player]["blocks"] / games_played, 1)
            row["失误"] = round(
                self.target_team_personal_stats.loc[player]["tos"] / games_played, 1)
            row["后+前场篮板"] = "{}+{}".format(round(
                self.target_team_personal_stats.loc[player]["def_rebounds"] / games_played, 1), round(
                self.target_team_personal_stats.loc[player]["off_rebounds"] / games_played, 1))

            row["犯规"] = round(
                self.target_team_personal_stats.loc[player]["fouls"] / games_played, 1)
            row["造犯规"] = round(
                self.target_team_personal_stats.loc[player]["make_fouls"] / games_played, 1)

            made_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_mades"] / games_played, 1)
            made_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_mades"] / games_played, 1)
            made_ft = round(
                self.target_team_personal_stats.loc[player]["fts_mades"] / games_played, 1)
            atp_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_atpts"] / games_played, 1)
            atp_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_atpts"] / games_played, 1)
            atp_ft = round(
                self.target_team_personal_stats.loc[player]["fts_atpts"] / games_played, 1)

            row["2分"] = "{}/{}".format(made_2, atp_2)
            row["3分"] = "{}/{}".format(made_3, atp_3)
            row["罚球"] = "{}/{}".format(made_ft, atp_ft)

            row["2分命中"] = "{}".format(round((made_2) / max(atp_2, 0.001), 3))
            row["3分命中"] = "{}".format(round(made_3 / max(atp_3, 0.001), 3))
            row["罚球命中"] = "{}".format(round(made_ft / max(atp_ft, 0.001), 3))
            row["效率值"] = round((row["得分"] + row["助攻"] + row["篮板"] + row["抢断"] + row["盖帽"] - (
                    atp_3 + atp_2 + atp_ft - made_3 - made_2 - made_ft) - row["失误"]), 1)

            self.player_basic_stat_df = append(self.player_basic_stat_df, row)
        self.player_basic_stat_df.set_index('name', inplace=True)
        self.player_basic_stat_df = self.player_basic_stat_df.sort_values(by=["得分"], na_position="last", ascending=False)
        self.player_basic_stat_df = self.player_basic_stat_df[self.player_basic_stat_df["出场次数"] >= self.num_games_to_keep]

        print(self.player_basic_stat_df)

        self.player_basic_stat_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_player_basic_stat.csv"))



    def get_team_advanced_stat(self):
        team_advanced_stat_columns = ["进攻节奏", "进攻效率", "防守效率", "3分出手占比", "3分得分占比", "助攻得分占比", "篮板保护率", "前场篮板率"]
        self.team_advances_stat_df = pd.DataFrame(columns=team_advanced_stat_columns)

        teams = [self.target_team, "{}_opp".format(self.target_team)]
        titles = [self.target_team, "对手"]
        for i in range(2):
            row = {"name": titles[i]}
            games_played = round(self.target_team_personal_stats.loc[teams[i]]["games_played"], 3)
            off_rounds = round(self.target_team_personal_stats.loc[teams[i]]["oncourt_off_rounds"] / games_played, 2)
            def_rounds = round(self.target_team_personal_stats.loc[teams[i]]["oncourt_def_rounds"] / games_played, 2)


            row["进攻节奏"] = off_rounds
            row["进攻效率"] = round(self.target_team_personal_stats.loc[teams[i]]["scores"] / games_played / off_rounds * 100, 2)
            row["防守效率"] = round(self.target_team_personal_stats.loc[teams[1-i]]["scores"] / games_played / def_rounds * 100, 2)

            made_2 = round(
                self.target_team_personal_stats.loc[teams[i]]["2pts_mades"] / games_played, 2)
            made_3 = round(
                self.target_team_personal_stats.loc[teams[i]]["3pts_mades"] / games_played, 2)
            made_ft = round(
                self.target_team_personal_stats.loc[teams[i]]["fts_mades"] / games_played, 2)
            atp_2 = round(
                self.target_team_personal_stats.loc[teams[i]]["2pts_atpts"] / games_played, 2)
            atp_3 = round(
                self.target_team_personal_stats.loc[teams[i]]["3pts_atpts"] / games_played, 2)
            atp_ft = round(
                self.target_team_personal_stats.loc[teams[i]]["fts_atpts"] / games_played, 2)

            assists_2pts = round(
                self.target_team_personal_stats.loc[teams[i]]["assists_2pts"] / games_played, 2)

            assists_3pts = round(
                self.target_team_personal_stats.loc[teams[i]]["assists_3pts"] / games_played, 2)

            def_rebounds = round(
                self.target_team_personal_stats.loc[teams[i]]["def_rebounds"] / games_played, 2)

            opp_def_rebounds = round(
                self.target_team_personal_stats.loc[teams[1-i]]["def_rebounds"] / games_played, 2)

            off_rebounds = round(
                self.target_team_personal_stats.loc[teams[i]]["off_rebounds"] / games_played, 2)

            opp_off_rebounds = round(
                self.target_team_personal_stats.loc[teams[1-i]]["off_rebounds"] / games_played, 2)


            row["3分出手占比"] = "{}".format(round(atp_3 / (atp_2 + atp_3), 3))
            row["3分得分占比"] = "{}".format(round((made_3 * 3) / (made_2 * 2 + made_3 * 3), 3))
            row["助攻得分占比"] = "{}".format(round((assists_2pts * 2 + assists_3pts * 3) / (made_2 * 2 + made_3 * 3), 3))
            row["篮板保护率"] = "{}".format(round(def_rebounds / (opp_off_rebounds + def_rebounds), 3))
            row["前场篮板率"] = "{}".format(round(off_rebounds / (off_rebounds + opp_def_rebounds), 3))



            self.team_advances_stat_df = append(self.team_advances_stat_df, row)
        self.team_advances_stat_df.set_index('name', inplace=True)

        # print(self.team_advances_stat_df)
        self.team_advances_stat_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_team_advanced_stat.csv"))

    def get_player_score_stat(self):
        player_score_stat_columns = ["得分", "真实命中", "出手次数", "出场次数"]

        self.player_score_stat_df = pd.DataFrame(columns=player_score_stat_columns)
        all_players = list(self.target_team_personal_stats.index)
        not_players_list = [self.target_team, "{}_opp".format(self.target_team)]
        not_players_list.extend(self.remove_player_list)
        for player in not_players_list:
            if player in all_players:
                all_players.remove(player)

        # print(all_players)
        for player in all_players:
            row = {"name": player}
            games_played = round(self.target_team_personal_stats.loc[player]["games_played"], 1)
            # rounds_rate = 100. / round(self.target_team_personal_stats.loc[player]["oncourt_off_rounds"] / games_played, 1)
            row["出场次数"] = self.target_team_personal_stats.loc[player]["games_played"]
            time = round(self.target_team_personal_stats.loc[player]["time"] / 60. / games_played, 1)

            made_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_mades"] / games_played, 2)
            made_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_mades"] / games_played, 2)
            made_ft = round(
                self.target_team_personal_stats.loc[player]["fts_mades"] / games_played, 2)
            atp_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_atpts"] / games_played, 2)
            atp_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_atpts"] / games_played, 2)
            atp_ft = round(
                self.target_team_personal_stats.loc[player]["fts_atpts"] / games_played, 2)
            scores = round(
                self.target_team_personal_stats.loc[player]["scores"] / games_played, 2)

            row["得分"] = round(
                self.target_team_personal_stats.loc[player]["scores"] / games_played, 1)

            row["真实命中"] = round(scores / (2 * max(atp_2 + atp_3 + 0.44 * atp_ft, 0.001)), 2)

            # row["出场时间"] = round(
            #     self.target_team_personal_stats.loc[player]["time"] / 60. / games_played, 1)
            row["出手次数"] = round(atp_2 + atp_3, 3)



            self.player_score_stat_df = append(self.player_score_stat_df, row)
        # print(self.player_score_stat_df)
        self.player_score_stat_df.set_index('name', inplace=True)
        self.player_score_stat_df = self.player_score_stat_df.sort_values(by=["出场次数"], na_position="last", ascending=False)
        # print(self.player_basic_stat_df)
        self.player_score_stat_df = self.player_score_stat_df[self.player_score_stat_df["出场次数"] >= self.num_games_to_keep]
        self.player_score_stat_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_score.csv"))


    def get_player_team_spirit_stat(self):
        player_team_spirit_stat_columns = ["进攻效率", "防守效率", "出场时间", "出场次数"]

        self.player_team_spirit_stat_df = pd.DataFrame(columns=player_team_spirit_stat_columns)
        all_players = list(self.target_team_personal_stats.index)
        not_players_list = [self.target_team, "{}_opp".format(self.target_team)]
        not_players_list.extend(self.remove_player_list)
        for player in not_players_list:
            if player in all_players:
                all_players.remove(player)

        # print(all_players)
        for player in all_players:
            row = {"name": player}
            games_played = round(self.target_team_personal_stats.loc[player]["games_played"], 1)
            # rounds_rate = 100. / round(self.target_team_personal_stats.loc[player]["oncourt_off_rounds"] / games_played, 1)
            row["出场次数"] = self.target_team_personal_stats.loc[player]["games_played"]
            time = round(self.target_team_personal_stats.loc[player]["time"] / 60. / games_played, 1)

            made_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_mades"] / games_played, 2)
            made_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_mades"] / games_played, 2)
            made_ft = round(
                self.target_team_personal_stats.loc[player]["fts_mades"] / games_played, 2)
            atp_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_atpts"] / games_played, 2)
            atp_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_atpts"] / games_played, 2)
            atp_ft = round(
                self.target_team_personal_stats.loc[player]["fts_atpts"] / games_played, 2)
            scores = round(
                self.target_team_personal_stats.loc[player]["scores"] / games_played, 2)


            row["进攻效率"] = round(self.target_team_personal_stats.loc[player]["oncourt_scores"] / max(
                    self.target_team_personal_stats.loc[player]["oncourt_off_rounds"], 0.001) * 100, 2)
            row["防守效率"] = round(self.target_team_personal_stats.loc[player]["oncourt_loses"] / max(
                    self.target_team_personal_stats.loc[player]["oncourt_def_rounds"], 0.001) * 100, 2)

            row["出场时间"] = round(
                self.target_team_personal_stats.loc[player]["time"] / 60. / games_played, 1)



            self.player_team_spirit_stat_df = append(self.player_team_spirit_stat_df, row)
        # print(self.player_score_stat_df)
        self.player_team_spirit_stat_df.set_index('name', inplace=True)
        self.player_team_spirit_stat_df = self.player_team_spirit_stat_df.sort_values(by=["出场次数"], na_position="last", ascending=False)
        # print(self.player_basic_stat_df)
        self.player_team_spirit_stat_df = self.player_team_spirit_stat_df[self.player_team_spirit_stat_df["出场次数"] >= self.num_games_to_keep]
        self.player_team_spirit_stat_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_team_spirit.csv"))


    def get_player_offense_options_stat(self):
        player_offense_options_stat_columns = ["三分占比", "受助攻率", "真实命中", "出场次数"]

        self.player_offense_options_stat_df = pd.DataFrame(columns=player_offense_options_stat_columns)
        all_players = list(self.target_team_personal_stats.index)
        not_players_list = [self.target_team, "{}_opp".format(self.target_team)]
        not_players_list.extend(self.remove_player_list)
        for player in not_players_list:
            if player in all_players:
                all_players.remove(player)

        # print(all_players)
        for player in all_players:
            row = {"name": player}
            games_played = round(self.target_team_personal_stats.loc[player]["games_played"], 1)
            # rounds_rate = 100. / round(self.target_team_personal_stats.loc[player]["oncourt_off_rounds"] / games_played, 1)
            row["出场次数"] = self.target_team_personal_stats.loc[player]["games_played"]
            time = round(self.target_team_personal_stats.loc[player]["time"] / 60. / games_played, 1)

            made_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_mades"] / games_played, 2)
            made_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_mades"] / games_played, 2)
            made_ft = round(
                self.target_team_personal_stats.loc[player]["fts_mades"] / games_played, 2)
            atp_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_atpts"] / games_played, 2)
            atp_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_atpts"] / games_played, 2)
            atp_ft = round(
                self.target_team_personal_stats.loc[player]["fts_atpts"] / games_played, 2)
            scores = round(
                self.target_team_personal_stats.loc[player]["scores"] / games_played, 2)


            row["受助攻率"] = round(self.target_team_personal_stats.loc[player]["assisted"] / max(
                    self.target_team_personal_stats.loc[player]["mades"], 0.001), 2)

            row["三分占比"] = round(made_3 * 3 / (scores + 0.0001), 2)
            row["真实命中"] = round(scores / (2 * max(atp_2 + atp_3 + 0.44 * atp_ft, 0.001)), 2)



            self.player_offense_options_stat_df = append(self.player_offense_options_stat_df, row)
        # print(self.player_score_stat_df)
        self.player_offense_options_stat_df.set_index('name', inplace=True)
        self.player_offense_options_stat_df = self.player_offense_options_stat_df.sort_values(by=["出场次数"], na_position="last", ascending=False)
        # print(self.player_basic_stat_df)
        self.player_offense_options_stat_df = self.player_offense_options_stat_df[self.player_offense_options_stat_df["出场次数"] >= self.num_games_to_keep]
        self.player_offense_options_stat_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_offense_options.csv"))


    def get_player_rebound_feat_stat(self):
        player_offense_rebound_feat_columns = ["在场篮板率", "每分钟篮板数", "场均篮板", "出场次数"]

        self.player_rebound_feat_stat_df = pd.DataFrame(columns=player_offense_rebound_feat_columns)
        all_players = list(self.target_team_personal_stats.index)
        not_players_list = [self.target_team, "{}_opp".format(self.target_team)]
        not_players_list.extend(self.remove_player_list)
        for player in not_players_list:
            if player in all_players:
                all_players.remove(player)

        # print(all_players)
        for player in all_players:
            row = {"name": player}
            games_played = round(self.target_team_personal_stats.loc[player]["games_played"], 1)
            # rounds_rate = 100. / round(self.target_team_personal_stats.loc[player]["oncourt_off_rounds"] / games_played, 1)
            row["出场次数"] = self.target_team_personal_stats.loc[player]["games_played"]
            time = round(self.target_team_personal_stats.loc[player]["time"] / 60., 1)

            made_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_mades"] / games_played, 2)
            made_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_mades"] / games_played, 2)
            made_ft = round(
                self.target_team_personal_stats.loc[player]["fts_mades"] / games_played, 2)
            atp_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_atpts"] / games_played, 2)
            atp_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_atpts"] / games_played, 2)
            atp_ft = round(
                self.target_team_personal_stats.loc[player]["fts_atpts"] / games_played, 2)
            scores = round(
                self.target_team_personal_stats.loc[player]["scores"] / games_played, 2)



            row["在场篮板率"] = round(1 / (1 + self.target_team_personal_stats.loc[player]["oncourt_opponent_rebounds"] / (
                    self.target_team_personal_stats.loc[player]["oncourt_team_rebounds"] + 0.0001)), 2)

            row["每分钟篮板数"] = round(self.target_team_personal_stats.loc[player]["rebounds"] / time, 2)
            row["场均篮板"] = round(self.target_team_personal_stats.loc[player]["rebounds"] / games_played, 2)



            self.player_rebound_feat_stat_df = append(self.player_rebound_feat_stat_df, row)
        # print(self.player_score_stat_df)
        self.player_rebound_feat_stat_df.set_index('name', inplace=True)
        self.player_rebound_feat_stat_df = self.player_rebound_feat_stat_df.sort_values(by=["出场次数"], na_position="last", ascending=False)
        # print(self.player_basic_stat_df)
        self.player_rebound_feat_stat_df = self.player_rebound_feat_stat_df[self.player_rebound_feat_stat_df["出场次数"] >= self.num_games_to_keep]
        self.player_rebound_feat_stat_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_rebound_feat.csv"))



    def get_team_advanced_stat_VS_AVG_VS_OPPONENT(self):
        team_advanced_stat_VS_AVG_VS_OPPONENT_columns = ["净胜分", "得分", "篮板", "助攻", "失误", "回合数", "两分命中", "三分命中", "前场篮板", "后场篮板"]

        self.team_advanced_stat_VS_AVG_VS_OPPONENT_df = pd.DataFrame(columns=team_advanced_stat_VS_AVG_VS_OPPONENT_columns)

        jushoop = pd.Series([0.0, 73.5, 37.0, 13.3, 12.6, 69.9, 0.455, 0.276, 11.8, 25.1],
                         index=team_advanced_stat_VS_AVG_VS_OPPONENT_columns)
        jushoop["name"] = "JUSHOOP平均"


        self.team_advanced_stat_VS_AVG_VS_OPPONENT_df = append(self.team_advanced_stat_VS_AVG_VS_OPPONENT_df, jushoop)
        # print(self.team_advanced_stat_VS_AVG_VS_OPPONENT_df)

        teams = [self.target_team, "{}_opp".format(self.target_team)]
        titles = [self.target_team, "对手"]
        for i in range(2):
            row = {"name": titles[i]}
            games_played = round(self.target_team_personal_stats.loc[teams[i]]["games_played"], 3)
            off_rounds = round(self.target_team_personal_stats.loc[teams[i]]["oncourt_off_rounds"] / games_played, 2)
            def_rounds = round(self.target_team_personal_stats.loc[teams[i]]["oncourt_def_rounds"] / games_played, 2)

            made_2 = round(
                self.target_team_personal_stats.loc[teams[i]]["2pts_mades"] / games_played, 2)
            made_3 = round(
                self.target_team_personal_stats.loc[teams[i]]["3pts_mades"] / games_played, 2)
            made_ft = round(
                self.target_team_personal_stats.loc[teams[i]]["fts_mades"] / games_played, 2)
            atp_2 = round(
                self.target_team_personal_stats.loc[teams[i]]["2pts_atpts"] / games_played, 2)
            atp_3 = round(
                self.target_team_personal_stats.loc[teams[i]]["3pts_atpts"] / games_played, 2)
            atp_ft = round(
                self.target_team_personal_stats.loc[teams[i]]["fts_atpts"] / games_played, 2)

            row["回合数"] = off_rounds
            row["净胜分"] = round((self.target_team_personal_stats.loc[teams[i]]["oncourt_scores"] - self.target_team_personal_stats.loc[teams[i]]["oncourt_loses"]) / games_played, 1)
            row["得分"] = round(self.target_team_personal_stats.loc[teams[i]]["scores"] / games_played, 1)
            row["篮板"] = round(self.target_team_personal_stats.loc[teams[i]]["rebounds"] / games_played, 1)
            row["助攻"] = round(self.target_team_personal_stats.loc[teams[i]]["assists"] / games_played, 1)
            row["失误"] = round(self.target_team_personal_stats.loc[teams[i]]["tos"] / games_played, 1)
            row["前场篮板"] = round(self.target_team_personal_stats.loc[teams[i]]["off_rebounds"] / games_played, 1)
            row["后场篮板"] = round(self.target_team_personal_stats.loc[teams[i]]["def_rebounds"] / games_played, 1)

            row["两分命中"] = "{}".format(round((made_2) / max(atp_2, 0.001), 3))
            row["三分命中"] = "{}".format(round(made_3 / max(atp_3, 0.001), 3))



            self.team_advanced_stat_VS_AVG_VS_OPPONENT_df = append(self.team_advanced_stat_VS_AVG_VS_OPPONENT_df, row)
        self.team_advanced_stat_VS_AVG_VS_OPPONENT_df.set_index('name', inplace=True)

        # print(self.team_advanced_stat_VS_AVG_VS_OPPONENT_df)
        self.team_advanced_stat_VS_AVG_VS_OPPONENT_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_OPPONENT.csv"))


    def get_team_advanced_stat_VS_AVG_VS_PROS(self):
        team_advanced_stat_VS_AVG_VS_PROS_columns = ["进攻效率", "防守效率", "3分出手占比", "3分得分占比", "助攻得分占比","两分命中", "三分命中", "罚球命中", "篮板保护率", "前场篮板率"]
        # init_data = {
        #     "NBA平均": [110, 110, 0.38, 0.36, 0.62, 0.55, 0.36, 0.78, 0.71, 0.29],
        #     "JUSHOOP平均": [93.11, 93.11, 0.35, 0.33, 0.66, 0.46, 0.27, 0.56, 0.72, 0.28]
        # }
        self.team_advanced_stat_VS_AVG_VS_PROS_df = pd.DataFrame(columns=team_advanced_stat_VS_AVG_VS_PROS_columns)

        pros = pd.Series([110, 110, 0.38, 0.36, 0.62, 0.55, 0.36, 0.78, 0.71, 0.29],
                         index=team_advanced_stat_VS_AVG_VS_PROS_columns)
        jushoop = pd.Series([104.9, 104.9, 0.32, 0.30, 0.51, 0.46, 0.28, 0.63, 0.68, 0.32],
                         index=team_advanced_stat_VS_AVG_VS_PROS_columns)
        pros["name"] = "NBA平均"
        jushoop["name"] = "JUSHOOP平均"


        self.team_advanced_stat_VS_AVG_VS_PROS_df = append(self.team_advanced_stat_VS_AVG_VS_PROS_df, pros)
        self.team_advanced_stat_VS_AVG_VS_PROS_df = append(self.team_advanced_stat_VS_AVG_VS_PROS_df, jushoop)
        # print(self.team_advanced_stat_VS_AVG_VS_PROS_df)

        teams = [self.target_team, "{}_opp".format(self.target_team)]
        titles = [self.target_team, "对手"]
        for i in range(2):
            row = {"name": titles[i]}
            games_played = round(self.target_team_personal_stats.loc[teams[i]]["games_played"], 3)
            off_rounds = round(self.target_team_personal_stats.loc[teams[i]]["oncourt_off_rounds"] / games_played, 2)
            def_rounds = round(self.target_team_personal_stats.loc[teams[i]]["oncourt_def_rounds"] / games_played, 2)


            row["进攻效率"] = round(self.target_team_personal_stats.loc[teams[i]]["scores"] / games_played / off_rounds * 100, 2)
            row["防守效率"] = round(self.target_team_personal_stats.loc[teams[1-i]]["scores"] / games_played / def_rounds * 100, 2)

            made_2 = round(
                self.target_team_personal_stats.loc[teams[i]]["2pts_mades"] / games_played, 2)
            made_3 = round(
                self.target_team_personal_stats.loc[teams[i]]["3pts_mades"] / games_played, 2)
            made_ft = round(
                self.target_team_personal_stats.loc[teams[i]]["fts_mades"] / games_played, 2)
            atp_2 = round(
                self.target_team_personal_stats.loc[teams[i]]["2pts_atpts"] / games_played, 2)
            atp_3 = round(
                self.target_team_personal_stats.loc[teams[i]]["3pts_atpts"] / games_played, 2)
            atp_ft = round(
                self.target_team_personal_stats.loc[teams[i]]["fts_atpts"] / games_played, 2)

            assists_2pts = round(
                self.target_team_personal_stats.loc[teams[i]]["assists_2pts"] / games_played, 2)

            assists_3pts = round(
                self.target_team_personal_stats.loc[teams[i]]["assists_3pts"] / games_played, 2)

            def_rebounds = round(
                self.target_team_personal_stats.loc[teams[i]]["def_rebounds"] / games_played, 2)

            opp_def_rebounds = round(
                self.target_team_personal_stats.loc[teams[1-i]]["def_rebounds"] / games_played, 2)

            off_rebounds = round(
                self.target_team_personal_stats.loc[teams[i]]["off_rebounds"] / games_played, 2)

            opp_off_rebounds = round(
                self.target_team_personal_stats.loc[teams[1-i]]["off_rebounds"] / games_played, 2)
            row["两分命中"] = "{}".format(round((made_2) / max(atp_2, 0.001), 3))
            row["三分命中"] = "{}".format(round(made_3 / max(atp_3, 0.001), 3))
            row["罚球命中"] = "{}".format(round(made_ft / max(atp_ft, 0.001), 3))

            row["3分出手占比"] = "{}".format(round(atp_3 / (atp_2 + atp_3), 3))
            row["3分得分占比"] = "{}".format(round((made_3 * 3) / (made_2 * 2 + made_3 * 3), 3))
            row["助攻得分占比"] = "{}".format(round((assists_2pts * 2 + assists_3pts * 3) / (made_2 * 2 + made_3 * 3), 3))
            row["篮板保护率"] = "{}".format(round(def_rebounds / (opp_off_rebounds + def_rebounds), 3))
            row["前场篮板率"] = "{}".format(round(off_rebounds / (off_rebounds + opp_def_rebounds), 3))



            self.team_advanced_stat_VS_AVG_VS_PROS_df = append(self.team_advanced_stat_VS_AVG_VS_PROS_df, row)
        self.team_advanced_stat_VS_AVG_VS_PROS_df.set_index('name', inplace=True)

        # print(self.team_advanced_stat_VS_AVG_VS_PROS_df)
        self.team_advanced_stat_VS_AVG_VS_PROS_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_PRO.csv"))


    def get_player_advanced_stat(self):
        player_advanced_stat_columns = ["出场次数","效率值", "正负值", "真实命中", "回合占有率", "受助攻率", "助攻失误比", "在场篮板率", "进攻效率", "防守效率"]
        self.player_advances_stat_df = pd.DataFrame(columns=player_advanced_stat_columns)
        all_players = list(self.target_team_personal_stats.index)
        not_players_list = [self.target_team, "{}_opp".format(self.target_team)]
        not_players_list.extend(self.remove_player_list)
        for player in not_players_list:
            if player in all_players:
                all_players.remove(player)

        for player in all_players:
            row = {"name": player}
            games_played = int(self.target_team_personal_stats.loc[player]["games_played"])
            # rounds_rate = 100. / round(self.target_team_personal_stats.loc[player]["oncourt_off_rounds"] / games_played, 1)

            row["出场次数"] = games_played

            scores = round(
                self.target_team_personal_stats.loc[player]["scores"] / games_played, 2)
            assists = round(
                self.target_team_personal_stats.loc[player]["assists"] / games_played, 2)
            rebounds = round(
                self.target_team_personal_stats.loc[player]["rebounds"] / games_played, 2)
            steals = round(
                self.target_team_personal_stats.loc[player]["steals"] / games_played, 2)
            blocks = round(
                self.target_team_personal_stats.loc[player]["blocks"] / games_played, 2)
            tos = round(
                self.target_team_personal_stats.loc[player]["tos"] / games_played, 2)



            made_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_mades"] / games_played, 2)
            made_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_mades"] / games_played, 2)
            made_ft = round(
                self.target_team_personal_stats.loc[player]["fts_mades"] / games_played, 2)
            atp_2 = round(
                self.target_team_personal_stats.loc[player]["2pts_atpts"] / games_played, 2)
            atp_3 = round(
                self.target_team_personal_stats.loc[player]["3pts_atpts"] / games_played, 2)
            atp_ft = round(
                self.target_team_personal_stats.loc[player]["fts_atpts"] / games_played, )

            row["效率值"] = round((scores + assists + rebounds + steals + blocks - (atp_3 + atp_2 + atp_ft - made_3 - made_2 - made_ft) - tos), 1)
            row["正负值"] = round((self.target_team_personal_stats.loc[player]["oncourt_scores"] - self.target_team_personal_stats.loc[player]["oncourt_loses"]) / games_played, 1)
            row["回合占有率"] = round(self.target_team_personal_stats.loc[player]["used_rounds"] / max(self.target_team_personal_stats.loc[player]["oncourt_off_rounds"], 0.001), 2)
            row["助攻失误比"] = round(self.target_team_personal_stats.loc[player]["assists"] / max(self.target_team_personal_stats.loc[player]["tos"], 0.1), 2)
            row["受助攻率"] = round(self.target_team_personal_stats.loc[player]["assisted"] / max(self.target_team_personal_stats.loc[player]["mades"], 0.001), 2)
            row["真实命中"] = "{}".format(round(scores / (2 * max(atp_2 + atp_3 + 0.44 * atp_ft, 0.001)), 2))
            row["在场篮板率"] = round(1 / (1 + self.target_team_personal_stats.loc[player]["oncourt_opponent_rebounds"] / (self.target_team_personal_stats.loc[player]["oncourt_team_rebounds"] + 0.0001)), 2)
            row["进攻效率"] = round(self.target_team_personal_stats.loc[player]["oncourt_scores"] / max(self.target_team_personal_stats.loc[player]["oncourt_off_rounds"], 0.001) * 100, 2)
            row["防守效率"] = round(self.target_team_personal_stats.loc[player]["oncourt_loses"] / max(self.target_team_personal_stats.loc[player]["oncourt_def_rounds"], 0.001) * 100, 2)


            self.player_advances_stat_df = append(self.player_advances_stat_df, row)
        self.player_advances_stat_df.set_index('name', inplace=True)
        self.player_advances_stat_df = self.player_advances_stat_df.sort_values(by=["效率值"], na_position="last",
                                                                                    ascending=False)
        self.player_advances_stat_df = self.player_advances_stat_df[self.player_advances_stat_df["出场次数"] >= self.num_games_to_keep]
        # self.player_advances_stat_df[idx].drop("出场次数")

        # print(self.player_advances_stat_df)
        self.player_advances_stat_df.to_csv(os.path.join(self.target_dir, f"{self.target_team}_player_advanced_stat.csv"))



class TeamAvgStatsModel(BaseStatsModel):
    match_type = "友谊赛"
    max_teams = 2
    JUSHOOP_title_txt = "JUSHOOP全场友谊赛"

    same_team = False

    check_team = True
    def __init__(self, event_data, config):
        super().__init__(event_data, config)
        self.target_stats = ["scores", "assists", "rebounds", "off_rebounds",
                             "def_rebounds", "blocks", "steals", "time",
                             "oncourt_off_rounds", "oncourt_def_rounds", "atpts",
                             "mades", "3pts_atpts", "fts_atpts", "2pts_atpts",
                             "3pts_mades", "fts_mades", "2pts_mades", "tos", "fouls",
                             "make_fouls", "oncourt_scores", "oncourt_loses",
                            "assisted", "assists_2pts", "assists_3pts", "oncourt_team_rebounds",
                             "oncourt_opponent_rebounds", "used_rounds", "games_played"]


    def get_team_names(self):
        origin_team_names = self.config['match_name'].split("_")[1:]
        self.team_names = get_teams_from_game_name(self.config['match_name'])
        
        if not self.team_names[0] == origin_team_names[0]:
            self.event_data = self.event_data.replace(origin_team_names[0], self.team_names[0])
        if not self.team_names[1] == origin_team_names[1]:
            if self.team_names[1] == self.team_names[0]:
                tmp_name = f"{self.team_names[1]}_tmp_name_postfix"
                self.team_names[1] = tmp_name
                self.same_team = True
            self.event_data = self.event_data.replace(origin_team_names[1], self.team_names[1])



    def get_team_stats(self):
        """只球队数据"""
        self.get_stat_item_dfs()
        columns = [stat_item for stat_item in self.target_stats]
        self.player_stats = [pd.DataFrame(columns=columns) for i in range(2)]
        for i, team in enumerate(self.team_names):
            row = {"name": team}
            for stat_item in self.target_stats:
                value = eval("self.get_team_{}('{}', {})".format(stat_item, team, i))
                row[stat_item] = value
            self.player_stats[i] = append(self.player_stats[i], row)

        self.player_stats[0].set_index('name', inplace = True)
        self.player_stats[1].set_index('name', inplace = True)
        scores = self.get_total_scores()
        win_id = scores.index(max(scores))
        self.player_stats[win_id]["games_wined"] = 1
        self.player_stats[1-win_id]["games_wined"] = 0
        self.scores = scores



    def get_stats(self):
        self.get_stat_item_dfs()
        columns = [stat_item for stat_item in self.target_stats]
        self.player_stats = [pd.DataFrame(columns=columns) for i in range(2)]
        for i, team in enumerate(self.team_names):
            for name in self.player_names[i]:
                row = {"name":process_name(name, team)}
                for stat_item in self.target_stats:
                    value = eval("self.get_{}('{}', {})".format(stat_item, name, i))
                    row[stat_item] = value
                # print(row)
                self.player_stats[i] = append(self.player_stats[i], row)

        for i, team in enumerate(self.team_names):
            row = {"name": team}
            if "tmp_name_postfix" in team:
                row["name"] = team.split("_tmp")[0]
            for stat_item in self.target_stats:
                value = eval("self.get_team_{}('{}', {})".format(stat_item, team, i))
                row[stat_item] = value
            

            self.player_stats[i] = append(self.player_stats[i], row)


            row["name"] = "{}_opp".format(self.team_names[1-i])
            if "tmp_name_postfix" in self.team_names[1-i]:
                new_name = self.team_names[1-i].split("_tmp")[0]
                row["name"] = f"{new_name}_opp"
            self.player_stats[1-i] = append(self.player_stats[i-1], row)

            # print(self.player_stats)

        self.player_stats[0].set_index('name', inplace = True)
        self.player_stats[1].set_index('name', inplace = True)
        scores = self.get_total_scores()
        self.scores = scores

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

        return time



    def get_team_scores(self, team, team_id):
        scores = 0
        scores_df = self.df_query(Event="scores", Team=team)
        assisted_df = self.df_query(Event="assists", Team=team)

        scores += len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(scores_df[scores_df.Event == "2分球出手"]) * 2 + len(scores_df[scores_df.Event == "罚球出手"])
        scores += len(assisted_df[assisted_df.Info == "3分"]) * 3 + len(assisted_df[assisted_df.Info == "2分"]) * 2

        return scores
    

    def get_team_assists(self, team, team_id):
        assists_df = self.df_query(Event="assists", Team=team)
        return len(assists_df)

    def get_team_rebounds(self, team, team_id):
        rebounds_df = self.df_query(Event="rebounds", Team=team)
        return len(rebounds_df)

    def get_team_off_rebounds(self, team, team_id):
        off_rebound_df = self.df_query(Event="rebounds", Team=team, Info="前场")
        return len(off_rebound_df)


    def get_team_def_rebounds(self, team, team_id):
        def_rebound_df = self.df_query(Event="rebounds", Team=team, Info="后场")
        return len(def_rebound_df)


    def get_team_blocks(self, team, team_id):
        block_df = self.df_query(Event="blocks", Team=team)
        return len(block_df)


    def get_team_steals(self, team, team_id):
        steal_df = self.df_query(Event="steals", Team=team)
        return len(steal_df)

    def get_team_time(self, team, team_id):
        return self.quarter_time * self.quarters

    def get_team_oncourt_off_rounds(self, team, team_id):
        team_op = self.team_names[1-team_id]
        stealed_rounds = len(
            self.event_data[(self.event_data.Team == team_op) & (self.event_data.Event == "抢断")])
        off_foul_rounds = len(
            self.event_data[(self.event_data.Team == team) & (self.event_data.Info == "进攻犯规")]) + len(
            self.event_data[(self.event_data.Team == team) & (self.event_data.Info == "违体进攻犯规")])
        scored_rounds = len(
            self.event_data[(self.event_data.Team == team) & (self.event_data.Info == "进球")]) + len(
            self.event_data[(self.event_data.Team == team) & (self.event_data.Event == "助攻")]) - len(
            self.event_data[(self.event_data.Team == team) & (self.event_data.Info == "进球") & (
                    self.event_data.Event == "罚球出手")])
        TO_rounds = len(
            self.event_data[(self.event_data.Team == team) & (self.event_data.Event == "失误")])
        def_rebounded_rounds = len(
            self.event_data[(self.event_data.Team == team_op) & (self.event_data.Info == "后场")])
        fouled_rounds = len(self.event_data[(self.event_data.Team == team_op) & (
                self.event_data.Info == "普通犯规犯满")]) + len(
            self.event_data[(self.event_data.Team == team_op) & (self.event_data.Info == "投篮犯规")])

        return stealed_rounds + off_foul_rounds + scored_rounds + TO_rounds + def_rebounded_rounds + fouled_rounds

    def get_team_oncourt_def_rounds(self, team, team_id):
        team_op = self.team_names[1 - team_id]
        stealed_rounds = len(
            self.event_data[(self.event_data.Team == team) & (self.event_data.Event == "抢断")])
        off_foul_rounds = len(
            self.event_data[(self.event_data.Team == team_op) & (self.event_data.Info == "进攻犯规")]) + len(
            self.event_data[(self.event_data.Team == team_op) & (self.event_data.Info == "违体进攻犯规")])
        scored_rounds = len(
            self.event_data[(self.event_data.Team == team_op) & (self.event_data.Info == "进球")]) + len(
            self.event_data[(self.event_data.Team == team_op) & (self.event_data.Event == "助攻")]) - len(
            self.event_data[(self.event_data.Team == team_op) & (self.event_data.Info == "进球") & (
                    self.event_data.Event == "罚球出手")])
        TO_rounds = len(
            self.event_data[(self.event_data.Team == team_op) & (self.event_data.Event == "失误")])
        def_rebounded_rounds = len(
            self.event_data[(self.event_data.Team == team) & (self.event_data.Info == "后场")])
        fouled_rounds = len(self.event_data[(self.event_data.Team == team) & (
                self.event_data.Info == "普通犯规犯满")]) + len(
            self.event_data[(self.event_data.Team == team) & (self.event_data.Info == "投篮犯规")])


        # print(stealed_rounds, off_foul_rounds, scored_rounds, TO_rounds, def_rebounded_rounds, fouled_rounds)
        return stealed_rounds + off_foul_rounds + scored_rounds + TO_rounds + def_rebounded_rounds + fouled_rounds


    def get_team_atpts(self, team, team_id):
        team_op = self.team_names[1 - team_id]
        twopts_atpt_df = self.df_query(Event="twopts_atpt", Team=team)
        assisted_df = self.df_query(Event="assists", Team=team)
        blocked_df = self.df_query(Event="blocks", Team=team_op)
        return len(twopts_atpt_df) + len(assisted_df) + len(blocked_df)


    def get_team_mades(self, team, team_id):
        twopts_made_df = self.df_query(Event="twopts_atpt", Team=team, Info="进球")
        threepts_made_df = self.df_query(Event="threepts_atpt", Team=team, Info="进球")
        assisted_df = self.df_query(Event="assists", Team=team)

        return len(twopts_made_df) + len(threepts_made_df) + len(assisted_df)


    def get_team_3pts_atpts(self, team, team_id):
        team_op = self.team_names[1 - team_id]
        threepts_atpt_df = self.df_query(Event="threepts_atpt", Team=team)
        assisted_df = self.df_query(Event="assists", Team=team, Info="3分")
        blocked_df = self.df_query(Event="blocks", Team=team_op, Info="3分")
        return len(threepts_atpt_df) + len(assisted_df) + len(blocked_df)


    def get_team_fts_atpts(self, team, team_id):
        fts_atpt_df = self.df_query(Event="fts_atpt", Team=team)
        return len(fts_atpt_df)
    


    def get_team_2pts_atpts(self, team, team_id):
        team_op = self.team_names[1 - team_id]
        twopts_atpt_df = self.df_query(Event="twopts_atpt", Team=team)
        assisted_df = self.df_query(Event="assists", Team=team, Info="2分")
        blocked_df = self.df_query(Event="blocks", Team=team_op, Info="2分")
        return len(twopts_atpt_df) + len(assisted_df) + len(blocked_df)


    def get_team_3pts_mades(self, team, team_id):
        threepts_made_df = self.df_query(Event="threepts_atpt", Team=team, Info="进球")
        assisted_df = self.df_query(Event="assists", Team=team, Info="3分")

        return len(threepts_made_df) + len(assisted_df)


    def get_team_fts_mades(self, team, team_id):
        fts_made_df = self.df_query(Event="fts_atpt", Team=team, Info="进球")
        return len(fts_made_df)

    def get_team_2pts_mades(self, team, team_id):
        twopts_made_df = self.df_query(Event="twopts_atpt", Team=team, Info="进球")
        assisted_df = self.df_query(Event="assists", Team=team, Info="2分")

        return len(twopts_made_df) + len(assisted_df)


    def get_team_tos(self, team, team_id):
        team_op = self.team_names[1 - team_id]
        TOs_df = self.df_query(Event="tos", Team=team)

        stealed_df = self.df_query(Event="steals", Team=team_op)

        off_fouls_df = self.df_query(Event="fouls", Info="进攻犯规", Team=team)

        return len(TOs_df) + len(stealed_df) + len(off_fouls_df)


    def get_team_fouls(self, team, team_id):
        fouls_df = self.df_query(Event="fouls", Team=team)
        return len(fouls_df)


    def get_team_make_fouls(self, team, team_id):
        team_op = self.team_names[1 - team_id]
        make_fouls_df = self.df_query(Event="fouls", Team=team_op)
        return len(make_fouls_df)


    def get_team_assists_2pts(self, team, team_id):
        assisted_df = self.df_query(Event="assists", Team=team, Info="2分")
        return len(assisted_df)


    def get_team_assists_3pts(self, team, team_id):
        assisted_df = self.df_query(Event="assists", Team=team, Info="3分")
        return len(assisted_df)

    def get_team_assisted(self, team, team_id):
        return 0

    def get_team_oncourt_scores(self, team, team_id):
        scores = 0
        # 独立进球记录
        scores_df = self.event_data[
            (self.event_data.Team == team) & (self.event_data.Info == "进球")]
        # 受助攻记录
        get_assist_df = self.event_data[
            (self.event_data.Team == team) & (self.event_data.Event == "助攻")]
        scores += len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(scores_df[scores_df.Event == "2分球出手"]) * 2 + len(
            scores_df[scores_df.Event == "罚球出手"])
        scores += len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(
            get_assist_df[get_assist_df.Info == "2分"]) * 2

        return scores

    def get_team_oncourt_loses(self, team, team_id):
        team_op = self.team_names[1 - team_id]
        scores = 0
        # 独立进球记录
        scores_df = self.event_data[
            (self.event_data.Team == team_op) & (self.event_data.Info == "进球")]
        # 受助攻记录
        get_assist_df = self.event_data[
            (self.event_data.Team == team_op) & (self.event_data.Event == "助攻")]
        scores += len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(scores_df[scores_df.Event == "2分球出手"]) * 2 + len(
            scores_df[scores_df.Event == "罚球出手"])
        scores += len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(
            get_assist_df[get_assist_df.Info == "2分"]) * 2

        return scores

    def get_team_games_played(self, team, team_id):
        return 1

    def get_team_oncourt_team_rebounds(self, team, team_id):
        return 0

    def get_team_oncourt_opponent_rebounds(self, team, team_id):
        return 0

    def get_team_used_rounds(self, team, team_id):
        return 0
    
    def get_total_scores(self):
        return sum(list(self.player_stats[0]["scores"])), sum(list(self.player_stats[1]["scores"]))





