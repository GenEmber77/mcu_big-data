from mrjob.job import MRJob

class MRWordFrequencyCount(MRJob):
    def mapper(self, _, line):
        yield "chars", len(line) # count num of characters
        yield "words", len(line.split()) # count num of words
        yield "lines", 1 # count num of lines – with each line, add 1

    def reducer(self, key, values):
        yield key, sum(values)

if __name__ == '__main__':
    MRWordFrequencyCount.run() # main program to call/run MRWordFrequencyCount
