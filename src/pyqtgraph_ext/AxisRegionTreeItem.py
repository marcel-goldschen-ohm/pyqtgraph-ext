""" Data interface for a tree of axis regions.

REGION = {
    'region': {'x': [0, 1]},
    'text': 'my label\n details...',
    ...
}

REGION_LIST = [
    {'group A': REGION_LIST},
    {'group B': REGION_LIST},
    REGION,
    REGION,
    ...
]

REGION_TREE:
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


class AxisRegionTreeItem(AbstractTreeItem):
    
    def __init__(self, data: dict, parent: AxisRegionTreeItem | None = None) -> None:
        self._data: dict = data
        AbstractTreeItem.__init__(self, parent=parent)

        # recursively build subtree
        if self.is_group():
            for item in self._group_list():
                AxisRegionTreeItem(item, parent=self)
    
    def __repr__(self):
        return AbstractTreeItem.__repr__(self) + f', data={self._data}'
    
    def is_region(self) -> bool:
        return isinstance(self._data, dict) and ('region' in self._data)
    
    def is_group(self) -> bool:
        return isinstance(self._data, list) or (
            isinstance(self._data, dict) and ('region' not in self._data) and (len(self._data) == 1)
        )
    
    def _group_list(self) -> list | None:
        if not self.is_group():
            return None
        if isinstance(self._data, list):
            return self._data
        return list(self._data.values())[0]
    
    @property
    def group_name(self) -> str | None:
        if not self.is_group():
            return None
        if isinstance(self._data, list):
            return 'group'
        return list(self._data.keys())[0]

    @group_name.setter
    def group_name(self, name: str) -> None:
        if not self.is_group():
            return
        if isinstance(self._data, list):
            return
        if name in self._data:
            # group already exists
            return
        self._data[name] = self._data.pop(self.group_name)
    
    @property
    def region_label(self) -> str | None:
        if not self.is_region():
            return None
        label: str = self._data.get('text', '')
        if label:
            label = label.split('\n')[0].strip()
        if not label:
            region: dict | list = self._data['region']
            if isinstance(region, dict):
                dimlabels = []
                for dim in region:
                    lims = region[dim]
                    lb = f'{lims[0]:.6f}'.rstrip('0').rstrip('.')
                    ub = f'{lims[1]:.6f}'.rstrip('0').rstrip('.')
                    dimlabels.append(f'{dim}: {lb}-{ub}')
                label = ', '.join(dimlabels)
            elif isinstance(region, list):
                lims = region
                lb = f'{lims[0]:.6f}'.rstrip('0').rstrip('.')
                ub = f'{lims[1]:.6f}'.rstrip('0').rstrip('.')
                label = f'{lb}-{ub}'
        return label
    
    @region_label.setter
    def region_label(self, label: str) -> None:
        if not self.is_region():
            return
        if label is None:
            if 'text' in self._data:
                self._data.pop('text')
            return
        text = self._data.get('text', '').split('\n')
        if text:
            text[0] = label
            self._data['text'] = '\n'.join(text)
        else:
            self._data['text'] = label
    
    @AbstractTreeItem.parent.setter
    def parent(self, parent: AxisRegionTreeItem | None) -> None:
        if self.parent is parent:
            return
        if parent is not None:
            if not parent.is_group():
                raise ValueError('Parent must be a group.')
        old_parent: AxisRegionTreeItem | None = self.parent
        
        AbstractTreeItem.parent.fset(self, parent)
        
        if old_parent is not None:
            # remove region/group from old group
            old_group: list = old_parent._group_list()
            if self._data in old_group:
                old_group.remove(self._data)
        if parent is not None:
            # insert region/group into new group
            new_group: list = parent._group_list()
            if self._data not in new_group:
                new_group.append(self._data)
    
    @AbstractTreeItem.name.getter
    def name(self) -> str:
        if self.is_region():
            return self.region_label
        elif self.is_group():
            return self.group_name
        return AbstractTreeItem.name.fget(self)
    
    def insert_child(self, index: int, item: AxisRegionTreeItem) -> bool:
        if not self.is_group():
            return False
        
        AbstractTreeItem.insert_child(self, index, item)

        group: list = self._group_list()
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
                {'region': {'t': [8, 9]}, 'text': 'my label\n details...'}
            ],
        },
        {
            'group B': [
                {'region': {'x': [3, 4]}}, 
            ],
        },
        {'region': {'x': [35, 45]}}, 
    ]
    # print(json.dumps(data, indent=2))

    print('Initial tree...')
    root = AxisRegionTreeItem(data)
    print(root)

    print('Move 1st region in group A to group B...')
    root.children[0].children[0].parent = root.children[1]
    print(root)

    print('Move last region in group B to 3rd child of root...')
    root.insert_child(2, root.children[1].children[-1])
    print(root)

    print('Add group "test" as 2nd child of root...')
    root.insert_child(1, AxisRegionTreeItem({'test': []}, parent=root))
    print(root)

    print(json.dumps(data, indent=2))

    print(root.dumps())


if __name__ == '__main__':
    test_tree()
