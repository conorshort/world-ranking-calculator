import statistics
import requests
from world_ranking_calculator import get_rankings
LIVE_RESULTS_URL = "https://liveresultat.orientering.se/api.php"


def get_classes_for_event(event_id):
    r = requests.get(f"{LIVE_RESULTS_URL}?method=getclasses&comp={event_id}")

    classes_list = [item['className'] for item in r.json()['classes']]
    return classes_list


def get_results_in_class(event_id, class_id):
    r = requests.get(
        f"{LIVE_RESULTS_URL}?comp={event_id}&method=getclassresults&unformattedtimes=true&class={class_id}")
    print()
    rankings = get_rankings()

    results = [
        {
            "place": result['place'],
            'name': result['name'],
            'result': transform_time_to_seconds(result['result']),
            'result_mins': result['result'],
            **rankings.find_closest_match(result['name'])
        }
        for result in r.json()['results'] if result['status'] == 0
    ]

    wr_results = calculate_world_ranking(results)
    return wr_results


def transform_time_to_seconds(time):
    minutes, seconds = map(int, time.split(':'))
    total_seconds = minutes * 60 + seconds
    return total_seconds


def calculate_world_ranking(athletes):
    MIN_POINTS = 800
    MAX_POINTS = 1375
    ENHANCEMENT_FACTOR = 1
    # ranked athelete = has current WR
    # outlier athlete = >100 point difference preliminary

    # For each athlete, sum of ranking points / number of races
    ranked_athletes = filter_ranked_athletes(athletes)
    num_ranked = len(ranked_athletes)

    # Calculate mean MP and sd SP of all rankings
    mp, sp = calulate_mean_and_sd_by_key(ranked_athletes, 'Avg point')

    # Calculate mean MT and sd ST of all times
    mt, st = calulate_mean_and_sd_by_key(ranked_athletes, 'result')

    # Calculate winner preliminary points:
    # If num ranked >= 8: (MP + SP x (MT- RT)/ST) x IP
    #  1 < num ranked < 8: (2000 - RT x (2000 - MP) / MT) x IP
    # num ranked == 0: (2000 – RT x 1200/MT) x IP

    equation = None
    if num_ranked >= 8:
        def equation(rt): return mp + sp * (mt - rt) / st
    elif num_ranked >= 1:
        def equation(rt): return (2000 - rt * (2000 - mp) / mt)

    if equation:
        for athlete in athletes:
            athlete["preliminary_rp"] = equation(athlete["result"])

        # is this always the case?
        winner_prelim_rp = athletes[0]["preliminary_rp"]

        ip = 1 * ENHANCEMENT_FACTOR
        if winner_prelim_rp < MIN_POINTS:
            ip = MIN_POINTS / winner_prelim_rp * ENHANCEMENT_FACTOR
        elif winner_prelim_rp > MAX_POINTS:
            ip = MAX_POINTS / winner_prelim_rp * ENHANCEMENT_FACTOR

        non_outlier_athletes = filter_non_outlier_athletes(
            filter_ranked_athletes(athletes))
        num_non_outlier = len(non_outlier_athletes)

        mp, sp = calulate_mean_and_sd_by_key(non_outlier_athletes, 'Avg point')
        mt, st = calulate_mean_and_sd_by_key(non_outlier_athletes, 'result')

        if num_non_outlier >= 8:
            def equation(rt): return (mp + sp * (mt - rt) / st) * ip
        elif num_non_outlier >= 1:
            def equation(rt): return (2000 - rt * (2000 - mp) / mt) * ip

        for athlete in athletes:
            athlete["rp"] = equation(athlete["result"])
            print(athlete)
        return athletes
    else:
        # num ranked == 0: (2000 – RT x 1200/MT) x IP
        pass


def filter_ranked_athletes(athletes):
    filtered = filter(lambda a: a['Avg point'] !=
                      None and a['Avg point'] > 10, athletes)
    return list(filtered)


def filter_non_outlier_athletes(athletes):
    filtered = filter(
        lambda a:
            a['Avg point'] != None and
            not abs(a['Avg point'] - a['preliminary_rp']) > 100,
        athletes
    )
    return list(filtered)


def calulate_mean_and_sd_by_key(athletes: list, key: str) -> tuple[int, int]:
    all_avg_points = list(map(lambda a: a[key], athletes))
    mean = statistics.mean(all_avg_points)
    stdev = statistics.stdev(all_avg_points)
    return mean, stdev
