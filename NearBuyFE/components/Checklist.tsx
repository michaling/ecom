import React from 'react';
import { FlatList } from 'react-native';
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
  onToggle: (id: string) => void;
  onNameChange: (id: string, newName: string) => void;
  onDelete: (id: string) => void;
  
}

export default function Checklist({ items, onToggle, onNameChange, onDelete }: ChecklistProps) {
  return (
    <FlatList
      data={items}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => (
        <Item
        name={item.name}
        isChecked={item.isChecked}
        onToggle={() => onToggle(item.id)}
        onNameChange={(newName) => onNameChange(item.id, newName)}
        onDelete={() => onDelete(item.id)}
        deadline={item.deadline}   
        geo_alert={item.geo_alert} 
      />
      )}
      contentContainerStyle={{ paddingBottom: 20 }}
    />
  );
}

