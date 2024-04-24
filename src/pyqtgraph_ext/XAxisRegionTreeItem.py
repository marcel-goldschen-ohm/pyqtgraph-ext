""" Data interface for a tree of axis regions.

REGION = {
    'region': [0, 1],
    'dim': 'x',
    'text': 'my label\n details...',
    ...
}

REGIONS DATA = [
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
from pyqt_ext.tree import AbstractTreeItem


class XAxisRegionTreeItem(AbstractTreeItem):
    
    def __init__(self, data: dict | list, parent: XAxisRegionTreeItem | None = None) -> None:
        self._data: dict | list = data
        AbstractTreeItem.__init__(self, parent=parent)

        # recursively build subtree
        if self.is_group():
            for item in self.group_list:
                XAxisRegionTreeItem(item, parent=self)
    
    def __repr__(self):
        return AbstractTreeItem.__repr__(self) + f', data={self._data}'
    
    def is_region(self) -> bool:
        data = self._data
        return isinstance(data, dict) and ('region' in data)
    
    def is_group(self) -> bool:
        data = self._data
        return isinstance(data, list) or (
            isinstance(data, dict) and ('region' not in data) and (len(data) == 1) and isinstance(list(data.values())[0], list)
        )
    
    @property
    def group_name(self) -> str | None:
        if self.is_group():
            if isinstance(self._data, dict):
                return list(self._data.keys())[0]

    @group_name.setter
    def group_name(self, name: str) -> None:
        if self.is_group():
            if isinstance(self._data, dict):
                self._data = {name: self.group_list}
    
    @property
    def group_list(self) -> list | None:
        if self.is_group():
            if isinstance(self._data, list):
                return self._data
            elif isinstance(self._data, dict):
                return list(self._data.values())[0]
    
    @property
    def region_label(self) -> str | None:
        if self.is_region():
            region: dict = self._data
            label: str = region.get('text', '')
            if label:
                label = label.split('\n')[0].strip()
            if not label:
                lims = region['region']
                lb = f'{lims[0]:.6f}'.rstrip('0').rstrip('.')
                ub = f'{lims[1]:.6f}'.rstrip('0').rstrip('.')
                label = f'{lb}-{ub}'
                dim = region.get('dim', '')
                if dim:
                    label = f'{dim}: {label}'
            return label
    
    @region_label.setter
    def region_label(self, label: str) -> None:
        if self.is_region():
            region: dict = self._data
            text = region.get('text', '').split('\n')
            if text:
                text[0] = label
                region['text'] = '\n'.join(text)
            else:
                region['text'] = label
    
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
        
        if old_parent is not None:
            # remove region/group from old group
            if self._data in old_parent.group_list:
                old_parent.group_list.remove(self._data)
        if parent is not None:
            # insert region/group into new group
            if self._data not in parent.group_list:
                parent.group_list.append(self._data)
    
    @AbstractTreeItem.name.getter
    def name(self) -> str:
        if self.is_region():
            return self.region_label
        elif self.is_group():
            if self.is_root():
                return '/'
            return self.group_name
        return AbstractTreeItem.name.fget(self)
    
    def insert_child(self, index: int, item: XAxisRegionTreeItem) -> bool:
        if not self.is_group():
            return False
        
        AbstractTreeItem.insert_child(self, index, item)

        group: list = self.group_list
        pos = group.index(item._data)
        if pos != index:
            if pos < index:
                index -= 1
            if pos != index:
                group.insert(index, group.pop(pos))
    
    def get_data(self, column: int):
        if column == 0:
            if self.is_region():
                return self.region_label
            elif self.is_group():
                return self.group_name
    
    def set_data(self, column: int, value) -> bool:
        value = value.strip()
        if value == self.get_data(column):
            # nothing to do
            return False
        if column == 0:
            if self.is_region():
                self.region_label = value
                return True
            elif self.is_group():
                if self.is_root():
                    # should never happen
                    return False
                if value == 'region':
                    # groups cannot be named "region"
                    raise ValueError('Group name cannot be "region".')
                    return False
                self.group_name = value
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

    print('Initial tree...')
    root = XAxisRegionTreeItem(data)
    print(root)

    print('Move 1st region in group A to group B...')
    root.children[0].children[0].parent = root.children[1]
    print(root)

    print('Move last region in group B to 3rd child of root...')
    root.insert_child(2, root.children[1].children[-1])
    print(root)

    print('Add group "test" as 2nd child of root...')
    root.insert_child(1, XAxisRegionTreeItem({'test': []}, parent=root))
    print(root)

    print(json.dumps(data, indent=2))

    print(root.dumps())


if __name__ == '__main__':
    test_tree()
