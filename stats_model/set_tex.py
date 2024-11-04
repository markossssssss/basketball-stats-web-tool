from . import report_page_funcs, report_page_imgs, get_img
import os
import json

tex_param_config_template_league = {
    "__TEAM_NAME__": "EMJ",
    "__REPORT_YEAR__": "2024赛季",
    "__REPORT_TYPE__": "村BA联赛",
    "__NUM_YEARS__": "1",
    "__MATCH_TYPES__": "比赛",
    "__NUM_MATCHES__": "0",
    "__NUM_WINS__": "0",
    "__WIN_RATE__": "00",
    "__CONGRATS_TITLE__": "获得了",
    "__CONGRATS_OBJECT__": "冠军",
    "__CONGRATS_INFO__": "",
    "__TEAM_LOGO_PATH__": "logo.png",
    "__TEAM_LOGO_WIDTH__": "0.4",
    "__REPORT_LOGO_PATH__": "../../resources/logo.png",
    "__REPORT_LOGO_WIDTH__": "0.2",
    "__JUSHOOP_SQUARE_LOGO_PATH__": "../../resources/square_logo.png",
    "__JUSHOOP_OPPO_PATH__": "oppo.png",
    "__JUSHOOP_PRO_PATH__": "pro.png",
    "__JUSHOOP_SCORES_PATH__": "scores.png",
    "__JUSHOOP_TEAM_SPRIT_PATH__": "team_spirit.png",
    "__JUSHOOP_OPTION_PATH__": "options.png",
    "__JUSHOOP_REBOUNDS_PATH__": "rebounds.png",
    "__JUSHOOP_BASIC_STATS_PATH__": "basic_stats.pdf",
    "__JUSHOOP_ADVANCED_STATS_PATH__": "advanced_stats.pdf",
    "__JUSHOOP_LEADERS_PATH__": "leaders.png",
    "__JUSHOOP_BEST_PATH__": "best.png",
}



def set_params(resource_dir, tex_param_config, team):
    config_dir = os.path.join(resource_dir, "resources", team, "config.json")
    team_logo_path = get_img(resource_dir, team, "logo", get_path=True)
    config = json.load(open(config_dir, encoding='utf-8'))
    for key, value in config.items():
        if key in config:
            tex_param_config[key] = value
    # tex_param_config["__TEAM_LOGO_PATH__"] = team_logo_path
    tex_param_config["__WIN_RATE__"] = round(float(tex_param_config["__NUM_WINS__"]) / float(tex_param_config["__NUM_MATCHES__"]) * 100)
    # tex_param_config["__JUSHOOP_SQUARE_LOGO_PATH__"] = os.path.join(resource_dir, "resources", "square_logo.png")
    # tex_param_config["__REPORT_LOGO_PATH__"] = os.path.join(resource_dir, "resources", "logo.png")
    return tex_param_config
    

def get_tex(resource_dir, team):
    param_config = tex_param_config_template_league.copy()
    tex_text = open(os.path.join(resource_dir, "resources/template.tex")).read()

    param_config = set_params(resource_dir, param_config, team)

    # print(param_config)
    # print(tex_text)

    for key in param_config.keys():
        tex_text = tex_text.replace(key, str(param_config[key]))

    file_tex = open(os.path.join(resource_dir, "results", team, f"{team}_report.tex"), "w")
    file_tex.write(tex_text)
    file_tex.close()

