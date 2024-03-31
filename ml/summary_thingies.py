import re
import toml
import time
import asyncio
import json
import requests
import concurrent.futures
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM

from openai import OpenAI


def ask_llama(input_text,
              prompt="'system_prompt': ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ. Представь, что ты юридический консультант, который не говорит лишней информации и точно опирается на правовую документацию. ПОЛЬЗОВАТЕЛЬ ХОЧЕТ ВИДЕТЬ, НА КАКИЕ СТАТЬИ ПРАВОВЫХ АКТОВ ТЫ ОПИРАЕШЬСЯ. НЕ ПОЗВОЛЯЙ СЕБЕ ДОБАВЛЯТЬ ЛИШНЮЮ ИНФОРМАЦИЮ.",
              doc_context=""):
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="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"
    )

    completion = client.chat.completions.create(
        model="meta/llama2-70b",
        messages=[{"role": "user",
                   "content": prompt + '\nЗапрос пользователя: ' + input_text + '\nКонтекст документа: ' + doc_context}],
        temperature=0.25,
        top_p=1,
        max_tokens=1024,
        stream=False
    )

    return completion.choices[0].message.content


def read_toml_base(file_path):
    with open(file_path, 'r') as file:
        data = toml.load(file)
    return data


def generate_overall_summary(input_text):  # input_text - Запрос пользователя
    WHITESPACE_HANDLER = lambda k: re.sub('\s+', ' ', re.sub('\n+', ' ', k.strip()))

    model_name = "csebuetnlp/mT5_multilingual_XLSum"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    input_ids = tokenizer(
        [WHITESPACE_HANDLER(input_text)],
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=1024
    )["input_ids"]

    output_ids = model.generate(
        input_ids=input_ids,
        max_length=120,
        no_repeat_ngram_size=2,
        num_beams=4
    )[0]

    summary = tokenizer.decode(
        output_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )

    return summary


def generate_part_summary(input_text, prompt, max_new_tokens=300, temperature=0.5, top_p=0.95, repetition_penalty=1.2,
                          # input_text - Запрос пользователя, prompt - Промпт для саммари (фильтры и контекст)
                          do_sample=True, top_k=50, num_beams=1):
    WHITESPACE_HANDLER = lambda k: re.sub('\s+', ' ', re.sub('\n+', ' ', k.strip()))

    model_name = "llama-2-70b"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    input_ids = \
        tokenizer([WHITESPACE_HANDLER("Контекст:" + input_text), WHITESPACE_HANDLER("Промпт:" + prompt)],
                  return_tensors="pt", padding=True)[
            "input_ids"]

    output_ids = model.generate(
        input_ids=input_ids,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
        do_sample=do_sample,
        top_k=top_k,
        num_beams=num_beams
    )

    summary = tokenizer.batch_decode(output_ids, skip_special_tokens=True)

    return summary


def ask_yandex(input_text='Тестовый запрос', prompt='Это тестовый запрос'):
    folder_id = 'b1ghp7ek9a8v0c3e2qs0'
    gpt_api_key = 'AQVNyVa4CuEs9kZxUHwzyL8fUS_SihhIDni1kZti'
    yandex_gpt_api_url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'

    messages = [
        {
            "role": "system",
            "text": prompt
        },
        {
            "role": "user",
            "text": input_text
        }
    ]
    response = requests.post(
        yandex_gpt_api_url,
        headers={
            "Authorization": f"Api-Key {gpt_api_key}",
            "x-folder-id": folder_id
        },
        json={
            "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6
            },
            "messages": messages
        },
    )
    response = response.json()
    return response['result']['alternatives'][0]['message']['text']
