""" Data interface for a tree of axis regions.

REGION = {
    'region': [0, 1],
    'dim': 'x',
    'text': 'my label\n details...',
    ...
}

REGIONS = [
    {'group A': [REGION, REGION]},
    {'group B': [REGION]},
    REGION,
    REGION,
    ...
]

REGIONS TREE:
/
|-- group A
|   |-- REGION
|   |-- REGION
|-- group B
|   |-- REGION
|-- REGION
|-- REGION
"""

from __future__ import annotations
from pyqt_ext import AbstractTreeItem
from pyqtgraph_ext import AxisRegion


class XAxisRegionTreeItem(AbstractTreeItem):
    
    def __init__(self, data: dict | list, parent: XAxisRegionTreeItem | None = None) -> None:
        self._region: dict = None
        self._group_dict: dict = None
        self._group_list: list = None
        if isinstance(data, list):
            self._group_list: list = data
        elif isinstance(data, dict) and ('region' in data):
            self._region = data
        elif isinstance(data, dict) and ('region' not in data) and len(data) == 1 and isinstance(list(data.values())[0], list):
            self._group_dict = data
            self._group_list = list(data.values())[0]
        else:
            raise ValueError('Invalid data type for XAxisRegionTreeItem.')
        AbstractTreeItem.__init__(self, parent=parent)

        # recursively build subtree
        if self._group_list is not None:
            for item in self._group_list:
                XAxisRegionTreeItem(item, parent=self)
    
    def __repr__(self):
        if self.is_region():
            label: str = self._region.get('text', '')
            if label:
                label = label.split('\n')[0].strip()
            if not label:
                lims = self._region['region']
                lb = f'{lims[0]:.6f}'.rstrip('0').rstrip('.')
                ub = f'{lims[1]:.6f}'.rstrip('0').rstrip('.')
                label = f'{lb}-{ub}'
                dim = self._region.get('dim', '')
                if dim:
                    label = f'{dim}: {label}'
            return label
        elif self.is_root_group():
            return '/'
        elif self.is_group():
            return str(list(self._group_dict.keys())[0])
    
    @AbstractTreeItem.parent.setter
    def parent(self, parent: XAxisRegionTreeItem | None) -> None:
        if self.parent is parent:
            return
        if parent is not None:
            if not parent.is_group():
                raise ValueError('Parent must be a group.')
            if self.is_group() and not parent.is_root():
                raise ValueError('Groups must be children of root.')
        old_parent: XAxisRegionTreeItem | None = self.parent
        AbstractTreeItem.parent.fset(self, parent)
        if self.is_region():
            if old_parent is not None:
                # remove region from old group
                if self._region in old_parent._group_list:
                    old_parent._group_list.remove(self._region)
            if parent is not None:
                # insert region into new group
                if self._region not in parent._group_list:
                    parent._group_list.append(self._region)
        elif self.is_group():
            if old_parent is not None:
                # remove group from old group
                if self._group_dict in old_parent._group_list:
                    old_parent._group_list.remove(self._group_dict)
            if parent is not None:
                # insert group into new group
                if self._group_dict not in parent._group_list:
                    parent._group_list.append(self._group_dict)
    
    def is_region(self):
        return self._region is not None

    def is_group(self):
        return self._group_list is not None
    
    def is_root_group(self):
        return self.is_group() and self.is_root()
    
    def insert_child(self, index: int, item: XAxisRegionTreeItem) -> bool:
        if not self.is_group():
            return False
        item.parent = self
        # move item to index
        pos = self.children.index(item)
        if pos != index:
            self.children.insert(index, self.children.pop(pos))
        if item.is_region():
            pos = self._group_list.index(item._region)
            if pos != index:
                self._group_list.insert(index, self._group_list.pop(pos))
        elif item.is_group():
            pos = self._group_list.index(item._group_dict)
            if pos != index:
                self._group_list.insert(index, self._group_list.pop(pos))
    
    def data(self, column: int):
        if column == 0:
            return repr(self)
    
    def set_data(self, column: int, value) -> bool:
        value = value.strip()
        if value == self.data(column):
            return False
        if column == 0:
            if self.is_region():
                text = self._region.get('text', '').split('\n')
                if text:
                    text[0] = value
                    self._region['text'] = '\n'.join(text)
                else:
                    self._region['text'] = value
                return True
            if self.is_root_group():
                return False
            if self.is_group():
                if value == 'region':
                    # groups cannot be named "region"
                    return False
                self._group_dict = {value: self._group_list}
                return True
        return False


def test_tree():
    import json

    data = [
        {
            'group A': [
                {'region': [8, 9], 'dim': 't', 'text': 'my label\n details...'}
            ],
        },
        {
            'group B': [
                {'region': [3, 4], 'dim': 'x'}, 
            ],
        },
        {'region': [35, 45], 'dim': 'x'}, 
    ]
    # print(json.dumps(data, indent=2))

    root = XAxisRegionTreeItem(data)
    print(root)

    # root.children[0].children[0].parent = root.children[1]
    # print('move 1st region in group A to group B')
    # print(root)

    # root.insert_child(2, root.children[1].children[-1])
    # print('move last region in group B to 3rd child of root')
    # print(root)

    # root.insert_child(1, XAxisRegionTreeItem({'test': []}, parent=root))
    # print('add group "test" as 2nd child of root')
    # print(root)

    # print(json.dumps(data, indent=2))

    # for item in root.depth_first():
    #     # print(repr(item), repr(item.parent))
    #     print(item)


if __name__ == '__main__':
    test_tree()
