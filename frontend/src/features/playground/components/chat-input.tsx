import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, StopCircle } from 'lucide-react';
import { useState, type KeyboardEvent } from 'react';

// Updated ChatInputProps
interface ChatInputProps {
  onSubmit: (inputValue: string, effort: string, model: string) => void;
  onCancel: () => void;
  isLoading: boolean;
  hasHistory: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSubmit,
  onCancel,
  isLoading,
  hasHistory
}) => {
  const [internalInputValue, setInternalInputValue] = useState("");
  const [effort, setEffort] = useState("low");
  const [model, setModel] = useState("ark-code-latest");

  const handleInternalSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!internalInputValue.trim()) return;
    onSubmit(internalInputValue, effort, model);
    setInternalInputValue("");
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit with Ctrl+Enter (Windows/Linux) or Cmd+Enter (Mac)
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleInternalSubmit();
    }
  };

  const isSubmitDisabled = !internalInputValue.trim() || isLoading;

  return (
    <form
      onSubmit={handleInternalSubmit}
      className={`flex flex-col gap-2 p-3 pb-4`}>
      <div
        className={`flex flex-row items-center justify-between rounded-3xl rounded-bl-sm ${hasHistory ? "rounded-br-sm" : ""
          } wrap-break-word min-h-7 bg-muted px-4 pt-3`}
      >
        <Textarea
          value={internalInputValue}
          onChange={(e) => setInternalInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Bubble Sort algorithm in Python"
          style={{ background: "none" }}
          className={`w-full text-foreground placeholder:text-muted-foreground resize-none border-0 focus:outline-none focus:ring-0 outline-none focus-visible:ring-0 shadow-none 
                        md:text-base min-h-14 max-h-50`}
          rows={1}
        />
        <div className="-mt-3">
          {isLoading ? (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-red-500 hover:text-red-400 hover:bg-red-500/10 p-2 cursor-pointer rounded-full transition-all duration-200"
              onClick={onCancel}>
              <StopCircle className="h-5 w-5" />
            </Button>
          ) : (
            <Button
              type="submit"
              variant="ghost"
              className={`${isSubmitDisabled
                ? "text-muted-foreground"
                : "text-primary hover:text-primary/80 hover:bg-primary/10"
                } p-2 cursor-pointer rounded-full transition-all duration-200  text-base`}
              disabled={isSubmitDisabled}
            >
              Search
              <Send className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
    </form>
  )
}
