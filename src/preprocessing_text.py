import spacy
from spellchecker import SpellChecker

from .utils import make_async


nlp = spacy.load("ru_core_news_sm")
spell = SpellChecker(language="ru")

@make_async
def correct_text(text) -> str:
    words = text.split()
    corrected_words = []

    for word in words:
        corrected_word = spell.correction(word)
        if corrected_word is None:
            corrected_word = word
        corrected_words.append(corrected_word)
    
    return " ".join(corrected_words)

@make_async
def lemmatize_text(text) -> str:
    doc = nlp(text)
    lemmatized_text = " ".join([token.lemma_ for token in doc])
    return lemmatized_text

async def preprocess_text(text: str):
    return await lemmatize_text(await correct_text(text))