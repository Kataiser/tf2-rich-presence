# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import datetime
import re

import requests
from bs4 import BeautifulSoup


def main(silent=False):
    # watch out for rate limiting (60 requests per hour, this uses 3 per run)

    with open('Changelogs_source.html', 'r') as changelogs_source_html:
        source_html = changelogs_source_html.read()

    api_response = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases', headers={'User-Agent': 'Kataiser-TF2-Rich-Presence'})
    api_response_p2 = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases', headers={'User-Agent': 'Kataiser-TF2-Rich-Presence'}, params={'page': '2'})
    api_response_json = api_response.json() + api_response_p2.json()
    check_rate_limited(str(api_response_json))
    releases = []
    bodies = []

    for found_release in api_response_json:
        version_num = found_release['tag_name']
        body = found_release['body']
        published = found_release['published_at'][:10]
        releases.append({'version_num': version_num, 'published': published})
        bodies.append(body)

        if not silent:
            print(version_num)
            print(published)
            print(body)
            print()

    bodies_combined = '\n\nSPLITTER\n\n'.join(bodies)

    as_html_response = requests.post('https://api.github.com/markdown/raw', data=bodies_combined, headers={'User-Agent': 'Kataiser-TF2-Rich-Presence', 'Content-Type': 'text/plain'})
    as_html = as_html_response.text.replace('h2', 'h3')
    ratelimit_remaining = int(as_html_response.headers['X-RateLimit-Remaining']) - 1
    check_rate_limited(as_html)

    htmls = as_html.split('\n<p>SPLITTER</p>\n')
    extended_htmls = []

    htmls_index = 0
    for release in releases:
        extended_htmls.append(f"<h4><a class=\"version_a\" href=\"https://github.com/Kataiser/tf2-rich-presence/releases/tag/"
                              f"{release['version_num']}\">{release['version_num']}</a> ({release['published']})</h4>{htmls[htmls_index]}")
        htmls_index += 1

    generated_html_logs = ''.join(extended_htmls)
    generated_html_pretty = prettify_custom(BeautifulSoup(generated_html_logs, 'lxml')).replace('<html>\n    <body>', '').replace('</body>\n</html>', '').replace('2019-11-28', '2019-12-09')
    generated_html_with_items = source_html.replace('<!--REPLACEME-->', generated_html_pretty)
    generated_html = re.compile(r' aria-hidden="true" class="anchor" href="#(.+)" id="(.+)"').sub('', generated_html_with_items)

    with open('Changelogs.html', 'w') as changelog_file:
        changelog_file.write(generated_html)

    if not silent:
        print(f"\nDone (finished at {datetime.datetime.now().strftime('%I:%M:%S %p')})")
        print(f"Github requests remaining: {ratelimit_remaining}")

    return ratelimit_remaining


# runs bs4's prettify method, but with a custom indent width
# modified from https://stackoverflow.com/questions/15509397/custom-indent-width-for-beautifulsoup-prettify
def prettify_custom(soup):
    r = re.compile(r'^(\s*)', re.MULTILINE)
    return r.sub(r'\1' * 4, soup.prettify(encoding=None, formatter='html5'))


def check_rate_limited(text):
    if 'API rate limit exceeded' in text:
        print(f"\nGithub API rate limit exceeded at {datetime.datetime.now().strftime('%I:%M:%S %p')}, try again later")
        print(text)
        raise SystemExit


if __name__ == '__main__':
    print(main())
