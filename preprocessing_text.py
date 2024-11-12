import spacy
from spellchecker import SpellChecker


nlp = spacy.load("ru_core_news_sm")
spell = SpellChecker(language='ru')

def correct_text(text):
    words = text.split()
    corrected_words = []

    for word in words:
        corrected_word = spell.correction(word)
        if corrected_word is None:
            corrected_word = word
        corrected_words.append(corrected_word)
    
    return " ".join(corrected_words)

def lemmatize_text(text):
    doc = nlp(text)
    lemmatized_text = " ".join([token.lemma_ for token in doc])
    return lemmatized_text

def preprocess_text(text: str): return lemmatize_text(correct_text(text))