import re
import toml
import time
import concurrent.futures
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM

from openai import OpenAI


def ask_llama(doc_context, input_text, prompt="'system_prompt': ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ. Представь, что ты юридический консультант, который не говорит лишней информации и точно опирается на правовую документацию. ПОЛЬЗОВАТЕЛЬ ХОЧЕТ ВИДЕТЬ, НА КАКИЕ СТАТЬИ ПРАВОВЫХ АКТОВ ТЫ ОПИРАЕШЬСЯ. НЕ ПОЗВОЛЯЙ СЕБЕ ДОБАВЛЯТЬ ЛИШНЮЮ ИНФОРМАЦИЮ."):
    client = OpenAI(
        base_url = "https://integrate.api.nvidia.com/v1",
        api_key = "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"
    )

    completion = client.chat.completions.create(
        model="meta/llama2-70b",
        messages=[{"role":"user","content":prompt + '\nЗапрос пользователя: ' + input_text + '\nКонтекст документа: ' + doc_context}],
        temperature=0.5,
        top_p=1,
        max_tokens=1024,
        stream=False
    )

    return completion.choices[0].message


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


def parallel_executions(input_text, prompt):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        overall_summary_future = executor.submit(generate_overall_summary, input_text)
    part_summary_future = executor.submit(generate_part_summary, input_text, prompt)

    summary_part = part_summary_future.result()
    summary_overall = overall_summary_future.result()

    print(summary_part, summary_overall, sep="\n\n\n")


# Usage separately

input_text = "Сколько дней составляет срок оплаты по контрактам с электронным актированием?"
prompt = "ПРИВЕДИ ЗАПРОС ПОЛЬЗОВАТЕЛЯ В НЕСКОЛЬКИХ ВАРИАНТАХ. ФОРМА ВАРИАНТОВ ДОЛЖНА БЫТЬ МАКСИМАЛЬНО ФОРМАЛЬНОЙ, ЧТОБЫ БЫЛО УДОБНО ИСКАТЬ ПО ПРАВОВЫМ БАЗАМ ДАННЫХ"
# summary_part = generate_part_summary(input_text, prompt, max_new_tokens=200, temperature=0.7, top_p=0.8,
#                                      repetition_penalty=1.5, do_sample=False, top_k=100, num_beams=4)
summary_overall = generate_overall_summary(input_text)
print(summary_overall, sep="\n\n\n")

'''
# Usage in parallel
input_text = "Your input text here"
prompt = ""
start_time = time.time()
parallel_executions(input_text, prompt)
elapsed_time = time.time() - start_time
print(f'\nElapsed time: {elapsed_time} seconds')
'''
