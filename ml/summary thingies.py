import re
import concurrent.futures
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM


def generate_overall_summary(input_text):
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


def generate_part_summary(input_text, prompt, max_new_tokens=120, temperature=0.5, top_p=0.95, repetition_penalty=1.2,
                          do_sample=True, top_k=50, num_beams=1):
    WHITESPACE_HANDLER = lambda k: re.sub('\s+', ' ', re.sub('\n+', ' ', k.strip()))

    model_name = "llama-2-70b"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    input_ids = \
        tokenizer([WHITESPACE_HANDLER(input_text), WHITESPACE_HANDLER(prompt)], return_tensors="pt", padding=True)[
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
"""
input_text = "Your input text here"
prompt = "Your prompt here"
summary_part = generate_part_summary(input_text, prompt, max_new_tokens=200, temperature=0.7, top_p=0.8,
                                     repetition_penalty=1.5, do_sample=False, top_k=100, num_beams=4)
summary_overall = generate_overall_summary(input_text)
print(summary_part, summary_overall, sep="\n\n\n")
"""

# Usage in parallel
input_text = "Your input text here"
prompt = "Your prompt here"
parallel_executions(input_text, prompt)
