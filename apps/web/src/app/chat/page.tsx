"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ProtectedLayout } from "@/components/layout/protected-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Send, Bot, User, Sparkles } from "lucide-react";

type ChatMessage = {
  role: string;
  content: string;
};

export default function ChatPage() {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");
  const [conversation, setConversation] = useState<ChatMessage[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const chatMutation = useMutation({
    mutationFn: async (data: { message: string; conversation_history: ChatMessage[] }) =>
      (await api.post("/chat", data)).data,
    onSuccess: (response) => {
      setConversation(response.conversation_history);
      setMessage("");
      setIsSubmitting(false);
    },
    onError: () => {
      setIsSubmitting(false);
    },
  });

  const summaryMutation = useMutation({
    mutationFn: async (period: string) =>
      (await api.post("/chat/summary", { period })).data,
    onSuccess: (data) => {
      setConversation((prev) => [
        ...prev,
        { role: "assistant", content: data.summary },
      ]);
    },
  });

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isSubmitting) return;

    setIsSubmitting(true);

    chatMutation.mutate({
      message,
      conversation_history: conversation,
    });
    setMessage("");
  };

  const handleQuickSummary = (period: string) => {
    const userMessage = period === "week" ? "Show me the weekly summary" : "Show me the monthly summary";
    setConversation((prev) => [
      ...prev,
      { role: "user", content: userMessage },
    ]);
    summaryMutation.mutate(period);
  };

  return (
    <ProtectedLayout>
      <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">AI Financial Assistant</h1>
            <p className="text-muted-foreground">Ask questions about your finances, get insights, and summaries</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickSummary("week")}
              disabled={summaryMutation.isPending}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Weekly Summary
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickSummary("month")}
              disabled={summaryMutation.isPending}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Monthly Summary
            </Button>
          </div>
        </div>

        <Card className="flex-1 flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              Conversation
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col space-y-4 overflow-hidden">
            <div className="flex-1 overflow-y-auto space-y-4 pr-4">
              {conversation.length === 0 ? (
                <div className="text-center text-muted-foreground py-12">
                  <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">Start a conversation</p>
                  <p className="text-sm">Ask about your spending, budgets, or get a summary</p>
                  <div className="mt-4 flex flex-wrap justify-center gap-2">
                    <Badge variant="outline" className="cursor-pointer" onClick={() => setMessage("How much did I spend this month?")}>
                      How much did I spend this month?
                    </Badge>
                    <Badge variant="outline" className="cursor-pointer" onClick={() => setMessage("What are my top spending categories?")}>
                      Top spending categories
                    </Badge>
                    <Badge variant="outline" className="cursor-pointer" onClick={() => setMessage("How am I doing on my budgets?")}>
                      Budget progress
                    </Badge>
                  </div>
                </div>
              ) : (
                conversation.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {msg.role === "assistant" && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-4 w-4" />
                      </div>
                    )}
                    <div
                      className={`max-w-[70%] rounded-lg px-4 py-2 ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                    {msg.role === "user" && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                        <User className="h-4 w-4 text-primary-foreground" />
                      </div>
                    )}
                  </div>
                ))
              )}
              {(chatMutation.isPending || summaryMutation.isPending) && (
                <div className="flex gap-3 justify-start">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-4 w-4 animate-pulse" />
                  </div>
                  <div className="bg-muted rounded-lg px-4 py-2">
                    <p className="text-sm text-muted-foreground">Thinking...</p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} className="flex gap-2 mt-4">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask about your finances..."
                disabled={chatMutation.isPending || isSubmitting}
              />
              <Button type="submit" disabled={chatMutation.isPending || isSubmitting || !message.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </ProtectedLayout>
  );
}
