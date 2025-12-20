import React, { createContext, useContext, useState, ReactNode } from 'react';

interface DealModalContextType {
  isCreateModalOpen: boolean;
  openCreateModal: () => void;
  closeCreateModal: () => void;
}

const DealModalContext = createContext<DealModalContextType | undefined>(undefined);

export const DealModalProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const openCreateModal = () => setIsCreateModalOpen(true);
  const closeCreateModal = () => setIsCreateModalOpen(false);

  return (
    <DealModalContext.Provider value={{ isCreateModalOpen, openCreateModal, closeCreateModal }}>
      {children}
    </DealModalContext.Provider>
  );
};

export const useDealModal = () => {
  const context = useContext(DealModalContext);
  if (context === undefined) {
    throw new Error('useDealModal must be used within a DealModalProvider');
  }
  return context;
};


