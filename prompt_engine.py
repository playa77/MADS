# v3.0.0 - Work Package 4: Influence Shader
def apply_influence_shader(content: str, weight: float) -> str:
    """
    Wraps the Director's input based on the influence weight (0.0 - 1.0).
    
    Strategies:
    - 0.0 - 0.3 (Subtle): Presented as a side note or user suggestion.
    - 0.4 - 0.7 (Moderate): Presented as a mandatory topic to address.
    - 0.8 - 1.0 (Critical): Presented as a System Override / Directive.
    """
    if weight <= 0.3:
        return (
            f"[Contextual Note]: A user observer has remarked: '{content}'. "
            "You may choose to incorporate this perspective if relevant."
        )
    elif weight <= 0.7:
        return (
            f"[MANDATORY INSTRUCTION]: The debate moderator requires you to address this point: '{content}'. "
            "Integrate this into your next response."
        )
    else:
        return (
            f"*** SYSTEM OVERRIDE (Priority {weight:.1f}) ***\n"
            f"CRITICAL DIRECTIVE: Disregard previous flow if necessary. "
            f"You MUST focus entirely on this instruction: '{content}'."
        )
