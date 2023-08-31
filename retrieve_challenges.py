import requests
import os
import json
import re
from bs4 import BeautifulSoup

AWC_HOF_URL = 'https://anime.jhiday.net'
TMP_PATH = 'tmp/'
JSON_CHALLENGE_SOT = 'challengeList.json'
IMG_PLACEHORDER = [{"category": ['default'], "image":'https://i.imgur.com/V1cyNht.png'},
                   {"category": ['Series Collections', 'Creator Collections'], "image": 'https://i.imgur.com/EhKQOXd.gif'},
                   {"category": ['Affiliates Collections', 'Anime Guild Collections', 
                                 'Anime Watching Challenge Staff Collections', 'Monthly Anime Club Collections',
                                 'Staff Collections'], "image":'http://i.imgur.com/27xKTS8.png/useless-wip'}]
'https://i.imgur.com/V1cyNht.png'
URL_PLACEHOLDER = 'https://myanimelist.net/profile/ImagineBrkr/'
NOT_CONSIDER_FOR_BADGES = ['Sports', "Series-Per-2Days (Style 2)", "Unrated"]
LIMITED_CATEGORIES = ['Monthly', 'Limited']
BADGE_CATEGORIES = ["Year", "Franchise", "Creator", "Studios", "Genre", "Theme", "Characers",
                    "Type" ,"Statistics", "Miscellaneous", "Limited", "Monthly", "Series Collections",
                  "Creator Collections", "Staff Collections", "Monthly Anime Club Collections",
                  "Anime Watching Challenge Staff Collections", "Anime Guild Collections", "Affiliates Collections"]
NOT_ORDERED_CHALLENGES = ['Monthly', "Limited"]


def find_elements(soup, element=None, _id=None, _class=None, select=None):

    # Build the CSS selector based on the provided parameters
    selector = ''
    if element:
        selector += element
    if _id:
        selector += f'#{_id}'
    if _class is not None:
        if _class == '':
            selector += ':not([class])'
        else:
            selector += f'.{_class}'

    if select:
        selector = select
    # Find elements based on the selector
    elements = soup.select(selector)

    return elements


def get_html_content(url: str):
    print(f'GET Request to: {url}')
    response = requests.get(url, timeout=100)
    if response.status_code != 200:
        return
    return response.text


def get_url(url: str):
    filename = url.split('/')[-1]
    tmp_filepath = TMP_PATH+filename + '.html'
    if not os.path.exists(tmp_filepath):
        html_content = get_html_content(url)
        if html_content:
            with open(tmp_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

    with open(tmp_filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()

    return html_content

def extract_between(text: str, before_char, after_char):
    start_idx = text.find(before_char)
    if start_idx < 0:
        print(start_idx)
        return None
    end_idx = text.find(after_char, start_idx)

    # Si no se encontró after_char, devuelve None
    if end_idx < 0:
        return None
    return text[start_idx:end_idx].strip()

def list_challenges():
    filename = TMP_PATH+'challengeList.html'
    challenge_selector = 'div[id^="content-category-"] a'
    if not os.path.exists(TMP_PATH+'challengeList.html'):
        get_url('https://anime.jhiday.net/hof/challengeList')

    with open(filename, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    challenges = find_elements(soup, select=challenge_selector)
    challenges_dict = [{'title': challenge.text,
                       'hof_url': AWC_HOF_URL + challenge['href'],
                       'category': extract_between(challenge.parent.parent.parent.parent.parent.find('h3').text.strip(), '', '(')} for challenge in challenges]
    return challenges_dict


def retrieve_all_challenges_html():
    challenges = list_challenges()
    for url in challenges:
        get_url(url)


def retrieve_challenges_sot() -> list[dict]:
    with open(JSON_CHALLENGE_SOT, 'r', encoding='utf-8') as f:
        return json.load(f)


def sort_key(item):
    category = item['category']
    # Si la categoría está en la lista non_sorted_categories, mantenemos el orden original
    title_order = None if category in NOT_ORDERED_CHALLENGES else item['title']
    return (category, title_order)

def save_challenges_sot(challenges: list[dict]):
    def clean(challenge: dict):
        if "difficulties" in challenge:
            challenge.pop("difficulties")
        if "runs" in challenge:
            challenge.pop("runs")
        if "completion" in challenge:
            challenge.pop("completion")

        return challenge

    for challenge in challenges:

        if not "completed" in challenge.keys():
            challenge["completed"] = False

        if not "runs" in challenge.keys():
            runs = []
            for num_run in range(challenge["num_runs"]):
                run = {
                    "num_run": num_run + 1,
                    "topic": None
                }
                difficulties = []
                for num_difficulty in range(challenge["num_difficulties"]):
                    difficulty = {
                        'num_difficulty': num_difficulty + 1,
                        "completed": False,
                        "badge": None
                    }
                    difficulties.append(difficulty)
                run["difficulties"] = difficulties
                runs.append(run)
            challenge["runs"] = runs

    challenges = sorted(challenges, key=sort_key)

    json.dumps(challenges)
    with open(JSON_CHALLENGE_SOT, 'w', encoding='utf-8') as f:
        return json.dump(challenges, f)
    

def update_list_dicts(main_dicts: list[dict], update_dicts: list[dict]) -> list[dict]:
    main_dict = {d['title']: d for d in main_dicts}
    for update in update_dicts:
        if update['title'] in main_dict:
            main_dict[update['title']].update(update)
        else:
            main_dict[update['title']] = update
    return list(main_dict.values())

def parse_challenge(challenge_html: str) -> dict:
    mal_url_selector = 'a[href*="https://myanimelist.net/forum/?topicid="]'

    def parse_difficulties(soup: BeautifulSoup) -> int:
        difficulty_tag = soup.find('h3', string=re.compile(r'(\d+) Difficulties'))

        if difficulty_tag:
            number = int(re.search(r'(\d+) Difficulties', difficulty_tag.text).group(1))
        else:
            number = 1
        return number
    
    def parse_runs(soup: BeautifulSoup) -> int:
        run_numbers = {
            "once": 1,
            "twice": 2,
            "three": 3,
            "four": 4
        }
        text_patterns = ["submitted", "only count"]
        runs_text = soup.find(string=lambda s: any(pattern in s for pattern in text_patterns))
        number = 1

        if runs_text:
            for run_number in run_numbers.keys():
                if run_number in runs_text:
                    number = run_numbers[run_number]
        return number

    soup = BeautifulSoup(challenge_html, 'html.parser')
    num_difficulties = parse_difficulties(soup)
    num_runs = parse_runs(soup)
    mal_forum_url = soup.select(mal_url_selector)
    mal_forum_url = [tag for tag in mal_forum_url
                         if 'mal forum' in tag.text.lower()]
    
    if len(mal_forum_url) == 1:
        mal_forum_url = mal_forum_url[0]['href']
    else:
        mal_forum_url = 'https://myanimelist.net/clubs.php?cid=70446'
    
    return {'num_difficulties': num_difficulties,
            'num_runs': num_runs,
            'mal_url': mal_forum_url}

def challenges_to_json():
    challenges = list_challenges()
    mal_url_selector = 'a[href*="https://myanimelist.net/forum/?topicid="]'
    challenges_sot = retrieve_challenges_sot()
    
    for i, challenge in enumerate(challenges):
        challenge_html = get_url(challenge['hof_url'])
        challenge_data = parse_challenge(challenge_html)
        challenges[i] = {**challenge, **challenge_data}

    challenges_sot = update_list_dicts(challenges_sot, challenges)
    print(challenges_sot)
    save_challenges_sot(challenges_sot)

def get_challenge_sot(challenge_name: str) -> dict:
    challenges = retrieve_challenges_sot()
    for challenge in challenges:
        if challenge['title'] == challenge_name:
            return challenge
    print('Challenge not found')
    return None

def get_challenge_badges(challenge_name: str):
    challenge = get_challenge_sot(challenge_name)
    if not challenge:
        return None
    challenge_html = get_url(challenge["hof_url"])
    

def clean_title(title: str) -> str:
    title = title.replace(' ', '-').replace('[','').replace(']','').replace('\u00b0', '').replace('\u2606', '').replace('\u2764', '').replace("'", '').replace('Æ', '')
    return ''.join(char for char in title if ord(char) < 128)

def generate_bbcode_by_category(category):
    challenges = retrieve_challenges_sot()
    bbcode = f"""[center]
[quote][i][b][size=300]{category} Challenges[/size][/b][/i][/quote]

[spoiler]
"""

    for challenge in challenges:
        if challenge in NOT_CONSIDER_FOR_BADGES:
            continue
        if challenge["category"] != category:
            continue
        if challenge["num_difficulties"] == 1 and challenge["num_runs"] > 1:
            if not bbcode.endswith('\n'):
                bbcode += '\n'
        for run in challenge["runs"]:
            challenge_with_hyphens = clean_title(challenge['title'])
            topic = run["topic"]

            topic_code = f"[url={topic}" if topic else f"[url={challenge['mal_url']}#{challenge_with_hyphens}" 
            topic_code += f" challenge={challenge_with_hyphens} run={run['num_run']}]"

            for difficulty in run["difficulties"]:
                badge = difficulty["badge"]
                if not difficulty["badge"]:
                    if category in LIMITED_CATEGORIES:
                        continue
                    badge = IMG_PLACEHORDER[0]['image']
                    for categories in IMG_PLACEHORDER:
                        if category in categories['category']:
                            badge = categories['image']

                topic_code += f"[img challenge={challenge_with_hyphens} run={run['num_run']} difficulty={difficulty['num_difficulty']}]{badge}[/img]"
                if challenge["num_difficulties"] == 4:
                    if difficulty["num_difficulty"] == 2:
                        topic_code += "\n"    

            topic_code += "[/url]"



            # Add a newline if there are more than 2 difficulties in the run
            if challenge["num_difficulties"]  >= 2:
                if challenge['title'] != 'May 2021' and challenge['title'] != 'August 2020':
                    topic_code += "\n"
                    if not bbcode.endswith('\n'):
                        bbcode += '\n'
            if category in LIMITED_CATEGORIES:
                if not '[img' in topic_code:
                    topic_code = ''
            if topic_code != '' and challenge["title"].startswith('December'):
                topic_code += '\n'
            bbcode += topic_code
        if challenge["num_runs"] >= 2 and not bbcode.endswith('\n'):
            bbcode += "\n"
        
    bbcode += "\n[/spoiler][/center]"
    return bbcode

def print_bbcode_for_all_categories():
    categories = ["Year", "Franchise", "Creator", "Studios", "Genre", "Theme", "Characters", "Type",
                "Statistics", "Miscellaneous", "Limited", "Monthly", "Series Collections",
                  "Creator Collections", "Staff Collections", "Monthly Anime Club Collections",
                  "Anime Watching Challenge Staff Collections", "Anime Guild Collections", "Affiliates Collections"]
    for category in categories:
        print(generate_bbcode_by_category(category))
        print('\n\n')

def main():
    challenges = retrieve_challenges_sot()
    save_challenges_sot(challenges)
    print_bbcode_for_all_categories()


if __name__ == "__main__":
    main()
