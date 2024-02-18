import pandas as pd
from thefuzz import process

CSV_PATH = "/home/conor/world-ranking-calculator/iof_ranking_MEN_F_18-02-2024.csv"


class CurrentRankings:
    def __init__(self, csv_path) -> None:
        self.rankings_df = pd.read_csv(csv_path, sep=";")
        self.full_names = self.rankings_df['First Name'] + \
            ' ' + self.rankings_df['Last Name']

    def find_closest_match(self, name: str) -> dict:
        closest_match, _, _ = process.extractOne(name, self.full_names)
        matched_row = self.rankings_df[self.full_names == closest_match]
        if matched_row.empty:
            return {key: None for key in self.rankings_df.keys()}
        return matched_row.iloc[0].to_dict()


def get_rankings() -> CurrentRankings:
    return CurrentRankings(CSV_PATH)
