'use client';

import { useEffect, useState } from 'react';
import { getSystemConfig, updateSystemConfig, testModel, listModels } from '@/lib/api';
import { useSessionStore } from '@/lib/store';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FeatureUnavailable } from '@/components/FeatureUnavailable';

interface ModelConfig {
  provider: string;
  url: string;
  model: string;
  api_key?: string;
}

interface SystemConfig {
  version: string;
  server: { host: string; port: number };
  security: { session_rolling_ttl_hours: number; session_absolute_max_days: number };
  models: {
    main: ModelConfig;
    summarizer: ModelConfig;
    embedding: ModelConfig;
    image_embedding: ModelConfig;
    tts: ModelConfig;
  };
  tools: {
    filesystem: { enabled: boolean; allowed_paths: string[] };
    web: { enabled: boolean; interact_enabled: boolean };
  };
  comfyui: {
    mode: string;
    url: string;
    limits: Record<string, unknown>;
  };
}

const PROVIDERS = [
  { value: 'openai-compatible', label: 'OpenAI Compatible' },
  { value: 'llama-server', label: 'Llama Server' },
  { value: 'ollama', label: 'Ollama' },
];

export default function AdminSettingsPage() {
  const { user } = useSessionStore();
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [testingModel, setTestingModel] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setIsLoading(true);
    try {
      const data = await getSystemConfig();
      setConfig(data);
    } catch (err) {
      console.error('Failed to load config:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!config) return;
    setIsSaving(true);
    try {
      const { version, server, ...configToSave } = config;
      await updateSystemConfig(configToSave as Partial<SystemConfig>);
    } catch (err) {
      console.error('Failed to save config:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestModel = async (role: string) => {
    if (!config) return;
    const modelConfig = config.models[role as keyof typeof config.models];
    if (!modelConfig.url || !modelConfig.model) return;

    setTestingModel(role);
    setTestResult(null);
    try {
      const result = await testModel({
        url: modelConfig.url,
        model: modelConfig.model,
        api_key: modelConfig.api_key || null,
      });
      setTestResult({ success: result.success, message: result.message });
    } catch (err) {
      setTestResult({ success: false, message: 'Connection failed' });
    } finally {
      setTestingModel(null);
    }
  };

  const updateModelConfig = (role: string, field: string, value: string) => {
    if (!config) return;
    setConfig({
      ...config,
      models: {
        ...config.models,
        [role]: {
          ...config.models[role as keyof typeof config.models],
          [field]: value,
        },
      },
    });
  };

  if (user?.role !== 'admin') {
    return <FeatureUnavailable feature="Admin Settings" message="Admin access required." />;
  }

  if (isLoading || !config) {
    return <div className="container mx-auto py-8">Loading...</div>;
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">System Settings</h1>
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      <Tabs defaultValue="models" className="space-y-6">
        <TabsList>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="tools">Tools</TabsTrigger>
          <TabsTrigger value="comfyui">ComfyUI</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="space-y-6">
          {(['main', 'summarizer', 'embedding', 'image_embedding', 'tts'] as const).map((role) => (
            <Card key={role}>
              <CardHeader>
                <CardTitle className="capitalize">{role.replace('_', ' ')} Model</CardTitle>
                <CardDescription>
                  Configure the {role.replace('_', ' ')} model provider and endpoint
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Provider</Label>
                    <select
                      className="w-full p-2 border rounded"
                      value={config.models[role].provider}
                      onChange={(e) => updateModelConfig(role, 'provider', e.target.value)}
                    >
                      {PROVIDERS.map((p) => (
                        <option key={p.value} value={p.value}>{p.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label>URL</Label>
                    <Input
                      placeholder="http://localhost:11434"
                      value={config.models[role].url}
                      onChange={(e) => updateModelConfig(role, 'url', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Model Name</Label>
                    <Input
                      placeholder="llama3.2"
                      value={config.models[role].model}
                      onChange={(e) => updateModelConfig(role, 'model', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>API Key (optional)</Label>
                    <Input
                      type="password"
                      placeholder="sk-..."
                      value={config.models[role].api_key || ''}
                      onChange={(e) => updateModelConfig(role, 'api_key', e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <Button
                    variant="outline"
                    onClick={() => handleTestModel(role)}
                    disabled={testingModel === role || !config.models[role].url || !config.models[role].model}
                  >
                    {testingModel === role ? 'Testing...' : 'Test Connection'}
                  </Button>
                  {testResult && testingModel === role === false && (
                    <span className={testResult.success ? 'text-green-600' : 'text-red-600'}>
                      {testResult.message}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="tools" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Filesystem</CardTitle>
              <CardDescription>Allow the AI to access local files</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Enable Filesystem Access</Label>
                <Switch
                  checked={config.tools.filesystem.enabled}
                  onCheckedChange={(checked) =>
                    setConfig({
                      ...config,
                      tools: {
                        ...config.tools,
                        filesystem: { ...config.tools.filesystem, enabled: checked },
                      },
                    })
                  }
                />
              </div>
              {config.tools.filesystem.enabled && (
                <div className="space-y-2">
                  <Label>Allowed Paths (comma-separated)</Label>
                  <Input
                    placeholder="/home/user/docs, /tmp"
                    value={config.tools.filesystem.allowed_paths.join(', ')}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        tools: {
                          ...config.tools,
                          filesystem: {
                            ...config.tools.filesystem,
                            allowed_paths: e.target.value.split(',').map((p) => p.trim()).filter(Boolean),
                          },
                        },
                      })
                    }
                  />
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Web Access</CardTitle>
              <CardDescription>Allow the AI to search and fetch web content</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Enable Web Access</Label>
                <Switch
                  checked={config.tools.web.enabled}
                  onCheckedChange={(checked) =>
                    setConfig({
                      ...config,
                      tools: {
                        ...config.tools,
                        web: { ...config.tools.web, enabled: checked },
                      },
                    })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Enable Web Interaction (dangerous)</Label>
                <Switch
                  checked={config.tools.web.interact_enabled}
                  onCheckedChange={(checked) =>
                    setConfig({
                      ...config,
                      tools: {
                        ...config.tools,
                        web: { ...config.tools.web, interact_enabled: checked },
                      },
                    })
                  }
                  disabled={!config.tools.web.enabled}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="comfyui" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>ComfyUI Configuration</CardTitle>
              <CardDescription>Configure ComfyUI for image generation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Mode</Label>
                <select
                  className="w-full p-2 border rounded"
                  value={config.comfyui.mode}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      comfyui: { ...config.comfyui, mode: e.target.value },
                    })
                  }
                >
                  <option value="disabled">Disabled</option>
                  <option value="local">Local</option>
                  <option value="remote">Remote</option>
                </select>
              </div>
              {config.comfyui.mode !== 'disabled' && (
                <div className="space-y-2">
                  <Label>ComfyUI URL</Label>
                  <Input
                    placeholder="http://localhost:8188"
                    value={config.comfyui.url}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        comfyui: { ...config.comfyui, url: e.target.value },
                      })
                    }
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Session Security</CardTitle>
              <CardDescription>Configure session timeout and security settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Rolling Session TTL (hours)</Label>
                <Input
                  type="number"
                  value={config.security.session_rolling_ttl_hours}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      security: {
                        ...config.security,
                        session_rolling_ttl_hours: parseInt(e.target.value) || 24,
                      },
                    })
                  }
                />
                <p className="text-sm text-muted-foreground">
                  Session stays valid for this long after last activity
                </p>
              </div>
              <div className="space-y-2">
                <Label>Absolute Max Session Age (days)</Label>
                <Input
                  type="number"
                  value={config.security.session_absolute_max_days}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      security: {
                        ...config.security,
                        session_absolute_max_days: parseInt(e.target.value) || 7,
                      },
                    })
                  }
                />
                <p className="text-sm text-muted-foreground">
                  Maximum session lifetime regardless of activity
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
