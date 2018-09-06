import datetime
import re

import requests
from bs4 import BeautifulSoup


def main():
    # watch out for rate limiting (60 requests per hour)

    with open('changelogs_source.html', 'r') as changelogs_source_html:
        source_html = changelogs_source_html.read()

    requests_made = 1
    api_response = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases').json()
    check_rate_limited(str(api_response))
    htmls = []

    for release in api_response:
        version_num = release['tag_name']
        body = release['body']
        published = release['published_at'][:10]

        as_html = requests.post('https://api.github.com/markdown/raw', data=body, headers={'Content-Type': 'text/plain'}).text.replace('h2', 'h3')
        requests_made += 1
        htmls.append(f'<h4><a class="version_a" href="https://github.com/Kataiser/tf2-rich-presence/releases/tag/{version_num}">{version_num}</a> ({published})</h4>{as_html}')

        print(version_num)
        print(body)
        print(as_html.replace('\n', ''))
        print()

        check_rate_limited(as_html)

    generated_html_logs = ''.join(htmls)
    generated_html_pretty = prettify_custom(BeautifulSoup(generated_html_logs, 'lxml'))

    generated_html = source_html.replace('<!--REPLACEME-->', generated_html_pretty)
    with open('changelogs.html', 'w') as changelog_file:
        changelog_file.write(generated_html)

    print(f"\nDone (finished at {datetime.datetime.now().strftime('%I:%M:%S %p')})\nGithub API requests made: {requests_made}")


# runs bs4's pretty method, but with a custom indent width
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
    main()
