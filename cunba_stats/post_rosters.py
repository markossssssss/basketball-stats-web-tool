import argparse
import pandas as pd
import requests
import numpy as np

url_get = "http://www.jushoop1977.com/api/get-not-updated-teams"
url_post = "http://www.jushoop1977.com/api/update-rosters"


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
    
def get_request(url, headers=None):
    try:
        # 发送 POST 请求
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        
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
        if max_length >= 2:
            matches[target_team] = matched_team
        else:
            matches[target_team] = None
    return matches


def get_team_dicts(teams, matches, team_datas):
    play_number_dicts = []
    target_teams = []
    for team in teams:
        if matches[team] is None:
            continue
        target_teams.append(team)
        play_number_dict = {}
        team_data = team_datas[matches[team]]
        for i, r in team_data.iterrows():
            if np.isnan(r["号码"]):
                continue
            play_number_dict[f'{int(r["号码"])}号{r["姓名"]}'] = int(r["号码"])
        for i in range(1, 6):
            play_number_dict[f"未知{i}"] = ""
            

        play_number_dicts.append(play_number_dict)

    return target_teams, play_number_dicts
            


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Example')
    parser.add_argument('data_dir', type=str, help='path of data file')
    args = parser.parse_args()


    response = get_request(url_get)
    teams = response['team_names']
    team_ids = response['team_ids']


    team_data_from_csv = pd.read_excel(args.data_dir, sheet_name=None)


    matches = match_teams(teams, team_data_from_csv)
    print(matches)

    target_teams, players_dicts = get_team_dicts(teams, matches, team_data_from_csv)
    print(target_teams, players_dicts)

    command = input('input anything to continue pushing, q to quit\n')
    if command == 'q':
        exit(0)
    for i, team in enumerate(target_teams):
        data = {
            'team_id': str(team_ids[i]),
            'players_dict': str(players_dicts[i])
        }

        print(data)
        post_request(url_post, data=data)
    

    
   

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