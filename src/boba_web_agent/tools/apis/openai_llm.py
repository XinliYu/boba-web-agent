from typing import Union, List, Dict, Iterable, Sequence, Tuple

import openai
from enum import Enum
from os import environ, path

from boba_python_utils.general_utils.console_util import hprint_message
from boba_python_utils.io_utils.text_io import read_all_text

ENV_NAME_OPENAI_API_KEY = 'OPENAI_APIKEY'


class OpenAIModels(str, Enum):
    """
    Enumeration for major supported ChatGPT models.
    See details at https://platform.openai.com/docs/models/overview
    """
    GPT3 = 'gpt-3.5-turbo'
    GPT3_16K = 'gpt-3.5-turbo-16k'
    GPT4 = "gpt-4"
    GPT4_TURBO = 'gpt-4-turbo'
    GPT4_32K = "gpt-4-32k-0613"
    GPT4O = "gpt-4o"


DEFAULT_MAX_TOKENS = {
    f'{OpenAIModels.GPT4}': 2048,
    f'{OpenAIModels.GPT4_32K}': 3096,
    f'{OpenAIModels.GPT3}': 1024,
    f'{OpenAIModels.GPT3_16K}': 3096,
    f'{OpenAIModels.GPT4O}': 4096
}


def _get_messages(prompt_or_messages: Union[str, Dict, Sequence[str], Sequence[Dict]]):
    if isinstance(prompt_or_messages, str):
        if path.exists(prompt_or_messages):
            prompt_or_messages = read_all_text(prompt_or_messages)
        return [
            {
                'role': 'user',
                'content': prompt_or_messages
            }
        ]
    elif isinstance(prompt_or_messages, Dict):
        return [prompt_or_messages]
    elif isinstance(prompt_or_messages, (List, Tuple)):
        if isinstance(prompt_or_messages[0], str):
            messages = []
            for i in range(0, len(prompt_or_messages) - 1, 2):
                messages.extend(
                    (
                        {
                            'role': 'user',
                            'content': prompt_or_messages[i]
                        },
                        {
                            'role': 'assistant',
                            'content': prompt_or_messages[i + 1]
                        }
                    )
                )
            messages.append(
                {
                    'role': 'user',
                    'content': prompt_or_messages[-1]
                }
            )
            return messages
        elif isinstance(prompt_or_messages[0], Dict):
            return list(prompt_or_messages)
    raise ValueError(
        "'prompt_or_messages' must be one of str, Dict, or a sequence of strs or Dicts"
    )


def generate_text(
        prompt_or_messages: str,
        model: OpenAIModels = OpenAIModels.GPT4_TURBO,
        max_new_tokens: int = None,
        n: int = 1,
        stop: str = None,
        temperature: float = 0.7,
        api_key: str = None,
        return_raw_results: bool = False,
        verbose: bool = False,
        **kwargs
):
    """

    Args:
        prompt_or_messages: The prompt or messages to generate text from.
        model: The OpenAI model to use for generating text.
        max_new_tokens: The maximum number of new tokens to generate (excluding the prompt).
        n: The number of candidate answers to generate.
        stop: Provide sequences where the API will stop generating further tokens.
        temperature: Controls the "creativity" of the generated text. A higher temperature will result in more creative responses, while a lower temperature will result in more predictable responses.
        verbose: True to print out parameter values.
        api_key: Your OpenAI API key. If not provided, the key will be read from the environment variable `ENV_NAME_OPENAI_API_KEY`.
        return_raw_results: Whether to return the raw results from the API.

    Returns:
        The generated text, or the raw results returned by the API.

    Examples:
        >>> generate_text(
        ...    prompt_or_messages='hello',
        ...    model=OpenAIModels.GPT4,
        ...    max_new_tokens=1024,
        ...    n=1,
        ...    stop=None,
        ...    temperature=0,
        ...    api_key=None,
        ...    return_raw_results=False
        ... )
        'Hello! How can I help you today?'

        >>> generate_text(
        ...    prompt_or_messages='What would be a good company name for a company that makes colorful socks?',
        ...    model=OpenAIModels.GPT4,
        ...    max_new_tokens=1024,
        ...    n=2,
        ...    stop=None,
        ...    temperature=0,
        ...    api_key=None,
        ...    return_raw_results=False
        ... )
        ['SockSpectrum', 'SockSpectrum']
    """
    model = f'{model}'
    if not max_new_tokens:
        max_new_tokens = DEFAULT_MAX_TOKENS.get(model, 2048)
    if verbose:
        hprint_message(
            'prompt_or_messages', prompt_or_messages,
            'model', model,
            'max_tokens', max_new_tokens,
            'n', n,
            'stop', stop,
            'temperature', temperature,
            'return_raw_results', return_raw_results
        )
    messages = _get_messages(prompt_or_messages)
    api_key = api_key or environ[ENV_NAME_OPENAI_API_KEY]

    client = openai.OpenAI(api_key=api_key)

    completions = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_new_tokens,
        n=n,
        stop=stop,
        temperature=temperature,
        **kwargs
    )

    if return_raw_results:
        # An example raw result
        # {
        #     "choices": [
        #         {
        #             "finish_reason": "stop",
        #             "index": 0,
        #             "message": {
        #                 "content": "Hello! How can I help you today?",
        #                 "role": "assistant"
        #             }
        #         }
        #     ],
        #     "created": 1686840573,
        #     "id": "chatcmpl-7RiZxKVtbDTCPJiEOAoKDHB9mJ3mF",
        #     "model": "gpt-4-0314",
        #     "object": "chat.completion",
        #     "usage": {
        #         "completion_tokens": 9,
        #         "prompt_tokens": 8,
        #         "total_tokens": 17
        #     }
        # }
        return completions

    if n == 1:
        return completions.choices[0].message.content.strip()
    else:
        return [x.message.content.strip() for x in completions.choices]
