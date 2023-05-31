from bs4 import BeautifulSoup

class Paper:
    def __init__(self, url, browser):
        self.url = url
        self.browser = browser
        self.title = ''
        self.authors = []
        self.abstract = ''
        self.section_names = []
        self.section_texts = []

    def parse_pdf(self):
        self.browser.get(self.url)
        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Get the title
        title = soup.find('h1', class_=lambda x: 'ltx_title' in x and 'ltx_title_document' in x)
        if title is None:
            raise ValueError("Title element not found")
        title = title.text.strip()

        # Get the authors
        authors = ""
        author_group = soup.find('div', class_='ltx_authors')
        if author_group is not None:
            authors =  author_group.find_all('span', class_='ltx_personname')
            if authors is not None:
                authors = [author.text.strip() for author in authors]

        # Get the abstract
        abstract = soup.find('div', class_='ltx_abstract')
        if abstract is None:
            raise ValueError("Abstract element not found")
        abstract_text = abstract.find('p')
        abstract = abstract.text.strip()

        # Get each section and store it in a dictionary
        section_names = []
        section_texts = []
        sections = soup.find_all('section', class_='ltx_section')
        if sections is None:
            raise ValueError("Sections element not found")
        for section in sections:
            if section is None:
                continue
            section_title = section.find('h2', class_=lambda x: 'ltx_title' in x and 'ltx_title_section' in x)
            if section_title is None:
                section_title = "section title"
            else:
                section_title = section_title.text.strip()
            if section_title == 'References':
                continue
            section_names.append(section_title)
            section_text = ''
            # iterate all children recursively and concatenate all the text in all the children and subchildren
            # skip if the child is a figure
            # if the tag is math, then use text in alttext
            valid_tags = ['p', 'math', 'cite','h3']
            valid_sections = ['div', 'section']

            children = section.children if section.children is not None else []
            for child in children:
                if child.name in valid_sections:
                    descendents = child.descendants if child.descendants is not None else []
                    for descendent in descendents:
                        if descendent.name in valid_tags:
                            if descendent.name == 'math':
                                section_text += descendent['alttext']
                            if descendent.name == 'h3':
                                section_text += ' ' + descendent.text.strip() + '. '
                            else:
                                section_text += descendent.text.strip()
                    
            section_texts.append(section_text)
                
            self.title = title
            self.authors = authors
            self.abstract = abstract
            self.section_names = section_names
            self.section_texts = section_texts

    def to_dict(self):

        res = {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'sections': []
        }
        for i in range(len(self.section_names)):
            res['sections'].append({
                'name': self.section_names[i],
                'text': self.section_texts[i]
            })
        return res
