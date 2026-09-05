import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Users2, Target, Flame } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/Badges';
import { api } from '@/services/api';
import type { MapData, MapChallenge, PriorityLevel } from '@/types';

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;

function markerIcon(color: string) {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
}

const priorityColors: Record<PriorityLevel, string> = {
  HIGH: '#dc2626',
  MEDIUM: '#f59e0b',
  LOW: '#16a34a',
};

export function MapPage() {
  const [data, setData] = useState<MapData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getMapChallenges().then((d) => {
      setData(d);
      setLoading(false);
    });
  }, []);

  if (loading || !data) {
    return (
      <div className="flex h-[600px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-heading text-2xl font-bold tracking-tight">Geospatial Intelligence</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Interactive map of challenges across Jharkhand districts
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        {/* Sidebar */}
        <div className="space-y-4 lg:col-span-1">
          {/* Hotspots */}
          <Card className="border-border/60">
            <CardContent className="p-4">
              <div className="mb-3 flex items-center gap-2">
                <Flame className="h-4 w-4 text-red-500" />
                <h3 className="font-semibold text-sm">Problem Hotspots</h3>
              </div>
              <div className="space-y-2">
                {data.hotspots.map((h) => (
                  <div
                    key={h.name}
                    className="flex items-center justify-between rounded-lg border border-border/60 p-3 transition-colors hover:bg-secondary/50"
                  >
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">{h.name}</span>
                    </div>
                    <Badge variant="secondary" className="text-xs font-bold">
                      {h.count}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Legend */}
          <Card className="border-border/60">
            <CardContent className="p-4">
              <h3 className="mb-3 font-semibold text-sm">Legend</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded-full" style={{ backgroundColor: '#dc2626' }} />
                  <span className="text-sm">High Priority</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded-full" style={{ backgroundColor: '#f59e0b' }} />
                  <span className="text-sm">Medium Priority</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded-full" style={{ backgroundColor: '#16a34a' }} />
                  <span className="text-sm">Low Priority</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Map */}
        <div className="lg:col-span-3">
          <Card className="overflow-hidden border-border/60">
            <div className="h-[600px] w-full">
              <MapContainer
                center={[23.3441, 85.3096]}
                zoom={8}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; OpenStreetMap'
                />
                {data.challenges.map((c: MapChallenge) => (
                  <Marker
                    key={c.id}
                    position={[c.lat, c.lng]}
                    icon={markerIcon(priorityColors[c.priorityLevel])}
                  >
                    <Popup>
                      <div className="w-64 space-y-2">
                        <h4 className="font-semibold text-sm">{c.title}</h4>
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          <Badge variant="outline" className="text-xs">{c.category}</Badge>
                          <StatusBadge status={c.status} />
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div>
                            <p className="text-muted-foreground">Priority</p>
                            <p className="font-bold">{c.priority}/100</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Reports</p>
                            <p className="font-bold">{c.reportCount}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Affected</p>
                            <p className="font-bold">{c.affectedPopulation.toLocaleString()}</p>
                          </div>
                        </div>
                        <Link
                          to={`/challenges/${c.id}`}
                          className="block rounded bg-primary px-3 py-1.5 text-center text-xs font-medium text-primary-foreground hover:bg-primary/90"
                        >
                          View Challenge
                        </Link>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
