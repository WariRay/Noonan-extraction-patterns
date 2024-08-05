from os import path
import os
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString

html_doc = path.join(os.getcwd(), "Noonan-Syndrome-GeneReviews.html")

# Read the contents of the file
with open(html_doc, 'r', encoding='utf-8') as file:
    file_content = file.read()

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(file_content, 'html.parser')

class HTMLProcessor:
    def __init__(self, file_name):
        self.filename = file_name

        with open(file_name, 'r', encoding='utf-8') as file:
            self.html = BeautifulSoup(file.read(), features="lxml")
    
    def split_by_h2(self, avoid_sections=['Chapter Notes', 'References']):
        h2_tags = self.html.find_all('h2')
        self.sections = []

        for h2 in h2_tags: 
            if h2.text not in avoid_sections:
                sub_sections = [sibling for sibling in h2.find_next_siblings()]
                section = {'Section': h2.text, 'Contents': sub_sections}
                self.sections.append(section)

    def split_section(self, section_to_split):
        split_result = []
        for content in section_to_split['Contents']:
            recursive_split(content, split_result)

        for split in split_result:
            print(split)
            print(10*"=")

def split_table(table: Tag | NavigableString, result: list):
    stop = False
    merge = ["p", "span", "h3", "h4", "a", "i"]
    merged = False

    if type(table) is NavigableString:
        if table.parent.name in merge and len(result) != 0:
            last_elem = result[-1]
            result[-1] = f"{last_elem} {table}"
            merged = True
        stop = True

    if stop:
        if not merged:
            result.append(table)
    else:
        for child_tag in table.children:
            if child_tag.name == "table":
                table_string: str = "\n"
                table_string += "-" * 50 + "\n"
                ############################
                table_headings = child_tag.find_all("th")
                table_string += "|"
                for heading in table_headings:
                    table_string += f"{heading.get_text()}|"
                table_string += "\n"
                ############################
                row_counter = 0
                for row in child_tag.find_all("tr"):
                    column_counter = 0
                    columns = row.find_all("td")
                    columns_total = len(columns)-1
                    for column in columns:
                        if column_counter == 0:
                            table_string += f"{column.get_text()}"
                        elif column_counter == columns_total:
                            table_string += f"| {column.get_text()}\n"
                        else:
                            table_string += f"| {column.get_text()}"
                        column_counter += 1
                    row_counter += 1
                table_string += "-" * 50 + "\n"
                result.append(table_string)
            else:
                split_table(child_tag, result)

def split_list(ul_list: Tag | NavigableString):
    result_str = ""
    for li in ul_list.descendants:
        if type(li) is Tag and li.name == "div":
            result_str += f"- {li.get_text()}\n"
    return result_str

def recursive_split(tag: Tag | NavigableString, result: list):
    stop = False
    merge = ["p", "span", "h3", "h4", "a", "i"]
    merged = False
    has_table = False

    if type(tag) is Tag:
        elem_class = tag.has_attr("class")
        if elem_class and "table" in tag["class"]:
            has_table = True
            stop = True
            table_partition = []
            split_table(tag, table_partition)
            partition_strings = ""
            for split in table_partition:
                partition_strings += f"{split}"
            result.append(partition_strings)
        elif tag.name == "ul":
            list_partition: str = ""
            list_partition = split_list(tag)
            last_elem = result[-1]
            result[-1] = f"{last_elem}{list_partition}"
            return
        elif tag.name == "p":
            result.append(tag.get_text())
            return
    else:
        stop = True

    if stop:
        if not merged and not has_table:
            result.append(tag)
    else:
        for child_tag in tag.children:
            recursive_split(child_tag, result)

###########################################################################

header2 = HTMLProcessor(html_doc)
header2.split_by_h2()

summary: list = header2.sections[0]
#print(summary['Contents'][2])
#print(summary['Contents'][2])
#sub_summary = summary['Contents'][2]
sub_summary = summary['Contents'][0]

clinical_characteristics = header2.sections[2]
sub_clinical_characteristics = clinical_characteristics['Contents'][0]

test_split = header2.split_section(header2.sections[2])
