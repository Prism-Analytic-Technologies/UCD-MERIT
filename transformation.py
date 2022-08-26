import pydash

from utils import (
    pretty_print_enum,
    pretty_print_enums,
    get_year,
    map_by_keywords
)

############################################################
# Transform trial record
############################################################
def create_final_record(trial, pivotal_trial_ids=[]):
    if not isinstance(trial, dict):
        print(f"Putative trial of type {str(type(trial))}")
        return {}

    is_pivotal = trial["nctId"] in pivotal_trial_ids  # TODO

    return {
        "id": trial["nctId"],
        "NCT": trial["nctId"],
        "Concepts_Text": "",
        "CTgov_Link": "https://clinicaltrials.gov/ct2/show/" + trial["nctId"],
        "FDA_Approved_Interventions": get_approved_interventions(trial["interventions"]),
        "Purpose": pretty_print_enum(trial["purpose"]),
        "Randomization": pretty_print_enum(trial["randomization"]),
        "Enrollment": get_enrollment(trial),
        "Facility_Score": get_site_type(trial["locations"]),
        "Has_Results": "Yes" if trial["hasResults"] else "No",
        "Intervention_Comparator_Names": get_comparators(trial["interventions"]),
        "Intervention_Types": get_intervention_types(trial["interventions"]),
        "Masking": get_who_masked(trial),
        "Masking_Simple": pretty_print_enum(trial["masking"]),
        "Num_Primary_Outcomes": get_outcomes_count(trial["outcomes"], 'PRIMARY'),
        "Outcome_Count": get_outcomes_count(trial["outcomes"]),
        "Outcome_Analysis_Types": pretty_print_enums(
            get_comparison_types(trial["outcomes"])
        ),
        "Outcome_Measures": get_outcome_measures(trial["outcomes"]),
        "PCO": get_pco_types(trial["outcomes"]),
        "Phase": pretty_print_enum(trial["phase"]),
        "Pivotal_Trial": is_pivotal,
        "Quality_Score": get_quality_score(trial).get("score"),
        "Quality_Score_Explanation": "; ".join(get_quality_score(trial).get("explanation")),
        "Reporting_Score": get_reporting_score(trial).get("score"),
        "Reporting_Score_Explanation": "; ".join(get_reporting_score(trial).get("explanation")),
        "Sponsor": trial["leadSponsor"],
        "Sponsor_Type": pretty_print_enum(trial["sponsorType"]),
        "Start_Date": trial["startDate"],
        "Start_Year": get_year(trial["startDate"]),
        "Status": pretty_print_enum(trial["status"]),
        "Title": trial["officialTitle"],
        "Trial_Type": "Regulatory Trial" if is_pivotal else "Context Trial",
    }

def get_enrollment(trial):
    actual = trial["actualEnrollment"]
    planned = trial["plannedEnrollment"]
    return actual if actual > 0 else planned

############################################################
# Site/location type
############################################################
def get_site_type(locations):
    if len(locations) > 1:
        return "Multiple Sites"
    if len(locations) == 1:
        return "Single Site"

    return "No Data"

############################################################
# Get FDA approved intervention names
############################################################
def get_approved_interventions(interventions):
    approved_interventions = list(filter(
      lambda i: (i.get("canonical") or {}).get("isFdaApproved", False),
      interventions
    ))
    return list(map(normalize_intervention, approved_interventions))

############################################################
# Get comparator intervention names
############################################################
def get_comparators(interventions):
    comps = filter(
      lambda i: any(filter(
        lambda a: a["type"] in ["COMPARATOR"],
        i.get("arms", [])
      )),
      interventions
    )
    return list(map(normalize_intervention, comps))

############################################################
# Get intervention types
############################################################
def get_intervention_types(interventions):
    return list(map(
      lambda i: i.get("type", ""),
      interventions
    ))

############################################################
# Get outcome count, optionally by type (primary, etc)
############################################################
def get_outcomes_count(outcomes, o_type=None):
    if not o_type:
        return len(outcomes)

    primary_outcomes = get_primary_outcomes(outcomes)
    return len(primary_outcomes)

############################################################
# Get outcome names
############################################################
def get_outcome_measures(outcomes):
    return list(map(
      lambda i: i.get("name", ""),
      outcomes
    ))

############################################################
# Get comparison types from primary outcomes
############################################################
def get_comparison_types(outcomes):
    suppression_cts = ["OTHER", "UNKNOWN"]

    def get_comparison_type(outcome):
        c_type = outcome.get("comparisonType")
        if c_type in suppression_cts:
            return None
        return c_type

    comparison_types = list(map(
      get_comparison_type,
      get_primary_outcomes(outcomes)
    ))

    return pydash.compact(comparison_types)

############################################################
# Normalize intervention name
############################################################
def normalize_intervention(intervention):
    if intervention.get("canonical"):
        return intervention.get("canonical", {}).get("name")

    if "placebo" in intervention["name"].lower(): # TODO or arm name is placebo
        return "Placebo"

    return intervention.get("name").split(" ")[0].title()

############################################################
# Get PCO types for an array
############################################################
def get_pco_types(outcomes):
    primary_outcomes = get_primary_outcomes(outcomes)
    return list(map(get_pco_type, primary_outcomes))

############################################################
# Determine if outcome is a PCO (patient-centered outcome)
# and if so, which type
############################################################
def get_pco_type(outcome):
    keyword_map = [
        {
            "value": "Survival",
            "keywords": ['surviv', 'mortality', 'dead', 'death', 'alive'],
        },
        {
            "value": "Quality of Life",
            "keywords": ['daily life', 'quality of life', 'qol'],
        },
        {
            "value": "Symptom Resolution",
            "keywords": [
                'symptom resolution', 'symptoms resolution', 'resolution of symptom',
                'clinical cure',
            ], # todo: switch to spencer's logic
        },
        {
            "value": "Symptom Improvement",
            "keywords": [
                'symptom improvement', 'symptoms improvement', 'improvement of symptom',
                'clinical response'
            ], # todo: switch to spencer's logic
        },
    ]

    outcome_str = outcome.get("name", "") + outcome.get("description", "")

    pco_type = map_by_keywords(outcome_str, keyword_map, "Not PCO")
    if len(pco_type) > 1:
        return 'Composite'

    return pco_type[0]

############################################################
# Get primary outcomes
############################################################
def get_primary_outcomes(outcomes):
    return list(filter(lambda o: o["type"] == 'PRIMARY', outcomes))

############################################################
# Quality of outcome reporting
# (based on primary outcomes only)
############################################################
def get_outcome_reporting_score(outcomes):
    primary_outcomes = get_primary_outcomes(outcomes)

    missing_data = any(filter(
      lambda o: not o["name"] or not o["timeframe"] or not o["description"],
      primary_outcomes
    )) or len(primary_outcomes) == 0

    if missing_data:
        return {
          "explanation": "Record is missing data for at least 1 primary outcome [0].",
          "score": 0
        }

    return {
      "explanation": "Record has included a measure name, timeframe, and description for all primary outcomes [+1].",
      "score": 1
    }

############################################################
# Quality of intervention reporting
############################################################
def get_intervention_reporting_score(interventions):
    has_missing_description = any(filter(
      lambda i: not i["description"],
      interventions
    )) or len(interventions) == 0

    if has_missing_description:
        return {
          "explanation": "At least 1 intervention in this record lacked a description [0].",
          "score": 0,
        }

    return {
      "explanation": "All interventions in this record included descriptions [+1].",
      "score": 1
    }

############################################################
# Overall trial reporting score
# - locations
# - outcomes
# - interventions
############################################################
def get_reporting_score(trial):
    score = 0
    explanation = []

    if len(trial["locations"]) > 0:
        score += 1
        explanation.append("The record lists at least 1 facility [+1].")
    else:
        explanation.append("The record does not list any facilities [0].")

    i_score = get_intervention_reporting_score(trial["interventions"])
    o_score = get_outcome_reporting_score(trial["outcomes"])

    return {
      "explanation": [*explanation, i_score["explanation"], o_score["explanation"]],
      "score": score + i_score["score"] + o_score["score"]
    }

############################################################
# Trial quality score
# - is randomized
# - is multi-site
# - is masked
# - has 1 or 2 primary outcomes
# - has a reporting score of 3
# - has at least one patient-centered outcome
# - is a superiority comparison (vs non-inf or equiv. trial)
############################################################
def get_quality_score(trial):
    reporting_score = get_reporting_score(trial).get("score")
    score = 0
    explanation = []

    if trial["randomization"] == 'RANDOMIZED':
        score += 1
        explanation.append("This study was randomized [+1].")

    if len(trial["locations"]) > 1:
        score += 1
        explanation.append("The record lists more than 1 facility [+1].")

    if trial["masking"] in ['SINGLE', 'DOUBLE', 'TRIPLE', 'QUADRUPLE']:
        score += 1
        explanation.append("This study used some form of masking [+1].")

    num_primary_outcomes = get_outcomes_count(trial["outcomes"], 'PRIMARY')
    if num_primary_outcomes > 0 and num_primary_outcomes < 3:
        score += 1
        explanation.append("This record reports only 1 or 2 primary outcomes [+1].")

    if reporting_score == 3:
        score += 1
        explanation.append("This record has a reporting score of 3 [+1].")

    has_pco = any(filter(lambda pcot: pcot != 'Not PCO', get_pco_types(trial["outcomes"])))
    if has_pco:
        score += 1
        explanation.append("This study had a least 1 patient-centered outcome as a primary outcome [+1].")

    if 'SUPERIORITY' in get_comparison_types(trial["outcomes"]):
        score += 1
        explanation.append("This study reported using a superiority analysis for a primary outcome [+1].")

    return { "explanation": explanation, "score": score }

############################################################
# String of parties who are masked (e.g. participants)
############################################################
def get_who_masked(trial):
    masked_people = map(
        lambda m: pretty_print_enum(m["party"]),
        filter(lambda m: m["isMasked"], trial["maskings"])
    )
    return ", ".join(masked_people)

############################################################
# Should trial be included in returned array?
############################################################
def should_include_trial(final_record):
    # 1 when start date couldn't be found in record
    has_valid_start_date = final_record["Start_Year"] != 1

    return has_valid_start_date

############################################################
# Transforms data
############################################################
def transform(trials, pivotal_trial_ids):
    print(f'Got trials ({len(trials)}). Transforming.')
    transformed = list(map(
        lambda trial: create_final_record(trial, pivotal_trial_ids),
        trials
    ))
    filtered = list(filter(should_include_trial, transformed))
    print(f'Returning transformed + filtered results ({len(filtered)}).')

    return filtered
