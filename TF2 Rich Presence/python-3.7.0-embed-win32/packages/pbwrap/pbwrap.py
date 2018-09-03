"""Contains a wrapper for the Pastebin API for easier usage."""
import os

import requests

import pbwrap.formatter as formatter
from pbwrap.constants import API_OPTIONS
from pbwrap.models import Paste


class Pastebin(object):
    """Pastebin class represents your communication with the Pastebin API through its functions
       you can use every API endpoint avalaible.

       Most functions require at least an api_dev_key parameter.
       Functions for manipulating your pastes through the API require an api_user_key.
    """

    def __init__(self, api_dev_key=None):
        """Instantiate a Pastebin Object

           :param api_dev_key: Your API Pastebin key
           :type api_dev_key: string
        """
        self.api_dev_key = api_dev_key
        self.api_user_key = None

    def authenticate(self, username, password):
        """Authenticate through the API login endpoint
           Your api_user_key attribute is set automatically

           :type username: string
           :param username: Your username

           :type password: string
           :param password: Your password

           :returns: your user_id key
           :rtype: string
        """
        data = {
            "api_dev_key": self.api_dev_key,
            "api_user_name": username,
            "api_user_password": password,
        }

        r = requests.post("https://pastebin.com/api/api_login.php", data)

        self.api_user_key = r.text

        return self.api_user_key

    def get_user_details(self):
        """Return user details in a dictionary.
           Can only be user after authenticating with get_user_id(username, password).

           :returns: dictionary containing user details
           :rtype: dictionary
        """
        data = {"api_dev_key": self.api_dev_key, "api_user_key": self.api_user_key}

        r = requests.post("https://pastebin.com/api/api_post.php", data)

        return formatter.user_from_xml(r.text)

    def get_trending(self):
        """Return a list of paste objects created from the most trending pastes

           :returns: a list of Paste objects
           :rtype: list
        """
        data = {"api_dev_key": self.api_dev_key, "api_option": API_OPTIONS["TREND"]}

        r = requests.post("https://pastebin.com/api/api_post.php", data)

        return formatter.paste_list_from_xml(r.text)

    @staticmethod
    def get_archive():
        """Return archive paste link list.Archive contains 25 most recent pastes.

           :returns: a list of url strings
           :rtype: list
        """
        r = requests.get("https://pastebin.com/archive")

        return formatter.archive_url_format(r.text)

    @staticmethod
    def get_raw_paste(paste_id):
        """Return raw string of given paste_id.

           get_raw_paste(pasted_id)

           :type paste_id: string
           :param paste_id: The ID key of the paste

           :returns: the text of the paste
           :rtype: string
        """
        r = requests.get("https://pastebin.com/raw/" + paste_id)
        return r.text

    def create_paste(
        self,
        api_paste_code,
        api_paste_private=0,
        api_paste_name=None,
        api_paste_expire_date=None,
        api_paste_format=None,
    ):
        """Create a new paste if succesfull return it's url.

           :type api_paste_code: string
           :param api_paste_code: your paste text

           :type api_paste_private: int
           :param api_paste_private: valid values=0(public),1(unlisted),2(private)

           :type api_paste_name: string
           :param api_user_name: your paste name

           :type api_paste_expire_date: string
           :param api_paste_expire_date: check documentation for valid values

           :type api_paste_format: string
           :param api_paste_format: check documentation for valid values

           :returns: new paste url
           :rtype: string
        """
        data = {
            "api_dev_key": self.api_dev_key,
            "api_user_key": self.api_user_key,
            "api_paste_code": api_paste_code,
            "api_paste_private": api_paste_private,
            "api_paste_name": api_paste_name,
            "api_paste_expire_date": api_paste_expire_date,
            "api_paste_format": api_paste_format,
            "api_option": API_OPTIONS["PASTE"],
        }

        # Filter data and remove dictionary None keys.
        filtered_data = {k: v for k, v in data.items() if v is not None}

        r = requests.post("https://pastebin.com/api/api_post.php", filtered_data)

        return r.text

    def create_paste_from_file(
        self,
        filepath,
        api_paste_private=0,
        api_paste_name=None,
        api_paste_expire_date=None,
        api_paste_format=None,
    ):
        """Create a new paste from file if succesfull return it's url.

            :type filepath: string
            :param filepath: the path of the file

            :type api_paste_private: int
            :param api_paste_private: valid values=0(public),1(unlisted),2(private)

            :type api_paste_name: string
            :param api_user_name: your paste name

            :type api_paste_expire_date: string
            :param api_paste_expire_date: check documentation for valid values

            :type api_paste_format: string
            :param api_paste_format: check documentation for valid values

            :returns: new paste url
            :rtype: string
            """
        if os.path.exists(filepath):
            api_paste_code = open(filepath).read()
            return self.create_paste(
                api_paste_code,
                api_paste_private,
                api_paste_name,
                api_paste_expire_date,
                api_paste_format,
            )
        print("File not found")
        return None

    def get_user_pastes(self, api_results_limit=None):
        """Return a list of Pastes created from the user

            :type api_results_limit: int
            :param api_results_limit: min=1, max=1000

            :returns: a list of Pastes created from the user
            :rtype: list
        """
        data = {
            "api_dev_key": self.api_dev_key,
            "api_user_key": self.api_user_key,
            "api_results_limit": api_results_limit,
            "api_option": API_OPTIONS["USER_PASTE"],
        }

        # Filter data and remove dictionary None keys.
        filtered_data = {k: v for k, v in data.items() if v is not None}

        r = requests.post("https://pastebin.com/api/api_post.php", filtered_data)

        if r.text:
            return formatter.paste_list_from_xml(r.text)

        return "No pastes in this account"

    def get_user_raw_paste(self, api_paste_key):
        """Return the raw data of a user paste(even private pastes!) as string.

            :param api_paste_key: the id key of the paste you want to fetch
            :type api_paste_key: string

            :returns: the text of the paste
            :rtype: string
        """
        data = {
            "api_dev_key": self.api_dev_key,
            "api_user_key": self.api_user_key,
            "api_paste_key": api_paste_key,
            "api_option": API_OPTIONS["USER_RAW_PASTE"],
        }

        r = requests.post("https://pastebin.com/api/api_post.php", data)

        return r.text

    def delete_user_paste(self, api_paste_key):
        """Deletes a paste created by the user.

            :param api_paste_key: the id key of the paste you want to delete
            :type api_paste_key: string

            :returns: api response
            :rtype: string
        """
        data = {
            "api_dev_key": self.api_dev_key,
            "api_user_key": self.api_user_key,
            "api_paste_key": api_paste_key,
            "api_option": API_OPTIONS["DELETE_PASTE"],
        }

        r = requests.post("https://pastebin.com/api/api_post.php", data)

        return r.text

    @staticmethod
    def get_recent_pastes(limit=50, lang=None):
        """get_recent_pastes(limit=50, lang=None)

            Return a list containing dictionaries of paste.

            :param limit: the limit of the items returned defaults to 50
            :type limit: int

            :param lang: return only pastes from certain language defaults to None
            :type lang: string

            :returns: list of Paste objects.
            :rtype: list(Paste)
        """
        parameters = {"limit": limit, "lang": lang}

        r = requests.get(
            "https://scrape.pastebin.com/api_scraping.php", params=parameters
        )
        paste_list = list()
        for paste in r.json():
            paste_list.append(Paste(paste))
        return paste_list

    @staticmethod
    def scrape_raw_paste(paste_key):
        """scrape_raw_paste(paste_key)

            Return a string containing the text of the paste.

            :param paste_key: the unique key of the paste you want to scrape
            :type paste_key: string

            :returns: raw string containing the text of the paste
            :rtype: string
        """
        parameter = {"i": paste_key}
        r = requests.get(
            "https://scrape.pastebin.com/api_scrape_item.php", params=parameter
        )

        return r.text

    @staticmethod
    def scrape_paste_metadata(paste_key):
        """scrape_paste_metadata(paste_key)

            Return a dictionary containing the metadata of the paste.

            :param paste_key: the unique key of the paste you want to scrape
            :type paste_key: string

            :returns: dictionary containing the metadata of the paste
            :rtype: dictionary
        """
        parameter = {"i": paste_key}
        r = requests.get(
            "https://scrape.pastebin.com/api_scrape_item_meta.php", params=parameter
        )

        return r.json()
