"use client";

import {useEffect, useState} from "react";
import {toast} from "sonner";

import {$fetch} from "@/lib/fetch";

import ApiKeyForm, {APIKeysState} from "./components/ApiKeyForm";
import ChatInterface from "./components/ChatInterface";

export default function Home() {
  const [apiKeys, setAPIKeys] = useState<APIKeysState>();
  async function fetchAPIKeys() {
    const {data, error} = await $fetch<APIKeysState>("/has-keys");
    if (error?.message) {
      toast.error(error.message);
    }
    setAPIKeys(data!);
  }
  useEffect(() => {
    fetchAPIKeys();
  }, []);
  if (!apiKeys) return <div>Loading...</div>;
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-24">
      {apiKeys.missing?.length ? (
        <ApiKeyForm onSubmit={fetchAPIKeys} apiKeys={apiKeys} />
      ) : (
        <ChatInterface />
      )}
    </main>
  );
}
