import React, { useState } from 'react';
import { MarkdownViewerSmall } from './markdown-viewer';

const MathDemo: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [backgroundContext, setBackgroundContext] = useState<'user' | 'agent'>('agent');

  const mathExamples = `# KaTeX Math Formula Examples

## Inline Math

Here are some inline math examples:
- The quadratic formula: $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$
- Einstein's mass-energy equivalence: $E = mc^2$
- The golden ratio: $\\phi = \\frac{1 + \\sqrt{5}}{2} \\approx 1.618$

## Display Math

### Quadratic Formula
$$
x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}
$$

### Integral Example
$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

### Summation
$$
\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}
$$

### Matrix
$$
\\begin{pmatrix}
a & b \\\\
c & d
\\end{pmatrix}
\\begin{pmatrix}
x \\\\
y
\\end{pmatrix} =
\\begin{pmatrix}
ax + by \\\\
cx + dy
\\end{pmatrix}
$$

### Fraction with Complex Numbers
$$
\\frac{1 + i}{1 - i} = i
$$

### Calculus Example
$$
\\frac{d}{dx}\\left(\\int_{0}^{x} f(t) dt\\right) = f(x)
$$

### Physics Formula
$$
F = G\\frac{m_1 m_2}{r^2}
$$

## Financial Math

### Compound Interest
$$
FV = PV(1 + r)^n
$$

Where:
- **FV** = Future Value
- **PV** = Present Value  
- **r** = Interest Rate
- **n** = Number of Periods

### Present Value
$$
PV = \\frac{FV}{(1 + r)^n}
$$

## Statistics

### Normal Distribution
$$
f(x) = \\frac{1}{\\sigma\\sqrt{2\\pi}} e^{-\\frac{1}{2}\\left(\\frac{x-\\mu}{\\sigma}\\right)^2}
$$

### Standard Deviation
$$
\\sigma = \\sqrt{\\frac{1}{N}\\sum_{i=1}^{N}(x_i - \\bar{x})^2}
$$

---

> **Note**: All math formulas are rendered using KaTeX with enhanced styling!
`;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center gap-4 flex-wrap">
        <h1 className="text-2xl font-bold">KaTeX Math Formula Demo</h1>
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
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Background:</label>
          <select
            value={backgroundContext}
            onChange={(e) => setBackgroundContext(e.target.value as 'user' | 'agent')}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="agent">Agent (White)</option>
            <option value="user">User (Gray)</option>
          </select>
        </div>
      </div>

      <div className={`border rounded-lg overflow-hidden ${
        backgroundContext === 'user' ? 'bg-gray-50' : 'bg-white'
      }`}>
        <MarkdownViewerSmall 
          theme={theme}
          backgroundContext={backgroundContext}
        >
          {mathExamples}
        </MarkdownViewerSmall>
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold mb-2">KaTeX Features:</h3>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
          <li>✅ **Inline math** with single $ delimiters</li>
          <li>✅ **Display math** with double $$ delimiters</li>
          <li>✅ **LaTeX commands** like \\frac, \\sqrt, \\sum</li>
          <li>✅ **Greek letters** like \\pi, \\phi, \\sigma</li>
          <li>✅ **Matrices** and **arrays**</li>
          <li>✅ **Responsive design** for mobile devices</li>
          <li>✅ **Theme support** for light and dark modes</li>
          <li>✅ **Background context** awareness</li>
        </ul>
      </div>
    </div>
  );
};

export default MathDemo;
