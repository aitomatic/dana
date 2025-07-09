import { IconChartLine } from "@tabler/icons-react";
import { useState } from "react";

const ReactCodeBlock = ({ content }: { content: string }) => {
  const [_, setIsSplitScreen] = useState(false);
  const [__, setReactCode] = useState("");
  const blockId = `react-code-${Math.random().toString(36).substring(2, 8)}`;

  // Extract meaningful name from the component content
  const componentName = extractComponentName(content);

  // Generate a readable description of what the component does
  const componentDescription = generateComponentDescription(content);

  return (
    <div
      className="relative grid w-full grid-cols-1 mt-2 mb-4 overflow-hidden rounded-lg"
      id={blockId}
    >
      <div
        onClick={() => {
          setIsSplitScreen(true);
          setReactCode(content);
        }}
        className="flex flex-col w-full gap-4"
      >
        <div className="flex w-full gap-3 px-3 py-3 border rounded-lg cursor-pointer bg-brand-50 border-brand-100">
          <div className="flex items-center justify-center gap-2 p-2 rounded size-12 bg-brand-100 dark:bg-brand-200">
            <IconChartLine className="size-5 text-brand-700 dark:text-brand-800" />
          </div>
          <div className="flex flex-col gap-1">
            <span className="font-medium text-gray-900">{componentName}</span>
            <span className="text-xs text-gray-600">
              {componentDescription}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Extracts the component name from React code content
 * Looks for function or class component definitions
 */
const extractComponentName = (content: string): string => {
  // Try to find aria-label which provides the most accessible name
  const ariaLabelMatch = content.match(/aria-label=["']([^"']+)["']/i);
  if (ariaLabelMatch && ariaLabelMatch[1]) {
    return ariaLabelMatch[1];
  }

  // Try to find function component definition
  const functionMatches = content.match(/function\s+([A-Za-z0-9_]+)\s*\(/);
  if (functionMatches && functionMatches[1]) {
    return functionMatches[1];
  }

  // Try to find arrow function export
  const arrowExportMatches = content.match(
    /export\s+(?:default)?\s*const\s+([A-Za-z0-9_]+)\s*=/,
  );
  if (arrowExportMatches && arrowExportMatches[1]) {
    return arrowExportMatches[1];
  }

  // Try to find class component
  const classMatches = content.match(
    /class\s+([A-Za-z0-9_]+)\s+extends\s+React\.Component/,
  );
  if (classMatches && classMatches[1]) {
    return classMatches[1];
  }

  // Look for title or chart title in the code
  const titleMatch =
    content.match(/title[=:]\s*["']([^"']+)["']/i) ||
    content.match(/chart\s+title[=:]\s*["']([^"']+)["']/i);
  if (titleMatch && titleMatch[1]) {
    return titleMatch[1];
  }

  // Look for import statements to identify visualization libraries
  if (content.includes("recharts")) {
    // Check for specific chart types
    if (content.includes("LineChart")) return "Line Chart Component";
    if (content.includes("BarChart")) return "Bar Chart Component";
    if (content.includes("PieChart")) return "Pie Chart Component";
    if (content.includes("AreaChart")) return "Area Chart Component";
    if (content.includes("ComposedChart")) return "Composed Chart Component";
    if (content.includes("RadarChart")) return "Radar Chart Component";
    if (content.includes("Treemap")) return "Treemap Component";
    if (content.includes("ScatterChart")) return "Scatter Chart Component";
    return "Recharts Visualization";
  }

  if (content.includes("Chart from")) {
    return "Chart.js Visualization";
  }

  if (content.includes("d3")) {
    return "D3.js Visualization";
  }

  // Check for UI component patterns
  if (content.includes("<Form") || content.includes("onSubmit")) {
    return "Form Component";
  }

  if (
    content.includes("<Table") ||
    content.includes("<tr") ||
    content.includes("<td")
  ) {
    return "Table Component";
  }

  if (content.includes("useState") || content.includes("useEffect")) {
    return "React Hooks Component";
  }

  // Default fallback
  return "React Component";
};

/**
 * Generates a brief description of what the component does
 * based on content analysis
 */
const generateComponentDescription = (content: string): string => {
  // Check for data structures that might indicate what the component is about
  const chartDescription = [];

  // Check for chart-related imports
  if (
    content.includes("recharts") ||
    content.includes("Chart") ||
    content.includes("d3")
  ) {
    chartDescription.push("Data visualization");

    // Look for data keys that might reveal what's being shown
    const dataKeysMatch = content.match(/dataKey=["']([A-Za-z0-9_]+)["']/);
    if (dataKeysMatch && dataKeysMatch[1]) {
      chartDescription.push(`showing ${dataKeysMatch[1].toLowerCase()} data`);
    }
  }

  // Check if it's a form
  if (content.includes("onSubmit") || content.includes("<Form")) {
    return "Interactive form component";
  }

  // Check if it has state
  if (content.includes("useState")) {
    if (content.includes("fetch(") || content.includes("axios")) {
      return "Component with data fetching";
    }
    return "Interactive component with state";
  }

  // Check for specific keywords in the content
  if (content.toLowerCase().includes("dashboard")) {
    return "Dashboard component";
  }

  if (
    content.toLowerCase().includes("analytics") ||
    content.toLowerCase().includes("metrics")
  ) {
    return "Analytics visualization";
  }

  // Calculate component size/complexity as another descriptor
  const linesOfCode = content.split("\n").length;
  let complexityDesc = "";

  if (linesOfCode < 30) complexityDesc = "Simple";
  else if (linesOfCode < 100) complexityDesc = "Moderate";
  else complexityDesc = "Complex";

  if (chartDescription.length > 0) {
    return `${chartDescription.join(" ")}`;
  }

  return `${complexityDesc} React component. Click to edit`;
};

export default ReactCodeBlock;
