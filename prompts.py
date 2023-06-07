from customLLM import ChatBotType

'''
For bard:
  - always delete: "Sure, I can help you with that.",
  - For evidece: only look after "Evidence:"
  - For boolean: only look after first word
  - For answerable: "The question is answerable:" (true false)
'''



class PromptGenerator:
  """Generate prompts for the QA task"""

  def __init__(self, title: str, arxiv_id: str, question: str):
    self.title = title
    self.arxiv_id = arxiv_id
    self.question = question
    
    self.base_prompt = f"""The context of my question:
Title: {self.title}
arXiv ID: {self.arxiv_id}
arxiv URL: https://arxiv.org/pdf/{self.arxiv_id}.pdf

My first question:
{self.question}"""
  

  def freeFormQA(self, chatBotType: ChatBotType):
    """Generate prompts for the free-form (extractive/abstractive) answers"""
    if chatBotType == ChatBotType.BARD:
      return f"""I want you to respond with at most two sentences.
I want you to respond with at most two sentences.
I want you to respond with at most two sentences.
I want you to answer questions about a specific machine learning paper by following the instructions of the user.
I want you reply with only the answer and nothing else.
I want you to answer directly, concisely and precisely.
I want you to write in a plain text file.
Do not reply with tables or lists.
Do not write any preamble, context, introduction or explanation.
I want you to use precise terms and numbers as the answer when possible.

{self.base_prompt}"""
    
    else:
#       return f"""I want you to act as a scholarly assistant who has expertise in natural language processing and machine learning. 
# I want you to answer questions about a specific machine learning paper by following the instructions of the user.
# I want you reply with only the answer and nothing else.
# I want you to answer directly, concisely and precisely.
# I want you to write in a plain text file.
# Do not reply with tables or lists.
# Do not write any preamble, context, introduction or explanation.
# I want you to use precise terms and numbers as the answer when possible.
# I want you to use your knowledge in natural language processing and your training data to answer the questions.
# I want you to answer with detail and precision.
# If you cannot answer precisely or if the paper lacks sufficient evidence, respond with only one word: 'Unanswerable'.
# If the question is a yes/no question, reply with "Yes." or "No." and nothing else.

# {self.base_prompt}"""
        return f"""
Title: {self.title}
arXiv ID: {self.arxiv_id}
Using your knowledge, answer the following question related to this paper by following the instructions below:
Question: {self.question}

Instructions:
Please answer directly, concisely and precisely without providing additional explanations or context and without any preamble or introduction. 
If you cannot answer based or the paper doesn't provide enough evidence, respond with only the word 'Unanswerable'. Do not make up an answer.
If you can answer using 'Yes' or 'No', please respond with only the word 'Yes' or 'No'.
If you can asnwered using a term or a list of terms, please respond with only the term or list of terms.

Answer: """
    # the one below is for 1000 test
#       return f"""
# Title: {self.title}
# arXiv ID: {self.arxiv_id}
# Using your knowledge, answer the following question related to this paper:
# Question: {self.question}

# Please answer directly and concisely without providing additional explanations or context and without any preamble or introduction. 
# If the question cannot be answered based on available information or the paper doesn't provide enough evidence, respond with only the word 'Unanswerable'.
# If the paper does not provide the necesary evidence or information related to the question, please respond only with the word 'Unanswerable'.
# If the question can be answered using 'Yes' or 'No', please respond with only the word 'Yes' or 'No'.
# If the question can be asnwered using a term or a list of terms, please respond with only the term or list of terms.
# """
  def booleanQA(self, chatBotType: ChatBotType):
    """Generate prompts for the boolean (yes/no) answers"""
    if chatBotType == ChatBotType.BARD:
      return f"""I want you to respond with only one word "yes" or "no" and nothing else.
I want you to respond with only one word.
Do not reply with more than one word.

The context of my question:
Title: {self.title}
arXiv ID: {self.arxiv_id}
arxiv URL: https://arxiv.org/pdf/{self.arxiv_id}.pdf

My first yes/no boolean question:
{self.question}"""

    else:
      return f"""I want you to act as a scholarly assistant who has expertise in natural language processing and machine learning. 
You will answer a question using only one word "yes" or "no".
I want you to respond with only one word "yes" or "no" and nothing else.
I want you to respond with only one word.

{self.base_prompt}"""
  
  def evidenceQA(self, chatBotType: ChatBotType):
    """Generate prompts for the evidence task"""
    if chatBotType == ChatBotType.BARD:
      return f"""I want you to act as a scholarly assistant who has expertise in natural language processing and machine learning. 
You will answer a question in the context of a research paper. Please provide an answer and relevant evidence.
Do not write any introductions. Reply with the answer, evidence and nothing else.
I want you to answer directly, concisely and precisely.
I want you to write in a plain text file.
Do not reply with tables or lists.
I want you to use precise terms and numbers as the answer when possible.
I want you to answer in the following format:

Answer: <answer> (at most two sentences)
Evidence: <evidence> (at most five sentences)

{self.base_prompt}"""
    else:
      return f"""
Title: {self.title}
arXiv ID: {self.arxiv_id}
Using your knowledge, answer the following question related to this paper and provide evidence to support your answer:
Question: {self.question}

For the answer, respond directly and concisely without providing additional explanations or context and without any preamble or introduction. 
If the question cannot be answered based on available information or the paper doesn't provide enough evidence, respond with only the word 'Unanswerable'.
If the paper does not provide the necesary evidence or information related to the question, please respond only with the word 'Unanswerable' and leave the evidence blank.
If the question can be answered using 'Yes' or 'No', please respond with only the word 'Yes' or 'No'.
If the question can be answered using a number, please respond with only the number.
If the question can be asnwered using a term or a list of terms, please respond with only the term or list of terms.

For the evidence, please be detailed, precise and concise. Justify your answer with the evidence.
I want you to answer in the following format:

Answer: <answer> (at most two sentences)
Evidence: <evidence> (at most five sentences)"""
#       return f"""I want you to act as a scholarly assistant who has expertise in natural language processing and machine learning. 
# I want you to answer questions about a specific machine learning paper by following the instructions of the user.
# I want you to answer directly, concisely and precisely.
# I want you to write in a plain text file.
# Do not reply with tables or lists.
# Do not write any preamble, context, or introduction.
# I want you to use precise terms and numbers as the answer when possible.
# I want you to use your knowledge in natural language processing and your training data to answer the questions.
# I want you to answer with detail and precision.
# If you cannot answer the question in the context of the paper, reply with "Unanswerable." as the answer.
# If the question is a yes/no question, reply with "Yes." or "No." as the asnwer.
# I want you to answer in the following format:

# Answer: <answer> (at most two sentences)
# Evidence: <evidence> (at most five sentences)

# {self.base_prompt}"""

  def unanswerableQA(self, chatBotType: ChatBotType):
    """Generate prompts for the unanswerable questions"""
    if chatBotType == ChatBotType.BARD:
      return f"""I want you to act as a scholarly assistant who has expertise in natural language processing and machine learning. 
I want you to answer questions about a specific machine learning paper by following the instructions of the user.
I want you reply with only the answer and nothing else.
I want you to answer directly, concisely and precisely.
If the question is not answerable, reply with "Unanswerable." and nothing else.

The context of my question:
Title: {self.title}
arXiv ID: {self.arxiv_id}
arxiv URL: https://arxiv.org/pdf/{self.arxiv_id}.pdf

My first question:
{self.question} """
    
    else:
      return f"""I want you to act as a scholarly assistant who has expertise in natural language processing and machine learning. 
I want you to identify if a question is answerable or unanswerable.
I want you to respond with only one word "answerable" or "unanswerable" and nothing else.
I want you to answer in a plain text file.

The context of my question:
Title: {self.title}
arXiv ID: {self.arxiv_id}
arxiv URL: https://arxiv.org/pdf/{self.arxiv_id}.pdf

My first yes/no boolean question:
In the context of the paper? Is the question, "{self.question}" answerable?"""

  def visconde(self, exmaple1, example2):
    #  For each example, use the documents to create an \"Answer\" and an \"Explanation\" to the \"Question\". Answer \"Unanswerable\" when not enough information is provided in the documents. Pay attention to answer only \"yes\" or \"no\" in boolean questions.\n\n
    return f"""For each example, use the your own trainig data and knolwedge to create an "Answer" and an "Explanation" to the "Question". Write a one word answer "Answer: Unanswerable" when not enough information is provided in the paper. Pay attention to write a one word answer "Answer: yes" or "Answer: no" for boolean yes/no questions.

Example 1:

[Title]: {exmaple1['title']}

[arXiv ID]: {exmaple1['arxiv_id']}

Question: {exmaple1['question']}

Explanation: {exmaple1['explanation']}

Answer: {exmaple1['answer']}

Example 2:

[Title]: {example2['title']}

[arXiv ID]: {example2['arxiv_id']}

Question: {example2['question']}

Explanation: {example2['explanation']}

Answer: {example2['answer']}

Example 3:

[Title]: Abstractive Summarization for Low Resource Data using Domain Transfer and Data Synthesis

[arXiv ID]: 2002.03407

Question: What is the interannotator agreement for the human evaluation?

Explanation: No Evidence
  
Answer: Unanswerable

Example 4:

[Title]: Abstractive Summarization for Low Resource Data using Domain Transfer and Data Synthesis

[arXiv ID]: 2002.03407

Question: Is the template-based model realistic?

Explanation: Finally, while the goal of our template model was to synthesize data, using it for summarization is surprisingly competitive, supporting H6. This encourages us to enhance our template model and explore templates not so tailored to our data.\n\nHuman Evaluation Results. While automated evaluation metrics like ROUGE measure lexical similarity between machine and human summaries, humans can better measure how coherent and readable a summary is. Our evaluation study investigates whether tuning the PG-net model inc
  
Answer: Yes

Example 5:

[Title]: {self.title}

[arXiv ID]: {self.arxiv_id}

Question: {self.question}

Explanation: """