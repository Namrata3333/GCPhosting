import os
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# Load the model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Updated PROMPT BANK with dynamic Q2 and extended Q4 intents
PROMPT_BANK = {
    "Q1": [
        "Which accounts had CM% < 30 in the last quarter?",
        "Clients with less than 30% margin last quarter",
        "Which accounts had margins below 30 percent",
        "Show me accounts with less than 40% margin",
        "List clients with margin below threshold"
    ],
    "Q2": [
        "Which cost caused margin drop last month?",
        "Which cost increased last month vs previous month?",
        "What caused margin drop in Transportation?",
        "Which cost item triggered margin decline last month?",
        "Why did margin fall last month in Manufacturing?",
        "Last month's margin dropped — what cost increased?",
        "Find clients with higher costs and lower margin this month",
        "Margin dropped in Automotive — which cost increased?",
        "Identify cost buckets responsible for margin drop",
        "Segment-wise cost increase that led to margin decline"
    ],
    "Q3": [
        "Compare C&B cost by segment over two quarters",
        "Which segments had highest C&B change",
        "Show C&B cost trend by segment",
        "C&B cost comparison Q1 vs Q2 by segment",
        "Segment wise change in C&B cost"
    ],
    "Q4": [
        "What is the MoM trend of C&B cost?",
        "C&B vs revenue monthly trend",
        "Month over month comparison of C&B with revenue",
        "C&B cost as percentage of revenue trend",
        "Compare C&B cost % with revenue monthly",
        "What is the YoY, QoQ, MoM revenue trend?",
        "YoY revenue trend by account",
        "How has revenue changed quarter over quarter",
        "Monthly revenue comparison by client",
        "Revenue trends for each BU or DU",
        "Revenue trend analysis by DU or BU",
        "Show revenue trend without time filter",
        "Client wise revenue change trends",
        "Trend of revenue growth",
        "Compare revenue over time"
    ],
    "Q7": [
        "What is M-o-M HC for an account",
        "Show monthly headcount trend per client",
        "FTE trend over months",
        "Client wise MoM headcount movement",
        "Monthly total billable hours per account",
        "MoM FTE for customers",
        "Headcount trend month over month",
        "Month-wise headcount per client"
    ],
    "Q8": [
        "What is the UT trend for last 2 quarters for a DU/BU/account?",
        "Show utilization by account",
        "How is utilization % trending?",
        "Compare utilization quarter over quarter",
        "What is total UT% by BU this year?",
        "Utilization YoY trend",
        "Which DU has the highest UT this quarter?",
        "Utilization rate over time for each account",
        "Quarterly utilization % per segment",
        "Trend of utilization over time"
    ],
    "Q10": [
        "DU wise Fresher UT Trends",
        "fresher ut trend",
        "ut% trend for freshers",
        "fresher utilization trend by DU"
    ],
    "Q6": [
        "Realized Rate Drop",
        "realized rate drop",
        "Realized Rate",
        "realized rate"
    ],
    "Q9": [
        "Revenue Per Person",
        "revenue per person",
    ]
}

# Flatten prompt bank into parallel lists
questions, qids = [], []
for qid, qlist in PROMPT_BANK.items():
    for q in qlist:
        questions.append(q)
        qids.append(qid)

# Precompute question embeddings
question_embeddings = model.encode(questions)

SIM_THRESHOLD = 0.72  # similarity threshold for fallback

def find_best_matching_qid(user_query):
    query_embedding = model.encode([user_query])[0]
    similarities = util.cos_sim(query_embedding, question_embeddings)[0]
    best_idx = similarities.argmax().item()
    best_qid = qids[best_idx]
    matched_question = questions[best_idx]
    best_score = similarities[best_idx].item()

    # Apply threshold: if below, treat as no match
    if best_score < SIM_THRESHOLD:
        return None, matched_question, best_score

    return best_qid, matched_question, best_score
