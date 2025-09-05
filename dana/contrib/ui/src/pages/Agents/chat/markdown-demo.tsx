import React, { useState } from 'react';
import { MarkdownViewerSmall } from './markdown-viewer';

const MarkdownDemo: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  const sampleMarkdown = `# GitHub Markdown Styling Demo

This component now uses **GitHub Markdown CSS** instead of custom styling!

## Features

- **Clean typography** that matches GitHub READMEs
- **Proper spacing** and margins
- **Professional code blocks**
- **Responsive tables**

### Code Example

\`\`\`typescript
interface User {
  id: number;
  name: string;
  email: string;
}

const user: User = {
  id: 1,
  name: "John Doe",
  email: "john@example.com"
};
\`\`\`

### Lists

- **Bold items** now render normally
- *Italic text* works as expected
- \`Inline code\` is properly styled

### Tables

| Feature | Status | Notes |
|---------|--------|-------|
| Headers | ✅ | Proper styling |
| Content | ✅ | Clean borders |
| Responsive | ✅ | Mobile friendly |

### Math Support

Inline math: $E = mc^2$

Display math:
$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

---

> **Note**: This styling now matches GitHub's default markdown appearance exactly!
`;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-2xl font-bold">Markdown Styling Demo</h1>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Theme:</label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'light' | 'dark')}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </div>

      <div
        className={`border rounded-lg overflow-hidden ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'}`}
      >
        <MarkdownViewerSmall theme={theme}>{sampleMarkdown}</MarkdownViewerSmall>
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold mb-2">What Changed:</h3>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
          <li>
            ✅ <strong>Strong tags</strong> no longer have blue backgrounds or borders
          </li>
          <li>✅ Typography now matches GitHub's default styling</li>
          <li>✅ Consistent spacing and margins throughout</li>
          <li>✅ Professional code block appearance</li>
          <li>✅ Responsive table layouts</li>
        </ul>
      </div>
    </div>
  );
};

export default MarkdownDemo;
