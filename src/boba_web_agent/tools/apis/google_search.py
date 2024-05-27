from typing import Union, Iterable, Dict, List, Tuple

import requests
import json
from os import environ

from boba_python_utils.common_utils import iter_
from boba_python_utils.general_utils.console_util import hprint_message
from boba_python_utils.string_utils import join_

ENV_NAME_GOOGLE_SEARCH_APIKEY = 'GOOGLE_SEARCH_APIKEY'
ENV_NAME_GOOGLE_CSE_ID = 'GOOGLE_CSE_ID'
API_URL_GOOGLE_SEARCH = 'https://www.googleapis.com/customsearch/v1'


def google_search(
        search_term: str,
        start_date: str = None,
        end_date: str = None,
        sites: Union[str, Iterable[str]] = None,
        api_key: str = None,
        cse_id: str = None,
        verbose: bool = True,
        return_raw_results: bool = False,
        **extra_constraints
) -> Union[Dict, List[Tuple[str, str, str]]]:
    api_key = api_key or environ[ENV_NAME_GOOGLE_SEARCH_APIKEY]
    cse_id = cse_id or environ[ENV_NAME_GOOGLE_CSE_ID]

    # add time constraints to search term
    search_term = join_(
        (
            search_term,
            ("after:" + start_date) if start_date else None,
            ("before:" + end_date) if end_date else None,
            *((("site:" + site) for site in iter_(sites)) if sites else ()),
            *((f"{k}:{v}" for k, v in extra_constraints.items()))
        ), sep=' ')

    if verbose:
        hprint_message(
            'search_term', search_term
        )

    # The query parameters
    params = {
        'q': search_term,
        'key': api_key,
        'cx': cse_id
    }

    # Make a GET request to the API
    response = requests.get(API_URL_GOOGLE_SEARCH, params=params)

    # Parse the JSON response
    search_results = json.loads(response.text)

    if return_raw_results:
        return search_results
    else:
        if 'items' in search_results:
            return [
                (item['link'], item['title'], item['snippet'])
                for item in search_results['items']
            ]
        else:
            return []


if __name__ == '__main__':
    print(
        google_search(
            search_term='AAPL stock top stories',
            start_date='2023-04-02',
            end_date='2023-04-09'
        )
    )
