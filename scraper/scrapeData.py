from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import re

from paper import Paper

# Add options for headless browsing
options = FirefoxOptions()
options.add_argument("--headless")

browser = webdriver.Firefox(executable_path="C:\\Users\\marco\\geckodriver.exe", options=options)
# define sources to scrape
base_url = [
    'https://interactiveaudiolab.github.io/teaching/generative_deep_models.html', 
    'https://github.com/dair-ai/ML-Papers-of-the-Week'
]

def clean_url(link):
    # extract arxiv id from url
    arxiv_id = link.split('/')[-1]
    # remove .pdf from arxiv id if it exists
    arxiv_id = arxiv_id.replace('.pdf', '')
    # construct new ar5iv url 
    url = 'https://ar5iv.labs.arxiv.org/html/' + arxiv_id
    return url

def get_links(html):
    links = []
    # find all links that contain 'arxiv' in the url and end in .pdf or numbers
    for match in re.finditer(r'href=[\'"]?([^\'" >]+)', html):
        url = match.group(1)
        if 'arxiv' in url and ('.pdf' in url or url[-3].isdigit()):
            links.append(clean_url(url))
    return links

links = []
# get list of urls ending in .pdf and containing 'arxiv' in the url
for url in base_url:
    browser.get(url)
    html = browser.page_source
    links += get_links(html)

# remove duplicates
links = list(set(links))

papers = []
# scrape each paper
for index, link in enumerate(links):
    # print(link)
    paper = Paper(link, browser)
    url_id = link.split('/')[-1]
    try:
        paper.parse_pdf()
        print(f'success parsing {url_id} {index}/{len(links)}')
    except Exception as e:
        print(f'error parsing {link} - {e}')
        continue
    papers.append(paper)

# save papers to json
with open('./papers.json', 'w') as f:
    json.dump(papers, f, indent=4, default=lambda x: x.to_dict())

# cleanup
browser.quit()

# url = "https://ar5iv.labs.arxiv.org/html/2112.10741"
# browser.get(url)
# html = browser.page_source

# def scrape_paper(html):

#     soup = BeautifulSoup(html, 'html.parser')

#     # Get the title
#     title = soup.find('h1', class_='ltx_title ltx_title_document').text.strip()
#     print(title)

#     # Get the authors
#     authors = soup.find('div', class_='ltx_authors').find_all('span', class_='ltx_personname')
#     authors = [author.text.strip() for author in authors]
#     print(authors)

#     # Get the abstract
#     abstract = soup.find('div', class_='ltx_abstract').find('p').text.strip()
#     print(abstract[0:150])

#     # Get each section and store it in a dictionary
#     section_names = []
#     section_texts = []
#     sections = soup.find_all('section', class_='ltx_section')
#     for section in sections:
#         section_title = section.find('h2', class_='ltx_title ltx_title_section').text.strip()
#         if section_title == 'References':
#             continue
#         section_names.append(section_title)
#         section_text = ''
#         # iterate all children recursively and concatenate all the text in all the children and subchildren
#         # skip if the child is a figure
#         # if the tag is math, then use text in alttext
#         valid_tags = ['p', 'math', 'cite','h3']
#         valid_sections = ['div', 'section']
#         for child in section.children:
#             if child.name in valid_sections:
#                 for descendent in child.descendants:
#                     if descendent.name in valid_tags:
#                         if descendent.name == 'math':
#                             section_text += descendent['alttext']
#                         if descendent.name == 'h3':
#                             section_text += ' ' + descendent.text.strip() + '. '
#                         else:
#                             section_text += descendent.text.strip()
            
#         section_texts.append(section_text)
        
#     # write the first section text to a file
#     with open('sample_section.txt', 'w', encoding='utf-8') as f:
#         f.write(section_texts[1])

#     # write everything into a dictionary
#     paper = {
#         'title': title,
#         'authors': authors,
#         'abstract': abstract,
#         'sections': dict(zip(section_names, section_texts))
#     }

#     return paper

#     # browser.quit() # close the browser
