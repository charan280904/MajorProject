def apply_rules(conditions, lifestyle, kb_data):

    recommendations = []
    routine = {
        "morning": [],
        "afternoon": [],
        "night": []
    }
    treatment = []
    risk = "Low"

    # =====================
    # CONDITION BASED RULES
    # =====================
    for cond in conditions:
        data = kb_data.get(cond, {})

        # General recommendations
        recommendations.extend(data.get("recommendations", {}).get("general", []))

        # Routine
        for k in routine:
            routine[k].extend(data.get("daily_routine", {}).get(k, []))

        # Treatment
        treatment.extend(data.get("treatment", []))

    # =====================
    # LIFESTYLE RULES
    # =====================
    if lifestyle:

        if lifestyle.get("brush") == "once":
            recommendations.append("Increase brushing to twice daily")
            risk = "Medium"

        if "sweets" in lifestyle.get("food", []):
            recommendations.append("Reduce sugar intake immediately")
            risk = "High"

        if lifestyle.get("tobacco") == "yes":
            recommendations.append("Stop tobacco usage immediately")
            risk = "High"

        if lifestyle.get("diabetes") == "yes":
            recommendations.append("Maintain blood sugar levels carefully")
            risk = "High"

        if lifestyle.get("visit") == "never":
            recommendations.append("Visit dentist regularly")
            risk = "High"

    # Remove duplicates
    recommendations = list(set(recommendations))
    treatment = list(set(treatment))

    return {
        "recommendations": recommendations,
        "routine": routine,
        "treatment": treatment,
        "risk": risk
    }