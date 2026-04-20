from rag_engine.retriever import retrieve_conditions
from rag_engine.engine import apply_rules

def generate_ai_output(detections, lifestyle):

    kb_data = retrieve_conditions(detections)

    result = apply_rules(detections, lifestyle, kb_data)

    return result