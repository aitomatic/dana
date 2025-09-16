import { useEffect, useRef, useLayoutEffect, useState, useCallback } from 'react';
import { Textarea } from '@/components/ui/textarea';
import FileIcon from '@/components/file-icon';

// Define the mention option type
interface MentionOption {
  id: string;
  label: string;
  value: string;
  icon?: React.ReactNode;
}

interface ChatInputProps {
  id?: string;
  message: string | null | undefined;
  setMessage: (message: string) => void;
  placeholder: string;
  isBotThinking: boolean;
  mentionOptions?: MentionOption[]; // Optional custom mention options
}

const ChatInput = ({
  id,
  message,
  setMessage,
  placeholder,
  isBotThinking = false,
  mentionOptions,
}: ChatInputProps) => {
  // Internal state to ensure UI updates immediately
  const [internalValue, setInternalValue] = useState(message || '');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const prevBotThinkingRef = useRef(isBotThinking);
  const containerRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const selectedItemRef = useRef<HTMLLIElement>(null);

  // Mention popover states
  const [showMentionPopover, setShowMentionPopover] = useState(false);
  const [mentionQuery, setMentionQuery] = useState('');
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);
  const [atPosition, setAtPosition] = useState(-1); // Track the position of @ character

  // Use provided options or fallback to defaults
  const availableMentionOptions = mentionOptions || [];

  // Filtered mention options based on query
  const filteredMentionOptions = availableMentionOptions.filter((option) =>
    option.label.toLowerCase().includes(mentionQuery.toLowerCase()),
  );
  const [isComposing, setIsComposing] = useState(false);

  // Function to adjust textarea height based on content
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to calculate the scrollHeight correctly
    textarea.style.height = 'auto';

    // Set new height (scrollHeight or max 260px)
    const newHeight = Math.min(textarea.scrollHeight, 260);
    textarea.style.height = `${newHeight}px`;
  };

  // Check for @ character and show popover, with special handling for @document
  const checkForMentionTrigger = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const cursorPosition = textarea.selectionEnd;
    const text = textarea.value;

    // Find the position of the '@' character before cursor
    const atIndex = text.lastIndexOf('@', cursorPosition - 1);

    // If @ exists and there's no space between @ and cursor
    if (
      atIndex !== -1 &&
      cursorPosition > atIndex &&
      !text.substring(atIndex, cursorPosition).includes(' ')
    ) {
      // Check if it's @document specifically
      const isDocumentMention = text.substring(atIndex, cursorPosition).startsWith('@document');

      // Extract the query after @ or @document for filtering
      const query = isDocumentMention
        ? text.substring(atIndex + 10, cursorPosition) // 10 = length of '@document'
        : text.substring(atIndex + 1, cursorPosition);

      setMentionQuery(query);
      setAtPosition(atIndex);
      setSelectedMentionIndex(0);
      setShowMentionPopover(true);
    } else {
      if (showMentionPopover) {
        setShowMentionPopover(false);
        setAtPosition(-1);
      }
    }
  }, [showMentionPopover]);

  // Insert mention at cursor position
  const insertMention = useCallback(
    (option: MentionOption) => {
      const textarea = textareaRef.current;
      if (!textarea || atPosition === -1) return;

      const cursorPosition = textarea.selectionEnd;
      const text = textarea.value;

      // Check if we're in a @document context
      const isDocumentMention = text.substring(atPosition, cursorPosition).startsWith('@document');

      let newText;
      if (isDocumentMention) {
        // Replace @document query with @document:filename
        const beforeDocument = text.substring(0, atPosition);
        const afterQuery = text.substring(cursorPosition);
        newText = `${beforeDocument}@document:${option.value} ${afterQuery}`;
      } else {
        // Regular mention replacement
        newText =
          text.substring(0, atPosition) + '@' + option.value + ' ' + text.substring(cursorPosition);
      }

      // Update both internal and parent state
      setInternalValue(newText);
      setMessage(newText);

      // Hide popover
      setShowMentionPopover(false);
      setAtPosition(-1);

      // Set cursor position after the inserted mention
      setTimeout(() => {
        if (textarea) {
          const newCursorPosition = isDocumentMention
            ? atPosition + 10 + option.value.length + 1 // @document:filename + space
            : atPosition + option.value.length + 2; // @filename + space
          textarea.focus();
          textarea.setSelectionRange(newCursorPosition, newCursorPosition);
          adjustTextareaHeight();
        }
      }, 0);
    },
    [atPosition, setMessage],
  );

  // Sync internal state with prop - this ensures one-way data flow
  useEffect(() => {
    setInternalValue(message || '');
  }, [message]);

  // Adjust height and forcefully sync textarea when message changes
  useLayoutEffect(() => {
    // When message is empty, force the textarea to be empty
    if (message === '' && textareaRef.current) {
      textareaRef.current.value = '';
      adjustTextareaHeight();
    }
  }, [message]);

  // Set focus when bot stops thinking
  useEffect(() => {
    // Check if the bot just finished thinking
    if (prevBotThinkingRef.current && !isBotThinking) {
      // Use setTimeout to ensure the focus happens after rendering
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 10);
    }

    // Update the previous value for the next render
    prevBotThinkingRef.current = isBotThinking;
  }, [isBotThinking]);

  // Handle click outside to close popover
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(event.target as Node) &&
        event.target !== textareaRef.current
      ) {
        setShowMentionPopover(false);
        setAtPosition(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Scroll selected item into view when selectedMentionIndex changes
  useEffect(() => {
    if (showMentionPopover && selectedItemRef.current && popoverRef.current) {
      selectedItemRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [selectedMentionIndex, showMentionPopover]);

  // Handle changes with both internal state and parent state
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    setInternalValue(newValue);
    setMessage(newValue);

    // Check for @ mentions when typing
    checkForMentionTrigger();
  };

  // Handle key press to detect @ symbol specifically
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === '@') {
      setTimeout(() => {
        checkForMentionTrigger();
      }, 0);
    }
  };

  // Handle cursor movement to check if we need to hide popover
  const handleSelect = () => {
    if (showMentionPopover && textareaRef.current) {
      const cursorPosition = textareaRef.current.selectionEnd;
      if (cursorPosition <= atPosition || cursorPosition > atPosition + mentionQuery.length + 1) {
        // Cursor moved away from the mention context
        setShowMentionPopover(false);
        setAtPosition(-1);
      }
    }
  };

  const defaultOnKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      const form = e.currentTarget.form;
      if (form) {
        form.requestSubmit();
      }
    }
  };

  // Handle keyboard navigation in mention popover
  const handleKeyNavigation = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Only process if popover is visible
    if (!showMentionPopover || filteredMentionOptions.length === 0) {
      defaultOnKeyDown(e); // Pass to parent handler
      return;
    }

    const totalOptions = filteredMentionOptions.length;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedMentionIndex((prevIndex) =>
          prevIndex < totalOptions - 1 ? prevIndex + 1 : prevIndex,
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedMentionIndex((prevIndex) => (prevIndex > 0 ? prevIndex - 1 : prevIndex));
        break;
      case 'Enter':
        e.preventDefault();
        insertMention(filteredMentionOptions[selectedMentionIndex]);
        break;
      case 'Escape':
        e.preventDefault();
        setShowMentionPopover(false);
        setAtPosition(-1);
        break;
      case 'Tab':
        e.preventDefault();
        insertMention(filteredMentionOptions[selectedMentionIndex]);
        break;
      default:
        defaultOnKeyDown(e); // Pass to parent handler
        break;
    }
  };

  return (
    <div className="relative" ref={containerRef}>
      <Textarea
        id={id}
        ref={textareaRef}
        autoFocus
        value={internalValue}
        onChange={handleChange}
        onInput={adjustTextareaHeight}
        onKeyPress={handleKeyPress}
        onSelect={handleSelect}
        className="flex p-0 w-full text-sm xl:text-base font-normal text-gray-900 bg-transparent dark:bg-gray-50 border-none outline-none placeholder:text-gray-400 min-h-[60px] scrollbar-hide overflow-y-auto resize-none focus-visible:ring-0 focus-visible:ring-offset-0"
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        onKeyDown={handleKeyNavigation}
        placeholder={placeholder}
        autoComplete="off"
        disabled={isBotThinking}
        rows={1}
        data-testid="chat-input"
      />

      {/* Mention Popover - Fixed Position */}
      {showMentionPopover && (
        <div
          ref={popoverRef}
          className="overflow-y-auto absolute z-50 py-3 w-80 max-h-60 rounded-md border border-gray-200 shadow-lg dark:border-gray-300 scrollbar-hide bg-background"
          style={{
            bottom: '100%', // Position above the textarea
            left: '0', // Start from the left edge
            marginBottom: '4px', // Give a bit of space
          }}
        >
          {/* Check if this is a @document mention */}
          {availableMentionOptions.length > 0 && availableMentionOptions[0]?.icon === '📄' ? (
            // Document mention popover
            <>
              <span className="px-4 text-sm text-gray-500">
                Available Documents ({filteredMentionOptions.length})
              </span>
              {filteredMentionOptions.length > 0 && (
                <ul className="py-1">
                  {filteredMentionOptions.map((doc, index) => (
                    <li
                      onClick={() => insertMention(doc)}
                      onMouseEnter={() => setSelectedMentionIndex(index)}
                      key={doc.id}
                      className={`p-4 flex gap-2 cursor-pointer hover:bg-brand-50 ${
                        index === selectedMentionIndex ? 'bg-brand-100' : ''
                      }`}
                      ref={index === selectedMentionIndex ? selectedItemRef : null}
                    >
                      <div className="flex gap-3 items-center">
                        <div className="size-8">
                          <FileIcon ext={doc.value?.split('.').pop()} />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-sm font-medium">{doc.label}</span>
                          <span className="text-xs text-gray-500">Click to select</span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              <div className="px-4 py-2 text-xs text-gray-400 border-t">
                Type @document:filename to query specific documents
              </div>
            </>
          ) : (
            // Regular mention popover (fallback)
            <>
              <span className="px-4 text-sm text-gray-500">
                In this chat ({filteredMentionOptions.length})
              </span>
              {filteredMentionOptions.length > 0 && (
                <ul className="py-1">
                  {filteredMentionOptions.map((file, index) => (
                    <li
                      onClick={() => insertMention(file)}
                      onMouseEnter={() => setSelectedMentionIndex(index)}
                      key={file.id}
                      className={`p-4 flex gap-2 cursor-pointer hover:bg-brand-50 ${
                        index === selectedMentionIndex ? 'bg-brand-100' : ''
                      }`}
                      ref={index === selectedMentionIndex ? selectedItemRef : null}
                    >
                      <div className="flex">
                        <FileIcon ext={file?.value?.split('.').pop()} />
                      </div>
                      {file.value}
                    </li>
                  ))}
                </ul>
              )}
              <span className="px-4 text-sm text-gray-500">
                Assigned Sources ({filteredMentionOptions.length})
              </span>
              {filteredMentionOptions.length > 0 && (
                <ul className="py-1">
                  {filteredMentionOptions.map((option, index) => (
                    <li
                      key={option.id}
                      ref={index === selectedMentionIndex ? selectedItemRef : null}
                      className={`p-4 flex gap-2 cursor-pointer hover:bg-gray-100 ${
                        index === selectedMentionIndex ? 'bg-brand-50' : ''
                      }`}
                      onClick={() => insertMention(option)}
                      onMouseEnter={() => setSelectedMentionIndex(index)}
                    >
                      {option.icon && <span className="text-gray-600">{option.icon}</span>}
                      <span className="font-medium">{option.label}</span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatInput;
