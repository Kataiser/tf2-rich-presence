import datetime

import requests
from bs4 import BeautifulSoup


def main():
    # watch out for rate limiting (60 requests per hour)

    changelog_blank = """
        <!DOCTYPE html>
        <html lang="en-us">
        <head>
            <title>
                TF2 Rich Presence changelogs
            </title>
            <meta charset="UTF-8">
            <link href="https://github.com/Kataiser/tf2-rich-presence/raw/master/TF2%20Rich%20Presence/tf2_logo_blurple.ico" rel="shortcut icon" type="image/x-icon">
            <link href="https://github.com/Kataiser/tf2-rich-presence/raw/master/TF2%20Rich%20Presence/changelogs.css" rel="stylesheet">
            <link href="changelogs.css" rel="stylesheet">
            <link href="resources/changelogs.css" rel="stylesheet">
        </head>
        <body>
        <div>
            <h1><a href="https://github.com/Kataiser/tf2-rich-presence">
            <img src="https://github.com/Kataiser/tf2-rich-presence/raw/master/TF2%20Rich%20Presence/tf2_logo_blurple.ico">
            TF2 Rich Presence</a> changelogs</h1>
        {replace}
        </div>
        </body>
        </html>"""

    requests_made = 1
    api_response = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases').json()
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

    with open('changelogs.html', 'w') as changelog_file:
        generated_html = changelog_blank.replace('{replace}', ''.join(htmls))

        if 'API rate limit exceeded' in generated_html:
            print(f"\nGithub API rate limit exceeded at {datetime.datetime.now().strftime('%I:%M:%S %p')}, try again later")
            raise SystemExit
        else:
            generated_html_pretty = BeautifulSoup(generated_html, 'lxml').prettify(formatter='html5')
            changelog_file.write(generated_html_pretty)

    print(f"\nDone (finished at {datetime.datetime.now().strftime('%I:%M:%S %p')})\nGithub API requests made: {requests_made}")


if __name__ == '__main__':
    main()
