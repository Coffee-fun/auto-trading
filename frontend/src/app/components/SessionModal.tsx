"use client";

import {useState} from "react";

import {Button} from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {ScrollArea} from "@/components/ui/scroll-area";

type SessionModalProps = {
  sessions: string[];
  currentSession: string | null;
  onSelectSession: (session: string) => void;
  onCreateSession: () => void;
};

export default function SessionModal({
  sessions,
  currentSession,
  onSelectSession,
  onCreateSession,
}: SessionModalProps) {
  const [open, setOpen] = useState(false);

  const handleSelectSession = (session: string) => {
    onSelectSession(session);
    setOpen(false);
  };

  const handleCreateSession = () => {
    onCreateSession();
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          {currentSession ? <pre>Session {currentSession}</pre> : "Select Session"}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Select or Create Session</DialogTitle>
          <DialogDescription>
            Choose an existing session or create a new one to start trading.
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="mt-4 max-h-[300px] pr-4">
          {sessions.map((session) => (
            <Button
              key={session}
              variant={currentSession === session ? "secondary" : "ghost"}
              className="w-full justify-start mb-2"
              onClick={() => handleSelectSession(session)}
            >
              {session}
            </Button>
          ))}
        </ScrollArea>
        <Button onClick={handleCreateSession} className="w-full mt-4">
          Create New Session
        </Button>
      </DialogContent>
    </Dialog>
  );
}
