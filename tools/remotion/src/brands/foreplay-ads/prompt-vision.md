# Prompt para replicar criativo como template Remotion

Cole esta mensagem junto com a imagem do criativo no Claude (web/app) ou GPT-4o:

---

Analyze this ad creative image in detail. Then generate a complete Remotion React component that reproduces this exact layout as a reusable template.

## Remotion Patterns Used in This Project

```tsx
import { AbsoluteFill, Img, staticFile, spring, useCurrentFrame, interpolate, Sequence } from "remotion";
```

- Use `<AbsoluteFill>` for full-screen layers
- Use `<Sequence>` for timed sections
- Use `spring()` and `interpolate()` for animations
- Use inline `style` objects (no CSS modules)
- Props pattern: define an interface for all variable text, colors, images

## What to Analyze

1. **Layout structure** — zones, positions, proportions
2. **Typography** — font family, sizes, alignment, weights
3. **Color palette** — exact hex colors
4. **Image placement** — position, size, overlay effects
5. **Text hierarchy** — headline, subheadline, body, CTA, disclaimer, offer
6. **Visual effects** — shadows, gradients, borders, overlays

## Output Requirements

Generate a SINGLE file called `ForeplayAdTemplate.tsx` with:

```tsx
// 1. Props interface with ALL customizable fields
interface ForeplayAdProps {
  headline: string;
  subheadline?: string;
  cta: string;
  // ... all other variable fields
  backgroundColor?: string;
  accentColor?: string;
}

// 2. Default props with example values from the original ad
export const defaultProps: ForeplayAdProps = { ... };

// 3. The component using ONLY these patterns:
//    - AbsoluteFill, Img, staticFile, spring, useCurrentFrame, interpolate
//    - Inline styles
//    - All text/colors/images come from props
export const ForeplayAdTemplate: React.FC<ForeplayAdProps> = ({ ... }) => { ... };
```

Make every text string, color, image URL, and dimension a prop so variations can be generated programmatically.

---

Depois de gerar o componente, salve em:
`_factorio/remotion/src/brands/foreplay-ads/templates/ForeplayAdTemplate.tsx`

E adicione no `Root.tsx`:
```tsx
import { ForeplayAdTemplate, defaultProps } from "./brands/foreplay-ads/templates/ForeplayAdTemplate";

<Composition
  id="ForeplayAd-1"
  component={ForeplayAdTemplate}
  durationInFrames={150}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={defaultProps}
/>
```