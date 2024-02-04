import wx
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
                    self.element_dict[element_number] = {
                        'name': element_name,
                        'children': []
                    }

                    # Use 'Uncategorized' for elements without a specific category
                    current_category = self.element_dict.get(element_number, {}).get('name', 'Uncategorized')

                    if current_category in self.category_dict:
                        self.category_dict[current_category].append(element_number)
                    else:
                        self.category_dict[current_category] = [element_number]

                    # If the line has children, associate them with the current element
                    if '(' in parts[1]:
                        children_str = parts[1].split('(', 1)[1].split(')')[0]
                        children = [child.strip() for child in children_str.split(',')]
                        self.element_dict[element_number]['children'] = children


    def getReferencedElements(self, element_number):
        referenced_elements = []

        print("element_number :: ", element_number)

        # Find the line corresponding to the given element_number
        element_line = next((line for line in self.step_content if line.startswith(f'#{element_number}=')), None)

        if element_line:
            print(element_line)
           # Find all the references in the line
            references = re.findall(r'#\d+', element_line)

            # Add the references to the list
            for ref in references:
                referenced_elements.append(ref)

        return referenced_elements


class StepFileViewer(wx.Frame):
    def __init__(self, parent, title):
        super(StepFileViewer, self).__init__(parent, title=title, size=(800, 600))

        self.step_file_ops = StepFileOps()

        self.tree_ctrl = wx.TreeCtrl(self, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        self.ref_tree_ctrl = wx.TreeCtrl(self, style=wx.TR_DEFAULT_STYLE)

        self.load_button = wx.Button(self, label='Open STEP File')
        self.Bind(wx.EVT_BUTTON, self.openFile, self.load_button)

        self.highlight_manifold_button = wx.Button(self, label='Highlight Manifold')
        self.Bind(wx.EVT_BUTTON, self.highlightManifoldSolidRep, self.highlight_manifold_button)

        self.highlight_axis_button = wx.Button(self, label='Highlight Axis')
        self.Bind(wx.EVT_BUTTON, self.highlightAxis2Placement3D, self.highlight_axis_button)

        self.search_box = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.searchElements, self.search_box)

        self.info_text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)

        self.create_layout()

    def create_layout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        button_sizer.Add(self.load_button, 0, wx.ALL, 5)
        button_sizer.Add(self.highlight_manifold_button, 0, wx.ALL, 5)
        button_sizer.Add(self.highlight_axis_button, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.EXPAND)
        main_sizer.Add(self.tree_ctrl, 1, wx.EXPAND)
        main_sizer.Add(self.ref_tree_ctrl, 1, wx.EXPAND)
        main_sizer.Add(self.search_box, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.info_text, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_sizer)
        self.Layout()

    def openFile(self, event):
        wildcard = "STEP Files (*.stp;*.step)|*.stp;*.step|All Files (*.*)|*.*"
        dialog = wx.FileDialog(self, "Open STEP File", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if dialog.ShowModal() == wx.ID_OK:
            file_path = dialog.GetPath()
            self.step_file_ops.parseStepFile(file_path)

            # Remove old items from the tree before updating with new categories
            self.tree_ctrl.DeleteAllItems()

            # Add the root to the tree
            root = self.tree_ctrl.AddRoot("Categories")

            # Add its categories and elements to the tree
            for category, elements in self.step_file_ops.category_dict.items():
                category_item = self.tree_ctrl.AppendItem(root, f"{category} ({len(elements)})")

                for element in elements:
                    self.addTreeItem(element, category_item)

            self.tree_ctrl.ExpandAll()
            self.tree_ctrl.Refresh()

        dialog.Destroy()

    def addTreeItem(self, element_number, parent_item):
        element_number = element_number.replace('(', '')
        element_info = self.step_file_ops.element_dict.get(element_number, {})
        element_name = element_info.get('name', "")
        children = element_info.get('children', [])

        # Skip adding an empty child
        if not element_number or element_number == "''":
            print(f"Skipping element with empty ID: {element_number}")
            return

        # Construct the item text
        item_text = f"{element_number} - {element_name}" if element_name else f"{element_number}"

        # Check if the item already exists
        existing_item, cookie = self.tree_ctrl.GetFirstChild(parent_item)
        while existing_item.IsOk():
            if self.tree_ctrl.GetItemText(existing_item) == item_text:
                return  # Item already exists, no need to add again
            existing_item, cookie = self.tree_ctrl.GetNextChild(parent_item, cookie)

        # Add the item to the tree
        element_item = self.tree_ctrl.AppendItem(parent_item, item_text)

        for child_element in children:
            self.addTreeItem(child_element, element_item)

        referenced_elements = self.step_file_ops.getReferencedElements(element_number)

        for referenced_element in referenced_elements:
            # Skip adding an empty child
            if not referenced_element:
                print(f"Skipping referenced element with empty ID: {referenced_element}")
                continue

            self.addTreeItem(referenced_element, element_item)




    def highlightManifoldSolidRep(self, event):
        self.tree_ctrl.CollapseAll()
        root_item = self.tree_ctrl.GetRootItem()

        child, cookie = self.tree_ctrl.GetFirstChild(root_item)
        while child.IsOk():
            if self.tree_ctrl.GetItemText(child).startswith("manifold_solid_rep"):
                self.tree_ctrl.Expand(child)
                self.tree_ctrl.SelectItem(child)
                break

            child, cookie = self.tree_ctrl.GetNextChild(root_item, cookie)


    def highlightAxis2Placement3D(self, event):
        self.tree_ctrl.CollapseAll()
        root_item = self.tree_ctrl.GetRootItem()

        for child, _ in self.tree_ctrl.GetFirstChild(root_item):
            if self.tree_ctrl.GetItemText(child).startswith("axis2_placement_3d"):
                self.tree_ctrl.Expand(child)
                self.tree_ctrl.SelectItem(child)
                break

    def searchElements(self, event):
        query = self.search_box.GetValue().lower()
        if not query:
            return

        self.tree_ctrl.CollapseAll()
        root_item = self.tree_ctrl.GetRootItem()

        self.searchInChildren(root_item, query)

    def searchInChildren(self, parent_item, query):
        child, cookie = self.tree_ctrl.GetFirstChild(parent_item)

        while child.IsOk():
            item_text = self.tree_ctrl.GetItemText(child).lower()

            if query in item_text:
                self.tree_ctrl.Expand(parent_item)
                self.tree_ctrl.SelectItem(child)
                return

            self.searchInChildren(child, query)
            child, cookie = self.tree_ctrl.GetNextChild(parent_item, cookie)

if __name__ == '__main__':
    app = wx.App(False)
    frame = StepFileViewer(None, "STEP File Viewer")
    frame.Show()
    app.MainLoop()
