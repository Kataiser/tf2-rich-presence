import requests


class Paste:
    """Defines a Paste from Pastebin paste contains the following fields:
       key,
       date,
       title,
       size,
       expire_date,
       private,
       format_short,
       format_long,
       url,
       hits.
    """

    def __init__(self, paste_dict):
        self.key = None
        for k, v in paste_dict.items():
            setattr(self, k, v)

    def __cmp__(self, x):
        return vars(self) == vars(x)

    def get_raw_text(self):
        """Fetch the text of a paste via the public API.
            :returns: the paste's text
            :rtype: string, None
        """
        if self.key is not None:
            r = requests.get("https://pastebin.com/raw/" + self.key)
            return r.text
        return None

    def scrape_raw_text(self):
        """Fetch the ext of a paste via the Paid API.
            :returns: the paste's text
            :rtype: string, None
        """
        if self.key is not None:
            parameter = {"i": self.key}
            r = requests.get(
                "https://scrape.pastebin.com/api_scrape_item.php", params=parameter
            )

            return r.text
        return None


class User:
    """Defines a user contains the following fields:
       name
       format_short
       expiration
       avatar_url
       private
       website
       email
       location
       account_type
    """

    def __init__(self, user_dict):
        for k, v in user_dict.items():
            setattr(self, k, v)

    def __cmp__(self, x):
        return vars(self) == vars(x)
