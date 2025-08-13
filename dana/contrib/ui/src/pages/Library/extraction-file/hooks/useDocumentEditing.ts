import { useState, useEffect } from 'react';

interface Document {
  text: string;
  [key: string]: any;
}

export const useDocumentEditing = (selectedFile: any, currentPage: number) => {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedDocuments, setEditedDocuments] = useState<Document[]>(selectedFile?.documents || []);
  const [value, setValue] = useState<string>(editedDocuments[currentPage - 1]?.text || '');

  useEffect(() => {
    setValue(selectedFile?.documents?.[currentPage - 1]?.text || '');
  }, [selectedFile, currentPage]);

  const handleSave = (): void => {
    const updatedDocuments = [...editedDocuments];
    updatedDocuments[currentPage - 1] = { ...updatedDocuments[currentPage - 1], text: value };
    setEditedDocuments(updatedDocuments);

    if (selectedFile?.id) {
      // Note: The document store doesn't support updating document content
      // This would need to be handled by a different API endpoint
      console.log('Document content updated:', updatedDocuments);
    }
    setIsEditing(false);
  };

  const handleEdit = (): void => {
    setIsEditing(true);
  };

  const handleCancel = (): void => {
    setValue(selectedFile?.documents?.[currentPage - 1]?.text || '');
    setIsEditing(false);
  };

  return {
    isEditing,
    value,
    setValue,
    handleSave,
    handleEdit,
    handleCancel,
  };
};
