import os
import wx
import re


class StepFileViewer(wx.Frame):
    def __init__(self, *args, **kw):
        super(StepFileViewer, self).__init__(*args, **kw)

        self.category_dict = {}
        self.element_dict = {}
        self.step_content = []

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

    def openFile(self, event):
        wildcard = "STEP Files (*.stp; *.step)|*.stp;*.step|All Files (*)|*.*"
        dialog = wx.FileDialog(self, "Open STEP File", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            self.parseStepFile(filename)

        dialog.Destroy()

    def parseStepFile(self, filename):
        try:
            with open(filename, 'r') as file:
                self.step_content = file.readlines()

            self.tree_widget.DeleteAllItems()
            self.info_text.Clear()
            self.category_dict.clear()
            self.element_dict.clear()

            root = self.tree_widget.AddRoot(os.path.basename(filename).split('.')[0])
            self.tree_widget.SetItemText(root, "Categories")
            self.tree_widget.Expand(root)

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

            for category, elements in sorted(self.category_dict.items()):
                category_item = self.tree_widget.AppendItem(root, f"{category} ({len(elements)})")
                for element in sorted(elements, key=lambda x: self.element_dict[x]):
                    self.tree_widget.AppendItem(category_item, element)

        except Exception as e:
            wx.MessageBox(f"Error parsing the file: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def showElementInfo(self, event):
        item = event.GetItem()
        element_number = self.tree_widget.GetItemText(item)
        element_name = self.element_dict.get(element_number, "")
        element_content = self.getElementContent(element_number)

        self.info_text.Clear()
        self.info_text.AppendText(f"Element Number: {element_number}\n")
        self.info_text.AppendText(f"Element Name: {element_name}\n")
        self.info_text.AppendText("Element Content:\n")
        self.info_text.AppendText(element_content)

        referenced_elements = self.getReferencedElements(element_number)
        self.ref_tree_widget.DeleteAllItems()
        ref_root = self.ref_tree_widget.AddRoot("Referenced Elements")
        for ref in referenced_elements:
            self.ref_tree_widget.AppendItem(ref_root, ref)
        self.ref_tree_widget.ExpandAll()

    def getElementContent(self, element_number):
        content = []
        found = False

        for line in self.step_content:
            if line.strip().startswith(element_number):
                found = True
            elif found and line.strip().startswith('#'):
                break

            if found:
                content.append(line.strip())

        return '\n'.join(content)

    def getReferencedElements(self, element_number):
        element_content = self.getElementContent(element_number)
        referenced_elements = re.findall(r'#\d+', element_content)
        return list(set(referenced_elements))  # Remove duplicates

    def onDoubleClick(self, event):
        clicked_item = self.ref_tree_widget.GetSelection()
        item_text = self.ref_tree_widget.GetItemText(clicked_item).split(' ')[0]

        if item_text.startswith('#'):
            self.selectTreeItemByText(item_text)

    def selectTreeItemByText(self, text):
        def recursiveSearch(parent_item):
            item, cookie = self.tree_widget.GetFirstChild(parent_item)
            while item:
                if self.tree_widget.GetItemText(item) == text:
                    self.tree_widget.SelectItem(item, True)
                    return True
                if recursiveSearch(item):
                    return True
                item, cookie = self.tree_widget.GetNextChild(parent_item, cookie)
            return False

        recursiveSearch(self.tree_widget.GetRootItem())

    def searchElements(self, event):
        query = self.search_box.GetValue().lower()
        matching_elements = [num for num, name in self.element_dict.items()
                             if query in num.lower() or query in name.lower()]
        self.updateTreeWithSearchResults(matching_elements)

    def updateTreeWithSearchResults(self, matching_elements):
        self.tree_widget.DeleteAllItems()
        root = self.tree_widget.AddRoot("Search Results")
        for element_number in matching_elements:
            self.tree_widget.AppendItem(root, element_number)
        self.tree_widget.ExpandAll()


def main():
    app = wx.App(False)
    viewer = StepFileViewer(None)
    viewer.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
