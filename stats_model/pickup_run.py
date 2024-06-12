from . import BaseStatsModel, decimal_to_percent, terms, high_level_stats
from plottable.cmap import normed_cmap
from plottable.formatters import decimal_to_percent
from matplotlib.colors import LinearSegmentedColormap
from plottable import Table, ColDef
import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt

class PickupRunStatsModel(BaseStatsModel):
    check_event_team = False

    match_type = "球局"
    max_teams = 4
    JUSHOOP_title_txt = "JUSHOOP全场友谊赛"
    target_stats = ["atps", "scores", "assists", "rebounds", "steals", "blocks", "2PTs", "3PTs", "FTs", "OD_rebounds", "TOs", "TS", "EFF"]

    table_cols = ["得分", "篮板", "助攻", "抢断", "盖帽", "2分", "3分",
                  "后场+前场篮板", "失误", "真实命中率", "效率值"]

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

        # fig, ax = plt.subplots()

        fig.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        cmap = LinearSegmentedColormap.from_list(
            name="bugw", colors=["#FF0000", "#e0e8df", "#00EE76"], N=256
        )
        cmap_r = LinearSegmentedColormap.from_list(
            name="bugw", colors=["#00EE76", "#e0e8df", "#FF0000"], N=256
        )


        team_title = self.team_names[team_idx] if plot_team_name else ""
        table_col_defs = [
            ColDef("姓名", width=1.3, textprops={"fontsize": 23, "ha": "left", "weight": "bold"}, title=team_title),
            ColDef("得分", width=0.5),
            ColDef("助攻", width=0.5),
            ColDef("篮板", width=0.5),
            ColDef("抢断", width=0.5),
            ColDef("盖帽", width=0.5),
            ColDef("2分", width=0.5),
            ColDef("3分", width=0.5),
            ColDef("后场+前场篮板", width=0.8, title="后场+\n前场篮板"),
            ColDef("失误", width=0.5),
            ColDef("真实命中率", width=0.8, formatter=decimal_to_percent),
            ColDef("效率值", width=0.5,
                   text_cmap=normed_cmap(self.player_stats[team_idx]["效率值"], cmap=cmap, num_stds=0.5)),

        ]

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
                    textprops={"fontsize": 17, "ha": "center", "weight": "bold"}, )
        return tab



if __name__ == '__main__':
    # config = json.load(open("/Users/Markos/Desktop/basketball-stats-web-tool/GameStatsData/20230825_PURDUE_TG/config.json"))
    # event_data = pd.read_csv("/Users/Markos/Desktop/basketball-stats-web-tool/GameStatsData/20230825_PURDUE_TG/events.csv")
    # event_data = event_data.fillna("")

    # print(config)
    # print(event_data)
    # events = BasketballEvents(event_data, config)
    # events.print_info()
    # events.get_stats()
    # print(events.player_stats)
    # events.plot_stats_single_team(1)
    # events.plot_stats_both_team()

    mt_font = sorted([f.name for f in font_manager.fontManager.ttflist])
    print(mt_font)
            
            
            
            
            