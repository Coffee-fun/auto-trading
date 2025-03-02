"use client";

import {useEffect, useRef, useState} from "react";
import Markdown from "react-markdown";

import {Button} from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {Input} from "@/components/ui/input";
import {ScrollArea} from "@/components/ui/scroll-area";
import {$fetch, handleError} from "@/lib/fetch";

import SessionModal from "./SessionModal";

type ApiKeys = {
  BIRDEYE_API_KEY: string;
  ANTHROPIC_KEY: string;
  SOLANA_PRIVATE_KEY: string;
};

type Message = {
  role: "user" | "assistant";
  message: string;
  time: string;
};

export default function ChatInterface() {
  const [sessions, setSessions] = useState<string[]>([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isTrading, setIsTrading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const fetchSessions = async () => {
    // Replace with actual API call
    const {data, error} = await $fetch<{runs: string[]}>("/runs");
    if (handleError(error)) return;
    console.log(data);
    if (data && data.runs && data.runs.length! > 0) {
      setSessions(data?.runs);
    }
    return data?.runs;
  };

  useEffect(() => {
    // Fetch sessions from the backend

    fetchSessions().then((resp) => {
      if (resp) {
        setCurrentSession(resp[resp.length - 1]);
      }
    });
  }, []);

  const fetchLogs = async (currSess?: string) => {
    // Fetch latest updates from the backend
    if (!(currSess ?? currentSession)) return;
    const {data, error} = await $fetch<{
      logs: Message[];
      status: string;
    }>(`/runs/${currSess ?? currentSession}/logs`);
    if (handleError(error)) return;
    console.log(data);
    if (data?.status !== "trading") setIsTrading(false);
    if (data) setMessages(data.logs);
  };
  useEffect(() => {
    if (currentSession) {
      fetchLogs();
      const intervalId = setInterval(fetchLogs, 5000);
      return () => clearInterval(intervalId);
    }
  }, [currentSession]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleCreateSession = async () => {
    // Replace with actual API call
    const {data, error} = await $fetch<{run_id: string}>("/create_new_run");
    if (handleError(error)) return;
    if (data) {
      setSessions((prev) => [...(prev || []), data?.run_id]);
      setCurrentSession(data.run_id);
    }
  };

  const handleSelectSession = (sessionId: string) => {
    setCurrentSession(sessionId);
  };

  const handleSendMessage = async () => {
    if (inputMessage.trim() && currentSession) {
      // Replace with actual API call
      const {error} = await $fetch(`/user_feedback?session=${currentSession}`, {
        body: {feedback: inputMessage},
      });

      setInputMessage("");
      handleError(error);
    }
  };

  const handleStartTrading = async () => {
    // Replace with actual API call to start trading
    const {error, data} = await $fetch("/run_cycle", {
      body: {run_id: currentSession},
    });

    if (handleError(error)) return;
    setIsTrading(true);
  };

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle className="flex justify-between items-center">
          <span>Autotrader Chat</span>
          <SessionModal
            sessions={sessions}
            currentSession={currentSession}
            onSelectSession={handleSelectSession}
            onCreateSession={handleCreateSession}
          />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <ScrollArea
          className="h-[400px] p-4 rounded-md border"
          ref={scrollAreaRef}
        >
          {messages.map((message, i) => (
            <div
              key={i}
              style={{wordBreak: "break-word"}}
              className={`mb-4 break-words ${
                message.role === "user" ? "text-right" : "text-left"
              }`}
            >
              <div
                className={`inline-block p-2 rounded-lg max-w-[50%] ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground"
                }`}
              >
                <Markdown>
                  {(Array.isArray(message.message)
                    ? message.message.join("\n\n")
                    : message.message
                  ).trim()}
                </Markdown>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {new Date(message.time).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </ScrollArea>
        <Button
          onClick={handleStartTrading}
          disabled={!currentSession || isTrading}
          className="w-full"
        >
          {isTrading ? "Trading in Progress" : "Start Trading"}
        </Button>
        <div className="flex space-x-2">
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-grow"
            disabled={!currentSession}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                handleSendMessage();
              }
            }}
          />
          <Button disabled={!currentSession} onClick={handleSendMessage}>
            Send
          </Button>
        </div>
      </CardContent>
      <CardFooter></CardFooter>
    </Card>
  );
}
