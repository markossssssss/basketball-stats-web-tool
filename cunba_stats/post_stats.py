from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
import pandas as pd
import requests
import os

terms = {
    "realName": "姓名",
    "score": "得分",
    "assists": "助攻",
    "backboard": "篮板",
    "preemption": "抢断",
    "cap": "盖帽",
    "trisection": "3分",
    "fault": "失误",
    "foul": "犯规",
    "freeThrow": "罚球",
    "shot": "投篮",
    "duration": "上场时间",
    "dichotomy": "2分",
    "backboardAround": "后场+前场篮板",
    "usageRate": "球权使用率",
    "hitRate": "真实命中率",
    "efficiencyValue": "效率值",
    "scoreSite": "在场得分(10回合)",
    "scoreLost": "在场失分(10回合)"
}

APP_ID = "c9a81d677e9942779117cef24a5e2eec"
APP_KEY = "8bd1c04aca924554aeb7e24a22f1683b"
url = "https://cunba.jxa.plus/cunba-admin-api/api/v1/interface/sendPlayerScore"

def aes_encrypt(data):
    key = APP_KEY.encode('utf-8')
    data = data.encode('utf-8')

    cipher = AES.new(key, AES.MODE_ECB)
    padded_data = pad(data, AES.block_size)
    ciphered_data = cipher.encrypt(padded_data)
    encoded_ciphered_data = b64encode(ciphered_data).decode('utf-8')

    return encoded_ciphered_data

def aes_decrypt(data):
    key = APP_KEY.encode('utf-8')
    encoded_ciphered_data = data.encode('utf-8')
    ciphered_data = b64decode(encoded_ciphered_data)

    cipher = AES.new(key, AES.MODE_ECB)
    deciphered_padded_data = cipher.decrypt(ciphered_data)
    deciphered_data = unpad(deciphered_padded_data, AES.block_size)
    deciphered_data = eval(deciphered_data)
    return deciphered_data

def post_request(url, data=None, headers=None):
    try:
        # 发送 POST 请求
        response = requests.post(url, json=data, headers=headers, verify=False, timeout=10)
        
        # 检查响应状态码
        if response.status_code == 200:
            # 解析 JSON 数据
            data = response.json()
            return data
        else:
            # 如果状态码不是 200，则打印错误信息
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        # 处理请求过程中的异常
        print(f"An error occurred: {e}")
        return None 
    

def post_match_data():
    pass

def find_longest_common_substring(s1, s2):
    """
    找出两个字符串s1和s2之间的最长公共子串。
    """
    m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest: x_longest]

def match_teams(target_teams, teams_from_csv):
    """
    为target_teams中的每个队名找出teams_from_csv中的对应名字，
    匹配规则是最长公共子串。
    """
    matches = {}
    for target_team in target_teams:
        max_length = 0
        matched_team = None
        for team in teams_from_csv:
            common_substring = find_longest_common_substring(target_team, team)
            length = len(common_substring)
            if length > max_length:
                max_length = length
                matched_team = team
        matches[target_team] = matched_team
    return matches

def get_team_data_list(team_name, match_id, team_id, data_dir):
    data_csv = os.path.join(data_dir, f"{team_name}数据.csv")
    stats = pd.read_csv(data_csv)
    stats_list = []
    # print(stats)
    for j, r in stats.iterrows():
        
        if r["姓名"] == "全队":
            continue
        r["投篮"] = f'{int(r["2分"].split("/")[0]) + int(r["3分"].split("/")[0])}/{int(r["2分"].split("/")[1]) + int(r["3分"].split("/")[1])}'
        
        row_dict = {}
        try:
            row_dict["uniformNumber"] = r["姓名"].split("号")[0]
        except IndexError:
            row_dict["uniformNumber"] = ""
        try:
            r["姓名"] = r["姓名"].split("号")[1]
        except Exception as e:
            pass
        # row_dict["teamId"] = team_id
        # row_dict["gameId"] = match_id
        for term in terms.keys():
            row_dict[term] = str(r[terms[term]])
        
        stats_list.append(row_dict)
    # print(stats_list)
    return stats_list

# def get_team_dicts(teams, matches, team_datas):
#     play_number_dicts = []
#     for team in teams:
#         play_number_dict = {}
#         team_data = team_datas[matches[team]]
#         for i, r in team_data.iterrows():
#             play_number_dict[r["姓名"]] = r["号码"]

#         play_number_dicts.append(play_number_dict)

#     return play_number_dicts
            
def post_stats(data_dir, config):
    target_teams = [config["match_name"].split("_")[1], config["match_name"].split("_")[2]]
    match_id = config["match_id"]
    team_ids = config["team_ids"]
    

    data = {}
    data["gameId"] = match_id
    data["sourceTeam"] = get_team_data_list(target_teams[0], match_id, team_ids[0], data_dir)

    data["targetTeam"] = get_team_data_list(target_teams[1], match_id, team_ids[1], data_dir)


    # print(data)
    try:
        scores_txt = config["scores"]
        scores = [scores_txt.split(":")[0].strip(), scores_txt.split(":")[1].strip()]
    except Exception:
        scores = [sum([int(data[team_txt][i]["score"]) for i in range(len(data[team_txt]))]) for team_txt in ["sourceTeam", "targetTeam"]]

    # print(scores)

    winner_loser = [{"teamId":f"{team_ids[0]}", "score": f"{int(scores[0])}"}, {"teamId":f"{team_ids[1]}", "score": f"{int(scores[1])}"}]
    
    if scores[0] > scores[1]:
        data["winner"] = winner_loser[0]
        data["loser"] = winner_loser[1]
    else:
        data["winner"] = winner_loser[1]
        data["loser"] = winner_loser[0]
        

    # print(str(data))

    encrypted_data = aes_encrypt(str(data))

    post_json = {
        "appId": APP_ID,
        "data": encrypted_data,
    }
    # # print(post_json)

    response = post_request(url, data=post_json)
    print(response)




if __name__ == "__main__":

    target_teams = ["山西翼城凤翔园林", "贵州黑今骑士"]
    match_id = "1820626072934772737"
    team_ids = ["1820388429143699458", "1820388546798120962"]


    # team_data = pd.read_excel('data.xlsx', sheet_name=None)

    # matches = match_teams(target_teams, team_data)

    # play_number_dicts = get_team_dicts(target_teams, matches, team_data)







    # data = {}
    # data["gameId"] = match_id
    # data["sourceTeam"] = get_team_data_list(target_teams[0], match_id, team_ids[0], play_number_dicts[0])

    # data["targetTeam"] = get_team_data_list(target_teams[1], match_id, team_ids[1], play_number_dicts[1])

    # # print(str(data))

    # encrypted_data = aes_encrypt(str(data))
    # # # print(encrypted_data)

    # post_json = {
    #     "appId": APP_ID,
    #     "data": encrypted_data,
    # }

    # # print(post_json)

    # post_request(url, data=post_json)

    # response = post_request(url, data=post_json)

    # print(response)

    

    # for i, team_name in enumerate(target_teams):
    #     stats_list = get_team_data_list(team_name, match_id, team_ids[i])
    #     print(stats_list)


            



    # print(matches)
    # print(data.keys())
    # print(data["A6河南怀道居山药粉"])