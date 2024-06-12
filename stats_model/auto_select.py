from . import FriendshipMatchStatsModel, PickupRunStatsModel

def auto_select_stats_model(event_data, config):
    try:
        match_type = config["match_type"]
    except Exception as e:
        print("Config里没有设置类型match_type字段")
        raise e

    assert match_type in ["球局", "友谊赛"]

    return FriendshipMatchStatsModel(event_data, config) if match_type == "友谊赛" else PickupRunStatsModel(event_data, config)