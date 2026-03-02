import { useState, useCallback, useRef } from 'react';
import { streamChat } from '@/lib/api';

interface UseStreamingChatOptions {
  sessionId?: string;
  onComplete?: (streamId: number) => void;
  onError?: (error: Error, streamId: number) => void;
}

export function useStreamingChat({ sessionId, onComplete, onError }: UseStreamingChatOptions = {}) {
  const [content, setContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const streamIdRef = useRef(0);

  const send = useCallback(
    async (message: string, images?: string[]) => {
      const streamId = ++streamIdRef.current;
      setIsStreaming(true);
      setContent('');
      abortRef.current = new AbortController();

      try {
        for await (const event of streamChat(message, sessionId, images, abortRef.current.signal)) {
          // Check if this stream was canceled
          if (streamId !== streamIdRef.current) {
            return;
          }
          
          if (event.type === 'assistant_delta') {
            setContent((prev) => prev + event.data.content);
          } else if (event.type === 'done') {
            break;
          } else if (event.type === 'error') {
            onError?.(new Error(event.data.message), streamId);
          }
        }
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          return;
        }
        onError?.(err as Error, streamId);
        throw err;
      } finally {
        if (streamId === streamIdRef.current) {
          setIsStreaming(false);
          abortRef.current = null;
          onComplete?.(streamId);
        }
      }
    },
    [sessionId, onComplete, onError]
  );

  const cancel = useCallback(() => {
    streamIdRef.current++;  // Increment to invalidate any late chunks
    abortRef.current?.abort();
  }, []);

  return { content, isStreaming, send, cancel };
}
