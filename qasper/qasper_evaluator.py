"""
Official script for evaluating models built for the Qasper dataset. The script
outputs Answer F1 and Evidence F1 reported in the paper.
"""
from collections import Counter
import argparse
import string
import re
import json


def normalize_answer(s):
    """
    Taken from the official evaluation script for v1.1 of the SQuAD dataset.
    Lower text and remove punctuation, articles and extra whitespace.
    """

    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def token_scores(prediction, ground_truth):
    """
    Taken from the official evaluation script for v1.1 of the SQuAD dataset.
    """
    prediction_tokens = normalize_answer(prediction).split()
    ground_truth_tokens = normalize_answer(ground_truth).split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return (0.0, 0.0, 0.0)
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    # to fix prompting issues:
    # one_word = ["yes", "no", "unanswerable"]
    # if len(ground_truth_tokens) == 1 and ground_truth_tokens[0] in one_word and recall == 1.0:
    #     precision = 1.0
    f1 = (2 * precision * recall) / (precision + recall)
    return (precision, recall, f1)


def paragraph_scores(prediction, ground_truth):
    if not ground_truth and not prediction:
        # The question is unanswerable
        return (1.0, 1.0, 1.0)
    concat_ground_truth = " ".join(set(ground_truth))
    # only take the top-k predictions give k-pieces of evidence from ground truth
    concat_prediction = " ".join(prediction[0:len(set(ground_truth))])
    return token_scores(concat_prediction, concat_ground_truth)

    # num_same = len(set(ground_truth).intersection(set(prediction)))
    # if num_same == 0:
    #     return (0.0, 0.0, 0.0)
    # precision = num_same / len(prediction)
    # recall = num_same / len(ground_truth) 
    # f1 = (2 * precision * recall) / (precision + recall)
    # return (precision, recall, f1)


def get_answers_and_evidence(data, text_evidence_only):
    answers_and_evidence = {}
    for paper_data in data.values():
        for qa_info in paper_data["qas"]:
            question_id = qa_info["question_id"]
            references = []
            for annotation_info in qa_info["answers"]:
                answer_info = annotation_info["answer"]
                if answer_info["unanswerable"]:
                    references.append({"answer": "Unanswerable", "evidence": [], "type": "none"})
                else:
                    if answer_info["extractive_spans"]:
                        answer = ", ".join(answer_info["extractive_spans"])
                        answer_type = "extractive"
                    elif answer_info["free_form_answer"]:
                        answer = answer_info["free_form_answer"]
                        answer_type = "abstractive"
                    elif answer_info["yes_no"]:
                        answer = "Yes"
                        answer_type = "boolean"
                    elif answer_info["yes_no"] is not None:
                        answer = "No"
                        answer_type = "boolean"
                    else:
                        raise RuntimeError(f"Annotation {answer_info['annotation_id']} does not contain an answer")
                    if text_evidence_only:
                        evidence = [text for text in answer_info["evidence"] if "FLOAT SELECTED" not in text]
                    else:
                        evidence = answer_info["evidence"]
                    references.append({"answer": answer, "evidence": evidence, "type": answer_type})
            answers_and_evidence[question_id] = references

    return answers_and_evidence


def evaluate(gold, predicted):
    max_answer_scores = { "f1": [], "precision": [], "recall": [] }
    max_evidence_scores = { "f1": [], "precision": [], "recall": [] }
    max_answer_by_type = {
        "extractive": { "f1": [], "precision": [], "recall": [] },
        "abstractive": { "f1": [], "precision": [], "recall": [] },
        "boolean": { "f1": [], "precision": [], "recall": [] },
        "none": { "f1": [], "precision": [], "recall": [] },
    }

    num_missing_predictions = 0
    for question_id, references in gold.items():
        if question_id not in predicted:
            num_missing_predictions += 1
            # not sure why this is done? 
            # max_answer_f1s.append(0.0)
            # max_evidence_f1s.append(0.0)
            continue
        answer_scores_and_types = [
            (*token_scores(predicted[question_id]["answer"], reference["answer"]),
             reference["type"])
            for reference in gold[question_id]
        ]

        # 0: sort by precision, 1: sort by recall, 2: sort by f1
        sorted_scores_and_types = sorted(answer_scores_and_types, key=lambda x: x[0], reverse=True)
        max_answer_precision, _, _, answer_type = sorted_scores_and_types[0]
        max_answer_scores["precision"].append(max_answer_precision)
        max_answer_by_type[answer_type]["precision"].append(max_answer_precision)

        sorted_scores_and_types = sorted(answer_scores_and_types, key=lambda x: x[1], reverse=True)
        _, max_answer_recall, _, answer_type = sorted_scores_and_types[0]
        max_answer_scores["recall"].append(max_answer_recall)
        max_answer_by_type[answer_type]["recall"].append(max_answer_recall)

        sorted_scores_and_types = sorted(answer_scores_and_types, key=lambda x: x[2], reverse=True)
        _, _, max_answer_f1, answer_type = sorted_scores_and_types[0]
        max_answer_scores["f1"].append(max_answer_f1)
        max_answer_by_type[answer_type]["f1"].append(max_answer_f1) 


        # TODO: doesn't really make sense even with ranking
        # TODO: unless we cross reference every permutation with the top evidence
        evidence_scores = [
            paragraph_scores(predicted[question_id]["evidence"], reference["evidence"])
            for reference in gold[question_id]
        ]
        max_evidence_precision, max_evidence_recall, max_evidence_f1 = max(evidence_scores)
        max_evidence_scores["precision"].append(max_evidence_precision)
        max_evidence_scores["recall"].append(max_evidence_recall)
        max_evidence_scores["f1"].append(max_evidence_f1)



    mean = lambda x: sum(x) / len(x) if x else 0.0
    return {
        "Answer F1": mean(max_answer_scores["f1"]),
        "Answer F1 by type": {key: mean(value["f1"]) for key, value in max_answer_by_type.items()},
        "Answer Precision": mean(max_answer_scores["precision"]),
        "Answer Precision by type": {key: mean(value["precision"]) for key, value in max_answer_by_type.items()},
        "Answer Recall": mean(max_answer_scores["recall"]),
        "Answer Recall by type": {key: mean(value["recall"]) for key, value in max_answer_by_type.items()},
        "Evidence F1": mean(max_evidence_scores["f1"]),
        "Evidence Precision": mean(max_evidence_scores["precision"]),
        "Evidence Recall": mean(max_evidence_scores["recall"]),
        "Missing predictions": num_missing_predictions,
        "Length by type": {key: len(value["f1"]) for key, value in max_answer_by_type.items()},
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="""JSON lines file with each line in format:
                {'question_id': str, 'predicted_answer': str, 'predicted_evidence': List[str]}"""
    )
    parser.add_argument(
        "--gold",
        type=str,
        required=True,
        help="Test or dev set from the released dataset"
    )
    parser.add_argument(
        "--text_evidence_only",
        action="store_true",
        help="If set, the evaluator will ignore evidence in figures and tables while reporting evidence f1"
    )
    args = parser.parse_args()
    gold_data = json.load(open(args.gold))
    gold_answers_and_evidence = get_answers_and_evidence(gold_data, args.text_evidence_only)
    predicted_answers_and_evidence = {}
    for line in open(args.predictions):
        prediction_data = json.loads(line)
        predicted_answers_and_evidence[prediction_data["question_id"]] = {
            "answer": prediction_data["predicted_answer"],
            "evidence": prediction_data["predicted_evidence"]
        }
    evaluation_output = evaluate(gold_answers_and_evidence, predicted_answers_and_evidence)
    print(json.dumps(evaluation_output, indent=2))

