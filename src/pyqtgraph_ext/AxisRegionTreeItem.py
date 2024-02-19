""" Data interface for a tree of axis regions.

REGION = {
    'region': {'x': [0, 1], 'y': [7, 9]},
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


class AxisRegionTreeItem(AbstractTreeItem):
    
    def __init__(self, data: dict | list, parent: AxisRegionTreeItem | None = None) -> None:
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
        AbstractTreeItem.__init__(self, parent=parent)

        # recursively build subtree
        if self._group_list is not None:
            for item in self._group_list:
                AxisRegionTreeItem(item, parent=self)
    
    def __repr__(self):
        if self.is_region():
            label: str = self._region.get('text', '')
            if label:
                label = label.split('\n')[0].strip()
            if not label:
                label = []
                for dim, lim in self._region['region'].items():
                    lb = f'{lim[0]:.6f}'.rstrip('0').rstrip('.')
                    ub = f'{lim[1]:.6f}'.rstrip('0').rstrip('.')
                    label.append(f'{dim}: {lb}-{ub}')
                label = ', '.join(label)
            return label
        elif self.is_root_group():
            return '/'
        elif self.is_group():
            return str(list(self._group_dict.keys())[0])
    
    @AbstractTreeItem.parent.setter
    def parent(self, parent: AxisRegionTreeItem | None) -> None:
        if self.parent is parent:
            return
        if self.is_root_group():
            # cannot alter root group in hierarchy
            return
        if parent is not None:
            if not parent.is_group():
                raise ValueError('Parent must be a group.')
            # if self.is_group() and not parent.is_root():
            #     raise ValueError('Groups must be children of root.')
        old_parent: AxisRegionTreeItem | None = self.parent
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
        return self.is_group() and self._group_dict is None
    
    def insert_child(self, index: int, item: AxisRegionTreeItem) -> bool:
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
                # {'region': {'x': [0, 1]}}, 
                {'region': {'t': [8, 9]}, 'text': 'my label\n details...'}
            ],
        },
        {
            'group B': [
                {'region': {'x': [3, 4]}}, 
                # {'region': {'t': [18, 19]}}
            ],
        },
        {'region': {'x': [35, 45]}}, 
        # {'region': {'t': [180, 190]}},
    ]
    # print(json.dumps(data, indent=2))

    root = AxisRegionTreeItem(data)
    print(root)

    root.children[0].children[0].parent = root.children[1]
    print('move 1st region in group A to group B')
    print(root)

    root.insert_child(2, root.children[1].children[-1])
    print('move last region in group B to 3rd child of root')
    print(root)

    root.insert_child(1, AxisRegionTreeItem({'test': []}, parent=root))
    print('add group "test" as 2nd child of root')
    print(root)

    print(json.dumps(data, indent=2))

    # for item in root.depth_first():
    #     # print(repr(item), repr(item.parent))
    #     print(item)


if __name__ == '__main__':
    test_tree()
