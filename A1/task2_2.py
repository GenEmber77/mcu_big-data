from mrjob.job import MRJob
from mrjob.step import MRStep

class MRValueForMoneyPlayers(MRJob):

    def steps(self):
        return [
            MRStep(
                mapper=self.mapper_player_stats,
                reducer=self.reducer_calc_player_stats
                ),
            MRStep(
                reducer=self.reducer_aggregate_club_stats
            ),
            MRStep(
                reducer=self.reducer_top_clubs
            )
        ]

    def mapper_player_stats(self, _, line):
        fields = line.split(',')

        # Extract fields
        player_name = fields[0]
        club = fields[2]
        competition = fields[5]
        goals = int(fields[8])
        assists = int(fields[9])

        # Filter: Only keep records from "FIFA World Cup 2026"
        if competition == "FIFA World Cup 2026":
            attack_score = goals + assists
            yield (club, player_name) , attack_score

    def reducer_calc_player_stats(self, key, values):    
        club, player_name = key   
        player_attack_score = sum(values)    
        yield club, (player_name,player_attack_score)

    def reducer_aggregate_club_stats(self, club, values):
        player_list = list(values)   

        top_player, top_player_score = max(player_list, key=lambda x: x[1])

        total_players = len(player_list)
        total_attack_score = sum(player_attack_score for _, player_attack_score in player_list)
                    
        # Send all club summaries to a single reducer to find the global top 10
        yield None, (club, total_players, total_attack_score, top_player, top_player_score)

    def reducer_top_clubs(self, _, clubs_data):
        club_list = list(clubs_data)
        
        # Sort key: 
        # total_attack_score (descending)
        # club name (ascending, alphabetically)
        club_list.sort(key=lambda x: (-x[2], x[0]))
        top10_clubs = club_list[:10]
        
        for club, total_players, total_attack_score, top_player, top_player_score in top10_clubs:
            yield None, f"{club},{total_players},{total_attack_score},{top_player},{top_player_score}"

if __name__ == '__main__':
    MRValueForMoneyPlayers.run()
