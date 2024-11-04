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



MY_TITLE_TEXT_PRORPS = {"fontsize": 26, "ha": "center", "weight": "bold", "color": "#d48401", "family": "LogoSC Unbounded Sans"}

ROW_HEIGHT = 0.8

class myTable(Table):

    def _init_rows(self):
        """Initializes the Tables Rows."""
        self.rows = {}
        num_lines = len(self.df.to_records())
        label_y = -1 - (-num_lines // 2) * (1 - ROW_HEIGHT)
        self.col_label_row = self._get_col_label_row(label_y, self._get_column_titles())
        for idx, values in enumerate(self.df.to_records()):
            self.rows[idx] = self._get_row(idx, values, num_lines)

        

    def _get_col_label_row(self, idx: int, content: List[str | Number]) -> Row:
        """Creates the Column Label Row.

        Args:
            idx (int): index of the Row
            content (List[str  |  Number]): content that is plotted as text.

        Returns:
            Row: Column Label Row
        """
        widths = self._get_column_widths()

        if "height" in self.col_label_cell_kw:
            height = self.col_label_cell_kw["height"]
        else:
            height = 1

        x = 0

        row = Row(cells=[], index=idx)

        for col_idx, (colname, width, _content) in enumerate(
            zip(self.column_names, widths, content)
        ):
            col_def = self.column_definitions[colname]
            textprops = MY_TITLE_TEXT_PRORPS

            # don't apply bbox around text in header
            if "bbox" in textprops:
                textprops.pop("bbox")

            cell = create_cell(
                column_type=ColumnType.STRING,
                xy=(
                    x,
                    idx + 1 - height,
                ),  # if height is different from 1 we need to adjust y
                content=_content,
                row_idx=idx,
                col_idx=col_idx,
                width=width,
                height=height,
                rect_kw=self.col_label_cell_kw,
                textprops=textprops,
                ax=self.ax,
            )

            row.append(cell)
            cell.draw()

            x += width

        return row
    
    def _get_row(self, idx: int, content: List[str | Number], num_lines=0) -> Row:
        widths = self._get_column_widths()

        x = 0

        row = Row(cells=[], index=idx)
        middle = num_lines // 2
        idx -= (idx - middle) * (1 - ROW_HEIGHT)

        for col_idx, (colname, width, _content) in enumerate(
            zip(self.column_names, widths, content)
        ):
            col_def = self.column_definitions[colname]


            if "plot_fn" in col_def:
                plot_fn = col_def.get("plot_fn")
                plot_kw = col_def.get("plot_kw", {})

                cell = create_cell(
                    column_type=ColumnType.SUBPLOT,
                    xy=(x, idx),
                    content=_content,
                    plot_fn=plot_fn,
                    plot_kw=plot_kw,
                    row_idx=idx,
                    col_idx=col_idx,
                    width=width,
                    height=ROW_HEIGHT,
                    rect_kw=self.cell_kw,
                    ax=self.ax,
                )

            else:
                textprops = self._get_column_textprops(col_def)

                cell = create_cell(
                    column_type=ColumnType.STRING,
                    xy=(x, idx),
                    content=_content,
                    row_idx=idx,
                    col_idx=col_idx,
                    width=width,
                    height=ROW_HEIGHT,
                    rect_kw=self.cell_kw,
                    textprops=textprops,
                    ax=self.ax,
                )

            row.append(cell)
            self.columns[colname].append(cell)
            self.cells[(idx, col_idx)] = cell
            cell.draw()

            x += width

        return row


def my_normed_cmap(
    s: pd.Series, cmap: matplotlib.colors.LinearSegmentedColormap, num_stds: float = 2.5
) -> Callable:
    
    vmin, vmax = -15, 15

    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    
    m = myScalarMappable(norm=norm, cmap=cmap)


    return m.to_rgba

class myScalarMappable(matplotlib.cm.ScalarMappable):
    def to_rgba(self, x, alpha=None, bytes=False, norm=True):
        x = np.ma.asarray(x)
        if norm:
            x = self.norm(x)
        rgba = self.cmap(x, alpha=alpha, bytes=bytes)
        return rgba



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

    def get_ColDef(self, term):
        pass

    def plot_table(self, fig, ax, team_idx, plot_team_name=True, row_height=1, wide=True):
        ROW_HEIGHT = row_height
        colors = {
            "even": (0.4, 0.4, 0.4, 0.8),
            "bg": (0.2, 0.2, 0.2, 0.8),
            "title": "#123456",
            "text": "#FFFFFF"
        }

        text_color = "#FFFFFF"

        if not wide:
            MY_TITLE_TEXT_PRORPS["fontsize"] = 21
        else:
            MY_TITLE_TEXT_PRORPS["fontsize"] = 26


        # fig.set_facecolor(bg_color)
        ax.set_facecolor(colors["bg"])

        team_title = self.team_names[team_idx] if plot_team_name else ""

        table_col_defs = []
        table_col_defs.append(self.get_col("姓名", team_idx, title=team_title, team_name=self.team_names[team_idx], text_color=colors["text"]))
        if not self.user_table_cols is None:
            self.table_cols = self.user_table_cols
        for stat_name in self.table_cols:
            table_col_defs.append(self.get_col(stat_name, team_idx, team_name=self.team_names[team_idx], text_color=colors["text"]))

        player_stats = self.player_stats[team_idx].copy()
        player_stats["姓名"] = player_stats.index
        player_stats["姓名"][-1] = "全队"
        player_stats.set_index("姓名", inplace=True)

        # ax.set_ylim(-0.5, 1 - 0.5)


        tab = myTable(player_stats,
                    ax=ax,
                    column_definitions=table_col_defs,
                    row_dividers=False,
                    col_label_divider=False,
                    footer_divider=False,
                    columns=self.table_cols,
                    even_row_color=colors["even"],
                    # footer_divider_kw={"color": colors["bg"], "lw": 2},
                    # col_label_divider_kw={"linestyle": "-", "linewidth": 1},
                    # row_divider_kw={"color": colors["bg"], "lw": 2},
                    # column_border_kw={"color": colors["bg"], "lw": 2},
                    textprops={"ha": "center", "weight": "bold"}
                    )
        return tab
    
    def get_col(self, stat_name, team_idx, team_name="", text_color="#FFFFFF", title=None):
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
            return ColDef(stat_name, width=1.3, textprops={"fontsize": 22, "weight": "bold", "color": text_color, "family": "Microsoft YaHei"}, title=team_name)
        elif stat_name in ["上场时间", "后场+前场篮板", "球权使用率", "真实命中率"]:
            width = 1.0
            if "+" in stat_name:
                title = title.replace("+", "\n+")
            if "率" in stat_name:
                formatter=decimal_to_percent
        elif stat_name == "在场得分(10回合)":
            width = 1.0
            title = title.replace("(", "\n(")
            text_cmap = normed_cmap(self.player_stats[team_idx]["在场得分(10回合)"], cmap=cmap, num_stds=1)
        elif stat_name == "正负值":
            # print("hello")
            text_cmap = my_normed_cmap(self.player_stats[team_idx]["正负值"], cmap=cmap, num_stds=1.2)
        elif stat_name == "在场失分(10回合)":
            width = 1.0
            title = title.replace("(", "\n(")
            text_cmap = normed_cmap(self.player_stats[team_idx]["在场失分(10回合)"], cmap=cmap_r, num_stds=1)
        elif stat_name == "效率值":
            text_cmap = normed_cmap(self.player_stats[team_idx]["效率值"], cmap=cmap, num_stds=1.2)

        if len(stat_name) >= 4 and width == 0.5:
            width = 0.7
        elif len(stat_name) == 3 and width == 0.5:
            width = 0.6

        return ColDef(stat_name, width=width, title=title,
                   text_cmap=text_cmap, formatter=formatter, textprops={"fontsize": 20, "color": text_color, "family": "Microsoft YaHei"})
    
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
            
            
            
            
            