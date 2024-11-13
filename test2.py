CATEGORIES = ["Attire","Character","Concept","Style"]
QUALITIES = ["Scoring", "CloseAnalysis", "SFW", "Difficult", "Meh", "Okay", "Good", "Top", "Best"]





# Compile a regular expression with all CATEGORY_QUALITY combinations

def matches_any_category_quality_regex(target_string):
    # Use the pattern to search for any match in the target string
    return pattern.search(target_string)

# Example usage
target_string = "The concept has a Concept_To rating in style."
result = pattern.search(target_string)
if result:
    print(result.group())