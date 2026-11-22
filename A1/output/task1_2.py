from mrjob.job import MRJob

class MRSortPlayerData(MRJob):
    def mapper(self, _, line):
        row = line.split(",")

        player_name = row[0].strip()
        competition = row[5].strip()
        match_id = row[6].strip()

        sort_key = competition + player_name + match_id

        yield sort_key, line

    def reducer(self, key, values):
        for value in values:
            yield None, value

if __name__ == '__main__':
    MRSortPlayerData.run()
