# -*- coding: utf-8 -*-
import multiprocessing
import time
from joblib import Parallel, delayed
from json import loads
from ml.database_preparation import main_generate_data_store
from ml.summary_thingies import generate_overall_summary, ask_llama, ask_yandex
from ml.database_querying import query_from_chrome


def remove_duplicates(input_list):
    input_set = set(input_list)
    return ['' if s in input_set else s for s in input_list]


input_text = "Сколько дней составляет срок оплаты по контрактам с электронным актированием?"

prompt_llama_variants = '''
"'system_prompt': 'ОБЯЗАТЕЛЬНО ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ. Предложи два варианта  перефразирования запроса пользователя на русском языке. Они не должны быть искажены по смыслу, но должны быть максимально отличными по лексикону. ПИШИ В КАНЦЕЛЯРСКОМ СТИЛЕ НА РУССКОМ.'"
'''

prompt_yandex_variants = '''
Ты юридический консультант, который хочет быть максимально точным и полезным. Предложи два варианта  перефразирования запроса пользователя на русском языке. Они не должны быть искажены по смыслу, но должны быть максимально отличными по лексикону. ПИШИ В КАНЦЕЛЯРСКОМ СТИЛЕ, опираясь на "Федеральный закон nо закупках товаров, работ, услуг отдельными видами юридических лиц. СТРОГИЙ ФОРМАТ  ОТВЕТА: ["<Вариант1>", "<Вариант2>"]
'''
prompt_yandex_interpretate = '''
Ты система по конкретизации запросов пользователя для базы данных. В ТВОЁМ ОТВЕТЕ НЕ ДОЛЖНО БЫТЬ НИЧЕГО ПОМИМО ПЕРЕФРАЗИРОВАННОГО ЗАПРОСА. Перефразируй вопрос пользователя, сделав его более формальным, опираясь на "Федеральный закон nо закупках товаров, работ, услуг отдельными видами юридических лиц"
'''
prompt_yandex_legals = '''
Ты система юридической поддержки. Твоя задача, опираться на "Федеральный закон "О закупках товаров, работ, услуг отдельными видами юридических лиц" от 18.07.2011 N 223-ФЗ (последняя редакция)" и "Федеральный закон "О контрактной системе в сфере закупок товаров, работ, услуг для обеспечения государственных и муниципальных нужд" от 05.04.2013 N 44-ФЗ (последняя редакция)". В ЗАПРОСЕ ПОЛЬЗОВАТЕЛЯ НАЙДИ ВСЕ ССЫЛКИ НА ФЕДЕРАЛЬНЫЕ ЗАКОНЫ И СТАТЬИ, КОТОРЫЕ ОТНОСЯТСЯ К ВОПРОСУ ПОЛЬЗОВАТЕЛЯ. МАКСИМАЛЬНО ТОЧНО ОПИСЫВАЙ НОРМАТИВНО-ПРАВОВЫЕ АКТЫ, КОТОРЫЕ ТЫ НАШЁЛ.
'''
prompt_yandex_pre_final = '''
Ты агент правовой техподдержки. Ты должен отвечать максимально точно, опираясь на КОНТЕКСТ-ДОКУМЕНТ и "Федеральный закон "О контрактной системе в сфере закупок товаров, работ, услуг для обеспечения государственных и муниципальных нужд" от 05.04.2013 N 44-ФЗ (последняя редакция)" и "Федеральный закон "О закупках товаров, работ, услуг отдельными видами юридических лиц" от 18.07.2011 N 223-ФЗ (последняя редакция)". Ты должен составить идеальный, который будет ссылаться на нормативно-правовые акты, быть дружелюбным и понятным пользователю.
'''
prompt_yandex_final = '''
Ты консультант юридической поддержки. Основываясь на ответе по вопросу пользователя и на списке правовых актов, касающихся его вопроса, СФОРМИРУЙ ИДЕАЛЬНЫЙ ОТВЕТ В ФОРМАТЕ: 1. Ответ на ворос пользователя; 2. Список нормативно-правовых актов
'''


def main_parallel():
    start_time = time.time()

    input_data = [(input_text, prompt_yandex_interpretate), (input_text, prompt_yandex_variants)]
    with Parallel(n_jobs=2) as parallel_1:
        results_1 = parallel_1(delayed(ask_yandex)(input_data[i]) for i in range(len(input_data)))
    result_interpretate = results_1[0]
    result_variant_1, result_variant_2 = loads(results_1[1])

    print(f"\n\n\n---\n\n\nVariants + interpretate time: {time.time() - start_time}\n\n\n---\n\n\n")

    input_data = [result_interpretate, result_variant_1, result_variant_2]
    with Parallel(n_jobs=3) as parallel_2:
        results_2 = parallel_2(delayed(query_from_chrome)(input_data[i]) for i in range(len(input_data)))
    result_query_1, result_query_2, result_query_3 = remove_duplicates(results_2)

    print(f"\n\n\n---\n\n\nQuery time: {time.time() - start_time}\n\n\n---\n\n\n")

    query_context = '\nКОНТЕКСТ-ДОКУМЕНТ: ' + result_query_1 + '\n' + result_query_2 + '\n' + result_query_3
    yagpt_answer = ask_yandex(input_text + query_context, prompt_yandex_pre_final)

    print(f"\n\n\n---\n\n\nPre-final time: {time.time() - start_time}\n\n\n---\n\n\n")

    legals_context = ask_yandex(yagpt_answer, prompt_yandex_legals)

    print(f"\n\n\n---\n\n\nLegals time: {time.time() - start_time}\n\n\n---\n\n\n")

    legals_context = '\nПРАВОВЫЕ АКТЫ: ' + legals_context
    final_answer = ask_yandex(yagpt_answer + legals_context, prompt_yandex_final)

    print(f"\n\n\n---\n\n\nFinal time: {time.time() - start_time}\n\n\n---\n\n\n")

    print(final_answer)

    print(f"\n\n\n---\n\n\nOverall time: {time.time() - start_time}\n\n\n---\n\n\n")


def main_almost_linear():
    start_time = time.time()

    result_interpretate = ask_yandex(input_text, prompt_yandex_interpretate)
    result_variants = ask_yandex(input_text, prompt_yandex_variants)
    print(result_variants)
    result_variant_1, result_variant_2 = loads(result_variants.replace('«', '"').replace('»', '"'))

    print(f"\n\n\n---\n\n\nVariants + interpretate time: {time.time() - start_time}\n\n\n---\n\n\n")

    input_data = [result_interpretate, result_variant_1, result_variant_2]
    with Parallel(n_jobs=3) as parallel_2:
        results_2 = parallel_2(delayed(query_from_chrome)(input_data[i]) for i in range(len(input_data)))
    result_query_1, result_query_2, result_query_3 = remove_duplicates(results_2)

    print(f"\n\n\n---\n\n\nQuery time: {time.time() - start_time}\n\n\n---\n\n\n")

    query_context = '\nКОНТЕКСТ-ДОКУМЕНТ: ' + result_query_1 + '\n' + result_query_2 + '\n' + result_query_3
    yagpt_answer = ask_yandex(input_text + query_context, prompt_yandex_pre_final)

    print(f"\n\n\n---\n\n\nPre-final time: {time.time() - start_time}\n\n\n---\n\n\n")

    legals_context = ask_yandex(yagpt_answer, prompt_yandex_legals)

    print(f"\n\n\n---\n\n\nLegals time: {time.time() - start_time}\n\n\n---\n\n\n")

    legals_context = '\nПРАВОВЫЕ АКТЫ: ' + legals_context
    final_answer = ask_yandex(yagpt_answer + legals_context, prompt_yandex_final)

    print(f"\n\n\n---\n\n\nFinal time: {time.time() - start_time}\n\n\n---\n\n\n")

    print(final_answer)

    print(f"\n\n\n---\n\n\nOverall time: {time.time() - start_time}\n\n\n---\n\n\n")


if __name__ == "__main__":
    # main_generate_data_store()
    # main_parallel()
    main_almost_linear()
