// Original exported Figma vectors, bundled locally by Vite.
const files = import.meta.glob('./figma/*.svg', {
  eager: true,
  query: '?url&no-inline',
  import: 'default',
});

export function figmaAsset(name) {
  return files[`./figma/${name}.svg`];
}

export function artwork(name) {
  return name ? { backgroundImage: `url("${figmaAsset(name)}")` } : undefined;
}
