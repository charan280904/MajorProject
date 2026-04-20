from rag_engine.kb import DENTAL_KB

def retrieve_conditions(detections):
    retrieved = {}

    for d in detections:
        key = d.lower()
        if key in DENTAL_KB:
            retrieved[key] = DENTAL_KB[key]

    return retrieved