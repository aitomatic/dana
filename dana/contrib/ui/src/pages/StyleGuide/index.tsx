import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';

// Color palette component
const ColorPalette = () => {
  const colorGroups = [
    {
      name: 'Brand Colors (New Dark Theme)',
      colors: [
        { name: 'brand-25', value: 'rgb(248 249 250)', hex: '#F8F9FA' },
        { name: 'brand-50', value: 'rgb(241 243 245)', hex: '#F1F3F5' },
        { name: 'brand-100', value: 'rgb(233 236 239)', hex: '#E9ECEF' },
        { name: 'brand-200', value: 'rgb(206 212 218)', hex: '#CED4DA' },
        { name: 'brand-300', value: 'rgb(173 181 189)', hex: '#ADB5BD' },
        { name: 'brand-400', value: 'rgb(108 117 125)', hex: '#6C757D' },
        { name: 'brand-500', value: 'rgb(16 24 40)', hex: '#101828' },
        { name: 'brand-600', value: 'rgb(12 17 29)', hex: '#0C111D' },
        { name: 'brand-700', value: 'rgb(8 12 20)', hex: '#080C14' },
        { name: 'brand-800', value: 'rgb(4 6 10)', hex: '#04060A' },
        { name: 'brand-900', value: 'rgb(2 3 5)', hex: '#020305' },
        { name: 'brand-950', value: 'rgb(1 1 2)', hex: '#010102' },
      ],
    },
    {
      name: 'Blue Colors (Formerly Brand Colors)',
      colors: [
        { name: 'blue-25', value: 'rgb(241 245 254)', hex: '#F1F5FE' },
        { name: 'blue-50', value: 'rgb(239 244 254)', hex: '#EFF4FE' },
        { name: 'blue-100', value: 'rgb(225 235 254)', hex: '#E1EBFE' },
        { name: 'blue-200', value: 'rgb(201 216 252)', hex: '#C9D8FC' },
        { name: 'blue-300', value: 'rgb(168 191 249)', hex: '#A8BFF9' },
        { name: 'blue-400', value: 'rgb(134 156 243)', hex: '#869CF3' },
        { name: 'blue-500', value: 'rgb(105 121 235)', hex: '#6979EB' },
        { name: 'blue-600', value: 'rgb(61 69 220)', hex: '#3D45DC' },
        { name: 'blue-700', value: 'rgb(62 66 196)', hex: '#3E42C4' },
        { name: 'blue-800', value: 'rgb(53 58 158)', hex: '#353A9E' },
        { name: 'blue-900', value: 'rgb(49 54 126)', hex: '#31367E' },
        { name: 'blue-950', value: 'rgb(29 31 73)', hex: '#1D1F49' },
      ],
    },
    {
      name: 'Success Colors',
      colors: [
        { name: 'success-25', value: 'rgb(250 255 251)', hex: '#FAFFFB' },
        { name: 'success-50', value: 'rgb(240 253 244)', hex: '#F0FDF4' },
        { name: 'success-100', value: 'rgb(220 252 231)', hex: '#DCFCE7' },
        { name: 'success-200', value: 'rgb(187 247 208)', hex: '#BBF7D0' },
        { name: 'success-300', value: 'rgb(134 239 172)', hex: '#86EFAC' },
        { name: 'success-400', value: 'rgb(74 222 128)', hex: '#4ADE80' },
        { name: 'success-500', value: 'rgb(34 197 94)', hex: '#22C55E' },
        { name: 'success-600', value: 'rgb(22 163 74)', hex: '#16A34A' },
        { name: 'success-700', value: 'rgb(21 128 61)', hex: '#15803D' },
        { name: 'success-800', value: 'rgb(22 101 52)', hex: '#166534' },
        { name: 'success-900', value: 'rgb(20 83 45)', hex: '#14532D' },
        { name: 'success-950', value: 'rgb(5 46 22)', hex: '#052E16' },
      ],
    },
    {
      name: 'Warning Colors',
      colors: [
        { name: 'warning-25', value: 'rgb(255 253 250)', hex: '#FFFDFA' },
        { name: 'warning-50', value: 'rgb(255 251 235)', hex: '#FFFBF0' },
        { name: 'warning-100', value: 'rgb(254 243 199)', hex: '#FEF3C7' },
        { name: 'warning-200', value: 'rgb(253 230 138)', hex: '#FDE68A' },
        { name: 'warning-300', value: 'rgb(252 211 77)', hex: '#FCD34D' },
        { name: 'warning-400', value: 'rgb(251 191 36)', hex: '#FBBF24' },
        { name: 'warning-500', value: 'rgb(245 158 11)', hex: '#F59E0B' },
        { name: 'warning-600', value: 'rgb(217 119 6)', hex: '#D97706' },
        { name: 'warning-700', value: 'rgb(180 83 9)', hex: '#B45309' },
        { name: 'warning-800', value: 'rgb(146 64 14)', hex: '#92400E' },
        { name: 'warning-900', value: 'rgb(120 53 15)', hex: '#78350F' },
        { name: 'warning-950', value: 'rgb(69 26 3)', hex: '#451A03' },
      ],
    },
    {
      name: 'Error Colors',
      colors: [
        { name: 'error-25', value: 'rgb(255 251 250)', hex: '#FFFBF9' },
        { name: 'error-50', value: 'rgb(254 242 242)', hex: '#FEF2F2' },
        { name: 'error-100', value: 'rgb(254 226 226)', hex: '#FEE2E2' },
        { name: 'error-200', value: 'rgb(254 202 202)', hex: '#FECACA' },
        { name: 'error-300', value: 'rgb(252 165 165)', hex: '#FCA5A5' },
        { name: 'error-400', value: 'rgb(248 113 113)', hex: '#F87171' },
        { name: 'error-500', value: 'rgb(239 68 68)', hex: '#EF4444' },
        { name: 'error-600', value: 'rgb(220 38 38)', hex: '#DC2626' },
        { name: 'error-700', value: 'rgb(185 28 28)', hex: '#B91C1C' },
        { name: 'error-800', value: 'rgb(153 27 27)', hex: '#991B1B' },
        { name: 'error-900', value: 'rgb(127 29 29)', hex: '#7F1D1D' },
        { name: 'error-950', value: 'rgb(69 10 10)', hex: '#450A0A' },
      ],
    },
    {
      name: 'Gray Scale',
      colors: [
        { name: 'gray-25', value: 'rgb(252 252 253)', hex: '#FCFCFD' },
        { name: 'gray-50', value: 'rgb(249 250 251)', hex: '#F9FAFB' },
        { name: 'gray-100', value: 'rgb(242 244 247)', hex: '#F2F4F7' },
        { name: 'gray-200', value: 'rgb(228 231 236)', hex: '#E4E7EC' },
        { name: 'gray-300', value: 'rgb(208 213 221)', hex: '#D0D5DD' },
        { name: 'gray-400', value: 'rgb(152 162 179)', hex: '#98A2B3' },
        { name: 'gray-500', value: 'rgb(102 112 133)', hex: '#667085' },
        { name: 'gray-600', value: 'rgb(71 84 103)', hex: '#475467' },
        { name: 'gray-700', value: 'rgb(52 64 84)', hex: '#344054' },
        { name: 'gray-800', value: 'rgb(24 34 48)', hex: '#182230' },
        { name: 'gray-900', value: 'rgb(16 24 40)', hex: '#101828' },
        { name: 'gray-950', value: 'rgb(12 17 29)', hex: '#0C111D' },
      ],
    },
  ];

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold">Color Palette</h2>
      {colorGroups.map((group) => (
        <div key={group.name} className="space-y-4">
          <h3 className="text-lg font-medium">{group.name}</h3>
          <div className="grid grid-cols-6 gap-4">
            {group.colors.map((color) => (
              <div key={color.name} className="space-y-2">
                <div
                  className="w-full h-16 rounded-md border border-gray-200"
                  style={{ backgroundColor: color.value }}
                />
                <div className="text-xs space-y-1">
                  <div className="font-mono">{color.name}</div>
                  <div className="font-mono text-gray-600">{color.hex}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

// Typography showcase
const TypographyShowcase = () => {
  const fontSizes = [
    { name: 'xs', class: 'text-xs', description: '12px (0.75rem)' },
    { name: 'sm', class: 'text-sm', description: '14px (0.875rem)' },
    { name: 'base', class: 'text-base', description: '16px (1rem)' },
    { name: 'lg', class: 'text-lg', description: '18px (1.125rem)' },
    { name: 'xl', class: 'text-xl', description: '20px (1.25rem)' },
    { name: '2xl', class: 'text-2xl', description: '24px (1.5rem)' },
    { name: '3xl', class: 'text-3xl', description: '30px (1.875rem)' },
    { name: '4xl', class: 'text-4xl', description: '36px (2.25rem)' },
  ];

  const fontWeights = [
    { name: 'normal', class: 'font-normal', description: '400' },
    { name: 'medium', class: 'font-medium', description: '500' },
    { name: 'semibold', class: 'font-semibold', description: '600' },
    { name: 'bold', class: 'font-bold', description: '700' },
  ];

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold">Typography</h2>

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium mb-4">Font Sizes</h3>
          <div className="space-y-3">
            {fontSizes.map((size) => (
              <div key={size.name} className="flex items-center gap-4">
                <div className="w-16 text-sm text-gray-600">{size.name}</div>
                <div className={cn(size.class)}>The quick brown fox jumps over the lazy dog</div>
                <div className="text-sm text-gray-500">{size.description}</div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-medium mb-4">Font Weights</h3>
          <div className="space-y-3">
            {fontWeights.map((weight) => (
              <div key={weight.name} className="flex items-center gap-4">
                <div className="w-20 text-sm text-gray-600">{weight.name}</div>
                <div className={cn(weight.class, 'text-lg')}>
                  The quick brown fox jumps over the lazy dog
                </div>
                <div className="text-sm text-gray-500">{weight.description}</div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-medium mb-4">Font Family</h3>
          <div className="p-4 bg-gray-50 rounded-md">
            <code className="text-sm">
              system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue',
              Arial, 'Noto Sans', sans-serif
            </code>
          </div>
        </div>
      </div>
    </div>
  );
};

// Spacing showcase
const SpacingShowcase = () => {
  const spacingScale = [
    { name: '0', value: '0px', class: 'w-0' },
    { name: '1', value: '4px (0.25rem)', class: 'w-1' },
    { name: '2', value: '8px (0.5rem)', class: 'w-2' },
    { name: '3', value: '12px (0.75rem)', class: 'w-3' },
    { name: '4', value: '16px (1rem)', class: 'w-4' },
    { name: '5', value: '20px (1.25rem)', class: 'w-5' },
    { name: '6', value: '24px (1.5rem)', class: 'w-6' },
    { name: '8', value: '32px (2rem)', class: 'w-8' },
    { name: '10', value: '40px (2.5rem)', class: 'w-10' },
    { name: '12', value: '48px (3rem)', class: 'w-12' },
    { name: '16', value: '64px (4rem)', class: 'w-16' },
    { name: '20', value: '80px (5rem)', class: 'w-20' },
    { name: '24', value: '96px (6rem)', class: 'w-24' },
  ];

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold">Spacing System</h2>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Base Spacing Scale</h3>
        <div className="space-y-3">
          {spacingScale.map((space) => (
            <div key={space.name} className="flex items-center gap-4">
              <div className="w-16 text-sm text-gray-600">{space.name}</div>
              <div className={cn(space.class, 'h-4 bg-brand-500 rounded')} />
              <div className="text-sm text-gray-500">{space.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Border Radius</h3>
        <div className="flex gap-4 items-center">
          <div className="w-16 h-16 bg-brand-500 rounded-sm" />
          <div className="text-sm">sm: calc(var(--radius) - 4px)</div>
        </div>
        <div className="flex gap-4 items-center">
          <div className="w-16 h-16 bg-brand-500 rounded-md" />
          <div className="text-sm">md: calc(var(--radius) - 2px)</div>
        </div>
        <div className="flex gap-4 items-center">
          <div className="w-16 h-16 bg-brand-500 rounded-lg" />
          <div className="text-sm">lg: var(--radius) (0.625rem)</div>
        </div>
        <div className="flex gap-4 items-center">
          <div className="w-16 h-16 bg-brand-500 rounded-xl" />
          <div className="text-sm">xl: calc(var(--radius) + 4px)</div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Shadows</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-white shadow-xs rounded-lg">
            <div className="text-sm font-medium">shadow-xs</div>
            <div className="text-xs text-gray-600">0 1px 2px 0 rgba(0, 0, 0, 0.05)</div>
          </div>
          <div className="p-4 bg-white shadow-sm rounded-lg">
            <div className="text-sm font-medium">shadow-sm</div>
            <div className="text-xs text-gray-600">0 1px 2px 0 rgba(0, 0, 0, 0.05)</div>
          </div>
          <div className="p-4 bg-white shadow rounded-lg">
            <div className="text-sm font-medium">shadow</div>
            <div className="text-xs text-gray-600">0 1px 3px 0 rgba(0, 0, 0, 0.1)</div>
          </div>
          <div className="p-4 bg-white shadow-md rounded-lg">
            <div className="text-sm font-medium">shadow-md</div>
            <div className="text-xs text-gray-600">0 4px 6px -1px rgba(0, 0, 0, 0.1)</div>
          </div>
          <div className="p-4 bg-white shadow-lg rounded-lg">
            <div className="text-sm font-medium">shadow-lg</div>
            <div className="text-xs text-gray-600">0 10px 15px -3px rgba(0, 0, 0, 0.1)</div>
          </div>
          <div className="p-4 bg-white shadow-xl rounded-lg">
            <div className="text-sm font-medium">shadow-xl</div>
            <div className="text-xs text-gray-600">0 20px 25px -5px rgba(0, 0, 0, 0.1)</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Component showcase
const ComponentShowcase = () => {
  const [inputValue, setInputValue] = useState('');
  const [textareaValue, setTextareaValue] = useState('');
  const [checkboxChecked, setCheckboxChecked] = useState(false);

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold">Components</h2>

      {/* Buttons */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Buttons</h3>
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium mb-2">Variants</h4>
            <div className="flex flex-wrap gap-2">
              <Button variant="default">Default</Button>
              <Button variant="destructive">Destructive</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="link">Link</Button>
              <Button variant="success">Success</Button>
              <Button variant="warning">Warning</Button>
              <Button variant="tertiary">Tertiary</Button>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium mb-2">Sizes</h4>
            <div className="flex flex-wrap items-center gap-2">
              <Button size="sm">Small</Button>
              <Button size="default">Default</Button>
              <Button size="lg">Large</Button>
              <Button size="icon">⚙</Button>
            </div>
          </div>
        </div>
      </div>

      {/* Inputs */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Inputs</h3>
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium mb-2">Sizes</h4>
            <div className="space-y-2">
              <Input size="sm" placeholder="Small input" />
              <Input size="default" placeholder="Default input" />
              <Input size="lg" placeholder="Large input" />
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium mb-2">States</h4>
            <div className="space-y-2">
              <Input placeholder="Normal state" />
              <Input placeholder="Disabled state" disabled />
              <Input placeholder="Error state" className="border-error-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Badges */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Badges</h3>
        <div className="flex flex-wrap gap-2">
          <Badge variant="default">Default</Badge>
          <Badge variant="secondary">Secondary</Badge>
          <Badge variant="destructive">Destructive</Badge>
          <Badge variant="outline">Outline</Badge>
        </div>
      </div>

      {/* Form Elements */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Form Elements</h3>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="demo-input">Label</Label>
            <Input
              id="demo-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Controlled input"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="demo-textarea">Textarea</Label>
            <Textarea
              id="demo-textarea"
              value={textareaValue}
              onChange={(e) => setTextareaValue(e.target.value)}
              placeholder="Enter your message..."
            />
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="demo-checkbox"
              checked={checkboxChecked}
              onCheckedChange={setCheckboxChecked}
            />
            <Label htmlFor="demo-checkbox">Checkbox</Label>
          </div>
        </div>
      </div>
    </div>
  );
};

// Interactive playground
const ComponentPlayground = () => {
  const [selectedVariant, setSelectedVariant] = useState<
    | 'default'
    | 'destructive'
    | 'outline'
    | 'secondary'
    | 'ghost'
    | 'link'
    | 'success'
    | 'warning'
    | 'tertiary'
  >('default');
  const [selectedSize, setSelectedSize] = useState<'sm' | 'default' | 'lg' | 'icon'>('lg');
  const [buttonText, setButtonText] = useState('Click me');

  const variants = [
    { value: 'default', label: 'Default' },
    { value: 'destructive', label: 'Destructive' },
    { value: 'outline', label: 'Outline' },
    { value: 'secondary', label: 'Secondary' },
    { value: 'ghost', label: 'Ghost' },
    { value: 'link', label: 'Link' },
    { value: 'success', label: 'Success' },
    { value: 'warning', label: 'Warning' },
    { value: 'tertiary', label: 'Tertiary' },
  ];

  const sizes = [
    { value: 'sm', label: 'Small' },
    { value: 'default', label: 'Default' },
    { value: 'lg', label: 'Large' },
    { value: 'icon', label: 'Icon' },
  ];

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold">Component Playground</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Controls</h3>

          <div className="space-y-4">
            <div>
              <Label htmlFor="variant-select">Variant</Label>
              <select
                id="variant-select"
                value={selectedVariant}
                onChange={(e) => setSelectedVariant(e.target.value as any)}
                className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-md"
              >
                {variants.map((variant) => (
                  <option key={variant.value} value={variant.value}>
                    {variant.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label htmlFor="size-select">Size</Label>
              <select
                id="size-select"
                value={selectedSize}
                onChange={(e) => setSelectedSize(e.target.value as any)}
                className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-md"
              >
                {sizes.map((size) => (
                  <option key={size.value} value={size.value}>
                    {size.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label htmlFor="button-text">Button Text</Label>
              <Input
                id="button-text"
                value={buttonText}
                onChange={(e) => setButtonText(e.target.value)}
                placeholder="Enter button text"
              />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-medium">Preview</h3>
          <div className="p-8 bg-gray-50 rounded-lg">
            <div className="flex justify-center">
              <Button
                variant={selectedVariant}
                size={selectedSize}
                onClick={() => alert('Button clicked!')}
              >
                {selectedSize === 'icon' ? '⚙' : buttonText}
              </Button>
            </div>
          </div>

          <div className="p-4 bg-gray-100 rounded-md">
            <h4 className="text-sm font-medium mb-2">Code</h4>
            <pre className="text-xs overflow-x-auto">
              <code>{`<Button 
  variant="${selectedVariant}" 
  size="${selectedSize}"
  onClick={handleClick}
>
  ${selectedSize === 'icon' ? '⚙' : `"${buttonText}"`}
</Button>`}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main style guide page
export default function StyleGuidePage() {
  const [activeSection, setActiveSection] = useState('colors');

  const sections = [
    { id: 'colors', label: 'Colors', component: <ColorPalette /> },
    { id: 'typography', label: 'Typography', component: <TypographyShowcase /> },
    { id: 'spacing', label: 'Spacing', component: <SpacingShowcase /> },
    { id: 'components', label: 'Components', component: <ComponentShowcase /> },
    { id: 'playground', label: 'Playground', component: <ComponentPlayground /> },
  ];

  return (
    <div className="min-h-screen bg-white">
      <div className="border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Dana UI Style Guide</h1>
              <p className="text-gray-600 mt-1">Interactive design system documentation</p>
            </div>
            <div className="flex gap-2">
              {sections.map((section) => (
                <Button
                  key={section.id}
                  variant={activeSection === section.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setActiveSection(section.id)}
                >
                  {section.label}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {sections.find((section) => section.id === activeSection)?.component}
      </div>
    </div>
  );
}
