export interface TopicNoteContent {
  topicName: string;
  background?: string;
  status: string;
  keyQuestions: string[];
  expertInsights: string[];
  rawContent: string;
}

export function parseInterviewNotesByTopic(noteContent: string): Map<string, TopicNoteContent> {
  const topics = new Map<string, TopicNoteContent>();
  
  if (!noteContent) {
    return topics;
  }

  // Find all topic sections (### Topic Name)
  const topicPattern = /### ([^\n]+)/g;
  const topicMatches = Array.from(noteContent.matchAll(topicPattern));
  
  for (let i = 0; i < topicMatches.length; i++) {
    const match = topicMatches[i];
    const topicName = match[1].trim();
    
    // Find the content for this topic (from this ### to the next ### or end)
    const startPos = match.index!;
    const endPos = i + 1 < topicMatches.length 
      ? topicMatches[i + 1].index! 
      : noteContent.length;
    
    const topicSection = noteContent.substring(startPos, endPos);
    
    // Extract different sections
    const background = extractSection(topicSection, '**Background**:');
    const status = extractSection(topicSection, '**Status**:') || 'not_started';
    const keyQuestions = extractKeyQuestions(topicSection);
    const expertInsights = extractExpertInsights(topicSection);
    
    topics.set(topicName, {
      topicName,
      background,
      status: status.toLowerCase().trim(),
      keyQuestions,
      expertInsights,
      rawContent: topicSection
    });
  }
  
  return topics;
}

function extractSection(content: string, header: string): string | undefined {
  // Escape special regex characters in the header
  const escapedHeader = header.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`${escapedHeader}\\s*([^\\*]*?)(?=\\*\\*|$)`, 's');
  const match = content.match(regex);
  return match ? match[1].trim() : undefined;
}

function extractKeyQuestions(content: string): string[] {
  const questionsMatch = content.match(/\*\*Key Questions\*\*:\s*(.+?)(?=\n\*\*|\Z)/s);
  if (!questionsMatch) return [];
  
  const questionsText = questionsMatch[1].trim();
  // Extract numbered questions
  const questionItems = questionsText.match(/\d+\.\s*(.+?)(?=\n\d+\.|\Z)/gs);
  return questionItems ? questionItems.map(q => q.replace(/^\d+\.\s*/, '').trim()) : [];
}

function extractExpertInsights(content: string): string[] {
  // More robust regex that handles various formatting
  // Try multiple patterns to catch different insight formats
  
  // Pattern 1: Standard bullet points under "Expert Insights"


  let insightsMatch = content.match(/\*\*Expert Insights\*\*[:\s]*\n(.*?)(?=\n\*\*[A-Z]|\Z)/gs);

  // Pattern 2: Handle case where there might be extra spacing or colons
  if (!insightsMatch) {
    insightsMatch = content.match(/\*\*Expert Insights\*\*[:\s]*\n+((?:[-*•]\s*.+\n?)+)/m);
  }
  
  // Pattern 3: Handle numbered lists
  if (!insightsMatch) {
    insightsMatch = content.match(/\*\*Expert Insights\*\*[:\s]*\n+((?:\d+\.\s*.+\n?)+)/m);
  }
  
  if (!insightsMatch) {
    console.debug('No expert insights found in content');
    return [];
  }
  
  const insightsText = insightsMatch[0];

  console.debug(`Found insights text: ${insightsText.substring(0, 100)}...`);
  
  // Extract bullet points (supporting -, *, •)
  let bulletPoints = insightsText.match(/^[-*•]\s(.+)$/gm);
  
  // Try numbered lists if bullets not found
  if (!bulletPoints) {
    bulletPoints = insightsText.match(/^\d+\.\s(.+)$/gm);
  }
  
  const insights = bulletPoints ? bulletPoints.map(bp => bp.replace(/^[-*•\d]+[.\s]+/, '').trim()) : [];
  console.debug(`Extracted ${insights.length} insights`);
  
  return insights;
}
