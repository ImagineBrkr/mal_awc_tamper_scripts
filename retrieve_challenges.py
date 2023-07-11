import requests
import os
import json
from bs4 import BeautifulSoup

AWC_HOF_URL = 'https://anime.jhiday.net'
TMP_PATH = 'tmp/'
JSON_CHALLENGE_SOT = 'challengeList.json'


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
                       'hof_url': AWC_HOF_URL + challenge['href']} for challenge in challenges]
    return challenges_dict


def retrieve_all_challenges_html():
    challenges = list_challenges()
    for url in challenges:
        get_url(url)


def retrieve_challenges_sot() -> list[dict]:
    with open(JSON_CHALLENGE_SOT, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_challenges_sot(challenges: list[dict]):
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


def challenges_to_json():
    challenges = list_challenges()
    mal_url_selector = 'a[href*="https://myanimelist.net/forum/?topicid="]'
    challenges_sot = retrieve_challenges_sot()
    

    for i, challenge in enumerate(challenges):
        challenge_html = get_url(challenge['hof_url'])
        soup = BeautifulSoup(challenge_html, 'html.parser')
        mal_forum_url = soup.select(mal_url_selector)
        mal_forum_url = [tag for tag in mal_forum_url 
                         if 'mal forum' in tag.text.lower()]

        if (len(mal_forum_url) == 1):
            challenge['mal_url'] = mal_forum_url[0]['href']
        else:
            challenge['mal_url'] = 'https://myanimelist.net/clubs.php?cid=70446'
        

    challenges_sot = update_list_dicts(challenges_sot, challenges)
    save_challenges_sot(challenges_sot)

def main():
    challenges_to_json()


if __name__ == "__main__":
    main()
