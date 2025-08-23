import re


def evaluate_phone_number(phone_number: str) -> dict:
    """
    Evaluate the beauty of a phone number with weighted scoring and synergy:
    - Repeated digits (highest weight)
    - Sequential digits (medium weight)
    - Palindrome or mirror-like patterns (high weight)
    - Group repetition (medium-high weight)
    - Synergy bonus if multiple criteria are satisfied

    Returns a dictionary with score and explanation.
    """
    digits = re.sub(r"\D", "", phone_number)  # strip non-digits
    score = 0
    explanation = []

    criteria_hit = 0

    # --- 1. Repeated digits (highest weight) ---
    for d in set(digits):
        count = digits.count(d)
        if count > 2:
            val = count * 5
            score += val
            explanation.append(f"Repeated digit {d} (x{count}) +{val}")
            criteria_hit += 1

    # --- 2. Sequential digits (medium weight) ---
    for i in range(len(digits) - 2):
        seq = digits[i:i + 3]
        if seq in "0123456789":
            score += 12
            explanation.append(f"Ascending sequence {seq} +12")
            criteria_hit += 1
        if seq in "9876543210":
            score += 12
            explanation.append(f"Descending sequence {seq} +12")
            criteria_hit += 1

    # --- 3. Palindrome / mirror patterns (high weight) ---
    if digits == digits[::-1]:
        score += 40
        explanation.append("Full palindrome +40")
        criteria_hit += 1
    elif digits[:len(digits) // 2] == digits[-(len(digits) // 2):]:
        score += 25
        explanation.append("Mirror halves +25")
        criteria_hit += 1

    # --- 4. Group repetition (medium-high weight) ---
    groups = re.findall(r"(\d{2,})\1", digits)
    for g in groups:
        val = 20
        score += val
        explanation.append(f"Repeated group {g} +{val}")
        criteria_hit += 1

    # --- 5. Synergy bonus ---
    if criteria_hit > 1:
        synergy = criteria_hit * 10
        score += synergy
        explanation.append(f"Synergy bonus for {criteria_hit} patterns +{synergy}")

    # Normalize 1–100
    final_score = min(100, max(1, score))

    return final_score #{"number": phone_number, "score": final_score, "explanation": explanation}

def evaluate_phone_numbers(results):
    priced_numbers = []
    for number in results:
        number['price'] = 10
        #number['score'] = evaluate_phone_number(number['phone_number'])
        priced_numbers.append(number)
    return priced_numbers
#
# # ---- Examples ----
# examples = [
#     "+14388133336",
#     "123-456-7890",  # clear sequence
#     "555-555-5555",  # repeated number
#     "987-654-3210",  # descending sequence
#     "1221-1221",  # palindrome / mirror
#     "416-123-1234"  # grouped pattern
# ]
#
# for num in examples:
#     print(f"{num} -> Score: {evaluate_phone_number(num)}")
