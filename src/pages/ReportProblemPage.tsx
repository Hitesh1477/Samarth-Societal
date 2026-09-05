import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  MapPin,
  Crosshair,
  Upload,
  X,
  Mic,
  Image as ImageIcon,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { api } from '@/services/api';
import { toast } from 'sonner';
import type { Evidence, ProblemCategory, SubmitProblemData, UrgencyLevel } from '@/types';

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const categories: ProblemCategory[] = [
  'Infrastructure',
  'Water & Sanitation',
  'Healthcare',
  'Education',
  'Agriculture',
  'Environment',
  'Public Safety',
  'Transport',
  'Waste Management',
  'Other',
];

const urgencyLevels: UrgencyLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

const defaultLocation = { lat: 23.3441, lng: 85.3096, name: 'Ranchi, Jharkhand', district: 'Ranchi' };

function LocationPicker({
  position,
  onPick,
}: {
  position: { lat: number; lng: number };
  onPick: (lat: number, lng: number) => void;
}) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export function ReportProblemPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<ProblemCategory>('Infrastructure');
  const [subcategory, setSubcategory] = useState('');
  const [urgency, setUrgency] = useState<UrgencyLevel>('MEDIUM');
  const [affectedPopulation, setAffectedPopulation] = useState('');
  const [location, setLocation] = useState(defaultLocation);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const handlePick = useCallback((lat: number, lng: number) => {
    setLocation((prev) => ({ ...prev, lat, lng }));
  }, []);

  const useGeolocation = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not available');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        handlePick(pos.coords.latitude, pos.coords.longitude);
        toast.success('Location detected');
      },
      () => {
        toast.error('Could not get your location');
      }
    );
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    Array.from(files).forEach((file) => {
      const isImage = file.type.startsWith('image/');
      const isAudio = file.type.startsWith('audio/');
      if (!isImage && !isAudio) return;
      const ev: Evidence = {
        id: `ev-${Date.now()}-${Math.random()}`,
        type: isImage ? 'image' : 'audio',
        url: URL.createObjectURL(file),
        name: file.name,
      };
      setEvidence((prev) => [...prev, ev]);
    });
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeEvidence = (id: string) => {
    setEvidence((prev) => prev.filter((e) => e.id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !description) {
      toast.error('Please fill in all required fields');
      return;
    }
    setSubmitting(true);
    try {
      const data: SubmitProblemData = {
        title,
        description,
        category,
        subcategory: subcategory || 'General',
        urgency,
        affectedPopulation: parseInt(affectedPopulation) || 100,
        location,
        evidence,
        reporterName: 'Demo User',
      };
      const report = await api.submitProblem(data);
      toast.success('Problem submitted for AI analysis');
      navigate(`/report/${report.id}/analysis`);
    } catch {
      toast.error('Failed to submit problem');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6">
        <h1 className="font-heading text-2xl font-bold tracking-tight">Report a Problem</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Describe the issue in your community. Our AI will analyze and prioritize it.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-lg">Problem Details</CardTitle>
            <CardDescription>Tell us what's happening in your area</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Problem Title *</Label>
              <Input
                id="title"
                placeholder="e.g. Heavy rainfall causes waterlogging on main road"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                placeholder="Describe the problem in detail. What's happening, who's affected, and how long has it been going on?"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Category</Label>
                <Select value={category} onValueChange={(v) => setCategory(v as ProblemCategory)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="subcategory">Subcategory</Label>
                <Input
                  id="subcategory"
                  placeholder="e.g. Drainage / Road Accessibility"
                  value={subcategory}
                  onChange={(e) => setSubcategory(e.target.value)}
                />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Urgency Level</Label>
                <Select value={urgency} onValueChange={(v) => setUrgency(v as UrgencyLevel)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {urgencyLevels.map((u) => (
                      <SelectItem key={u} value={u}>{u}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="population">Affected Population</Label>
                <Input
                  id="population"
                  type="number"
                  placeholder="e.g. 2500"
                  value={affectedPopulation}
                  onChange={(e) => setAffectedPopulation(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Location */}
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-lg">Location</CardTitle>
            <CardDescription>Click on the map to pin the exact location</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-primary" />
                <span className="font-medium">{location.name}</span>
                <Badge variant="secondary" className="text-xs">
                  {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
                </Badge>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={useGeolocation} className="gap-2">
                <Crosshair className="h-4 w-4" />
                Use My Location
              </Button>
            </div>
            <div className="h-72 overflow-hidden rounded-lg border border-border">
              <MapContainer
                center={[location.lat, location.lng]}
                zoom={13}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; OpenStreetMap'
                />
                <Marker position={[location.lat, location.lng]} />
                <LocationPicker position={location} onPick={handlePick} />
              </MapContainer>
            </div>
          </CardContent>
        </Card>

        {/* Evidence */}
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-lg">Evidence</CardTitle>
            <CardDescription>Upload photos or voice recordings to support your report</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="gap-2"
              >
                <ImageIcon className="h-4 w-4" />
                Upload Photos
              </Button>
              <Button type="button" variant="outline" size="sm" className="gap-2">
                <Mic className="h-4 w-4" />
                Record Voice
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,audio/*"
                multiple
                className="hidden"
                onChange={handleFileUpload}
              />
            </div>
            {evidence.length > 0 && (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {evidence.map((ev) => (
                  <div key={ev.id} className="group relative overflow-hidden rounded-lg border border-border">
                    {ev.type === 'image' ? (
                      <img src={ev.url} alt={ev.name} className="h-24 w-full object-cover" />
                    ) : (
                      <div className="flex h-24 w-full items-center justify-center bg-secondary">
                        <Mic className="h-6 w-6 text-muted-foreground" />
                      </div>
                    )}
                    <div className="flex items-center justify-between gap-1 px-2 py-1">
                      <span className="truncate text-xs text-muted-foreground">{ev.name}</span>
                      <button
                        type="button"
                        onClick={() => removeEvidence(ev.id)}
                        className="text-muted-foreground hover:text-red-500"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {evidence.length === 0 && (
              <div className="flex items-center justify-center gap-2 rounded-lg border border-dashed border-border py-8 text-sm text-muted-foreground">
                <Upload className="h-4 w-4" />
                No evidence uploaded yet
              </div>
            )}
          </CardContent>
        </Card>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting} className="gap-2">
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                Analyze My Problem
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
