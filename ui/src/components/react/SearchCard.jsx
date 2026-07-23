import { useState } from 'react';
import { useStore } from '@nanostores/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';
import { jobsStore, profileStore, uiStore } from '@/stores/appStore.js';
import api from '@/lib/api.js';
import { toast } from 'sonner';

export default function SearchCard() {
  const [keyword, setKeyword] = useState('');
  const profile = useStore(profileStore);
  const ui = useStore(uiStore);

  const handleSearch = async () => {
    uiStore.setKey('isSearching', true);
    uiStore.setKey('searchError', null);
    try {
      const data = await api.search({ keyword });
      jobsStore.set(data.jobs || []);
      toast.success(`${data.filtered || 0} ofertas encontradas`);
    } catch (err) {
      uiStore.setKey('searchError', err.message);
      toast.error(err.message || 'Error buscando ofertas');
    } finally {
      uiStore.setKey('isSearching', false);
    }
  };

  const profileHint = profile?.target_titles?.slice(0, 2).join(', ');

  return (
    <Card className="border-jm-border bg-jm-card">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-jm-text-bright">
          <Search className="h-5 w-5 text-jm-primary-light" />
          Búsqueda
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Input
          placeholder="ej: Python, React, developer..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="border-jm-border bg-jm-surface text-jm-text placeholder:text-jm-text-muted focus-visible:ring-jm-primary"
        />
        <Button
          onClick={handleSearch}
          disabled={ui.isSearching}
          className="w-full bg-jm-primary hover:bg-jm-primary-hover"
        >
          <Search className="mr-2 h-4 w-4" />
          {ui.isSearching ? 'Buscando...' : 'Buscar ofertas'}
        </Button>
        {profileHint && (
          <p className="text-xs text-jm-text-muted">
            Términos sugeridos: <span className="text-jm-text-secondary">{profileHint}</span>
          </p>
        )}
      </CardContent>
    </Card>
  );
}
