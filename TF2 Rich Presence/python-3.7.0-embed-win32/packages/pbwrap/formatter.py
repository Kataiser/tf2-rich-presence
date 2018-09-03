"""Contains function that manipulate the API returns for easier data manipulation."""
import re
import xml.etree.ElementTree as et

from pbwrap.models import Paste, User


def paste_list_from_xml(xml_paste):
    """Input an xml list and return a list of paste objects.

        :param xml_paste: An xml formatted response containing Paste information
        :type: string

        :returns: a list of Paste objects parsed from the input xml formatted string
        :rtype: list(Paste)
    """
    paste_list = list()

    # xml demands a base root to create xml element from string.
    # So we have to hardcode it.
    root = et.fromstring("<root>" + xml_paste + "</root>")

    # Iterate <paste> child elements and create a paste object.
    for paste_root in root:
        paste_dict = dict()

        for paste_element in paste_root:
            key = paste_element.tag.split("_", 1)[-1]
            value = paste_element.text

            paste_dict[key] = value

        paste_list.append(Paste(paste_dict))

    return paste_list


def archive_url_format(archive_html):
    """Return a list with recent pastes ids

        :param archive_html: raw html of the archive url
        :type archive_html: string

        :returns: a list containing paste ids
        :rtype: list
    """
    pastes_ids = list()
    # Regex Magic
    pastes = re.findall(r"/><a href=\"/(.+?)\">", archive_html)

    for paste_id in pastes:

        if re.match(r"[a-zA-Z0-9]{8}", paste_id) is not None:
            pastes_ids.append(paste_id)

    return pastes_ids


def user_from_xml(user_xml_string):
    """Return user dictionary from an xml format string

        :param user_xml_string: xml formatted string containing user information
        :type user_xml_string: string

        :returns: A dictionary containing the user info
        :rtype: User
    """
    root = et.fromstring(user_xml_string)
    user_dict = dict()

    for user in root:
        key = user.tag.split("user_")[-1]
        value = user.text
        user_dict[key] = value

    return User(user_dict)
