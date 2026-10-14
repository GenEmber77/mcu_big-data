from pymongo import MongoClient 
import nltk 
from nltk.tokenize import word_tokenize 
from nltk.stem import PorterStemmer 
from nltk.corpus import stopwords 
import re 

def download_nltk(): 
    for pkg in ["stopwords", "punkt", "averaged_perceptron_tagger",
                "punkt_tab", "averaged_perceptron_tagger_eng"]:
        try:
            nltk.download(pkg)
        except Exception:
            pass

def remove_stopwords(words): 
    result= [] 
    for w in words: 
        if w not in stopwords.words("english"): 
            result.append(w) 
    return result 

def stem_words(words): 
    ps: PorterStemmer = PorterStemmer() 
    result= [] 
    for w in words: 
        result.append(ps.stem(w)) 
    return result 

def find_keywords_in_text(text): 
    text = re.sub(r"[^\w]"," ", text) #removes non-alphabetical symbols (like punctuation and numbers) 
    words= word_tokenize(text) #convert into list of words 
    words = remove_stopwords(words) #remove stopwords 
    words = stem_words(words) #make the words undergo a form of linguistic normalisation 
    keywords= nltk.pos_tag(words) #run Parts-of-Speech tagging to identify grammatical groupings of keywords 
    return keywords 

#accesses database and its collection 'Tweets' 
client=MongoClient("localhost:27017")
db = client.Practical1

download_nltk() 
for t in db.tweets.find(): 
    keywords = find_keywords_in_text(t["text"])
    for k in keywords:
        print(k)
    print("\n")