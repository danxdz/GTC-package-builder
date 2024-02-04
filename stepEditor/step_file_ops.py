import os
import wx
import re


class StepFileViewer(wx.Frame):
    def __init__(self, *args, **kw):
        super(StepFileViewer, self).__init__(*args, **kw)

        self.category_dict = {}
        self.initUI()

    def initUI(self):
        panel = wx.Panel(self)

        self.load_button = wx.Button(panel, label='Open STEP File')
        self.load_button.Bind(wx.EVT_BUTTON, self.openFile)

        self.tree_widget = wx.TreeCtrl(panel, style=wx.TR_DEFAULT_STYLE | wx.TR_SINGLE)
        self.tree_widget.Bind(wx.EVT_TREE_SEL_CHANGED, self.showElementInfo)

        self.search_box = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.search_box.Bind(wx.EVT_TEXT, self.searchElements)

        self.info_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)



        self.ref_tree_widget = wx.TreeCtrl(panel, style=wx.TR_DEFAULT_STYLE | wx.TR_SINGLE)
        self.ref_tree_widget.Bind(wx.EVT_LEFT_DCLICK, self.onDoubleClick)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.load_button, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(self.tree_widget, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(self.search_box, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(self.info_text, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(self.ref_tree_widget, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(vbox)

        self.SetSize((800, 600))
        self.SetTitle('STEP File Viewer')
        self.Centre()

    def onDoubleClick(self, event):
        #get item clicked text
        clicked_item = self.ref_tree_widget.GetSelection()
        item_text = self.ref_tree_widget.GetItemText(clicked_item)

        print("item_text :: ", item_text)

        # Se encontrar o número do elemento, busca e seleciona o item correspondente na TreeCtrl
        if item_text.startswith('#'):
            item_text = item_text.split(' ')[0]
            print("item_text :: ", item_text)
            #get item tree id 
            item = self.tree_widget.GetRootItem()
            print("item :: ", item)
            while item:
                if self.tree_widget.GetItemText(item) == "Categories":
                    #get childrens
                    category = self.tree_widget.GetChildren()
                    while category:
                        element = self.tree_widget.GetFirstChild(category)
                        while element:
                            if self.tree_widget.GetItemText(element) == item_text:
                                self.tree_widget.SelectItem(element, True)
                                break
                            element = self.tree_widget.GetNextSibling(element)
                        if element:
                            break
                        category = self.tree_widget.GetNextSibling(category)
                    if category:
                        break
                item = self.tree_widget.GetNextSibling(item)
            #select the item in the tree
            self.tree_widget.SelectItem(clicked_item, True)
  
    def openFile(self, event):
        wildcard = "STEP Files (*.stp; *.step)|*.stp;*.step|All Files (*)|*.*"
        dialog = wx.FileDialog(self, "Open STEP File", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            self.parseStepFile(filename)

        dialog.Destroy()

    def parseStepFile(self, filename):
        with open(filename, 'r') as file:
            step_content = file.readlines()

        self.tree_widget.DeleteAllItems()
        self.info_text.Clear()
        self.category_dict.clear()

        element_dict = {}

        root = self.tree_widget.AddRoot(os.path.basename(filename).split('.')[0])
        self.tree_widget.SetItemText(root, "Categories")
        self.tree_widget.Expand(root)

        for line in step_content:
            line = line.strip()

            if line.startswith('#'):
                parts = line.split('=')

                if len(parts) >= 2:
                    element_number = parts[0]
                    element_name = parts[1].split('(')[0].strip()
                    element_dict[element_number] = element_name

                    if element_name in self.category_dict:
                        self.category_dict[element_name].append(element_number)
                    else:
                        self.category_dict[element_name] = [element_number]

        sorted_categories = sorted(self.category_dict.keys())

        for category in sorted_categories:
            category_item = self.tree_widget.AppendItem(root, f"{category} ({len(self.category_dict[category])})")
            for element in sorted(self.category_dict[category], key=lambda x: element_dict[x]):
                element_item = self.tree_widget.AppendItem(category_item, element)

        self.element_dict = element_dict
        self.step_content = step_content

    def showElementInfo(self, event):
        item = event.GetItem()
        element_number = self.tree_widget.GetItemText(item)
        element_name = self.element_dict.get(element_number, "")
        element_content = self.getElementContent(element_number)
        self.info_text.Clear()
        self.info_text.AppendText(f"Element Number: {element_number}\n")
        self.info_text.AppendText(f"Element Name: {element_name}\n")
        self.info_text.AppendText(f"Element Content:\n")
        self.info_text.AppendText(element_content)

        referenced_elements = self.getReferencedElements(element_number)
        self.ref_tree_widget.DeleteAllItems()
        ref_root = self.ref_tree_widget.AddRoot("Referenced Elements")

        for element in referenced_elements:
            ref_item = self.ref_tree_widget.AppendItem(ref_root, element)

        self.ref_tree_widget.ExpandAll()

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

    def formatParameters(self, parameters):
        formatted_parameters = []
        parameter_tokens = re.split(r'([,;()])', parameters)
        for token in parameter_tokens:
            token = token.strip()
            if token.startswith('#'):
                referenced_name = self.element_dict.get(token, "")
                formatted_parameters.append(f"{referenced_name} ({token})")
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

    def getElementValue(self, element_number):
        content = self.getElementContent(element_number)
        parameters = content.split('(')[1].split(')')[0]
        return parameters

    def searchElements(self, event):
        text = self.search_box.GetValue().lower()
        matching_elements = []

        for element_number, element_name in self.element_dict.items():
            if text in element_number.lower() or text in element_name.lower():
                matching_elements.append(element_number)

        self.updateTreeWithSearchResults(matching_elements)

    def updateTreeWithSearchResults(self, matching_elements):
        self.tree_widget.DeleteAllItems()

        root = self.tree_widget.AddRoot("Categories")
        self.tree_widget.Expand(root)

        expanded_categories = set()

        for element_number in matching_elements:
            element_name = self.element_dict.get(element_number, "")
            category = element_name
            if not category:
                category = "Uncategorized"
            expanded_categories.add(category)

        for category in expanded_categories:
            category_item = self.tree_widget.AppendItem(root, f"{category} ({len(self.category_dict[category])})")
            for element in sorted(self.category_dict[category], key=lambda x: self.element_dict[x]):
                element_item = self.tree_widget.AppendItem(category_item, element)

        self.tree_widget.ExpandAll()


def main():
    app = wx.App(False)
    viewer = StepFileViewer(None)
    viewer.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
