# from revChatGPT.V1 import Chatbot
# print("init chat bot")
# chatbot = Chatbot(config={
#     "access_token":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJzdGFubGV5d2FuZzI5OTlAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXItMGM2OVpaZ3BYUXltQ2Jiems3djA2QlVCIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExNTQ1NDgwNTA3MzcyMTk3MTE5OCIsImF1ZCI6WyJodHRwczovL2FwaS5vcGVuYWkuY29tL3YxIiwiaHR0cHM6Ly9vcGVuYWkub3BlbmFpLmF1dGgwYXBwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2ODU0OTU1MjAsImV4cCI6MTY4NjcwNTEyMCwiYXpwIjoiVGRKSWNiZTE2V29USHROOTVueXl3aDVFNHlPbzZJdEciLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG1vZGVsLnJlYWQgbW9kZWwucmVxdWVzdCBvcmdhbml6YXRpb24ucmVhZCBvcmdhbml6YXRpb24ud3JpdGUifQ.sHK-1IXcgMgSMLoeyt1wvqGafUlv5D0rFfjFN-DdMKyeq1ply10ouC3g6pd39yy25xnjlcmA-E98wC7uDC5yWfl8N7X_H7g4GtQQNwfquYT8ua3MvRnThhbwRNKaLeNc7MuC3Yh8KP4BaF8RwWcQziQttpMRQTgzP6I4iNq_7H4ugWSJ7sh1wnMZS6YKZVFU5tzwmWA7qgxwxeuTrdUsgZA_eRBenffsa8aAaTidD-9Gyif7UQb5vYr6f8FuIP_Fy9lMGfyloJTprYb50lkgbKmSiZvk7U6XKwwYjPAk6ylbAAy9-uvgcFoXWCo4g6YQBeGwHlj84mVJh_Mn1SXVfA",
#     "model":"text-davinci-002-render-sha",
#     "disable_history": True,
#     "proxy": "http://localhost:9090/api/"
# })

# prompt = "how many beaches does portugal have?"
# response = ""

# # print(chatbot.ask(prompt))
# for data in chatbot.ask(prompt):
#     response = data["message"]

# print(response)

def find_substrings(input_string):
    # Find the substring between "Answer:" and "Evidence:"
    start_index = input_string.find("Answer:")
    if start_index == -1:
        raise ValueError("Answer not found in the input string")

    start_index += len("Answer:")
    end_index = input_string.find("Evidence:", start_index)
    if end_index == -1:
        raise ValueError("Evidence not found in the input string")

    answer_substring = input_string[start_index:end_index].strip()

    # Find the substring after "Evidence:"
    evidence_substring = input_string[end_index + len("Evidence:"):].strip()

    return answer_substring, evidence_substring


# Example usage
# input_string = "This is a sample string. Answer: Here is the answer. \nEvidence: Some evidence to support the answer.\n some other shit"
# try:
#     answer, evidence = find_substrings(input_string)
#     print("Answer sub:", answer)
#     print("Evidence sub:", evidence)
# except ValueError as e:
#     print("Error:", str(e))


import requests
import feedparser
from bs4 import BeautifulSoup

def scrape_taxonomy():
    url = "https://arxiv.org/category_taxonomy"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    
    taxonomy = {}
    for div in soup.find_all('div', {'class': 'columns divided'}):
        text = div.find('h4').text
        # finds the substring after the first ( and before the last )
        code = text.split(' ')[0]
        index = text.find('(')
        if index != -1:
            category = text[index + 1:-1]
        else:
            category = ""
        taxonomy[code] = category
    return taxonomy

def get_arxiv_paper_details(arxiv_id, taxonomy):
    base_url = 'http://export.arxiv.org/api/query?'
    query = 'id_list={}'.format(arxiv_id)
    response = requests.get(base_url + query)
    feed = feedparser.parse(response.content)
    
    if len(feed.entries) > 0:
        entry = feed.entries[0]
        print("Title: ", entry.title)
        print("Published: ", entry.published)
        print("Subjects: ", [taxonomy.get(t['term'], t['term']) for t in entry.tags])
        print(entry.keys())
    else:
        print("No paper found with the given arXiv id.")

taxonomy = scrape_taxonomy()

# Test the function with an example arXiv id
get_arxiv_paper_details('2101.11408', taxonomy)

# test custom


