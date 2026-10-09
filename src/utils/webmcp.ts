export interface WebTool { name: string; description: string; title: string; inputSchema: object; annotations: { readOnlyHint: boolean; untrustedContentHint: boolean }; execute: (input: unknown) => unknown; }
export function registerWebTool(tool: WebTool) {
  const context = (document as Document & { modelContext?: { registerTool: (tool: WebTool, options: { signal: AbortSignal }) => void | Promise<void> } }).modelContext;
  if (!context?.registerTool) return () => {};
  const lifecycle = new AbortController();
  try { Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(() => {}); } catch { /* unsupported context does not affect user controls */ }
  return () => lifecycle.abort();
}
