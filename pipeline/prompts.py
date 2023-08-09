from langchain.schema import Document
from typing import List

def qasper_extract_answer_evidence(answers):
  # extracted from qasper_evaluator.py
  annotation_info = answers[0]
  answer_info = annotation_info["answer"]
  res = {}
  if answer_info["unanswerable"]:
    res = {"answer": "Unanswerable", "evidence": []}
  else:
    if answer_info["extractive_spans"]:
        answer = ", ".join(answer_info["extractive_spans"])
    elif answer_info["free_form_answer"]:
        answer = answer_info["free_form_answer"]
    elif answer_info["yes_no"]:
        answer = "Yes"
    elif answer_info["yes_no"] is not None:
        answer = "No"
    else:
        raise RuntimeError(f"Annotation {answer_info['annotation_id']} does not contain an answer")
    
    evidence = [text for text in answer_info["evidence"] if "FLOAT SELECTED" not in text]
    res = {"answer": answer, "evidence": evidence}
  return res

def qasper_construct_examples(dev_dataset, k=5):
  # returns string that has all the examples
  import random

  rand_keys = random.sample(list(dev_dataset.keys()), k)

  example_count = 1
  examples = ""

  for key in rand_keys:
    question_obj = dev_dataset[key]["qas"][0]
    answer_evidence = qasper_extract_answer_evidence(question_obj["answers"])

    """prompt template:
    Example 1:

    [Document 1]: The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France.

    [Document 2]: The Eiffel Tower is named after the engineer Gustave Eiffel, whose company designed and built the tower.

    Question: Who designed the Eiffel Tower?

    Answer: Gustave Eiffel

    Example 2:

    [Document 1]: The Venus de Milo is an ancient Greek statue and one of the most famous works of ancient Greek sculpture.

    Question: Who is the Venus de Milo?

    Answer:"""

    # title = question_obj["title"]
    question = question_obj["question"]
    # arxiv_id = key
    evidence = answer_evidence["evidence"]
    # TODO: add explanation later, can infer on the fly?

    examples += f"\n\nExample {example_count}:\n\n"
    # can experiment with this later to see if including title and arxiv_id is helpful
    for idx, document in enumerate(evidence):
      examples += f"[Document {idx + 1}]: {document}\n\n"

    examples += f"Question: {question}\n\n"
    examples += f"Answer: {answer_evidence['answer']}"
    example_count += 1
  
  return examples
    

def qasper_construct_prompt(question, documents: List[Document], examples="", k=0):
  prompt = 'For each example, use the documents to create to create an "Answer" and an "Explanation" to the "Question". Write a one word answer "Answer: Unanswerable" when not enough information is provided in the documents. Pay attention to write a one word answer "Answer: yes" or "Answer: no" for boolean yes/no questions.'
  # prompt = "For each example, use the documents to create an \"Answer\" and an \"Explanation\" to the \"Question\". Answer \"Unanswerable\" when not enough information is provided in the documents. Pay attention to answer only \"yes\" or \"no\" in boolean questions."
  prompt += examples
  prompt += f"\n\nExample {k + 1}:"
  for idx, document in enumerate(documents):
    prompt += f"\n\n[Document {idx + 1}]: {document.page_content}"
  prompt += f"\n\nQuestion: {question}"
  prompt += "\n\nAnswer:"

  return prompt


def glide_construct_prompt(question, documents: List[Document]):
  prompt = "Use the following pieces of context and your own training knowledge to answer the question at the end concisely. If you don't know the answer, just say that you don't know, don't try to make up an answer.\n\n"
  for idx, document in enumerate(documents):
    prompt += f"[Context {idx + 1}]: {document.page_content}\n\n"

  prompt += f"Question: {question}\n\nHelpful Answer:"
  return prompt

def glide_constrct_demo_prompt(question, documents: List[Document]):
  prompt = "Use the following pieces of context and your own training knowledge to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.\n\n"
  for idx, document in enumerate(documents):
    prompt += f"[Context {idx + 1}]: {document.page_content[0:100]}...\n\n"

  prompt += f"Question: {question}\n\nHelpful Answer:"

  return prompt

# TODO: a
# find the actual full texts, and then use shorter chunk length?
# albations? chunk length, few shot, num of docs, 
# better prompts in general for both
