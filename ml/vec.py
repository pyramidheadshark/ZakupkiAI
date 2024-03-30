from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


questions = []
answers = []
test_questions = []
test_answers = []


def calculate_vectorization(texts):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(texts)
    return vectors


def compare_answers(questions, answers, vectors):
    max_similarity = 0
    most_accurate_answer = ""
    for i, question in enumerate(questions):
        for j, answer in enumerate(answers):
            similarity = cosine_similarity(vectors[i], vectors[j])
            if similarity > max_similarity:
                max_similarity = similarity
                most_accurate_answer = answer
    return most_accurate_answer, max_similarity


vectorization = calculate_vectorization(answers + test_answers)
most_accurate_answer, max_similarity = compare_answers(questions + test_questions, answers + test_answers, vectorization)
print(most_accurate_answer)
print(max_similarity)