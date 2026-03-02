'use client';

import { useState, useRef, useEffect } from 'react';
import { useStreamingChat } from '@/hooks/useStreamingChat';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { ChatInput } from '@/components/chat/ChatInput';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import type { ChatMessage as ChatMessageType } from '@/types/api';

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const streamIdRef = useRef(0);

  const handleComplete = (completedStreamId: number) => {
    if (completedStreamId !== streamIdRef.current) {
      return;
    }
    if (streamingContent) {
      setMessages((prev) => [
        ...prev,
        {
          msg_id: crypto.randomUUID(),
          session_id: '',
          role: 'assistant',
          content: streamingContent,
          timestamp: new Date().toISOString(),
        },
      ]);
      setStreamingContent('');
    }
  };

  const { content, isStreaming, send, cancel } = useStreamingChat({
    onComplete: handleComplete,
  });

  useEffect(() => {
    setStreamingContent(content);
  }, [content]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

  const handleSend = async (message: string) => {
    const userMessage: ChatMessageType = {
      msg_id: crypto.randomUUID(),
      session_id: '',
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    await send(message);
  };

  return (
    <div className="flex flex-col h-screen">
      <header className="border-b p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Chat</h1>
          {isStreaming && (
            <Button variant="outline" size="sm" onClick={cancel}>
              Cancel
            </Button>
          )}
        </div>
      </header>

      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {messages.map((msg) => (
          <ChatMessage key={msg.msg_id} message={msg} />
        ))}
        {streamingContent && (
          <ChatMessage
            message={{
              msg_id: 'streaming',
              session_id: '',
              role: 'assistant',
              content: streamingContent,
              timestamp: new Date().toISOString(),
            }}
          />
        )}
        {isStreaming && !streamingContent && (
          <div className="text-muted-foreground text-sm">Thinking...</div>
        )}
      </ScrollArea>

      <div className="border-t p-4">
        <ChatInput onSend={handleSend} disabled={isStreaming} />
      </div>
    </div>
  );
}
