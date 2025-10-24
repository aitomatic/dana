/**
 * Utilities for processing and animating template diffs
 */

export interface DiffSection {
  type: 'add' | 'remove' | 'unchanged';
  content: string;
  lineStart?: number | null;
  lineEnd?: number | null;
}

export interface TemplateDiff {
  sections: DiffSection[];
  oldContent?: string | null;
  newContent?: string | null;
}

/**
 * Parse backend diff response into usable format
 */
export function parseDiffResponse(diff: any): TemplateDiff | null {
  if (!diff || !diff.sections) {
    return null;
  }

  return {
    sections: diff.sections.map((section: any) => ({
      type: section.type,
      content: section.content,
      lineStart: section.line_start,
      lineEnd: section.line_end,
    })),
    oldContent: diff.old_content,
    newContent: diff.new_content,
  };
}

/**
 * Get only the changed sections (add/remove) for display
 */
export function getChangedSections(diff: TemplateDiff): DiffSection[] {
  return diff.sections.filter(s => s.type === 'add' || s.type === 'remove');
}

/**
 * Compute character-level diff between two strings
 * Returns array of chunks with type and content
 */
export function computeCharDiff(oldText: string, newText: string): DiffSection[] {
  // Simple character-level diff algorithm
  const sections: DiffSection[] = [];
  
  let i = 0;
  let j = 0;
  
  while (i < oldText.length || j < newText.length) {
    // Find common prefix
    let commonStart = 0;
    while (
      i + commonStart < oldText.length &&
      j + commonStart < newText.length &&
      oldText[i + commonStart] === newText[j + commonStart]
    ) {
      commonStart++;
    }
    
    if (commonStart > 0) {
      sections.push({
        type: 'unchanged',
        content: oldText.substring(i, i + commonStart),
      });
      i += commonStart;
      j += commonStart;
    }
    
    // Find next match or end
    let removed = '';
    let added = '';
    
    while (i < oldText.length && j < newText.length && oldText[i] !== newText[j]) {
      // Look ahead to find where they match again
      let matchFound = false;
      for (let lookahead = 1; lookahead < 10; lookahead++) {
        if (i + lookahead < oldText.length && oldText[i + lookahead] === newText[j]) {
          // Found match in old text
          removed += oldText.substring(i, i + lookahead);
          i += lookahead;
          matchFound = true;
          break;
        }
        if (j + lookahead < newText.length && oldText[i] === newText[j + lookahead]) {
          // Found match in new text
          added += newText.substring(j, j + lookahead);
          j += lookahead;
          matchFound = true;
          break;
        }
      }
      
      if (!matchFound) {
        if (i < oldText.length) {
          removed += oldText[i];
          i++;
        }
        if (j < newText.length) {
          added += newText[j];
          j++;
        }
      }
    }
    
    // Handle remaining characters
    if (i < oldText.length) {
      removed += oldText.substring(i);
      i = oldText.length;
    }
    if (j < newText.length) {
      added += newText.substring(j);
      j = newText.length;
    }
    
    if (removed) {
      sections.push({ type: 'remove', content: removed });
    }
    if (added) {
      sections.push({ type: 'add', content: added });
    }
  }
  
  return sections;
}

/**
 * Truncate diff sections for animation (prevent overly long animations)
 */
export function truncateDiffForAnimation(sections: DiffSection[], maxChars: number = 500): DiffSection[] {
  let totalChars = 0;
  const truncated: DiffSection[] = [];
  
  for (const section of sections) {
    if (totalChars >= maxChars) {
      break;
    }
    
    const remaining = maxChars - totalChars;
    if (section.content.length <= remaining) {
      truncated.push(section);
      totalChars += section.content.length;
    } else {
      // Truncate this section
      truncated.push({
        ...section,
        content: section.content.substring(0, remaining) + '...',
      });
      totalChars = maxChars;
      break;
    }
  }
  
  return truncated;
}

/**
 * Format diff sections for display in chat
 */
export function formatDiffForChat(sections: DiffSection[]): string {
  let formatted = '';
  
  for (const section of sections) {
    if (section.type === 'add') {
      formatted += `+ ${section.content}`;
    } else if (section.type === 'remove') {
      formatted += `- ${section.content}`;
    }
  }
  
  return formatted;
}

