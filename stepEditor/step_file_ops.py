import re

class StepFileOps:
    def __init__(self):
        self.category_dict = {}
        self.element_dict = {}
        self.step_content = []
        self.filename = ""

    def parseStepFile(self, filename):
        self.filename = filename
        with open(filename, 'r') as file:
            self.step_content = file.readlines()

        self.category_dict.clear()
        self.element_dict.clear()

        for line in self.step_content:
            line = line.strip()

            if line.startswith('#'):
                parts = line.split('=')

                if len(parts) >= 2:
                    element_number = parts[0]
                    element_name = parts[1].split('(')[0].strip()
                    self.element_dict[element_number] = element_name

                    if element_name in self.category_dict:
                        self.category_dict[element_name].append(element_number)
                    else:
                        self.category_dict[element_name] = [element_number]

    def formatParameters(self, parameters):
        formatted_parameters = []
        parameter_tokens = re.split(r'([,;()])', parameters)
        for token in parameter_tokens:
            token = token.strip()
            if token.startswith('#'):
                formatted_parameters.append(f"{token}")
            else:
                formatted_parameters.append(token)

        return ''.join(formatted_parameters)

    def getReferencedElements(self, element_number):
        referenced_elements = []
        content = self.getElementContent(element_number)
        tokens = re.split(r'([,;()])', content)
        for token in tokens:
            token = token.strip()
            if token.startswith('#'):
                element_details = self.getElementDetails(token)
                element_details = token + " - " + element_details
                referenced_elements.append(element_details)

        return referenced_elements

    def getElementDetails(self, element_number):
        content = self.getElementContent(element_number)
        formatted_content = []

        parameter_tokens = re.split(r'([,;()])', content)
        for token in parameter_tokens:
            token = token.strip()
            if token == element_number:
                referenced_name = self.element_dict.get(token, "")
                referenced_value = self.getElementContent(token)
                formatted_content.append(
                    f"{referenced_name} ({referenced_value})")
            else:
                formatted_content.append(token)

        return ''.join(formatted_content)

    def getElementContent(self, element_number):
        content = []
        found_element = False

        for line in self.step_content:
            line = line.strip()

            if line.startswith(element_number):
                found_element = True
            elif found_element and line.startswith('#'):
                break

            if found_element:
                content.append(line)

        formatted_content = []
        for line in content:
            parts = line.split('=')
            if len(parts) >= 2:
                parameters = parts[1].strip()
                formatted_parameters = self.formatParameters(parameters)
                formatted_content.append(f"{formatted_parameters}")

        return '\n'.join(formatted_content)

    def getElementValue(self, element_number):
        content = self.getElementContent(element_number)
        parameters = ""
        if '(' in content and ')' in content:
            parameters = content.split('(')[1].split(')')[0]
        return parameters

    def searchElements(self, text):
        text = text.lower()
        matching_elements = []

        for element_number, element_name in self.element_dict.items():
            if text in element_number.lower() or text in element_name.lower():
                matching_elements.append(element_number)

        return matching_elements
