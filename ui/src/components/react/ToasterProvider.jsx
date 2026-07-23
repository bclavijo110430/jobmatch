import { Toaster } from 'sonner';

export default function ToasterProvider() {
  return (
    <Toaster
      position="bottom-right"
      toastOptions={{
        style: {
          background: '#161A28',
          color: '#E2E4EC',
          border: '1px solid #252A3A',
        },
      }}
    />
  );
}
