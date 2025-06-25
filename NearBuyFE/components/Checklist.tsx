// components/Checklist.tsx
import React from 'react';
import { View } from 'react-native';
import Item from './Item';

interface ListItem {
  id: string;
  name: string;
  isChecked: boolean;
  deadline?: string | null;
  geo_alert?: boolean;
}

interface ChecklistProps {
  items: ListItem[];
  listId: string;
  onToggle: (id: string) => void;
  onNameChange: (id: string, newName: string) => void;
  onDelete: (id: string) => void;
}

export default function Checklist({ items, listId, onToggle, onNameChange, onDelete }: ChecklistProps) {
  return (
    <View style={{ paddingBottom: 20 }}>
      {items.map((item) => (
        <Item
          key={item.id}
          list_id={listId}
          item_id={item.id}
          name={item.name}
          isChecked={item.isChecked}
          onToggle={() => onToggle(item.id)}
          onNameChange={(newName) => onNameChange(item.id, newName)}
          onDelete={() => onDelete(item.id)}
          deadline={item.deadline}
          geo_alert={item.geo_alert}
        />
      ))}
    </View>
  );
}
