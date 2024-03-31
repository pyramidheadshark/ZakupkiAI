from ml.database_querying import query_from_chrome
from ml.summary_thingies import generate_part_summary, ask_llama
from ml.database_preparation import main_generate_data_store


input_text = "Сколько дней составляет срок оплаты по контрактам с электронным актированием?"


if __name__ == "__main__":
    main_generate_data_store()