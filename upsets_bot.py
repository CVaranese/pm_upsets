import pandas as pd
import numpy as np
import requests
import json
import praw
import time

def main():
    # event_json2 = requests.get('http://api.smash.gg/tournament/ceo-2018-fighting-game-championships/event/super-smash-bros-melee?expand[]=groups')
    # event_json2 = requests.get('https://api.smash.gg/tournament/backthrow-thursdays-66/event/singles?expand[]=groups')
    # event_json2 = requests.get('https://api.smash.gg/tournament/the-even-bigger-balc/event/project-m-singles?expand[]=groups')
    event_json2 = requests.get('https://api.smash.gg/tournament/the-even-bigger-balc/event/slap-city-singles?expand[]=groups')
    # event_json2 = requests.get('https://api.smash.gg/tournament/northwest-majors-x-a-cpt-ranking-event-june-23rd-and-1/event/street-fighter-v-arcade-edition?expand[]=groups')
    reddit = praw.Reddit(user_agent='upsets_bot (by /u/xenerot)',
                        client_id='-n59g5B7MRIJmw', client_secret="PGbtH-F5Gw5Q6biv72qDKWJr_7U",
                        username='pm_upsets_bot', password='balcyiscool')
    # print(event_json2.text)

    event_json = json.loads(event_json2.text)

    phase_ids = np.array([])
    for group in event_json['entities']['groups']:
        phase_ids = np.append(phase_ids, str(group['id']))

    with open('phase.txt') as phase_file:
        phase_json = json.load(phase_file)

    upsets = []
    for p_id in phase_ids:
        phase_json2 = requests.get('http://api.smash.gg/phase_group/{}?expand[]=seeds&expand[]=sets'.format(p_id))
        # print("\n\n" + phase_json2.text)
        upsets += get_upsets_list(json.loads(phase_json2.text))

    if upsets == []:
        return

    upsets = pd.DataFrame(upsets)
    upsets = upsets.sort_values(by=['loser_seed'])
    upsets = upsets.sort_values(by=['bracket'])

    upsets['string'] = upsets['winner'] + " (" + upsets['winner_region'] + ")"" beat "
    upsets['string'] = upsets['string'] + upsets['loser'] + " (" + upsets['loser_region'] + ")"

    post = 'Upsets as of ' + time.ctime() + ":\n\n" 
    bracket = ''
    for string, brack in zip(upsets['string'], upsets['bracket']):
        if brack != bracket:
            post += "\n\t\tBracket: " + brack + "\n\n"
            bracket = brack
        post += "\t" + string + "\n\n"

    post += "\n\n\n^^^Powered ^^^by ^^^Dox"

    #subreddit = reddit.subreddit('reddit_api_test')
    #subreddit.submit(title='Smashgg upset test', selftext=post)
    submission = reddit.submission(id='8wkd9y')
    submission.edit(post)

def get_upsets_list(phase_json):
    l = []
    for seed in phase_json['entities']['seeds']:
        player_dict = {}
        entrantId = str(seed['entrantId'])
        player_dict['id'] = entrantId
        player_dict['group_seed'] = seed['groupSeedNum']
        player_dict['name'] = seed['mutations']['entrants'][entrantId]['name']
        if 'initialSeedNum' in seed['mutations']['entrants'][entrantId].keys():
            player_dict['seed'] = seed['mutations']['entrants'][entrantId]['initialSeedNum']
        else:
            return []
            player_dict['seed'] = '0'
        participant_id = str(seed['mutations']['entrants'][entrantId]['participantIds'][0])
        player_dict['region'] = seed['mutations']['participants'][participant_id]['contactInfo']['cityState']
        if player_dict['region'] == None:
            player_dict['region'] = ""
        row = pd.Series(player_dict)
        #print(row)
        l += [row]
    player_df = pd.DataFrame(l)
    player_df.index = player_df['id']
    
    l = []
    for match in phase_json['entities']['sets']:
    #print(match)
        upset_dict = {}
        winner = match['winnerId']
        if winner is None:
            continue
        loser = match['loserId']
        if loser is None:
            continue
        winner_seed = player_df['seed'][str(winner)]
        loser_seed = player_df['seed'][str(loser)]
        if(winner_seed > loser_seed and loser_seed < 128):
            upset_dict['winner'] = player_df['name'][str(winner)]
            upset_dict['loser'] = player_df['name'][str(loser)]
            upset_dict['winner_seed'] = winner_seed
            upset_dict['loser_seed'] = loser_seed
            upset_dict['winner_region'] = player_df['region'][str(winner)]
            upset_dict['loser_region'] = player_df['region'][str(loser)]
            upset_dict['bracket'] = phase_json['entities']['groups']['displayIdentifier']
            l += [pd.Series(upset_dict)]

        upsets = pd.DataFrame(l)
    return l

if __name__ == "__main__":
    while(True):
        print("Starting...")
        main()
        print("Sleeping...")
        time.sleep(1200)
