import { useRef, useState } from 'react';
import { useStore } from '@nanostores/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Upload, Trash2, User, Sparkles, FileUp } from 'lucide-react';
import { profileStore, candidateLevelStore, setProfile, clearProfile } from '@/stores/appStore.js';
import api from '@/lib/api.js';
import { toast } from 'sonner';

export default function ProfileCard() {
  const profile = useStore(profileStore);
  const level = useStore(candidateLevelStore);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [fileName, setFileName] = useState('');
  const fileInputRef = useRef(null);

  const hasProfile = profile.skills?.length > 0 || profile.target_titles?.length > 0;

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setIsUploading(true);
    try {
      const data = await api.uploadProfile(file);
      setProfile(data);
      setFileName('');
      toast.success(`CV analizado · Nivel de inglés: ${data.candidate_level || 'Ninguno'}`);
    } catch (err) {
      toast.error(err.message || 'Error al analizar el CV');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await api.deleteProfile();
      clearProfile();
      toast.success('CV borrado');
    } catch (err) {
      toast.error(err.message || 'Error al borrar el CV');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Card className="border-jm-border bg-jm-card">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-jm-text-bright">
          <User className="h-5 w-5 text-jm-primary-light" />
          Tu Perfil
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isUploading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full bg-jm-elevated" />
            <Skeleton className="h-4 w-2/3 bg-jm-elevated" />
            <p className="text-sm text-jm-text-muted">Analizando CV...</p>
          </div>
        ) : !hasProfile ? (
          <div className="space-y-3">
            <p className="text-sm text-jm-text-secondary">
              Sube tu CV en PDF para extraer skills, cargos objetivo y nivel de inglés.
            </p>
            <div className="grid w-full items-center gap-1.5">
              <Label className="text-jm-text-secondary">Archivo PDF</Label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFile}
                disabled={isUploading}
                className="hidden"
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="h-10 w-full border-jm-border bg-jm-surface text-jm-text hover:bg-jm-surface-hover"
              >
                <FileUp className="mr-2 h-4 w-4 text-jm-primary-light" />
                {fileName ? fileName : 'Seleccionar archivo PDF'}
              </Button>
              {!fileName && (
                <p className="text-xs text-jm-text-muted">Ningún archivo seleccionado</p>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-jm-primary-light" />
                <span className="text-sm font-medium text-jm-text-bright">Nivel de inglés</span>
              </div>
              <Badge variant="primary">{level || 'Ninguno'}</Badge>
            </div>

            {profile.skills?.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-medium uppercase tracking-wider text-jm-text-muted">
                  Habilidades
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {profile.skills.slice(0, 10).map((s) => (
                    <Badge key={s} variant="secondary" className="text-xs">
                      {s}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {profile.target_titles?.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-medium uppercase tracking-wider text-jm-text-muted">
                  Cargos objetivo
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {profile.target_titles.slice(0, 4).map((t) => (
                    <Badge key={t} variant="outline" className="text-xs">
                      {t}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {profile.years_experience > 0 && (
              <p className="text-sm text-jm-text-secondary">
                Experiencia: <span className="font-medium text-jm-text-bright">{profile.years_experience} años</span>
              </p>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting}
              className="w-full border-jm-border text-jm-danger hover:bg-jm-danger-soft hover:text-jm-danger"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Borrar CV
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
