import difflib

def find_fuzzy_matches(items, extractor, target, threshold=0.6):
    """
    Finds objects with a string value similar to the target using 
    edit distance similarity and substring detection.

    Args:
        items (list): List of objects to search through.
        extractor (func): Function to extract the comparison string from an object.
        target (str): The 'etalon' string to compare against.
        threshold (float): Cutoff for similarity (0.0 to 1.0). Default 0.6.

    Returns:
        list: A list of objects sorted by similarity (most similar first).
    """
    matches = []
    
    # Normalize target for case-insensitive comparison
    target_clean = target.lower().strip()
    
    for item in items:
        # 1. Extract the string
        try:
            extracted_value = extractor(item)
            if extracted_value is None:
                continue
            value_clean = str(extracted_value).lower().strip()
        except Exception:
            continue

        # 2. Substring Detection
        # Check if target is inside value OR value is inside target (e.g., "phone" <-> "iphone")
        is_substring = (target_clean in value_clean) or (value_clean in target_clean)

        # 3. Simple Editing Distance Similarity
        # difflib.SequenceMatcher calculates a ratio [0, 1] based on the 
        # longest common subsequence (closely related to Levenshtein distance).
        matcher = difflib.SequenceMatcher(None, target_clean, value_clean)
        similarity = matcher.ratio()

        # Scoring Logic:
        # If it is a substring, we ensure the score is at least the threshold 
        # (or a high fixed value like 0.9) to guarantee it appears in results 
        # even if the strings are very different in length (e.g., "Pi" vs "Simple Raspberry Pi").
        final_score = similarity
        
        if is_substring:
            # Boost score for substrings, but allow exact matches (1.0) to remain highest
            final_score = max(similarity, 0.9)

        # Filter by threshold
        if final_score >= threshold:
            matches.append({
                'object': item, 
                'score': final_score,
                'value': extracted_value # Storing this just for debugging/sorting if needed
            })

    # Sort results by score descending (best matches first)
    matches.sort(key=lambda x: x['score'], reverse=True)

    # Return only the objects
    return [m['object'] for m in matches]