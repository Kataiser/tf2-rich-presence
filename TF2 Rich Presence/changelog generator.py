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
            <style>
                body {
                    text-align: center;
                    font-family: sans-serif;
                    background: #111314;
                }
                div {
                    background: white;
                    width: 1000px;
                    margin: 0 auto;
                    text-align: left;
                    padding: 0 20px;
                    border: 4px solid #7289DA;
                }
                h4 {
                    font-weight: lighter;
                    border-bottom: 1px solid #99AAB5;
                    padding-top: 10px;
                    font-size: 1.5em;
                    color: rgba(0, 0, 0, 0.8);
                }
                a {
                    text-decoration: none;
                }
                h3 {
                    padding-left: 20px;
                }
                ul {
                    padding-left: 60px;
                }
                p {
                    padding-left: 20px;
                    padding-bottom: 20px;
                }
                .version_a {
                    font-size: 1.25em;
                }
                img {
                    width: 1em;
                    height: 1em;
                    vertical-align: middle;
                    padding-bottom: 0.3em;
                }
            </style>
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
