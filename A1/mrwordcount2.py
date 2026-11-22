from mrjob.job import MRJob
from mrjob.step import MRStep
import re

class MRWordCount(MRJob):
    def steps(self):
        return [
            MRStep(mapper=self.mapper1,
                combiner=self.combiner1,
                reducer=self.reducer1), 
            MRStep(reducer=self.reducer2)] 

    def mapper1(self, _, line):
        for word in re.findall("[\w]+", line):
            yield word.lower(), 1 
 
    def combiner1(self, word, counts):
        yield word, sum(counts) 
 
    def reducer1(self, word, word_count):
        yield None, (word, sum(word_count)) 
 
    def reducer2(self, _, word_count_pairs):
        yield max(word_count_pairs, key=lambda p: p[1]) 
 
if __name__=="__main__":
    MRWordCount.run() 