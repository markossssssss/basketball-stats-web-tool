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
    JUSHOOP_title_txt = "JUSHOOP FULLCOURT RUN"
    target_stats = ["atpts", "scores", "assists", "rebounds", "steals", "blocks", "2pts", "3pts", "fts", "od_rebounds", "tos", "TS", "EFF"]

    table_cols = ["得分", "篮板", "助攻", "抢断", "盖帽", "2分", "3分",
                  "后场+前场篮板", "失误", "真实命中率", "效率值"]


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
            
            
            
            
            