import { useEffect, useState } from 'react';
import { Bell, Globe, Lock } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';

const SETTINGS_KEY = 'samarth_settings';

type AppSettings = {
  emailAlerts: boolean;
  challengeUpdates: boolean;
  impactDigest: boolean;
  language: string;
};

const defaultSettings: AppSettings = {
  emailAlerts: true,
  challengeUpdates: true,
  impactDigest: false,
  language: 'en-IN',
};

function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    return raw ? { ...defaultSettings, ...(JSON.parse(raw) as AppSettings) } : defaultSettings;
  } catch {
    return defaultSettings;
  }
}

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);

  useEffect(() => {
    setSettings(loadSettings());
  }, []);

  const update = (patch: Partial<AppSettings>) => {
    setSettings((current) => ({ ...current, ...patch }));
  };

  const handleSave = () => {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    toast.success('Settings saved');
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">Notification and language preferences for this browser</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-primary" />
            <CardTitle>Notifications</CardTitle>
          </div>
          <CardDescription>Choose which updates you want to receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center justify-between gap-4">
            <div>
              <Label htmlFor="emailAlerts">Email alerts</Label>
              <p className="text-sm text-muted-foreground">High-priority challenges and report status</p>
            </div>
            <Switch
              id="emailAlerts"
              checked={settings.emailAlerts}
              onCheckedChange={(emailAlerts) => update({ emailAlerts })}
            />
          </div>
          <div className="flex items-center justify-between gap-4">
            <div>
              <Label htmlFor="challengeUpdates">Challenge updates</Label>
              <p className="text-sm text-muted-foreground">Matching, validation, and project progress</p>
            </div>
            <Switch
              id="challengeUpdates"
              checked={settings.challengeUpdates}
              onCheckedChange={(challengeUpdates) => update({ challengeUpdates })}
            />
          </div>
          <div className="flex items-center justify-between gap-4">
            <div>
              <Label htmlFor="impactDigest">Weekly impact digest</Label>
              <p className="text-sm text-muted-foreground">Summary of completed pilots and outcomes</p>
            </div>
            <Switch
              id="impactDigest"
              checked={settings.impactDigest}
              onCheckedChange={(impactDigest) => update({ impactDigest })}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Globe className="h-4 w-4 text-primary" />
            <CardTitle>Language</CardTitle>
          </div>
          <CardDescription>Display language for dates and copy</CardDescription>
        </CardHeader>
        <CardContent>
          <Select value={settings.language} onValueChange={(language) => update({ language })}>
            <SelectTrigger className="max-w-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en-IN">English (India)</SelectItem>
              <SelectItem value="hi-IN">Hindi</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-primary" />
            <CardTitle>Security</CardTitle>
          </div>
          <CardDescription>Password changes are managed through your SAMARTH login provider</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Sign out from any shared device when you are done. Role and email cannot be changed from
            this page.
          </p>
        </CardContent>
      </Card>

      <Button onClick={handleSave}>Save settings</Button>
    </div>
  );
}
