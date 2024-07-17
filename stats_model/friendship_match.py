from . import BaseStatsModel, decimal_to_percent, terms, high_level_stats
from plottable.cmap import normed_cmap
from matplotlib.colors import LinearSegmentedColormap
from plottable import Table, ColDef
import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import os
import pandas as pd


class FriendshipMatchStatsModel(BaseStatsModel):
    match_type = "友谊赛"
    max_teams = 2
    JUSHOOP_title_txt = "JUSHOOP全场友谊赛"

    check_team = True


    # 需要计算的数据项
    target_stats = ["atpts", "fts_atpts", "time", "scores", "assists", "rebounds", "steals", "blocks", "2pts", "3pts",
                    "fts", "od_rebounds", "fouls", "tos", "make_fouls", "USG", "TS", "EFF", "oncourt_per_scores",
                    "oncourt_per_loses"]

    # 需要展示的数据项
    table_cols = ["上场时间", "得分", "篮板", "助攻", "抢断", "盖帽", "2分", "3分", "罚球",
                  "后场+前场篮板", "失误", "球权使用率", "真实命中率", "效率值", "在场得分(10回合)",
                  "在场失分(10回合)"]
    
    # table_cols_ENG = ["MIN", "PTS", "REB", "AST", "STL", "BLK", "2FG", "3FG", "FT",
    #               "DREB+OREB", "TO", "USG%", "TS%", "EFF", "ORtg(10 rounds)",
    #               "DRtg(10 rounds)"]

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

    def get_ColDef(self, term):
        pass

    def plot_table(self, fig, ax, team_idx, plot_team_name=True):

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


        fig.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        team_title = self.team_names[team_idx] if plot_team_name else ""

        table_col_defs = []
        table_col_defs.append(self.get_col("姓名", team_idx, title=team_title))
        for stat_name in self.table_cols:
            table_col_defs.append(self.get_col(stat_name, team_idx))

        # print(table_col_defs)
        # table_col_defs = [
        #     ColDef("姓名", width=1.3, textprops={"fontsize": 19,"ha": "left", "weight": "bold"}, title=team_title),
        #     ColDef("上场时间", width=0.8),
        #     ColDef("得分", width=0.5),
        #     ColDef("助攻", width=0.5),
        #     ColDef("篮板", width=0.5),
        #     ColDef("抢断", width=0.5),
        #     ColDef("盖帽", width=0.5),
        #     ColDef("2分", width=0.5),
        #     ColDef("3分", width=0.5),
        #     ColDef("罚球", width=0.5),
        #     ColDef("后场+前场篮板", width=0.8, title="后场+\n前场篮板"),
        #     ColDef("失误", width=0.5),
        #     ColDef("球权使用率", width=0.8, formatter=decimal_to_percent),
        #     ColDef("真实命中率", width=0.8, formatter=decimal_to_percent),
        #     ColDef("效率值", width=0.5,
        #            text_cmap=normed_cmap(self.player_stats[team_idx]["效率值"], cmap=cmap, num_stds=1.2)),
        #     ColDef("在场得分(10回合)", width=1.0, title="在场得分\n(10回合)",
        #            text_cmap=normed_cmap(self.player_stats[team_idx]["在场得分(10回合)"], cmap=cmap, num_stds=1)),
        #     ColDef("在场失分(10回合)", width=1.0, title="在场失分\n(10回合)",
        #            text_cmap=normed_cmap(self.player_stats[team_idx]["在场失分(10回合)"], cmap=cmap_r, num_stds=1))
        # ]

        # print(table_col_defs)
        # exit()

        tab = Table(self.player_stats[team_idx],
                    ax=ax,
                    column_definitions=table_col_defs,
                    row_dividers=True,
                    col_label_divider=False,
                    footer_divider=True,
                    columns=self.table_cols,
                    even_row_color=row_colors["even"],
                    footer_divider_kw={"color": bg_color, "lw": 2},
                    row_divider_kw={"color": bg_color, "lw": 2},
                    column_border_kw={"color": bg_color, "lw": 2},
                    # 如果设置字体需要添加"fontname": "Roboto"
                    textprops={"fontsize": 17, "ha": "center","weight": "bold"}, )
        return tab
    
    def get_col(self, stat_name, team_idx, title=None):
        width = 0.5
        formatter = None
        text_cmap = None
        cmap = LinearSegmentedColormap.from_list(
            name="bugw", colors=["#FF0000", "#e0e8df", "#00EE76"], N=256
        )
        cmap_r = LinearSegmentedColormap.from_list(
            name="bugw", colors=["#00EE76", "#e0e8df", "#FF0000"], N=256
        )
        if title is None:
            title = self.terms_en[stat_name] if self.use_en else stat_name
        if stat_name == "姓名":
            return ColDef(stat_name, width=1.3, textprops={"fontsize": 19,"ha": "left", "weight": "bold"}, title=title)
        elif stat_name in ["上场时间", "后场+前场篮板", "球权使用率", "真实命中率"]:
            width = 0.8
            if "+" in stat_name:
                title = title.replace("+", "\n+")
            if "率" in stat_name:
                formatter=decimal_to_percent
        elif stat_name == "在场得分(10回合)":
            width = 1.0
            title = title.replace("(", "\n(")
            text_cmap=normed_cmap(self.player_stats[team_idx]["在场得分(10回合)"], cmap=cmap, num_stds=1)
        elif stat_name == "在场失分(10回合)":
            width = 1.0
            title = title.replace("(", "\n(")
            text_cmap=normed_cmap(self.player_stats[team_idx]["在场失分(10回合)"], cmap=cmap_r, num_stds=1)
        elif stat_name == "效率值":
            text_cmap = normed_cmap(self.player_stats[team_idx]["效率值"], cmap=cmap, num_stds=1.2)

        return ColDef(stat_name, width=width, title=title,
                   text_cmap=text_cmap, formatter=formatter)
    
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
            
            
            
            
            