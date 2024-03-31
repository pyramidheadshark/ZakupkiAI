from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores.chroma import Chroma

from ml.database_preparation import CHROMA_PATH


def query_from_chrome(query_text: str):
    embedding_function = SentenceTransformerEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    results = db.similarity_search_with_relevance_scores(query_text, k=2)

    most_relevant = results[0][0].page_content
    if len(results) > 1:
        second_most_relevant = results[1][0].page_content
    else: second_most_relevant = ''
    answer = most_relevant
              #+ '\n\n' + second_most_relevant)

    return answer
