from mrjob.job import MRJob
from mrjob.step import MRStep

class MRPerformanceGapReview(MRJob):

    def steps(self):
        return [
            MRStep(
                mapper=self.mapper_get_player_stats,
                reducer=self.reducer_calculate_player_gap
            ),
            MRStep(
                reducer=self.reducer_top10_perf_gaps
            )
        ]

    #  STEP 1: Extract Player Stats
    def mapper_get_player_stats(self, _, line):
        fields = line.split(',')
        
        # Extract player statistics from the line
        player_name = fields[0]
        nationality = fields[1]
        club = fields[2]
        competition = fields[5]
        minutes_played = float(fields[7])
        goals = int(fields[8])
        assists = int(fields[9])
        match_rating = float(fields[10])

        points = (goals * 4) + (assists * 3) + match_rating
                        
        # Determine match category
        if competition == "FIFA World Cup 2026":
            yield (player_name, nationality, club), ('wc', minutes_played, points)
        elif competition in ["League", "Champions League", "Domestic Cup"]:
            yield (player_name, nationality, club), ('club', minutes_played, points)

    def reducer_calculate_player_gap(self, key, values):
        player_name, nationality, club = key
        
        wc_mins = 0
        wc_points = 0.0
        
        club_mins = 0
        club_points = 0.0
        
        # Accumulate minutes and performance points
        for category, minutes, points in values:
            if category == 'wc':
                wc_mins += minutes
                wc_points += points
            elif category == 'club':
                club_mins += minutes
                club_points += points
                
        # Filter condition: Both worldcup_minutes >= 180 and club_minutes >= 180
        if wc_mins >= 180 and club_mins >= 180:
            worldcup_per90 = (wc_points / wc_mins) * 90
            club_per90 = (club_points / club_mins) * 90
            
            # Calculate gap
            performance_gap = worldcup_per90 - club_per90
            
            yield None, (player_name, nationality, club, performance_gap)


    #  STEP 2: Find Top 10 Players by Performance Gap
    def reducer_top10_perf_gaps(self, _, players_data):
        all_players = list(players_data)
        
        # Sort: 
        # performance_gap descending
        # player_name ascending
        all_players.sort( key=lambda x: (-x[3], x[0]))
        
        # Select the top 10 players
        top_10 = all_players[:10]
        
        for player_name, nationality, club, performance_gap in top_10:
            yield None, f"{player_name},{nationality},{club},{performance_gap:.2f}"

if __name__ == '__main__':
    MRPerformanceGapReview.run()
