from mrjob.job import MRJob
from mrjob.step import MRStep

class MRPlayerValueByPosition(MRJob):

    def steps(self):
        return [
            MRStep(mapper=self.mapper_player_stats,
                   reducer=self.reducer_calc_value_score),
            MRStep(reducer=self.reducer_top3)
        ]

    def mapper_player_stats(self, _, line):
        fields = line.split(',')

        # Extract player statistics from the line
        player_name = fields[0]
        nationality = fields[1]
        club = fields[2]
        position = fields[3]
        market_value_eur_m = float(fields[4])
        competition = fields[5]
        minutes_played = float(fields[7])
        goals = float(fields[8])
        assists = float(fields[9])
        match_rating = float(fields[10])

        if competition == "FIFA World Cup 2026":
            performance_points = (goals * 4) + (assists * 3) + match_rating
            
            key = (player_name, nationality, club, position)
            yield key, (performance_points, minutes_played, market_value_eur_m)

    def reducer_calc_value_score(self, key, player_stats):
        total_perf_points = 0
        total_minutes = 0
        market_values = []

        for perf_points, minutes, mv in player_stats:
            total_perf_points += perf_points
            total_minutes += minutes
            if mv != "NA":
                market_values.append(float(mv))

        avg_market_value = sum(market_values) / len(market_values)
     
        if total_minutes >= 180 and avg_market_value > 0:
            performance_per90 = (total_perf_points / total_minutes) * 90
            value_score = performance_per90 / avg_market_value
                
            player_name, nationality, club, position = key
                
            yield position, (value_score, player_name, nationality, club)

    def reducer_top3(self, position, players):
        player_list = list(players)
        
        # Sort: 
        # 1. value_score in descending
        # 2. player_name in ascending
        player_list.sort(key=lambda x: (-x[0], x[1]))
        
        # Take top 3 players
        top_three = player_list[:3]
        
        for value_score, player_name, nationality, club in top_three:
            yield None, f"{position},{player_name},{nationality},{club},{value_score:.4f}"

if __name__ == '__main__':
    MRPlayerValueByPosition.run()
