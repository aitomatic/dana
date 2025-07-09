import { useState, useCallback, useMemo, memo } from "react";
import { cn } from "@/lib/utils";

import ChatInput from "./chat-input";
import SendButton from "./send-button";

// Create separate, memoized components
const MemoizedChatInput = memo(ChatInput);

const ChatBox = ({ handleSendMessage, placeholder, files, id }: any) => {
  const [message, setMessage] = useState<string | null>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const onSubmit = useCallback(() => {
    if (isSubmitting || !message?.trim()) return;
    setIsSubmitting(true);
    const messageToSend = message?.trim();
    setMessage("");
    requestAnimationFrame(() => {
      handleSendMessage({
        message: messageToSend,
        role: "user",
      });
      setMessage("");
      setTimeout(() => {
        setIsSubmitting(false);
      }, 100);
    });
  }, [handleSendMessage, message, isSubmitting]);

  const viewType = useMemo(() => {
    return "input";
  }, []);

  const MemoizedSendButton = useMemo(
    () => (
      <SendButton
        message={message}
        files={files}
        onSubmit={onSubmit}
        isSubmitting={isSubmitting}
      />
    ),
    [message, files, onSubmit, isSubmitting],
  );

  // Memoized controls area - doesn't rerender when message changes except for the SendButton
  const ControlsArea = useMemo(
    () => (
      <div className={cn("flex items-end w-full h-10 gap-2 justify-between")}>
        <div className={cn("flex items-center gap-4")}>
          {MemoizedSendButton}
        </div>
      </div>
    ),
    [MemoizedSendButton],
  );

  return (
    <form
      className="bottom-0 left-0 right-0 flex w-full border border-gray-200 dark:border-gray-100 rounded-xl"
      onSubmit={(e) => {
        e.preventDefault();
        if (!isSubmitting) {
          onSubmit();
        }
      }}
      style={{
        boxShadow:
          "0px 20px 24px -4px rgba(16, 24, 40, 0.04), 0px 8px 8px -4px rgba(16, 24, 40, 0.03)",
      }}
    >
      {viewType === "input" && (
        <div className="flex flex-col w-full gap-2 p-3 bg-background dark:bg-gray-50 rounded-xl">
          <div className="flex flex-col">
            <MemoizedChatInput
              id={id}
              message={message}
              setMessage={setMessage}
              placeholder={placeholder}
              isBotThinking={false}
            />
          </div>
          {ControlsArea}
        </div>
      )}
    </form>
  );
};

export default ChatBox;
