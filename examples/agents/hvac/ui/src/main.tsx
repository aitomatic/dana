import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Toaster } from 'sonner';
import App from './App';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Toaster
      position="top-right"
      closeButton
      duration={4000}
      expand={true}
      visibleToasts={5}
      toastOptions={{
        style: {
          background: '#101828',
          color: '#ffffff',
          border: '1px solid #101828',
          borderRadius: '8px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          fontSize: '14px',
          fontWeight: '500',
        },
        // @ts-expect-error - Sonner toast options
        success: {
          style: {
            background: '#101828',
            color: '#ffffff',
            border: '1px solid #101828',
          },
          iconTheme: {
            primary: '#ffffff',
            secondary: '#101828',
          },
        },
        error: {
          style: {
            background: '#101828',
            color: '#ffffff',
            border: '1px solid #101828',
          },
          iconTheme: {
            primary: '#ffffff',
            secondary: '#101828',
          },
        },
      }}
    />
    <App />
  </StrictMode>,
);
